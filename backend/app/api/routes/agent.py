"""Compact endpoints for OpenClaw and other agent workflows."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Capture, Device, InventoryReview, InventoryState

router = APIRouter()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _iso(dt: Optional[datetime]) -> Optional[str]:
    value = _as_aware(dt)
    return value.isoformat() if value else None


def _device_status(device: Device, now: datetime) -> str:
    last_seen = _as_aware(device.last_seen_at)
    if not last_seen:
        return "inactive"

    age = now - last_seen
    if age < timedelta(hours=1):
        return "active"
    if age < timedelta(days=1):
        return "idle"
    if age < timedelta(days=7):
        return "inactive"
    return "offline"


def _state_item(state: InventoryState) -> dict:
    return {
        "name": state.item.canonical_name,
        "brand": state.item.brand,
        "category": state.item.category,
        "count": state.count_estimate,
        "confidence": state.confidence,
        "location": state.location.name if state.location else None,
        "par_level": state.par_level,
        "expires_at": _iso(state.expires_at),
        "opened_at": _iso(state.opened_at),
        "last_seen_at": _iso(state.last_seen_at),
        "is_manual": state.is_manual,
        "notes": state.notes,
    }


def _low_stock_rows(db: Session, threshold: int) -> list[InventoryState]:
    states = db.query(InventoryState).all()
    rows = []
    for state in states:
        if state.confidence <= 0:
            continue
        if state.par_level is not None:
            if state.count_estimate < state.par_level:
                rows.append(state)
        elif state.count_estimate <= threshold:
            rows.append(state)
    return sorted(rows, key=lambda s: (s.item.canonical_name or "").lower())


def _expiring_rows(db: Session, days: int) -> list[InventoryState]:
    now = _utcnow()
    cutoff = now + timedelta(days=days)
    states = (
        db.query(InventoryState)
        .filter(InventoryState.expires_at.is_not(None))
        .all()
    )
    rows = []
    for state in states:
        expires_at = _as_aware(state.expires_at)
        if expires_at and state.count_estimate > 0 and expires_at <= cutoff:
            rows.append(state)
    return sorted(rows, key=lambda s: _as_aware(s.expires_at) or cutoff)


@router.get("/low-stock")
async def get_agent_low_stock(
    threshold: int = Query(1, ge=0),
    db: Session = Depends(get_db),
):
    """Return compact low-stock rows using par levels when configured."""

    rows = _low_stock_rows(db, threshold)
    return {
        "threshold": threshold,
        "item_count": len(rows),
        "items": [_state_item(row) for row in rows],
        "updated_at": _utcnow().isoformat(),
    }


@router.get("/expiring")
async def get_agent_expiring(
    days: int = Query(14, ge=0, le=365),
    db: Session = Depends(get_db),
):
    """Return items expired or expiring within the requested window."""

    rows = _expiring_rows(db, days)
    now = _utcnow()
    items = []
    for row in rows:
        item = _state_item(row)
        expires_at = _as_aware(row.expires_at)
        item["days_until_expiry"] = (expires_at.date() - now.date()).days if expires_at else None
        items.append(item)

    return {
        "days": days,
        "item_count": len(items),
        "items": items,
        "updated_at": now.isoformat(),
    }


@router.get("/review-queue")
async def get_agent_review_queue(db: Session = Depends(get_db)):
    """Return pending manual review tasks with basic capture context."""

    rows = (
        db.query(InventoryReview)
        .filter(InventoryReview.status == "pending")
        .order_by(InventoryReview.created_at.asc())
        .all()
    )
    items = []
    for review in rows:
        capture = review.capture
        items.append(
            {
                "id": review.id,
                "capture_id": review.capture_id,
                "status": review.status,
                "notes": review.notes,
                "created_at": _iso(review.created_at),
                "capture_status": capture.status if capture else None,
                "device_id": capture.device_id if capture else None,
                "captured_at": _iso(capture.captured_at) if capture else None,
                "error_message": capture.error_message if capture else None,
            }
        )

    return {
        "item_count": len(items),
        "items": items,
        "updated_at": _utcnow().isoformat(),
    }


@router.get("/summary")
async def get_agent_summary(
    low_stock_threshold: int = Query(1, ge=0),
    expiry_days: int = Query(14, ge=0, le=365),
    db: Session = Depends(get_db),
):
    """Return a compact operational summary for agents and Discord digests."""

    now = _utcnow()
    states = [s for s in db.query(InventoryState).all() if s.confidence > 0]
    captures_total = db.query(Capture).count()
    captures_failed = db.query(Capture).filter(Capture.status == "failed").count()
    captures_analyzing = db.query(Capture).filter(Capture.status == "analyzing").count()
    reviews_pending = (
        db.query(InventoryReview)
        .filter(InventoryReview.status == "pending")
        .count()
    )

    devices = db.query(Device).all()
    device_rows = []
    for device in devices:
        status = _device_status(device, now)
        failed_uploads = (
            db.query(Capture)
            .filter(Capture.device_id == device.id, Capture.status == "failed")
            .count()
        )
        device_rows.append(
            {
                "id": device.id,
                "name": device.name,
                "status": status,
                "last_seen_at": _iso(device.last_seen_at),
                "battery_v": device.last_battery_v,
                "rssi": device.last_rssi,
                "failed_uploads": failed_uploads,
            }
        )

    low_stock = _low_stock_rows(db, low_stock_threshold)
    expiring = _expiring_rows(db, expiry_days)
    unhealthy_devices = [d for d in device_rows if d["status"] not in ("active", "idle")]

    status = "green"
    if captures_failed or reviews_pending or unhealthy_devices or low_stock or expiring:
        status = "yellow"
    if captures_analyzing > 5:
        status = "red"

    return {
        "status": status,
        "updated_at": now.isoformat(),
        "inventory": {
            "item_count": len(states),
            "low_stock_count": len(low_stock),
            "expiring_count": len(expiring),
        },
        "captures": {
            "total": captures_total,
            "failed": captures_failed,
            "analyzing": captures_analyzing,
        },
        "reviews": {
            "pending": reviews_pending,
        },
        "devices": {
            "total": len(device_rows),
            "unhealthy": len(unhealthy_devices),
            "items": device_rows,
        },
        "low_stock": [_state_item(row) for row in low_stock[:10]],
        "expiring": [_state_item(row) for row in expiring[:10]],
    }
