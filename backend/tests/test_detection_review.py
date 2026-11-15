"""Detection review — approve/reject of vision pipeline results.

Regression tests for two defects found in the 2026-11-02 code-health audit:

1. ``reject_detection`` filtered ``InventoryState`` on a ``capture_id`` column
   that does not exist on the model, so every reject of an already-tracked
   item raised ``AttributeError`` (HTTP 500). Its fallback also deleted
   user-verified (``is_manual``) stock.
2. ``approve_detection`` let the vision-derived ``quantity_estimate`` win over
   an explicit ``count`` supplied by the user, so the user's corrected count
   was written and then immediately overwritten.
"""

import pytest
from datetime import datetime

from app.db.models import Capture, Device, InventoryItem, InventoryState, Observation


def _seed_capture(db, items):
    """Create a device + capture + observation whose raw_json holds `items`."""
    device = Device(name="Cam", token_hash="deadbeef")
    db.add(device)
    db.flush()

    capture = Capture(
        device_id=device.id,
        trigger_type="manual",
        captured_at=datetime.utcnow(),
        image_path="captures/test.jpg",
        status="complete",
    )
    db.add(capture)
    db.flush()

    db.add(
        Observation(
            capture_id=capture.id,
            raw_json={"scene_type": "pantry", "scene_confidence": 0.9, "items": items},
            scene_confidence=0.9,
        )
    )
    db.commit()
    return capture


def _seed_item(db, name, count=2, confidence=0.9, is_manual=False):
    item = InventoryItem(canonical_name=name)
    db.add(item)
    db.flush()
    state = InventoryState(
        item_id=item.id,
        count_estimate=count,
        confidence=confidence,
        is_manual=is_manual,
        last_seen_at=datetime.utcnow(),
    )
    db.add(state)
    db.commit()
    return item, state


def test_list_detections_reports_inventory_state(client, db):
    """The review UI reads detections + whether each one is already tracked."""
    capture = _seed_capture(
        db,
        [
            {"name": "Milk", "quantity_estimate": 1, "confidence": 0.9},
            {"name": "Ghost Item", "quantity_estimate": 2, "confidence": 0.4},
        ],
    )
    _seed_item(db, "Milk", count=2, confidence=0.9)

    resp = client.get(f"/v1/captures/{capture.id}/detections")

    assert resp.status_code == 200
    data = resp.json()
    assert data["detection_count"] == 2
    by_name = {item["name"]: item for item in data["items"]}
    assert by_name["Milk"]["in_inventory"] is True
    assert by_name["Milk"]["current_count"] == 2
    assert by_name["Ghost Item"]["in_inventory"] is False
    # Sorted by confidence, highest first
    assert data["items"][0]["name"] == "Milk"


def test_reject_detection_removes_vision_added_state(client, db):
    """Rejecting a detection for a vision-tracked item must return 200 and drop the state."""
    capture = _seed_capture(
        db, [{"name": "Milk", "quantity_estimate": 1, "confidence": 0.9}]
    )
    item, state = _seed_item(db, "Milk", count=2, confidence=0.9, is_manual=False)
    state_id = state.id

    resp = client.post(f"/v1/captures/{capture.id}/detections/0/reject")

    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert (
        db.query(InventoryState).filter(InventoryState.id == state_id).first() is None
    )


def test_reject_detection_preserves_manual_state(client, db):
    """Rejecting a detection must never delete user-verified (is_manual) stock."""
    capture = _seed_capture(
        db, [{"name": "Milk", "quantity_estimate": 1, "confidence": 0.9}]
    )
    item, state = _seed_item(db, "Milk", count=4, confidence=1.0, is_manual=True)
    state_id = state.id

    resp = client.post(f"/v1/captures/{capture.id}/detections/0/reject")

    assert resp.status_code == 200
    kept = db.query(InventoryState).filter(InventoryState.id == state_id).first()
    assert (
        kept is not None
    ), "manual (user-verified) state must survive a detection reject"
    assert kept.count_estimate == 4
    assert kept.is_manual is True


def test_approve_detection_honours_explicit_count(client, db):
    """An explicit `count` from the reviewer must not be overwritten by quantity_estimate."""
    capture = _seed_capture(
        db, [{"name": "Eggs", "quantity_estimate": 12, "confidence": 0.9}]
    )

    resp = client.post(
        f"/v1/captures/{capture.id}/detections/0/approve",
        json={"count": 5},
    )

    assert resp.status_code == 200
    item = (
        db.query(InventoryItem).filter(InventoryItem.canonical_name == "Eggs").first()
    )
    assert item is not None
    state = db.query(InventoryState).filter(InventoryState.item_id == item.id).first()
    assert state is not None
    assert state.count_estimate == 5


def test_approve_detection_falls_back_to_quantity_estimate(client, db):
    """Without an explicit count, the detection's quantity_estimate is still used."""
    capture = _seed_capture(
        db, [{"name": "Yogurt", "quantity_estimate": 6, "confidence": 0.9}]
    )

    resp = client.post(f"/v1/captures/{capture.id}/detections/0/approve", json={})

    assert resp.status_code == 200
    item = (
        db.query(InventoryItem).filter(InventoryItem.canonical_name == "Yogurt").first()
    )
    state = db.query(InventoryState).filter(InventoryState.item_id == item.id).first()
    assert state.count_estimate == 6
    assert state.confidence == 1.0  # unchanged existing contract
    assert state.is_manual is True


def test_approve_detection_with_different_brand_reuses_existing_item(client, db):
    """inventory_items.canonical_name is unique — a different brand must reuse the row."""
    existing = InventoryItem(canonical_name="Milk", brand="Horizon")
    db.add(existing)
    db.flush()
    db.add(
        InventoryState(
            item_id=existing.id,
            count_estimate=1,
            confidence=0.6,
            last_seen_at=datetime.utcnow(),
        )
    )
    db.commit()

    capture = _seed_capture(
        db,
        [
            {
                "name": "Milk",
                "brand": "Great Value",
                "quantity_estimate": 2,
                "confidence": 0.9,
            },
        ],
    )

    resp = client.post(f"/v1/captures/{capture.id}/detections/0/approve")

    assert resp.status_code == 200
    assert (
        db.query(InventoryItem).filter(InventoryItem.canonical_name == "Milk").count()
        == 1
    )


def test_edit_detection_honours_explicit_count(client, db):
    """Editing a detection must write the reviewer's count, not the vision estimate."""
    capture = _seed_capture(
        db, [{"name": "Tomatoes", "quantity_estimate": 12, "confidence": 0.8}]
    )

    resp = client.post(
        f"/v1/captures/{capture.id}/detections/0/edit",
        json={"name": "Tomatoes", "quantity_estimate": 12, "count": 3},
    )

    assert resp.status_code == 200
    item = (
        db.query(InventoryItem)
        .filter(InventoryItem.canonical_name == "Tomatoes")
        .first()
    )
    state = db.query(InventoryState).filter(InventoryState.item_id == item.id).first()
    assert state.count_estimate == 3
