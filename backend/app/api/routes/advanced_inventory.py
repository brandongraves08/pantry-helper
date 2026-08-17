"""Advanced inventory query endpoints for analytics and reporting."""

import logging
import uuid
from datetime import datetime, timedelta, date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import (
    InventoryItem, InventoryState, InventoryEvent, Capture,
    ConsumptionEvent, HouseholdMember,
)
from app.models.schemas import (
    InventoryItem as InventoryItemSchema,
    InventoryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/inventory/stats")
async def get_inventory_statistics(db: Session = Depends(get_db)):
    """
    Get comprehensive inventory statistics and metrics.
    """
    total_items = db.query(func.count(InventoryItem.id)).scalar() or 0
    total_states = db.query(func.count(InventoryState.id)).scalar() or 0
    total_events = db.query(func.count(InventoryEvent.id)).scalar() or 0
    total_captures = db.query(func.count(Capture.id)).scalar() or 0

    # Confidence breakdown
    high_conf = db.query(func.count(InventoryState.id)).filter(
        InventoryState.confidence >= 0.8
    ).scalar() or 0
    med_conf = db.query(func.count(InventoryState.id)).filter(
        InventoryState.confidence >= 0.5, InventoryState.confidence < 0.8
    ).scalar() or 0
    low_conf = db.query(func.count(InventoryState.id)).filter(
        InventoryState.confidence < 0.5
    ).scalar() or 0

    return {
        "total_items": total_items,
        "total_states": total_states,
        "total_events": total_events,
        "total_captures": total_captures,
        "confidence_breakdown": {
            "high": high_conf,
            "medium": med_conf,
            "low": low_conf,
        },
    }


@router.get("/inventory/{item_id}/history")
async def get_item_history(
    item_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get event history for a specific inventory item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    events = (
        db.query(InventoryEvent)
        .filter(InventoryEvent.item_id == item_id)
        .order_by(InventoryEvent.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "item_id": item.id,
        "canonical_name": item.canonical_name,
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "delta": e.delta,
                "details": e.details,
                "created_at": str(e.created_at),
            }
            for e in events
        ],
    }


@router.get("/inventory/low-stock")
async def get_low_stock_items(
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    """Get items that are below their par level."""
    from app.db.models import InventoryItem as ItemModel
    from app.db.models import InventoryState as StateModel

    # Find items where current count < par_level
    items = (
        db.query(ItemModel, StateModel)
        .join(StateModel, ItemModel.id == StateModel.item_id)
        .filter(
            StateModel.confidence >= min_confidence,
            StateModel.par_level.isnot(None),
            StateModel.count_estimate < StateModel.par_level,
        )
        .all()
    )

    return [
        {
            "item_id": item.id,
            "canonical_name": item.canonical_name,
            "count_estimate": state.count_estimate,
            "par_level": state.par_level,
            "deficit": state.par_level - state.count_estimate,
            "confidence": state.confidence,
        }
        for item, state in items
    ]


@router.get("/inventory/stale")
async def get_stale_items(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get items not seen in N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    states = (
        db.query(InventoryState)
        .filter(InventoryState.last_seen_at < cutoff)
        .order_by(InventoryState.last_seen_at.asc())
        .all()
    )

    return [
        {
            "item_id": s.item_id,
            "canonical_name": s.item.canonical_name if s.item else "Unknown",
            "last_seen_at": str(s.last_seen_at),
            "days_since": (datetime.utcnow() - s.last_seen_at).days if s.last_seen_at else None,
            "count_estimate": s.count_estimate,
        }
        for s in states
    ]


@router.get("/inventory/recent-changes")
async def get_recent_changes(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get recent inventory events."""
    events = (
        db.query(InventoryEvent)
        .order_by(InventoryEvent.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": e.id,
            "item_id": e.item_id,
            "item_name": e.item.canonical_name if e.item else "Unknown",
            "event_type": e.event_type,
            "delta": e.delta,
            "details": e.details,
            "created_at": str(e.created_at),
        }
        for e in events
    ]


@router.get("/inventory/export")
async def export_inventory(
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db),
):
    """Export full inventory."""
    items = db.query(InventoryItem).all()
    return {"items": [_item_to_dict(i) for i in items]}


def _item_to_dict(item: InventoryItem) -> dict:
    state = item.states[0] if item.states else None
    return {
        "id": item.id,
        "canonical_name": item.canonical_name,
        "brand": item.brand,
        "category": item.category,
        "count_estimate": state.count_estimate if state else 0,
        "confidence": state.confidence if state else 0,
        "par_level": state.par_level if state else None,
        "location": state.location.name if state and state.location else None,
        "last_seen_at": str(state.last_seen_at) if state else None,
    }


# ── Supply Forecast ───────────────────────────────────────────────────

@router.post("/consumption")
async def record_consumption(
    data: dict,
    db: Session = Depends(get_db),
):
    """Record a consumption event.

    Body: { member_id, inventory_item_id, quantity_used, consumed_at?, notes? }
    consumed_at defaults to now if omitted.
    """
    member_id = data.get("member_id")
    item_id = data.get("inventory_item_id")
    qty = data.get("quantity_used")

    if not member_id or not item_id or qty is None:
        raise HTTPException(status_code=422, detail="member_id, inventory_item_id, quantity_required")

    member = db.query(HouseholdMember).filter(HouseholdMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    consumed_at_str = data.get("consumed_at")
    consumed_at = (
        datetime.fromisoformat(consumed_at_str)
        if consumed_at_str
        else datetime.utcnow()
    )

    event = ConsumptionEvent(
        member_id=member_id,
        inventory_item_id=item_id,
        quantity_used=float(qty),
        consumed_at=consumed_at,
        notes=data.get("notes"),
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "id": event.id,
        "member_id": event.member_id,
        "inventory_item_id": event.inventory_item_id,
        "quantity_used": event.quantity_used,
        "consumed_at": str(event.consumed_at),
        "notes": event.notes,
    }


@router.get("/inventory/supply-forecast")
async def supply_forecast(
    window_days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """Estimate days-until-empty for each tracked item.

    Uses consumption_events over the last `window_days` to calculate
    average daily consumption rate, then divides current stock by that
    rate. Items with no consumption data get 'unknown' status.
    """
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    today = date.today()

    # Pre-compute total consumption per item over the window
    consumption = (
        db.query(
            ConsumptionEvent.inventory_item_id,
            func.sum(ConsumptionEvent.quantity_used).label("total_used"),
            func.count(ConsumptionEvent.id).label("event_count"),
        )
        .filter(ConsumptionEvent.consumed_at >= cutoff)
        .group_by(ConsumptionEvent.inventory_item_id)
        .all()
    )

    consumption_map = {}
    for item_id, total_used, event_count in consumption:
        consumption_map[item_id] = {
            "total_used": total_used or 0,
            "event_count": event_count,
            "daily_rate": (total_used or 0) / window_days,
        }

    # Get current stock for all items
    items = db.query(InventoryItem).all()
    forecasts = []

    for item in items:
        state = item.states[0] if item.states else None
        current_stock = state.count_estimate if state else 0
        par_level = state.par_level if state else None

        cons = consumption_map.get(item.id)
        daily_rate = cons["daily_rate"] if cons else 0
        total_used = cons["total_used"] if cons else 0
        event_count = cons["event_count"] if cons else 0

        if daily_rate > 0:
            days_left = current_stock / daily_rate if daily_rate > 0 else None
            status = "depleting"
            if days_left is not None and days_left <= 7:
                status = "critical"
            elif days_left is not None and days_left <= 14:
                status = "low"
        elif event_count == 0:
            days_left = None
            status = "no_data"
        else:
            days_left = None
            status = "stable"

        # Calculate reorder suggestion
        reorder_by = None
        if days_left is not None and par_level is not None:
            deficit = par_level - current_stock
            if deficit > 0:
                reorder_by = today + timedelta(days=max(0, int(days_left) - 3))

        forecasts.append({
            "item_id": item.id,
            "canonical_name": item.canonical_name,
            "current_stock": current_stock,
            "par_level": par_level,
            "daily_rate": round(daily_rate, 4),
            "total_used_window": total_used,
            "consumption_events": event_count,
            "days_left": round(days_left, 1) if days_left is not None else None,
            "status": status,
            "reorder_by": str(reorder_by) if reorder_by else None,
        })

    # Sort: critical first, then low, depleting, stable, no_data
    status_order = {"critical": 0, "low": 1, "depleting": 2, "stable": 3, "no_data": 4}
    forecasts.sort(key=lambda f: (status_order.get(f["status"], 9), f["days_left"] or 999))

    return {
        "window_days": window_days,
        "total_items": len(forecasts),
        "with_consumption_data": len([f for f in forecasts if f["consumption_events"] > 0]),
        "critical": len([f for f in forecasts if f["status"] == "critical"]),
        "low": len([f for f in forecasts if f["status"] == "low"]),
        "forecasts": forecasts,
    }
