from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_validation_errors_use_stable_envelope_and_correlation_id() -> None:
    response = client.post(
        "/feedback",
        headers={"X-Request-ID": str(uuid4())},
        json={"user_id": "not-a-uuid", "action": "maybe"},
    )

    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "validation_error"
    assert body["message"] == "Request validation failed."
    assert body["correlation_id"] == response.headers["X-Request-ID"]


def test_missing_feedback_item_has_stable_code() -> None:
    response = client.post(
        "/feedback",
        json={
            "user_id": str(uuid4()),
            "wardrobe_item_id": str(uuid4()),
            "action": "like",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "item_not_found"


def test_invalid_request_id_is_replaced_with_safe_correlation_id() -> None:
    response = client.get("/health", headers={"X-Request-ID": "unsafe value"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "unsafe value"
