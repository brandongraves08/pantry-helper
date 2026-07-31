from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import ShoppingListResponse, ShoppingListItem
from app.services.shopping import recompute_shopping_list, get_unresolved_items

router = APIRouter()


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
