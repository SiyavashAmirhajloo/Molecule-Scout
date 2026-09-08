from fastapi.testclient import TestClient

from app.main import create_app


def test_health_shape():
    with TestClient(create_app()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert set(response.json()) == {"db", "redis"}
