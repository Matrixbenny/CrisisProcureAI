import json
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Compliance Risk Agent", version="1.0.0")

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
    policy_path = Path(__file__).with_name("policy_pack.json")
    if not policy_path.exists():
        return DEFAULT_POLICY
    with policy_path.open("r", encoding="utf-8") as f:
        policy = json.load(f)
    return policy


POLICY = _load_policy()


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
    line_items: List[LineItem]


class ExceptionResponse(BaseModel):
    order_id: str
    risk_score: float
    confidence: float
    decision: str
    requires_human_approval: bool
    policy_version: str
    triggered_rules: List[str]
    recommended_next_step: str
    reasons: List[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "compliance-risk-agent"}


@app.get("/policy")
def get_policy() -> dict:
    return POLICY


@app.post("/evaluate", response_model=ExceptionResponse)
def evaluate(req: ExceptionRequest) -> ExceptionResponse:
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

    return ExceptionResponse(
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
