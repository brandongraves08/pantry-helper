from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import (
    InventoryItem,
    InventoryState,
    InventoryEvent,
)


class InventoryManager:
    """Applies manual inventory corrections.

    Note: the vision→state transition lives in ``app/workers/capture.py``
    (CaptureProcessor). The former ``process_observation`` / ``mark_stale``
    duplicates here had no callers and were removed — keep the worker as the
    single writer for vision-derived counts/confidence.
    """

    def __init__(self, db: Session):
        self.db = db

    def manual_override(
        self,
        item_name: str,
        new_count: int,
        notes: str = None,
    ) -> InventoryItem:
        """Apply a manual inventory correction"""
        inv_item = (
            self.db.query(InventoryItem).filter_by(canonical_name=item_name).first()
        )

        if not inv_item:
            inv_item = InventoryItem(canonical_name=item_name, heb_status="pending")
            self.db.add(inv_item)
            self.db.flush()

        state = self.db.query(InventoryState).filter_by(item_id=inv_item.id).first()

        if not state:
            state = InventoryState(item_id=inv_item.id, count_estimate=0)
            self.db.add(state)
            self.db.flush()

        delta = new_count - (state.count_estimate or 0)
        state.count_estimate = new_count
        state.confidence = 1.0  # Manual entries have full confidence
        state.is_manual = True
        state.notes = notes
        state.last_seen_at = datetime.utcnow()

        event = InventoryEvent(
            item_id=inv_item.id,
            event_type="manual_override",
            delta=delta,
            details={"notes": notes},
        )
        self.db.add(event)
        self.db.commit()

        return inv_item
