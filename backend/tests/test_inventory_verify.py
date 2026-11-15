"""Inventory verification queue — the user-facing trust control.

`confidence` is the app's trust model (high ≥ 0.8, medium 0.5–0.8, low < 0.5) with
`is_manual` alongside it. These routes are the only way a low-confidence
photo-derived row becomes trusted, so pin their behaviour: unverified lists rows
below the threshold and `POST /verify` writes confidence 1.0 + is_manual.
"""

from datetime import datetime

from app.db.models import InventoryItem, InventoryState


def _item(db, name, count, confidence, is_manual=False):
    item = InventoryItem(canonical_name=name)
    db.add(item)
    db.flush()
    db.add(
        InventoryState(
            item_id=item.id,
            count_estimate=count,
            confidence=confidence,
            is_manual=is_manual,
            last_seen_at=datetime.utcnow(),
        )
    )
    db.commit()
    return item


def test_unverified_lists_only_low_confidence_rows(client, db):
    low = _item(db, "Milk", 1, 0.3)
    _item(db, "Eggs", 6, 1.0, is_manual=True)
    medium = _item(db, "Bread", 1, 0.6)  # below the default 0.5? no — above it

    resp = client.get("/v1/inventory/unverified")

    assert resp.status_code == 200
    data = resp.json()
    ids = [row["item_id"] for row in data["items"]]
    assert ids == [low.id]
    assert medium.id not in ids
    assert data["total"] == 1


def test_unverified_honours_min_confidence(client, db):
    _item(db, "Milk", 1, 0.3)
    med = _item(db, "Bread", 1, 0.6)

    resp = client.get("/v1/inventory/unverified?min_confidence=0.8")

    assert resp.status_code == 200
    ids = [row["item_id"] for row in resp.json()["items"]]
    assert med.id in ids


def test_verify_sets_full_confidence_and_manual_flag(client, db):
    item = _item(db, "Milk", 1, 0.3)

    resp = client.post(f"/v1/inventory/{item.id}/verify", json={"count_estimate": 4})

    assert resp.status_code == 200
    body = resp.json()
    assert body["count_estimate"] == 4
    assert body["confidence"] == 1.0

    state = db.query(InventoryState).filter(InventoryState.item_id == item.id).first()
    assert state.count_estimate == 4
    assert state.confidence == 1.0
    assert state.is_manual is True
    assert "USER VERIFIED" in state.notes

    # Verified rows must drop out of the unverified queue
    queued = client.get("/v1/inventory/unverified").json()["items"]
    assert all(row["item_id"] != item.id for row in queued)


def test_verify_creates_state_when_missing(client, db):
    item = InventoryItem(canonical_name="Orphan")
    db.add(item)
    db.commit()

    resp = client.post(
        f"/v1/inventory/{item.id}/verify",
        json={"count_estimate": 2, "notes": "counted"},
    )

    assert resp.status_code == 200
    state = db.query(InventoryState).filter(InventoryState.item_id == item.id).first()
    assert state.count_estimate == 2
    assert "counted" in state.notes


def test_verify_unknown_item_is_404(client, db):
    resp = client.post("/v1/inventory/nope/verify", json={"count_estimate": 1})

    assert resp.status_code == 404
