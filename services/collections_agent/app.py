from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List

app = FastAPI(title="Prioritization Agent", version="1.0.0")


class Requisition(BaseModel):
    requisition_id: str
    requester_department: str
    amount: float = Field(gt=0)
    hours_to_stockout: int = Field(ge=0)
    compliance_blocked: bool = False


class CollectionsRequest(BaseModel):
    requisitions: List[Requisition]


class ActionItem(BaseModel):
    requisition_id: str
    priority: str
    recommended_action: str
    rationale: str


class CollectionsResponse(BaseModel):
    action_items: List[ActionItem]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "prioritization-agent"}


@app.post("/prioritize", response_model=CollectionsResponse)
def prioritize(req: CollectionsRequest) -> CollectionsResponse:
    actions: List[ActionItem] = []

    for req_item in req.requisitions:
        if req_item.compliance_blocked:
            actions.append(
                ActionItem(
                    requisition_id=req_item.requisition_id,
                    priority="high",
                    recommended_action="Route to procurement lead for manual override",
                    rationale="Compliance block requires explicit human decision.",
                )
            )
            continue

        if req_item.hours_to_stockout <= 6:
            actions.append(
                ActionItem(
                    requisition_id=req_item.requisition_id,
                    priority="high",
                    recommended_action="Escalate immediate sourcing and supplier callout",
                    rationale="Critical stockout risk in <= 6 hours.",
                )
            )
        elif req_item.hours_to_stockout <= 24:
            actions.append(
                ActionItem(
                    requisition_id=req_item.requisition_id,
                    priority="medium",
                    recommended_action="Fast-track quote comparison and approval",
                    rationale="Near-term stockout risk in <= 24 hours.",
                )
            )
        else:
            actions.append(
                ActionItem(
                    requisition_id=req_item.requisition_id,
                    priority="low",
                    recommended_action="Process in standard emergency queue",
                    rationale="No immediate stockout or compliance block.",
                )
            )

    actions.sort(key=lambda a: {"high": 0, "medium": 1, "low": 2}[a.priority])
    return CollectionsResponse(action_items=actions)
