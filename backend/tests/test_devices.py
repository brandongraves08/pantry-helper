"""Tests for device management endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import get_db
from app.db.models import Device, Capture
from app.auth import TokenManager
import hashlib


client = TestClient(app)


# Fixtures

@pytest.fixture
def test_device(db: Session):
    """Create a test device"""
    token = TokenManager.generate_token()
    token_hash = TokenManager.hash_token(token)
    
    device = Device(
        id="test-device-001",
        name="Test Camera",
        token_hash=token_hash,
    )
    db.add(device)
    db.commit()
    
    return {
        "device": device,
        "token": token,
        "token_hash": token_hash,
    }


@pytest.fixture
def test_device_with_captures(test_device: dict, db: Session):
    """Create a test device with capture history"""
    from datetime import datetime, timedelta
    
    device = test_device["device"]
    
    # Create 5 test captures
    now = datetime.utcnow()
    for i in range(5):
        capture = Capture(
            device_id=device.id,
            trigger_type="door" if i % 2 == 0 else "light",
            captured_at=now - timedelta(hours=i),
            image_path=f"/storage/image_{i}.jpg",
            battery_v=3.95 - (i * 0.05),
            rssi=-65 + i,
            status="complete" if i < 4 else "failed",
        )
        db.add(capture)
    
    db.commit()
    
    return test_device


# Tests: List Devices

def test_list_devices_empty(client: TestClient, db: Session):
    """Test listing devices when none exist"""
    # Clean up any test devices
    db.query(Device).delete()
    db.commit()
    
    response = client.get("/v1/devices")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_devices_with_pagination(client: TestClient, test_device: dict):
    """Test listing devices with pagination parameters"""
    response = client.get("/v1/devices?skip=0&limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 0
    assert data["limit"] == 10
    assert data["total"] >= 1


def test_list_devices_invalid_pagination(client: TestClient):
    """Test invalid pagination parameters"""
    response = client.get("/v1/devices?skip=-1")
    assert response.status_code == 422  # Validation error


# Tests: Get Device

def test_get_device(client: TestClient, test_device: dict):
    """Test getting a specific device"""
    device_id = test_device["device"].id
    
    response = client.get(f"/v1/devices/{device_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == device_id
    assert data["name"] == "Test Camera"
    assert "status" in data


def test_get_device_not_found(client: TestClient):
    """Test getting a non-existent device"""
    response = client.get("/v1/devices/non-existent-id")
    
    assert response.status_code == 404


def test_get_device_health(client: TestClient, test_device_with_captures: dict):
    """Test getting device health metrics"""
    device_id = test_device_with_captures["device"].id
    
    response = client.get(f"/v1/devices/{device_id}/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == device_id
    assert "is_healthy" in data
    assert "battery_v" in data
    assert "captures_7d" in data
    assert "success_rate_7d" in data


# Tests: Create Device

def test_create_device(client: TestClient, db: Session):
    """Test creating a new device"""
    db.query(Device).filter_by(id="new-device").delete()
    db.commit()
    
    response = client.post(
        "/v1/devices",
        json={
            "name": "New Camera",
            "device_id": "new-device",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "new-device"
    assert data["name"] == "New Camera"
    assert data["status"] == "inactive"
    assert "device_token" in data  # Token should be returned on creation


def test_create_device_auto_id(client: TestClient, db: Session):
    """Test creating device with auto-generated ID"""
    response = client.post(
        "/v1/devices",
        json={"name": "Auto ID Camera"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Auto ID Camera"
    assert "device_token" in data


def test_create_device_duplicate(client: TestClient, test_device: dict):
    """Test creating a device with duplicate ID"""
    device_id = test_device["device"].id
    
    response = client.post(
        "/v1/devices",
        json={
            "name": "Duplicate Device",
            "device_id": device_id,
        }
    )
    
    assert response.status_code == 409  # Conflict


def test_create_device_missing_name(client: TestClient):
    """Test creating device without name"""
    response = client.post(
        "/v1/devices",
        json={"device_id": "test"}
    )
    
    assert response.status_code == 422  # Validation error


# Tests: Update Device

def test_update_device(client: TestClient, test_device: dict):
    """Test updating device settings"""
    device_id = test_device["device"].id
    
    response = client.patch(
        f"/v1/devices/{device_id}",
        json={"name": "Updated Camera"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Camera"


def test_update_device_not_found(client: TestClient):
    """Test updating non-existent device"""
    response = client.patch(
        "/v1/devices/non-existent",
        json={"name": "Updated"}
    )
    
    assert response.status_code == 404


def test_update_device_partial(client: TestClient, test_device: dict):
    """Test partial update of device"""
    device_id = test_device["device"].id
    original_name = test_device["device"].name
    
    response = client.patch(
        f"/v1/devices/{device_id}",
        json={}  # Empty update
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == original_name  # Name unchanged


# Tests: Delete Device

def test_delete_device(client: TestClient, test_device: dict, db: Session):
    """Test deleting a device"""
    device_id = test_device["device"].id
    
    response = client.delete(f"/v1/devices/{device_id}")
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify device is deleted
    device = db.query(Device).filter_by(id=device_id).first()
    assert device is None


def test_delete_device_not_found(client: TestClient):
    """Test deleting non-existent device"""
    response = client.delete("/v1/devices/non-existent")
    
    assert response.status_code == 404


# Tests: Get Device Captures

def test_get_device_captures(client: TestClient, test_device_with_captures: dict):
    """Test getting device capture history"""
    device_id = test_device_with_captures["device"].id
    
    response = client.get(f"/v1/devices/{device_id}/captures?days=7")
    
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == device_id
    assert data["days"] == 7
    assert len(data["captures"]) > 0


def test_get_device_captures_by_status(client: TestClient, test_device_with_captures: dict):
    """Test filtering captures by status"""
    device_id = test_device_with_captures["device"].id
    
    response = client.get(
        f"/v1/devices/{device_id}/captures?days=7&status=complete"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status_filter"] == "complete"
    # Should have 4 complete captures
    assert len([c for c in data["captures"] if c["status"] == "complete"]) >= 4


def test_get_device_captures_not_found(client: TestClient):
    """Test getting captures for non-existent device"""
    response = client.get("/v1/devices/non-existent/captures")
    
    assert response.status_code == 404


# Integration Tests

def test_device_lifecycle(client: TestClient, db: Session):
    """Test complete device lifecycle"""
    # 1. Create device
    create_response = client.post(
        "/v1/devices",
        json={"name": "Lifecycle Test"}
    )
    assert create_response.status_code == 200
    device_id = create_response.json()["id"]
    
    # 2. List devices
    list_response = client.get("/v1/devices")
    assert list_response.status_code == 200
    assert any(d["id"] == device_id for d in list_response.json()["items"])
    
    # 3. Get device
    get_response = client.get(f"/v1/devices/{device_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == device_id
    
    # 4. Update device
    update_response = client.patch(
        f"/v1/devices/{device_id}",
        json={"name": "Updated Lifecycle Test"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Lifecycle Test"
    
    # 5. Delete device
    delete_response = client.delete(f"/v1/devices/{device_id}")
    assert delete_response.status_code == 200
    
    # 6. Verify deleted
    get_response = client.get(f"/v1/devices/{device_id}")
    assert get_response.status_code == 404


def test_device_status_transitions(client: TestClient, test_device: dict, db: Session):
    """Test device status based on activity"""
    from datetime import datetime, timedelta
    
    device = test_device["device"]
    device_id = device.id
    
    # Initially inactive (no last_seen_at)
    response = client.get(f"/v1/devices/{device_id}")
    assert response.json()["status"] == "inactive"
    
    # Set last_seen_at to 30 minutes ago (should be active)
    device.last_seen_at = datetime.utcnow() - timedelta(minutes=30)
    db.commit()
    
    response = client.get(f"/v1/devices/{device_id}")
    assert response.json()["status"] == "active"
    
    # Set last_seen_at to 12 hours ago (should be idle)
    device.last_seen_at = datetime.utcnow() - timedelta(hours=12)
    db.commit()
    
    response = client.get(f"/v1/devices/{device_id}")
    assert response.json()["status"] == "idle"
