"""Test health check endpoint."""


def test_health_check(client):
    """Health check returns 200 with status info."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")  # degraded = Redis down in tests
    assert "checks" in data
    assert "database" in data["checks"]
    assert data["checks"]["database"]["status"] == "ok"
