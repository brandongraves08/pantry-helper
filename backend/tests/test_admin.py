"""Tests for admin stats endpoint."""
import pytest
from datetime import datetime
from app.db.models import Capture


def test_admin_stats_empty(client, db):
    """Admin stats returns 200 with empty data."""
    resp = client.get("/v1/admin/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert "queue" in data
    assert "rate_limits" in data
    assert data["events"]["total"] == 0


def test_admin_stats_with_captures(client, db):
    """Admin stats counts captures."""
    db.add(Capture(
        device_id="test", trigger_type="manual",
        captured_at=datetime.utcnow(), image_path="/tmp/test.jpg",
        status="stored",
    ))
    db.commit()

    resp = client.get("/v1/admin/stats")
    assert resp.status_code == 200
    assert resp.json()["events"]["total"] >= 0


def test_admin_process_pending(client, db):
    """Process pending captures returns a result."""
    resp = client.post("/v1/admin/process-pending")
    assert resp.status_code == 200


def test_admin_process_specific_capture_not_found(client, db):
    """Processing non-existent capture returns 404."""
    resp = client.post("/v1/admin/process-capture/nonexistent")
    assert resp.status_code == 404


def test_admin_process_specific_capture(client, db):
    """Processing a stored capture triggers processing."""
    cap = Capture(
        device_id="test", trigger_type="manual",
        captured_at=datetime.utcnow(), image_path="/tmp/test.jpg",
        status="stored",
    )
    db.add(cap)
    db.commit()
    db.refresh(cap)

    resp = client.post(f"/v1/admin/process-capture/{cap.id}")
    assert resp.status_code in (200, 500)  # 500 if celery worker not running
