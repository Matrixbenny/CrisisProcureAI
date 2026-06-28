import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Prioritization Agent", version="1.0.0")

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "crisisprocure.db"
POLICY_PATH = Path(__file__).with_name("policy_pack.json")

DEFAULT_POLICY = {
    "policy_version": "fallback-priority-v1",
    "weights": {
        "stockout_critical": 0.55,
        "stockout_near_term": 0.35,
        "compliance_blocked": 0.6,
        "high_amount": 0.15,
        "vulnerability_boost": 0.2,
    },
    "thresholds": {
        "critical_hours": 6,
        "near_term_hours": 24,
        "high_amount": 25000,
        "high_priority": 0.75,
        "medium_priority": 0.45,
    },
}


def _load_policy() -> Dict:
    if not POLICY_PATH.exists():
        return DEFAULT_POLICY
    with POLICY_PATH.open("r", encoding="utf-8") as f:
        policy = json.load(f)
    return policy


def _validate_policy(policy: Dict) -> tuple[bool, List[str]]:
    errors: List[str] = []
    required_sections = ["policy_version", "thresholds", "weights"]
    for section in required_sections:
        if section not in policy:
            errors.append(f"Missing section: {section}")

    thresholds = policy.get("thresholds", {})
    weights = policy.get("weights", {})

    for key in ["critical_hours", "near_term_hours", "high_amount", "high_priority", "medium_priority"]:
        if key not in thresholds:
            errors.append(f"Missing threshold: {key}")

    for key in ["stockout_critical", "stockout_near_term", "compliance_blocked", "high_amount", "vulnerability_boost"]:
        if key not in weights:
            errors.append(f"Missing weight: {key}")

    if "medium_priority" in thresholds and "high_priority" in thresholds:
        if thresholds["medium_priority"] > thresholds["high_priority"]:
            errors.append("medium_priority must be <= high_priority")

    return len(errors) == 0, errors


POLICY = _load_policy()
POLICY_VALID, POLICY_ERRORS = _validate_policy(POLICY)

METRICS = {
    "prioritizations_total": 0,
    "items_processed": 0,
    "high": 0,
    "medium": 0,
    "low": 0,
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
            CREATE TABLE IF NOT EXISTS prioritization_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                item_count INTEGER NOT NULL,
                high_count INTEGER NOT NULL,
                medium_count INTEGER NOT NULL,
                low_count INTEGER NOT NULL,
                fairness_report TEXT NOT NULL,
                action_items TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _persist_prioritization(
    *,
    created_at: str,
    correlation_id: str,
    policy_version: str,
    action_items: List[Dict[str, Any]],
    fairness_report: Dict[str, Any],
) -> None:
    high_count = sum(1 for item in action_items if item["priority"] == "high")
    medium_count = sum(1 for item in action_items if item["priority"] == "medium")
    low_count = sum(1 for item in action_items if item["priority"] == "low")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO prioritization_runs (
                created_at, correlation_id, policy_version, item_count,
                high_count, medium_count, low_count, fairness_report, action_items
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                correlation_id,
                policy_version,
                len(action_items),
                high_count,
                medium_count,
                low_count,
                json.dumps(fairness_report),
                json.dumps(action_items),
            ),
        )
        conn.commit()


def _compute_fairness(req_items: List["Requisition"], action_items: List["ActionItem"]) -> Dict[str, Any]:
    bucket: Dict[str, List[float]] = {}
    score_by_id = {a.requisition_id: a.priority_score for a in action_items}

    for item in req_items:
        dept = item.requester_department.strip() or "unknown"
        bucket.setdefault(dept, []).append(score_by_id.get(item.requisition_id, 0.0))

    departments = {dept: round(sum(scores) / len(scores), 3) for dept, scores in bucket.items()}

    if departments:
        max_avg = max(departments.values())
        min_avg = min(departments.values())
    else:
        max_avg = 0.0
        min_avg = 0.0

    disparity = round(max_avg - min_avg, 3)
    flagged = disparity > 0.45
    notes = (
        "Potential prioritization disparity detected; review policy weights and routing."
        if flagged
        else "No major prioritization disparity detected across departments in this batch."
    )

    return {
        "departments": departments,
        "max_avg_score": max_avg,
        "min_avg_score": min_avg,
        "disparity_index": disparity,
        "flagged": flagged,
        "notes": notes,
    }


