"""Test health check endpoint"""
from fastapi.testclient import TestClient


def test_health_endpoint_returns_200_ok(client: TestClient):
    """Verify health endpoint returns 200 OK with correct response"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "nex-ledger"
    assert "version" in data
