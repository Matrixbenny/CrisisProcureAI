import json
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI
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


POLICY = _load_policy()


class Requisition(BaseModel):
    requisition_id: str
    requester_department: str
    amount: float = Field(gt=0)
    hours_to_stockout: int = Field(ge=0)
    vulnerability_index: float = Field(default=0.0, ge=0.0, le=1.0)
    compliance_blocked: bool = False


class CollectionsRequest(BaseModel):
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
    action_items: List[ActionItem]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "prioritization-agent"}


@app.get("/policy")
def get_policy() -> dict:
    return POLICY


@app.post("/prioritize", response_model=CollectionsResponse)
def prioritize(req: CollectionsRequest) -> CollectionsResponse:
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

    actions.sort(key=lambda a: {"high": 0, "medium": 1, "low": 2}[a.priority])
    return CollectionsResponse(action_items=actions)
