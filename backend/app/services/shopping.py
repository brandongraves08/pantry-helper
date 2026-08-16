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


def add_voice_item(db: Session, item_name: str, quantity: int = 1) -> dict:
    """Add an item by name (Alexa/voice path) to the shopping list.

    If an inventory item matches the name, links item_id; otherwise creates a
    free-text row (item_id NULL) — get_unresolved_items falls back to item_name,
    so it still reaches the HEB cart filler. Dedupes against unresolved rows:
    bump needed to max(existing, requested).
    """
    name = (item_name or "").strip()
    if not name:
        raise ValueError("item_name is required")
    qty = max(1, int(quantity or 1))

    from app.db.models import InventoryItem

    item = (
        db.query(InventoryItem)
        .filter(InventoryItem.canonical_name.ilike(name))
        .first()
    )

    existing = (
        db.query(ShoppingListItemModel)
        .filter(ShoppingListItemModel.resolved_at.is_(None))
        .filter(
            ShoppingListItemModel.item_id == (item.id if item else None)
            if item
            else ShoppingListItemModel.item_name.ilike(name)
        )
        .first()
    )

    if existing:
        existing.needed = max(existing.needed, qty)
        existing.reason = existing.reason or "voice"
    else:
        db.add(
            ShoppingListItemModel(
                item_id=item.id if item else None,
                item_name=None if item else name,
                needed=qty,
                reason="voice",
            )
        )
    db.commit()
    return {
        "item_name": item.canonical_name if item else name,
        "needed": qty,
        "linked_inventory": item is not None,
    }


def get_unresolved_items(db: Session) -> list[dict]:
    """Return unresolved shopping list items as plain dicts (name, needed, reason, location).

    item_name falls back to the free-text name for untracked/meal-plan rows
    (item_id NULL), so they still surface for the HEB cart filler.
    """
    rows = (
        db.query(ShoppingListItemModel)
        .filter(ShoppingListItemModel.resolved_at.is_(None))
        .all()
    )
    return [
        {
            "item_name": row.item_name
            or (row.item.canonical_name if row.item else "unknown"),
            "needed": row.needed,
            "reason": row.reason,
            "location": (row.location.name if row.location else None),
        }
        for row in rows
    ]