def _prioritize_with_policy(req_items: List["Requisition"], policy: Dict[str, Any]) -> List["ActionItem"]:
    thresholds = policy["thresholds"]
    weights = policy["weights"]
    actions: List[ActionItem] = []

    for req_item in req_items:
        score = 0.0
        triggered_rules: List[str] = []

        if req_item.compliance_blocked:
            score += weights["compliance_blocked"]
            triggered_rules.append("compliance_blocked")

        if req_item.hours_to_stockout <= thresholds["critical_hours"]:
            score += weights["stockout_critical"]
            triggered_rules.append("stockout_critical")
        elif req_item.hours_to_stockout <= thresholds["near_term_hours"]:
            score += weights["stockout_near_term"]
            triggered_rules.append("stockout_near_term")

        if req_item.amount >= thresholds["high_amount"]:
            score += weights["high_amount"]
            triggered_rules.append("high_amount")

        if req_item.vulnerability_index > 0:
            score += req_item.vulnerability_index * weights["vulnerability_boost"]
            triggered_rules.append("vulnerability_boost")

        score = min(score, 1.0)

        if score >= thresholds["high_priority"]:
            priority = "high"
            recommended_action = "Escalate immediate sourcing and procurement lead visibility"
            rationale = "High composite urgency score from policy-weighted signals."
        elif score >= thresholds["medium_priority"]:
            priority = "medium"
            recommended_action = "Fast-track quote comparison and approval path"
            rationale = "Moderate urgency score requires accelerated handling."
        else:
            priority = "low"
            recommended_action = "Process in standard emergency queue"
            rationale = "Current risk and urgency score allows standard handling."

        actions.append(
            ActionItem(
                requisition_id=req_item.requisition_id,
                priority_score=round(score, 2),
                priority=priority,
                policy_version=policy.get("policy_version", "unknown"),
                recommended_action=recommended_action,
                triggered_rules=triggered_rules,
                rationale=rationale,
            )
        )

    actions.sort(key=lambda a: {"high": 0, "medium": 1, "low": 2}[a.priority])
    return actions


_init_db()


class Requisition(BaseModel):
    requisition_id: str
    requester_department: str
    amount: float = Field(gt=0)
    hours_to_stockout: int = Field(ge=0)
    vulnerability_index: float = Field(default=0.0, ge=0.0, le=1.0)
    compliance_blocked: bool = False


class CollectionsRequest(BaseModel):
    correlation_id: Optional[str] = None
    requisitions: List[Requisition]


class FairnessReport(BaseModel):
    departments: Dict[str, float]
    max_avg_score: float
    min_avg_score: float
    disparity_index: float
    flagged: bool
    notes: str


class ActionItem(BaseModel):
    requisition_id: str
    priority_score: float
    priority: str
    policy_version: str
    recommended_action: str
    triggered_rules: List[str]
    rationale: str


class CollectionsResponse(BaseModel):
    correlation_id: str
    prioritized_at: str
    simulation_mode: bool = False
    action_items: List[ActionItem]
    fairness_report: FairnessReport


class PolicyPayload(BaseModel):
    policy: Dict[str, Any]


class ComparePoliciesRequest(BaseModel):
    requisitions: List[Requisition]
    policy_a: Dict[str, Any]
    policy_b: Dict[str, Any]


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "prioritization-agent",
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

    with POLICY_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload.policy, f, indent=2)

    POLICY = payload.policy
    POLICY_VALID, POLICY_ERRORS = valid, []
    return {
        "applied": True,
        "valid": True,
        "policy_version": POLICY.get("policy_version", "unknown"),
    }


@app.get("/metrics")
def get_metrics() -> dict:
    return {
        "service": "prioritization-agent",
        "policy_version": POLICY.get("policy_version", "unknown"),
        "metrics": METRICS,
    }


