from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import InventoryState, ShoppingListItem as ShoppingListItemModel
from app.models.schemas import ShoppingListResponse, ShoppingListItem

router = APIRouter()


@router.get("/shopping-list", response_model=ShoppingListResponse)
async def get_shopping_list(db: Session = Depends(get_db)):
    """Return unresolved shopping list items."""
    rows = (
        db.query(ShoppingListItemModel)
        .filter(ShoppingListItemModel.resolved_at.is_(None))
        .all()
    )
    items = [
        ShoppingListItem(
            item_name=row.item.canonical_name,
            needed=row.needed,
            reason=row.reason,
            location=(row.location.name if row.location else None),
        )
        for row in rows
    ]
    return ShoppingListResponse(items=items, updated_at=datetime.utcnow())


@router.post("/shopping-list/recompute")
async def recompute_shopping_list(db: Session = Depends(get_db)):
    """Recompute shopping list based on par levels.

    Simple rule: if par_level is set and count_estimate < par_level, add/update.
    """
    states = db.query(InventoryState).all()

    created_or_updated = 0
    for state in states:
        if state.par_level is None:
            continue
        needed = max(0, int(state.par_level) - int(state.count_estimate))
        if needed <= 0:
            continue

        existing = (
            db.query(ShoppingListItemModel)
            .filter(
                ShoppingListItemModel.item_id == state.item_id,
                ShoppingListItemModel.location_id == state.location_id,
                ShoppingListItemModel.resolved_at.is_(None),
            )
            .first()
        )
        if existing:
            existing.needed = needed
            existing.reason = existing.reason or "below par"
        else:
            db.add(
                ShoppingListItemModel(
                    item_id=state.item_id,
                    location_id=state.location_id,
                    needed=needed,
                    reason="below par",
                )
            )
        created_or_updated += 1

    db.commit()
    return {"success": True, "updated": created_or_updated}
