"""Shopping list service — shared recompute + query logic (DRY for route & worker)."""
from sqlalchemy.orm import Session

from app.db.models import InventoryState, ShoppingListItem as ShoppingListItemModel


def recompute_shopping_list(db: Session) -> int:
    """Add/update shopping list entries for items below par. Returns count of created/updated."""
    states = db.query(InventoryState).all()

    created_or_updated = 0
    for state in states:
        if state.par_level is None:
            continue
        needed = max(0, int(state.par_level) - int(state.count_estimate or 0))
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
    return created_or_updated


def get_unresolved_items(db: Session) -> list[dict]:
    """Return unresolved shopping list items as plain dicts (name, needed, reason, location)."""
    rows = (
        db.query(ShoppingListItemModel)
        .filter(ShoppingListItemModel.resolved_at.is_(None))
        .all()
    )
    return [
        {
            "item_name": row.item.canonical_name,
            "needed": row.needed,
            "reason": row.reason,
            "location": (row.location.name if row.location else None),
        }
        for row in rows
    ]
