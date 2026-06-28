import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Prioritization Agent", version="1.0.0")

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
    policy_path = Path(__file__).with_name("policy_pack.json")
    if not policy_path.exists():
        return DEFAULT_POLICY
    with policy_path.open("r", encoding="utf-8") as f:
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


@app.get("/metrics")
def get_metrics() -> dict:
    return {
        "service": "prioritization-agent",
        "policy_version": POLICY.get("policy_version", "unknown"),
        "metrics": METRICS,
    }


@app.post("/prioritize", response_model=CollectionsResponse)
def prioritize(req: CollectionsRequest) -> CollectionsResponse:
    correlation_id = req.correlation_id or f"corr-{uuid4()}"
    prioritized_at = datetime.now(timezone.utc).isoformat()
    thresholds = POLICY["thresholds"]
    weights = POLICY["weights"]
    actions: List[ActionItem] = []

    for req_item in req.requisitions:
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
                policy_version=POLICY.get("policy_version", "unknown"),
                recommended_action=recommended_action,
                triggered_rules=triggered_rules,
                rationale=rationale,
            )
        )

        METRICS[priority] += 1

    METRICS["prioritizations_total"] += 1
    METRICS["items_processed"] += len(req.requisitions)
    actions.sort(key=lambda a: {"high": 0, "medium": 1, "low": 2}[a.priority])
    return CollectionsResponse(
        correlation_id=correlation_id,
        prioritized_at=prioritized_at,
        action_items=actions,
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
