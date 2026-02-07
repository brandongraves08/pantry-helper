from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import InventoryState, InventoryItem, Location, ShoppingListItem as ShoppingListItemModel, InventoryReview
from app.models.schemas import (
    InventoryResponse,
    InventoryItem as InventoryItemSchema,
    InventoryOverride,
    ShoppingListResponse,
    ShoppingListItem,
    ReviewRequest,
    ReviewResponse,
)
from app.services.inventory import InventoryManager

router = APIRouter()

@router.get("/inventory", response_model=InventoryResponse)
async def get_inventory(db: Session = Depends(get_db)):
    """Get current inventory state"""
    
    states = db.query(InventoryState).all()
    
    items = [
        InventoryItemSchema(
            canonical_name=state.item.canonical_name,
            brand=state.item.brand,
            package_type=state.item.package_type,
            category=getattr(state.item, "category", None),
            unit=getattr(state.item, "unit", None),
            count_estimate=state.count_estimate,
            confidence=state.confidence,
            last_seen_at=state.last_seen_at or datetime.utcnow(),
            location=(state.location.name if getattr(state, "location", None) else None),
            expires_at=getattr(state, "expires_at", None),
            opened_at=getattr(state, "opened_at", None),
            par_level=getattr(state, "par_level", None),
            is_manual=state.is_manual,
            notes=state.notes,
        )
        for state in states
        if state.confidence > 0  # Filter out stale items
    ]

    return InventoryResponse(
        items=items,
        updated_at=datetime.utcnow(),
    )

@router.post("/inventory/override")
async def override_inventory(
    override: InventoryOverride,
    db: Session = Depends(get_db),
):
    """Manually correct an inventory item count (and optionally set home fields)."""

    manager = InventoryManager(db)
    try:
        item = manager.manual_override(
            item_name=override.item_name,
            new_count=override.count_estimate,
            notes=override.notes,
        )

        # Apply extra metadata/location/expiry if provided
        if override.location:
            loc = (
                db.query(Location)
                .filter(Location.name == override.location, Location.parent_id.is_(None))
                .first()
            )
            if not loc:
                loc = Location(name=override.location)
                db.add(loc)
                db.flush()

            # attach location + fields to the item's state row
            state = db.query(InventoryState).filter(InventoryState.item_id == item.id).first()
            if state:
                state.location_id = loc.id

        state = db.query(InventoryState).filter(InventoryState.item_id == item.id).first()
        if state:
            if override.expires_at is not None:
                state.expires_at = override.expires_at
            if override.opened_at is not None:
                state.opened_at = override.opened_at
            if override.par_level is not None:
                state.par_level = override.par_level

        db.commit()

        return {
            "success": True,
            "item_id": item.id,
            "message": f"Updated {override.item_name} to {override.count_estimate}",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/history")
async def get_inventory_history(
    days: int = 7,
    db: Session = Depends(get_db),
):
    """Get inventory change history"""
    
    from app.db.models import InventoryEvent
    from datetime import timedelta
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    events = db.query(InventoryEvent).filter(
        InventoryEvent.created_at >= cutoff
    ).order_by(InventoryEvent.created_at.desc()).all()

    return {
        "events": [
            {
                "item_name": event.item.canonical_name,
                "event_type": event.event_type,
                "delta": event.delta,
                "timestamp": event.created_at,
                "details": event.details,
            }
            for event in events
        ],
        "total_events": len(events),
    }
