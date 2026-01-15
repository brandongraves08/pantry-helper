"""Tests for health check endpoint"""

def test_health_check(client):
    """Test that health check endpoint works"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