@app.get("/history")
def get_history(limit: int = 30) -> dict:
    bounded_limit = min(max(limit, 1), 200)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            SELECT created_at, correlation_id, policy_version, item_count,
                   high_count, medium_count, low_count, fairness_report
            FROM prioritization_runs
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
            "policy_version": row[2],
            "item_count": row[3],
            "high_count": row[4],
            "medium_count": row[5],
            "low_count": row[6],
            "fairness_report": json.loads(row[7]),
        }
        for row in rows
    ]

    return {"service": "prioritization-agent", "timeline": timeline}


@app.post("/prioritize", response_model=CollectionsResponse)
def prioritize(req: CollectionsRequest) -> CollectionsResponse:
    correlation_id = req.correlation_id or f"corr-{uuid4()}"
    prioritized_at = datetime.now(timezone.utc).isoformat()
    actions = _prioritize_with_policy(req.requisitions, POLICY)
    fairness_report = _compute_fairness(req.requisitions, actions)

    for action in actions:
        METRICS[action.priority] += 1

    METRICS["prioritizations_total"] += 1
    METRICS["items_processed"] += len(req.requisitions)

    _persist_prioritization(
        created_at=prioritized_at,
        correlation_id=correlation_id,
        policy_version=POLICY.get("policy_version", "unknown"),
        action_items=[item.model_dump() for item in actions],
        fairness_report=fairness_report,
    )

    return CollectionsResponse(
        correlation_id=correlation_id,
        prioritized_at=prioritized_at,
        action_items=actions,
        fairness_report=FairnessReport(**fairness_report),
    )


@app.post("/simulate/surge", response_model=CollectionsResponse)
def simulate_surge() -> CollectionsResponse:
    simulated = CollectionsRequest(
        correlation_id=f"sim-{uuid4()}",
        requisitions=[
            Requisition(
                requisition_id="SIM-1001",
                requester_department="Emergency",
                amount=12000,
                hours_to_stockout=5,
                vulnerability_index=0.7,
                compliance_blocked=False,
            ),
            Requisition(
                requisition_id="SIM-1002",
                requester_department="ICU",
                amount=42000,
                hours_to_stockout=10,
                vulnerability_index=0.9,
                compliance_blocked=False,
            ),
            Requisition(
                requisition_id="SIM-1003",
                requester_department="Surgery",
                amount=8000,
                hours_to_stockout=20,
                vulnerability_index=0.4,
                compliance_blocked=True,
            ),
        ],
    )
    result = prioritize(simulated)
    result.simulation_mode = True
    return result


@app.post("/compare/policies")
def compare_policies(payload: ComparePoliciesRequest) -> dict:
    valid_a, errors_a = _validate_policy(payload.policy_a)
    valid_b, errors_b = _validate_policy(payload.policy_b)

    if not valid_a or not valid_b:
        return {
            "valid": False,
            "errors": {
                "policy_a": errors_a,
                "policy_b": errors_b,
            },
        }

    result_a = _prioritize_with_policy(payload.requisitions, payload.policy_a)
    result_b = _prioritize_with_policy(payload.requisitions, payload.policy_b)

    fairness_a = _compute_fairness(payload.requisitions, result_a)
    fairness_b = _compute_fairness(payload.requisitions, result_b)

    avg_a = round(sum(item.priority_score for item in result_a) / max(len(result_a), 1), 3)
    avg_b = round(sum(item.priority_score for item in result_b) / max(len(result_b), 1), 3)

    return {
        "valid": True,
        "comparison": {
            "policy_a": {
                "policy_version": payload.policy_a.get("policy_version", "policy-a"),
                "average_priority_score": avg_a,
                "fairness_report": fairness_a,
                "action_items": [item.model_dump() for item in result_a],
            },
            "policy_b": {
                "policy_version": payload.policy_b.get("policy_version", "policy-b"),
                "average_priority_score": avg_b,
                "fairness_report": fairness_b,
                "action_items": [item.model_dump() for item in result_b],
            },
            "delta_average_priority_score": round(avg_b - avg_a, 3),
        },
    }
