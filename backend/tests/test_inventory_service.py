"""InventoryManager service — the manual correction path.

``InventoryManager`` used to carry ``process_observation`` and ``mark_stale``,
duplicates of the live vision pipeline in ``app/workers/capture.py`` that nothing
called (CodeGraph: 0 callers, 0 tests). They were removed in the 2026-11-02
code-health pass; ``manual_override`` is the only surviving entry point and is
pinned here so the removal cannot silently take it out too.
"""

from datetime import datetime

from app.db.models import InventoryEvent, InventoryItem, InventoryState
from app.services.inventory import InventoryManager


def test_manual_override_creates_item_state_and_event(db):
    manager = InventoryManager(db)

    item = manager.manual_override("Peanut Butter", 5, notes="restocked")

    state = db.query(InventoryState).filter(InventoryState.item_id == item.id).first()
    assert state.count_estimate == 5
    assert state.confidence == 1.0
    assert state.is_manual is True
    assert state.notes == "restocked"

    events = db.query(InventoryEvent).filter(InventoryEvent.item_id == item.id).all()
    assert [e.event_type for e in events] == ["manual_override"]

    # A second correction overwrites the count and records the delta
    manager.manual_override("Peanut Butter", 2)
    db.refresh(state)
    assert state.count_estimate == 2
    deltas = [
        e.delta
        for e in db.query(InventoryEvent)
        .filter(InventoryEvent.item_id == item.id)
        .all()
    ]
    assert sorted(deltas) == [-3, 5]


def test_manual_override_reuses_existing_item(db):
    item = InventoryItem(canonical_name="Milk")
    db.add(item)
    db.flush()
    db.add(
        InventoryState(
            item_id=item.id,
            count_estimate=1,
            confidence=0.4,
            last_seen_at=datetime.utcnow(),
        )
    )
    db.commit()

    manager = InventoryManager(db)
    returned = manager.manual_override("Milk", 3)

    assert returned.id == item.id
    assert db.query(InventoryItem).count() == 1
