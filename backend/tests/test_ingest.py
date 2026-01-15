"""Tests for image ingestion endpoint"""

from io import BytesIO
from datetime import datetime

def test_ingest_requires_device(client):
    """Test that ingest requires valid device"""
    # Create a fake image
    fake_image = BytesIO(b"fake jpeg data")
    
    response = client.post(
        "/v1/ingest",
        data={
            "device_id": "nonexistent-device",
            "timestamp": datetime.utcnow().isoformat(),
            "trigger_type": "door",
            "battery_v": 4.2,
            "rssi": -45,
        },
        files={"image": ("test.jpg", fake_image, "image/jpeg")}
    )
    assert response.status_code == 401
    assert "Device not found" in response.json()["detail"]

def test_ingest_valid_device(client, db):
    """Test successful image ingestion"""
    fake_image = BytesIO(b"fake jpeg data")
    
    response = client.post(
        "/v1/ingest",
        data={
            "device_id": "test-device-001",
            "timestamp": datetime.utcnow().isoformat(),
            "trigger_type": "door",
            "battery_v": 4.2,
            "rssi": -45,
        },
        files={"image": ("test.jpg", fake_image, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stored"
    assert "capture_id" in data
    assert data["message"] is not None

def test_ingest_invalid_timestamp(client):
    """Test that ingest validates timestamp format"""
    fake_image = BytesIO(b"fake jpeg data")
    
    response = client.post(
        "/v1/ingest",
        data={
            "device_id": "test-device-001",
            "timestamp": "not-a-timestamp",
            "trigger_type": "door",
            "battery_v": 4.2,
            "rssi": -45,
        },
        files={"image": ("test.jpg", fake_image, "image/jpeg")}
    )
    assert response.status_code == 400
    assert "Invalid timestamp format" in response.json()["detail"]

def test_ingest_updates_device_last_seen(client, db):
    """Test that ingest updates device metadata"""
    from app.db.models import Device
    
    device = db.query(Device).filter_by(id="test-device-001").first()
    assert device.last_seen_at is None
    
    fake_image = BytesIO(b"fake jpeg data")
    response = client.post(
        "/v1/ingest",
        data={
            "device_id": "test-device-001",
            "timestamp": datetime.utcnow().isoformat(),
            "trigger_type": "door",
            "battery_v": 4.1,
            "rssi": -50,
        },
        files={"image": ("test.jpg", fake_image, "image/jpeg")}
    )
    assert response.status_code == 200
    
    # Refresh device from DB
    db.expire(device)
    assert device.last_seen_at is not None
    assert device.last_battery_v == 4.1
    assert device.last_rssi == -50
