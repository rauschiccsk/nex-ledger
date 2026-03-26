"""Test health check endpoint."""

from fastapi.testclient import TestClient


def test_health_endpoint_returns_200_ok(client: TestClient) -> None:
    """Verify health endpoint returns 200 OK with correct response."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "nex-ledger"}
