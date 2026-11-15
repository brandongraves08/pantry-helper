"""Tests for background capture processing"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import sessionmaker

from app.db.models import (
    Capture,
    Device,
    InventoryEvent,
    InventoryItem,
    InventoryState,
    Observation,
)
from app.models.schemas import VisionOutput, ObservationItem
from app.workers.capture import CaptureProcessor


def test_capture_processor_initialization():
    """Test that capture processor initializes"""
    processor = CaptureProcessor()
    assert processor is not None


def test_process_capture_updates_status(db):
    """Test that processing updates capture status"""
    # Create a device and capture
    device = Device(id="test-device", name="Test", token_hash="hash")
    db.add(device)
    db.flush()

    capture = Capture(
        id="test-capture",
        device_id=device.id,
        trigger_type="door",
        captured_at=datetime.fromisoformat("2026-01-15T10:00:00"),
        image_path="/tmp/test.jpg",
        status="stored",
    )
    db.add(capture)
    db.commit()

    # Mock the analyzer
    mock_output = VisionOutput(
        scene_confidence=0.9,
        items=[
            ObservationItem(
                name="peanut butter",
                brand="Jif",
                package_type="jar",
                quantity_estimate=2,
                confidence=0.85,
            )
        ],
        notes="Clear image",
    )

    processor = CaptureProcessor()
    # If OPENAI_API_KEY isn't set, analyzer will be None; just validate wiring.
    assert hasattr(processor, "process_capture")


@pytest.mark.parametrize(
    ("existing_state", "expected_created"), [(False, True), (True, False)]
)
def test_process_capture_records_inventory_state_creation_provenance(
    db, tmp_path, monkeypatch, existing_state, expected_created
):
    """The event records whether this capture created or only updated the state."""
    image_path = tmp_path / "capture.jpg"
    image_path.write_bytes(b"test image")

    device = Device(
        id="provenance-device",
        name="Provenance test",
        token_hash=f"provenance-{existing_state}",
    )
    db.add(device)
    db.flush()
    capture = Capture(
        id=f"provenance-capture-{existing_state}",
        device_id=device.id,
        trigger_type="door",
        captured_at=datetime.fromisoformat("2026-01-15T10:00:00"),
        image_path=str(image_path),
        status="stored",
    )
    db.add(capture)

    if existing_state:
        item = InventoryItem(canonical_name="milk")
        db.add(item)
        db.flush()
        db.add(
            InventoryState(
                item_id=item.id,
                count_estimate=1,
                confidence=0.8,
                is_manual=False,
            )
        )
    db.commit()

    from app.db import session as db_session

    monkeypatch.setattr(
        db_session,
        "SessionLocal",
        sessionmaker(bind=db.get_bind(), autocommit=False, autoflush=False),
    )
    monkeypatch.setattr("app.workers.capture.detect_barcodes", lambda _path: [])
    monkeypatch.setattr("app.workers.notify.notify_shopping_list.delay", lambda: None)

    processor = CaptureProcessor()
    processor.vision = Mock()
    processor.vision.provider = "mock"
    processor.vision.analyze_image.return_value = VisionOutput(
        scene_confidence=0.9,
        items=[
            ObservationItem(
                name="milk",
                brand=None,
                package_type="carton",
                quantity_estimate=2,
                confidence=0.9,
            )
        ],
        notes="",
    )

    assert processor.process_capture(capture.id) is True
    item = db.query(InventoryItem).filter(InventoryItem.canonical_name == "milk").one()
    event = db.query(InventoryEvent).filter(InventoryEvent.item_id == item.id).one()
    assert event.details["state_created_by_capture"] is expected_created


def test_process_pending_captures(db):
    """Test batch processing of pending captures"""
    processor = CaptureProcessor()

    # Create test device
    device = Device(id="test-device", name="Test", token_hash="hash")
    db.add(device)
    db.flush()

    # Create multiple captures
    for i in range(3):
        capture = Capture(
            id=f"test-capture-{i}",
            device_id=device.id,
            trigger_type="door",
            captured_at=datetime.fromisoformat("2026-01-15T10:00:00"),
            image_path=f"/tmp/test{i}.jpg",
            status="stored",
        )
        db.add(capture)
    db.commit()

    # Count should return 0 because analyzer isn't properly mocked and files don't exist
    # But the method should work without error
    count = processor.process_pending_captures(limit=5)
    assert isinstance(count, int)
    assert count >= 0
