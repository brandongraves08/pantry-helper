from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models import (
    InventoryItem,
    InventoryState,
    InventoryEvent,
    Observation,
)
from app.models.schemas import VisionOutput

class InventoryManager:
    """Manages inventory state transitions and delta calculations"""

    CONFIDENCE_THRESHOLD = 0.70
    STALE_DAYS = 7

    def __init__(self, db: Session):
        self.db = db

    def process_observation(
        self,
        observation: Observation,
        vision_output: VisionOutput,
        scene_confidence_override: float = None,
    ) -> None:
        """
        Process a vision observation and update inventory state.
        
        Args:
            observation: Database observation record
            vision_output: Parsed vision API output
            scene_confidence_override: Override scene confidence if needed
        """
        scene_conf = scene_confidence_override or vision_output.scene_confidence

        for item_data in vision_output.items:
            if item_data.confidence < self.CONFIDENCE_THRESHOLD:
                continue

            # Get or create inventory item
            inv_item = self.db.query(InventoryItem).filter_by(
                canonical_name=item_data.name
            ).first()

            if not inv_item:
                inv_item = InventoryItem(
                    canonical_name=item_data.name,
                    brand=item_data.brand,
                    package_type=item_data.package_type,
                )
                self.db.add(inv_item)
                self.db.flush()

            # Get or create inventory state
            state = self.db.query(InventoryState).filter_by(
                item_id=inv_item.id
            ).first()

            if not state:
                state = InventoryState(item_id=inv_item.id)
                self.db.add(state)

            # Update state
            if item_data.quantity_estimate:
                delta = item_data.quantity_estimate - state.count_estimate
                state.count_estimate = item_data.quantity_estimate
            else:
                delta = 1  # Increment by 1 if count unknown

            state.confidence = item_data.confidence
            state.last_seen_at = datetime.utcnow()
            state.is_manual = False

            # Record event
            event = InventoryEvent(
                item_id=inv_item.id,
                capture_id=observation.capture_id,
                event_type="seen",
                delta=delta,
                details={
                    "scene_confidence": scene_conf,
                    "brand": item_data.brand,
                    "package_type": item_data.package_type,
                },
            )
            self.db.add(event)

        self.db.commit()

    def mark_stale(self) -> None:
        """Mark items not seen for STALE_DAYS as stale"""
        cutoff = datetime.utcnow() - timedelta(days=self.STALE_DAYS)
        stale_items = self.db.query(InventoryState).filter(
            InventoryState.last_seen_at < cutoff
        ).all()

        for item in stale_items:
            item.confidence = 0.0  # Mark as stale via zero confidence
            self.db.add(item)

        self.db.commit()

    def manual_override(
        self,
        item_name: str,
        new_count: int,
        notes: str = None,
    ) -> InventoryItem:
        """Apply a manual inventory correction"""
        inv_item = self.db.query(InventoryItem).filter_by(
            canonical_name=item_name
        ).first()

        if not inv_item:
            inv_item = InventoryItem(canonical_name=item_name)
            self.db.add(inv_item)
            self.db.flush()

        state = self.db.query(InventoryState).filter_by(
            item_id=inv_item.id
        ).first()

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
