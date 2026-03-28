"""
NEX Ledger — Health endpoint tests.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test GET /health returns 200 with correct JSON structure."""
    response = client.get("/health")

    assert response.status_code == 200

    json_data = response.json()
    assert json_data["status"] == "ok"
    assert "timestamp" in json_data
    # Verify timestamp is valid ISO8601
    assert "T" in json_data["timestamp"]
