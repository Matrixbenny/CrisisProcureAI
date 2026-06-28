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
    assert body["correlation_id"].startswith("corr-")
    assert body["evaluated_at"]
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


def test_exception_agent_policy_validate_and_apply() -> None:
    client = TestClient(exception_app)
    base_policy = client.get("/policy").json()

    bad_policy_response = client.post(
        "/policy/validate",
        json={"policy": {"policy_version": "invalid"}},
    )
    bad_policy = bad_policy_response.json()
    assert bad_policy["valid"] is False

    good_policy_response = client.post(
        "/policy/validate",
        json={"policy": base_policy},
    )
    good_policy = good_policy_response.json()
    assert good_policy["valid"] is True

    apply_response = client.post("/policy/apply", json={"policy": base_policy})
    apply_body = apply_response.json()
    assert apply_body["applied"] is True


def test_exception_agent_metrics_endpoint() -> None:
    client = TestClient(exception_app)
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "metrics" in body
    assert "evaluations_total" in body["metrics"]


def test_exception_agent_history_endpoint() -> None:
    client = TestClient(exception_app)
    _ = client.post(
        "/evaluate",
        json={
            "order_id": "REQ-HIST-1",
            "customer_tier": "new",
            "category": "medical",
            "discount_percent": 21,
            "line_items": [
                {"sku": "MASK-1", "quantity": 4, "unit_price": 18, "expected_price": 12}
            ],
        },
    )

    response = client.get("/history?limit=5")
    assert response.status_code == 200
    body = response.json()
    assert "timeline" in body
    assert isinstance(body["timeline"], list)


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
    assert body["correlation_id"].startswith("corr-")
    assert body["prioritized_at"]
    assert "fairness_report" in body
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


def test_prioritization_policy_validate_apply_and_compare() -> None:
    client = TestClient(prioritization_app)
    base_policy = client.get("/policy").json()

    validate_response = client.post("/policy/validate", json={"policy": base_policy})
    validate_body = validate_response.json()
    assert validate_body["valid"] is True

    apply_response = client.post("/policy/apply", json={"policy": base_policy})
    apply_body = apply_response.json()
    assert apply_body["applied"] is True

    compare_response = client.post(
        "/compare/policies",
        json={
            "requisitions": [
                {
                    "requisition_id": "REQ-CMP-1",
                    "requester_department": "Emergency",
                    "amount": 20000,
                    "hours_to_stockout": 8,
                    "vulnerability_index": 0.7,
                    "compliance_blocked": False,
                }
            ],
            "policy_a": base_policy,
            "policy_b": base_policy,
        },
    )
    compare_body = compare_response.json()
    assert compare_body["valid"] is True
    assert "comparison" in compare_body


def test_prioritization_metrics_and_surge() -> None:
    client = TestClient(prioritization_app)
    surge_response = client.post("/simulate/surge")
    assert surge_response.status_code == 200
    surge_body = surge_response.json()
    assert surge_body["simulation_mode"] is True
    assert len(surge_body["action_items"]) == 3
    assert "fairness_report" in surge_body

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    metrics_body = metrics_response.json()
    assert "metrics" in metrics_body
    assert "items_processed" in metrics_body["metrics"]

    history_response = client.get("/history?limit=5")
    assert history_response.status_code == 200
    history_body = history_response.json()
    assert "timeline" in history_body
