import csv
import io
import os
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
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
from app.services.storage import get_storage_manager

router = APIRouter()

@router.get("/inventory", response_model=InventoryResponse)
async def get_inventory(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(0, ge=0, le=500),
):
    """Get current inventory state."""
    # Default (page_size=0) returns all items (backwards-compatible with the frontend).
    states = db.query(InventoryState).all()
    
    items = [
        InventoryItemSchema(
            item_id=state.item.id,
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
            rating=getattr(state.item, "rating", None),
            is_favorite=bool(getattr(state.item, "is_favorite", False)),
            image_url=f"/v1/inventory/{state.item.id}/image" if state.item.image_path else None,
        )
        for state in states
        if state.confidence > 0  # Filter out stale items
    ]

    total = len(items)
    if page_size > 0:
        start = (page - 1) * page_size
        items = items[start:start + page_size]

    return InventoryResponse(
        items=items,
        updated_at=datetime.utcnow(),
        total=total,
        page=page if page_size > 0 else 1,
        page_size=page_size if page_size > 0 else total,
        has_more=page_size > 0 and (page * page_size) < total,
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

        # Brand / rating / favorite live on the inventory item (not the state row)
        if override.brand is not None:
            item.brand = override.brand
        if override.rating is not None:
            item.rating = override.rating
        if override.is_favorite is not None:
            item.is_favorite = override.is_favorite

        db.commit()

        # Event-driven shopping-list notification (par-level check → Discord)
        try:
            from app.workers.notify import notify_shopping_list
            notify_shopping_list.delay()
        except Exception:
            pass  # queue hiccup should not fail the API call

        return {
            "success": True,
            "item_id": item.id,
            "message": f"Updated {override.item_name} to {override.count_estimate}",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/{item_id}/image")
async def get_inventory_item_image(item_id: str, db: Session = Depends(get_db)):
    """Serve the image for an inventory item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item or not item.image_path:
        raise HTTPException(status_code=404, detail="Image not found")
    
    image_path = item.image_path
    if not os.path.isabs(image_path):
        storage_mgr = get_storage_manager()
        image_path = str(storage_mgr.storage_path / image_path)
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file missing")
    
    return FileResponse(image_path, media_type="image/jpeg")


@router.get("/inventory/export/csv")
async def export_inventory_csv(db: Session = Depends(get_db)):
    """Export inventory as CSV file download."""
    states = db.query(InventoryState).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Item ID", "Name", "Brand", "Package Type", "Category", "Unit",
        "Count", "Confidence", "Last Seen", "Location", "Expires At",
        "Opened At", "Par Level", "Manual Entry", "Notes",
    ])

    for state in states:
        if state.confidence <= 0:
            continue

        loc_name = ""
        if hasattr(state, "location") and state.location:
            loc_name = state.location.name

        writer.writerow([
            state.item.id,
            state.item.canonical_name,
            state.item.brand or "",
            state.item.package_type or "",
            getattr(state.item, "category", "") or "",
            getattr(state.item, "unit", "") or "",
            state.count_estimate,
            state.confidence,
            state.last_seen_at.isoformat() if state.last_seen_at else "",
            loc_name,
            state.expires_at.isoformat() if hasattr(state, "expires_at") and state.expires_at else "",
            state.opened_at.isoformat() if hasattr(state, "opened_at") and state.opened_at else "",
            getattr(state, "par_level", "") or "",
            "Yes" if state.is_manual else "No",
            state.notes or "",
        ])

    csv_content = output.getvalue()
    output.close()

    filename = f"pantry-inventory-{datetime.utcnow().strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


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
