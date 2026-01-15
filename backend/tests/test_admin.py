"""Tests for admin endpoints"""

from app.db.models import Device, Capture


def test_admin_stats_empty(client, db):
    """Test admin stats endpoint with empty database"""
    response = client.get("/v1/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["devices"]["total"] == 0
    assert data["captures"]["total"] == 0
    assert data["captures"]["pending"] == 0


def test_admin_stats_with_captures(client, db):
    """Test admin stats endpoint with data"""
    # Create a device and captures
    device = Device(id="test-device", name="Test", token_hash="hash")
    db.add(device)
    db.flush()
    
    for i in range(3):
        status = ["stored", "complete", "failed"][i]
        capture = Capture(
            id=f"cap-{i}",
            device_id=device.id,
            trigger_type="door",
            captured_at="2026-01-15T10:00:00",
            image_path=f"/tmp/test{i}.jpg",
            status=status,
        )
        db.add(capture)
    db.commit()
    
    response = client.get("/v1/admin/stats")
    assert response.status_code == 200
    data = response.json()
    
    assert data["devices"]["total"] == 1
    assert data["captures"]["total"] == 3
    assert data["captures"]["pending"] == 1
    assert data["captures"]["completed"] == 1
    assert data["captures"]["failed"] == 1


def test_admin_process_pending(client, db):
    """Test manual process pending endpoint"""
    response = client.post("/v1/admin/process-pending?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "processed" in data


def test_admin_process_specific_capture_not_found(client):
    """Test processing nonexistent capture"""
    response = client.post("/v1/admin/process-capture/nonexistent")
    assert response.status_code == 404


def test_admin_process_specific_capture(client, db):
    """Test processing specific capture"""
    device = Device(id="test-device", name="Test", token_hash="hash")
    db.add(device)
    db.flush()
    
    capture = Capture(
        id="test-capture",
        device_id=device.id,
        trigger_type="door",
        captured_at="2026-01-15T10:00:00",
        image_path="/tmp/test.jpg",
        status="stored",
    )
    db.add(capture)
    db.commit()
    
    response = client.post("/v1/admin/process-capture/test-capture")
    assert response.status_code == 200
    data = response.json()
    assert data["capture_id"] == "test-capture"
    # Status will be "failed" because the image file doesn't exist
    assert "status" in data
