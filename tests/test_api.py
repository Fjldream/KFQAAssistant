from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_rejects_empty_question():
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"question": "   "})

    assert response.status_code == 422
