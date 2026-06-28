import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Compliance Risk Agent", version="1.0.0")

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "crisisprocure.db"
POLICY_PATH = Path(__file__).with_name("policy_pack.json")
POLICY_HISTORY_DIR = POLICY_PATH.parent / "policy_history"

DEFAULT_POLICY = {
    "policy_version": "fallback-core-v1",
    "thresholds": {
        "discount_soft_limit": 20.0,
        "price_variance_limit": 0.15,
        "supervisor_review": 0.3,
        "human_review": 0.6,
    },
    "weights": {
        "discount_violation": 0.35,
        "new_profile": 0.2,
        "price_variance": 0.2,
        "critical_category_boost": 0.15,
    },
    "critical_categories": ["medical", "utilities", "safety", "food"],
}


def _load_policy() -> Dict:
    if not POLICY_PATH.exists():
        return DEFAULT_POLICY
    with POLICY_PATH.open("r", encoding="utf-8") as f:
        policy = json.load(f)
    return policy


def _snapshot_policy(policy: Dict, reason: str) -> str:
    POLICY_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{ts}-{reason}.json"
    snapshot_path = POLICY_HISTORY_DIR / filename
    with snapshot_path.open("w", encoding="utf-8") as f:
        json.dump(policy, f, indent=2)
    return filename


def _validate_policy(policy: Dict) -> tuple[bool, List[str]]:
    errors: List[str] = []
    required_sections = ["policy_version", "thresholds", "weights", "critical_categories"]
    for section in required_sections:
        if section not in policy:
            errors.append(f"Missing section: {section}")

    thresholds = policy.get("thresholds", {})
    weights = policy.get("weights", {})

    for key in ["discount_soft_limit", "price_variance_limit", "supervisor_review", "human_review"]:
        if key not in thresholds:
            errors.append(f"Missing threshold: {key}")

    for key in ["discount_violation", "new_profile", "price_variance", "critical_category_boost"]:
        if key not in weights:
            errors.append(f"Missing weight: {key}")

    if "supervisor_review" in thresholds and "human_review" in thresholds:
        if thresholds["supervisor_review"] > thresholds["human_review"]:
            errors.append("supervisor_review must be <= human_review")

    return len(errors) == 0, errors


POLICY = _load_policy()
POLICY_VALID, POLICY_ERRORS = _validate_policy(POLICY)

METRICS = {
    "evaluations_total": 0,
    "auto_approve": 0,
    "supervisor_review": 0,
    "human_review": 0,
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                order_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                risk_score REAL NOT NULL,
                confidence REAL NOT NULL,
                policy_version TEXT NOT NULL,
                triggered_rules TEXT NOT NULL,
                reasons TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _persist_run(
    *,
    created_at: str,
    correlation_id: str,
    order_id: str,
    decision: str,
    risk_score: float,
    confidence: float,
    policy_version: str,
    triggered_rules: List[str],
    reasons: List[str],
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO risk_runs (
                created_at, correlation_id, order_id, decision, risk_score,
                confidence, policy_version, triggered_rules, reasons
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                correlation_id,
                order_id,
                decision,
                risk_score,
                confidence,
                policy_version,
                json.dumps(triggered_rules),
                json.dumps(reasons),
            ),
        )
        conn.commit()


_init_db()


class LineItem(BaseModel):
    sku: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    expected_price: float = Field(ge=0)


class ExceptionRequest(BaseModel):
    order_id: str
    customer_tier: str
    discount_percent: float = Field(ge=0, le=100)
    category: str = "general"
    correlation_id: Optional[str] = None
    line_items: List[LineItem]


class ExceptionResponse(BaseModel):
    correlation_id: str
    evaluated_at: str
    order_id: str
    risk_score: float
    confidence: float
    decision: str
    requires_human_approval: bool
    policy_version: str
    triggered_rules: List[str]
    recommended_next_step: str
    reasons: List[str]


class PolicyPayload(BaseModel):
    policy: Dict[str, Any]


class RollbackPayload(BaseModel):
    snapshot_file: Optional[str] = None


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "compliance-risk-agent",
        "policy_valid": POLICY_VALID,
        "policy_errors": POLICY_ERRORS,
    }


@app.get("/policy")
def get_policy() -> dict:
    return POLICY


@app.post("/policy/validate")
def validate_policy(payload: PolicyPayload) -> dict:
    valid, errors = _validate_policy(payload.policy)
    return {
        "valid": valid,
        "errors": errors,
        "policy_version": payload.policy.get("policy_version", "unknown"),
    }


@app.post("/policy/apply")
def apply_policy(payload: PolicyPayload) -> dict:
    global POLICY, POLICY_VALID, POLICY_ERRORS

    valid, errors = _validate_policy(payload.policy)
    if not valid:
        return {"applied": False, "valid": False, "errors": errors}

    _snapshot_policy(POLICY, "before-apply")

    with POLICY_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload.policy, f, indent=2)

    POLICY = payload.policy
    POLICY_VALID, POLICY_ERRORS = valid, []
    return {
        "applied": True,
        "valid": True,
        "policy_version": POLICY.get("policy_version", "unknown"),
    }


@app.get("/policy/history")
def get_policy_history() -> dict:
    POLICY_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    snapshots = sorted([p.name for p in POLICY_HISTORY_DIR.glob("*.json")], reverse=True)
    return {"snapshots": snapshots}


