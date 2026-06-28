from fastapi.testclient import TestClient

from services.exception_agent.app import app as exception_app
from services.collections_agent.app import app as prioritization_app


def test_exception_agent_high_risk_path() -> None:
    client = TestClient(exception_app)
    payload = {
        "order_id": "REQ-901",
        "customer_tier": "new",
        "category": "medical",
        "discount_percent": 30,
        "line_items": [
            {"sku": "VENT-KIT", "quantity": 2, "unit_price": 3000, "expected_price": 2000}
        ],
    }

    response = client.post("/evaluate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "human_review"
    assert body["requires_human_approval"] is True
    assert body["policy_version"]
    assert len(body["triggered_rules"]) > 0


def test_exception_agent_policy_endpoint() -> None:
    client = TestClient(exception_app)
    response = client.get("/policy")
    assert response.status_code == 200
    body = response.json()
    assert "policy_version" in body
    assert "thresholds" in body


def test_prioritization_agent_high_priority() -> None:
    client = TestClient(prioritization_app)
    payload = {
        "requisitions": [
            {
                "requisition_id": "REQ-3001",
                "requester_department": "ICU",
                "amount": 40000,
                "hours_to_stockout": 4,
                "vulnerability_index": 0.9,
                "compliance_blocked": False,
            }
        ]
    }

    response = client.post("/prioritize", json=payload)
    assert response.status_code == 200
    body = response.json()
    item = body["action_items"][0]
    assert item["priority"] == "high"
    assert item["priority_score"] >= 0.75
    assert item["policy_version"]


def test_prioritization_policy_endpoint() -> None:
    client = TestClient(prioritization_app)
    response = client.get("/policy")
    assert response.status_code == 200
    body = response.json()
    assert "policy_version" in body
    assert "weights" in body
