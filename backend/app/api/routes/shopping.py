from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import ShoppingListResponse, ShoppingListItem, VoiceShoppingAdd
from app.services.shopping import recompute_shopping_list, get_unresolved_items, add_voice_item

router = APIRouter()


@router.post("/shopping-list/items")
async def add_item_by_voice(payload: VoiceShoppingAdd, db: Session = Depends(get_db)):
    """Add an item to the shopping list by name (Alexa/voice path).

    Links to an existing inventory item when the name matches; otherwise creates a
    free-text row (item_id NULL) that still flows to the HEB cart filler. Dedupes
    against unresolved rows (bump needed to max). Reason: voice.
    """
    try:
        result = add_voice_item(db, payload.item_name, payload.quantity)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"success": True, **result}


@router.get("/shopping-list", response_model=ShoppingListResponse)
async def get_shopping_list(db: Session = Depends(get_db)):
    """Return unresolved shopping list items."""
    rows = get_unresolved_items(db)
    items = [
        ShoppingListItem(
            item_name=row["item_name"],
            needed=row["needed"],
            reason=row["reason"],
            location=row["location"],
        )
        for row in rows
    ]
    return ShoppingListResponse(items=items, updated_at=datetime.utcnow())


@router.post("/shopping-list/recompute")
async def recompute(db: Session = Depends(get_db)):
    """Recompute shopping list based on par levels, then notify Discord if below par."""
    updated = recompute_shopping_list(db)

    # Fire the event-driven Discord notification (Celery task, no cron needed).
    try:
        from app.workers.notify import notify_shopping_list
        notify_shopping_list.delay()
    except Exception:
        pass  # queue hiccup should not fail the API call

    return {"success": True, "updated": updated}