@app.post("/policy/rollback")
def rollback_policy(payload: RollbackPayload) -> dict:
    global POLICY, POLICY_VALID, POLICY_ERRORS

    POLICY_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    snapshots = sorted([p for p in POLICY_HISTORY_DIR.glob("*.json")], reverse=True)
    if not snapshots:
        return {"rolled_back": False, "error": "No policy snapshots available"}

    if payload.snapshot_file:
        target = POLICY_HISTORY_DIR / payload.snapshot_file
        if not target.exists():
            return {"rolled_back": False, "error": "Snapshot file not found"}
    else:
        target = snapshots[0]

    with target.open("r", encoding="utf-8") as f:
        candidate = json.load(f)

    valid, errors = _validate_policy(candidate)
    if not valid:
        return {"rolled_back": False, "error": "Snapshot policy invalid", "details": errors}

    _snapshot_policy(POLICY, "before-rollback")
    with POLICY_PATH.open("w", encoding="utf-8") as f:
        json.dump(candidate, f, indent=2)

    POLICY = candidate
    POLICY_VALID, POLICY_ERRORS = True, []

    return {
        "rolled_back": True,
        "policy_version": POLICY.get("policy_version", "unknown"),
        "from_snapshot": target.name,
    }


@app.get("/metrics")
def get_metrics() -> dict:
    return {
        "service": "compliance-risk-agent",
        "policy_version": POLICY.get("policy_version", "unknown"),
        "metrics": METRICS,
    }


@app.get("/history")
def get_history(limit: int = 30) -> dict:
    bounded_limit = min(max(limit, 1), 200)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            SELECT created_at, correlation_id, order_id, decision, risk_score,
                   confidence, policy_version, triggered_rules, reasons
            FROM risk_runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (bounded_limit,),
        )
        rows = cursor.fetchall()

    timeline = [
        {
            "created_at": row[0],
            "correlation_id": row[1],
            "order_id": row[2],
            "decision": row[3],
            "risk_score": row[4],
            "confidence": row[5],
            "policy_version": row[6],
            "triggered_rules": json.loads(row[7]),
            "reasons": json.loads(row[8]),
        }
        for row in rows
    ]

    return {"service": "compliance-risk-agent", "timeline": timeline}


@app.post("/evaluate", response_model=ExceptionResponse)
def evaluate(req: ExceptionRequest) -> ExceptionResponse:
    correlation_id = req.correlation_id or f"corr-{uuid4()}"
    evaluated_at = datetime.now(timezone.utc).isoformat()
    reasons: List[str] = []
    triggered_rules: List[str] = []
    score = 0.0
    thresholds = POLICY["thresholds"]
    weights = POLICY["weights"]
    critical_categories = {c.lower() for c in POLICY.get("critical_categories", [])}

    if req.discount_percent > thresholds["discount_soft_limit"]:
        score += weights["discount_violation"]
        triggered_rules.append("discount_soft_limit")
        reasons.append("Requested discount exceeds policy soft limit (20%).")

    if req.customer_tier.lower() == "new":
        score += weights["new_profile"]
        triggered_rules.append("new_profile")
        reasons.append("New supplier or requester profile requires stricter review.")

    if req.category.lower() in critical_categories:
        score += weights["critical_category_boost"]
        triggered_rules.append("critical_category")
        reasons.append("Critical category request receives added governance weighting.")

    for item in req.line_items:
        if item.expected_price == 0:
            continue
        variance = abs(item.unit_price - item.expected_price) / item.expected_price
        if variance > thresholds["price_variance_limit"]:
            score += weights["price_variance"]
            triggered_rules.append(f"price_variance:{item.sku}")
            reasons.append(f"SKU {item.sku} has >15% price variance.")

    score = min(score, 1.0)

    if score >= thresholds["human_review"]:
        decision = "human_review"
    elif score >= thresholds["supervisor_review"]:
        decision = "supervisor_review"
    else:
        decision = "auto_approve"
        if not reasons:
            reasons.append("No significant anomalies found.")

    if decision == "human_review":
        confidence = min(0.96, 0.62 + (0.08 * len(triggered_rules)))
        recommended_next_step = "Route to procurement lead for explicit approval."
    elif decision == "supervisor_review":
        confidence = min(0.9, 0.56 + (0.07 * len(triggered_rules)))
        recommended_next_step = "Route to supervisor queue with policy checklist."
    else:
        confidence = min(0.88, 0.52 + (0.05 * len(triggered_rules)))
        recommended_next_step = "Proceed with automated procurement path."

    METRICS["evaluations_total"] += 1
    METRICS[decision] += 1

    _persist_run(
        created_at=evaluated_at,
        correlation_id=correlation_id,
        order_id=req.order_id,
        decision=decision,
        risk_score=round(score, 2),
        confidence=round(confidence, 2),
        policy_version=POLICY.get("policy_version", "unknown"),
        triggered_rules=triggered_rules,
        reasons=reasons,
    )

    return ExceptionResponse(
        correlation_id=correlation_id,
        evaluated_at=evaluated_at,
        order_id=req.order_id,
        risk_score=round(score, 2),
        confidence=round(confidence, 2),
        decision=decision,
        requires_human_approval=decision == "human_review",
        policy_version=POLICY.get("policy_version", "unknown"),
        triggered_rules=triggered_rules,
        recommended_next_step=recommended_next_step,
        reasons=reasons,
    )
