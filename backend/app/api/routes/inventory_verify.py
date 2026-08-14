"""Inventory verification queue + HEB product enrichment."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import InventoryItem, InventoryState
from app.models.schemas import InventoryVerifyRequest, HebEnrichmentPayload

router = APIRouter()


@router.get("/inventory/unverified")
async def list_unverified(
    limit: int = 10,
    min_confidence: float = 0.5,
    db: Session = Depends(get_db),
):
    """List items whose count has NOT been user-verified (confidence below threshold).

    Ordered oldest-last-seen first so the user works through stale items first.
    """
    base = (
        db.query(InventoryItem)
        .join(InventoryState, InventoryState.item_id == InventoryItem.id)
        .filter(InventoryState.confidence < min_confidence)
    )
    total = base.count()
    items = (
        base.order_by(InventoryState.last_seen_at.asc().nullsfirst(), InventoryItem.canonical_name.asc())
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "item_id": it.id,
                "canonical_name": it.canonical_name,
                "brand": it.brand,
                "count_estimate": (it.states[0].count_estimate if it.states else 0),
                "par_level": (it.states[0].par_level if it.states else None),
                "confidence": (it.states[0].confidence if it.states else 0),
                "last_seen_at": (it.states[0].last_seen_at.isoformat() if it.states and it.states[0].last_seen_at else None),
            }
            for it in items
        ],
        "total": total,
    }


@router.post("/inventory/{item_id}/verify")
async def verify_item_count(item_id: str, payload: InventoryVerifyRequest, db: Session = Depends(get_db)):
    """Record a user-confirmed count for an item (sets confidence=1.0, marks verified)."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    state = db.query(InventoryState).filter(InventoryState.item_id == item.id).first()
    if not state:
        state = InventoryState(item_id=item.id, count_estimate=0)
        db.add(state)
        db.flush()

    state.count_estimate = max(0, payload.count_estimate)
    state.confidence = 1.0
    state.is_manual = True
    state.last_seen_at = datetime.utcnow()
    note = payload.notes or "USER VERIFIED"
    state.notes = (state.notes or "") + f" [{note} {datetime.utcnow().date().isoformat()}]"

    db.commit()
    return {
        "success": True,
        "item_id": item.id,
        "canonical_name": item.canonical_name,
        "count_estimate": state.count_estimate,
        "confidence": state.confidence,
    }


@router.post("/inventory/{item_id}/heb-enrich")
async def heb_enrich(item_id: str, payload: HebEnrichmentPayload, db: Session = Depends(get_db)):
    """Store HEB product info fetched from heb.com for an inventory item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if payload.product_name:
        item.heb_product_name = payload.product_name
    if payload.url:
        item.heb_url = payload.url
    if payload.price is not None:
        item.heb_price = payload.price
    if payload.image_url:
        item.heb_image_url = payload.image_url
    item.heb_status = "done"
    item.heb_lookup_at = datetime.utcnow()

    # If we have an HEB image and no local image yet, adopt it
    if payload.image_url and not item.image_path:
        item.image_path = payload.image_url  # stored as remote URL; UI resolves absolute

    db.commit()
    return {
        "success": True,
        "item_id": item.id,
        "canonical_name": item.canonical_name,
        "heb_product_name": item.heb_product_name,
        "heb_price": item.heb_price,
        "heb_status": item.heb_status,
    }


@router.get("/inventory/{item_id}/heb-status")
async def heb_status(item_id: str, db: Session = Depends(get_db)):
    """Return the HEB enrichment status for an item (used by the automator)."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "item_id": item.id,
        "canonical_name": item.canonical_name,
        "heb_status": item.heb_status,
        "heb_product_name": item.heb_product_name,
        "heb_price": item.heb_price,
        "heb_lookup_at": item.heb_lookup_at.isoformat() if item.heb_lookup_at else None,
    }


@router.get("/inventory/heb-enrich/pending")
async def heb_pending(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List items waiting for HEB enrichment (heb_status='pending'), oldest created first."""
    items = (
        db.query(InventoryItem)
        .filter(InventoryItem.heb_status == "pending")
        .order_by(InventoryItem.created_at.asc())
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "item_id": it.id,
                "canonical_name": it.canonical_name,
                "brand": it.brand,
            }
            for it in items
        ],
        "total": len(items),
    }
