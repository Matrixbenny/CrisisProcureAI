from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List

app = FastAPI(title="Compliance Risk Agent", version="1.0.0")


class LineItem(BaseModel):
    sku: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    expected_price: float = Field(ge=0)


class ExceptionRequest(BaseModel):
    order_id: str
    customer_tier: str
    discount_percent: float = Field(ge=0, le=100)
    line_items: List[LineItem]


class ExceptionResponse(BaseModel):
    order_id: str
    risk_score: float
    decision: str
    reasons: List[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "compliance-risk-agent"}


@app.post("/evaluate", response_model=ExceptionResponse)
def evaluate(req: ExceptionRequest) -> ExceptionResponse:
    reasons: List[str] = []
    score = 0.0

    if req.discount_percent > 20:
        score += 0.35
        reasons.append("Requested discount exceeds policy soft limit (20%).")

    if req.customer_tier.lower() == "new":
        score += 0.2
        reasons.append("New supplier or requester profile requires stricter review.")

    for item in req.line_items:
        if item.expected_price == 0:
            continue
        variance = abs(item.unit_price - item.expected_price) / item.expected_price
        if variance > 0.15:
            score += 0.2
            reasons.append(f"SKU {item.sku} has >15% price variance.")

    score = min(score, 1.0)

    if score >= 0.6:
        decision = "human_review"
    elif score >= 0.3:
        decision = "supervisor_review"
    else:
        decision = "auto_approve"
        if not reasons:
            reasons.append("No significant anomalies found.")

    return ExceptionResponse(
        order_id=req.order_id,
        risk_score=round(score, 2),
        decision=decision,
        reasons=reasons,
    )
