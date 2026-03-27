"""Tests for health check endpoint."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test GET /health returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_endpoint_content_type():
    """Test /health returns JSON content type."""
    response = client.get("/health")
    assert response.headers["content-type"] == "application/json"
