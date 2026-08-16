"""Inventory flagging — user-reported issues on items (wrong image/brand/count/name).

Flags are the correction channel: the UI posts a flag with a free-text reason, the
agent (Hermes) lists open flags via GET /v1/inventory/flags, fixes the underlying
item, then resolves the flag. This closes the loop on bad OFF image backfills and
wrong-brand matches.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import InventoryFlag, InventoryItem
from app.models.schemas import FlagCreate, FlagResolve, FlagResponse

router = APIRouter()

ALLOWED_FIELDS = {"image", "brand", "count", "name", "other"}


def _serialize(flag: InventoryFlag) -> dict:
    return {
        "id": flag.id,
        "item_id": flag.item_id,
        "canonical_name": flag.item.canonical_name if flag.item else None,
        "field": flag.field,
        "reason": flag.reason,
        "status": flag.status,
        "resolution_note": flag.resolution_note,
        "created_at": flag.created_at.isoformat() if flag.created_at else None,
        "resolved_at": flag.resolved_at.isoformat() if flag.resolved_at else None,
    }


@router.post("/inventory/{item_id}/flag", response_model=FlagResponse)
async def flag_item(item_id: str, payload: FlagCreate, db: Session = Depends(get_db)):
    """Flag an inventory item with a reason (wrong image, brand, count, name...)."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    field = payload.field
    if field is not None and field not in ALLOWED_FIELDS:
        raise HTTPException(status_code=422, detail=f"field must be one of: {', '.join(sorted(ALLOWED_FIELDS))}")
    reason = (payload.reason or "").strip()
    if not reason:
        raise HTTPException(status_code=422, detail="reason is required")

    flag = InventoryFlag(item_id=item.id, field=field, reason=reason, status="open")
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return _serialize(flag)


@router.get("/inventory/flags", response_model=dict)
async def list_flags(
    status: str = "open",  # open | resolved | all
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List inventory flags for the agent/user to process. Newest first."""
    q = db.query(InventoryFlag)
    if status == "open":
        q = q.filter(InventoryFlag.status == "open")
    elif status == "resolved":
        q = q.filter(InventoryFlag.status == "resolved")

    total = q.count()
    flags = q.order_by(InventoryFlag.created_at.desc()).limit(limit).all()
    return {
        "flags": [_serialize(f) for f in flags],
        "total": total,
        "status": status,
    }


@router.get("/inventory/{item_id}/flags", response_model=dict)
async def list_item_flags(item_id: str, db: Session = Depends(get_db)):
    """List flags for a single item (any status)."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    flags = (
        db.query(InventoryFlag)
        .filter(InventoryFlag.item_id == item.id)
        .order_by(InventoryFlag.created_at.desc())
        .all()
    )
    return {"flags": [_serialize(f) for f in flags], "total": len(flags)}


@router.post("/inventory/flags/{flag_id}/resolve", response_model=FlagResponse)
async def resolve_flag(flag_id: str, payload: FlagResolve, db: Session = Depends(get_db)):
    """Mark a flag resolved (after the underlying issue was fixed)."""
    flag = db.query(InventoryFlag).filter(InventoryFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    if flag.status == "resolved":
        raise HTTPException(status_code=409, detail="Flag already resolved")

    flag.status = "resolved"
    flag.resolved_at = datetime.utcnow()
    if payload.resolution_note:
        flag.resolution_note = payload.resolution_note.strip()
    db.commit()
    db.refresh(flag)
    return _serialize(flag)
