from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["app_name"] == "Project1 API"
    assert data["version"] == "0.1.0"


def test_health_endpoint_structure():
    response = client.get("/api/health")
    data = response.json()
    required_fields = ["status", "timestamp", "app_name", "version"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
