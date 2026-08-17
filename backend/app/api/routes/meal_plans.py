"""Meal planning: weekly plans, scheduled recipes, pantry verification, shopping merge."""
import math
import re
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import (
    MealPlan as MealPlanModel,
    MealPlanEntry as MealPlanEntryModel,
    InventoryItem,
    InventoryState,
    ShoppingListItem as ShoppingListItemModel,
    Recipe as RecipeModel,
    HouseholdMember as HouseholdMemberModel,
    DietaryRestriction as DietaryRestrictionModel,
    ItemAllergen as ItemAllergenModel,
)
from app.models.schemas import (
    MealPlanCreate,
    MealPlanEntryInput,
    MealPlanEntryResponse,
    MealPlanListResponse,
    MealPlanResponse,
    MealPlanVerifyResponse,
    MealPlanItemNeed,
    MealPlanUpdateShoppingResponse,
)

router = APIRouter()

# Unicode fractions commonly used in recipe quantities
_FRACTIONS = {
    "½": 0.5,
    "¼": 0.25,
    "¾": 0.75,
    "⅓": 1 / 3,
    "⅔": 2 / 3,
    "⅛": 0.125,
    "⅜": 0.375,
    "⅝": 0.625,
    "⅞": 0.875,
}

# Units that make the quantity non-countable (weight/volume → "1 unit per use" heuristic)
_APPROX_UNITS = ("lb", "oz", "cup", "tbsp", "tsp", "ml", "l ", "kg", "g ", "quart", "pint", "gallon", "liter", "litre")


def parse_quantity(qty: str | None) -> tuple[float | None, bool]:
    """Parse a recipe quantity string into (numeric value, approx).

    Handles: "4", "1½", "½", "1 1/2", "1.5", "1/2", "¼ cup", "4 slices".
    approx=True when the value is a weight/volume measure (we fall back to the
    '1 unit per use' heuristic against integer inventory counts) or the string
    couldn't be parsed at all.
    """
    if not qty:
        return None, True
    s = qty.strip().lower()
    if not s or s in ("to taste", "optional", "dash", "pinch", "as needed"):
        return None, True

    value = _parse_numeric_token(s)

    if value is None:
        return None, True

    # Find the remainder after the leading numeric token
    m = re.match(r"^[\s\d./¼½¾⅓⅔⅛⅜⅝⅞]+", s)
    rest = s[m.end():].strip() if m else s

    approx = any(rest.startswith(u) for u in _APPROX_UNITS)
    return value, approx


def _parse_numeric_token(s: str) -> float | None:
    """Parse the leading numeric token: unicode fraction, mixed number, or decimal."""
    m = re.match(r"^([\d./\s¼½¾⅓⅔⅛⅜⅝⅞]+)", s)
    if not m:
        return None
    tok = m.group(1).strip()
    if not tok:
        return None

    total = 0.0
    seen = False

    # Unicode fraction chars
    for ch, val in _FRACTIONS.items():
        if ch in tok:
            before, after = tok.split(ch, 1)
            if before.strip():
                try:
                    total += float(before.strip())
                except ValueError:
                    pass
            total += val
            seen = True
            tok = after
            break

    tok = tok.strip()
    if not tok:
        return total if seen else None

    # Mixed number "1 1/2" or "1 1/2 cup"
    mixed = re.match(r"^(\d+)\s+(\d+)\s*/\s*(\d+)$", tok)
    if mixed:
        whole, num, den = int(mixed.group(1)), int(mixed.group(2)), int(mixed.group(3))
        if den == 0:
            return None
        total += whole + num / den
        return total

    # Fraction "1/2"
    frac = re.match(r"^(\d+)\s*/\s*(\d+)$", tok)
    if frac:
        num, den = int(frac.group(1)), int(frac.group(2))
        if den == 0:
            return None
        total += num / den
        return total

    # Plain decimal/int
    try:
        total += float(tok)
        return total
    except ValueError:
        return None


def _serialize_plan(plan: MealPlanModel) -> MealPlanResponse:
    entries = [
        MealPlanEntryResponse(
            id=e.id,
            plan_date=e.plan_date,
            meal_type=e.meal_type,
            recipe_id=e.recipe_id,
            recipe_name=e.recipe.name if e.recipe else None,
            servings_multiplier=e.servings_multiplier,
            notes=e.notes,
        )
        for e in plan.entries
    ]
    return MealPlanResponse(
        id=plan.id,
        week_start=plan.week_start,
        name=plan.name,
        entries=entries,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


# ── Plan CRUD ────────────────────────────────────────────────────────

@router.get("/meal-plans", response_model=MealPlanListResponse)
async def list_meal_plans(db: Session = Depends(get_db)):
    """List all meal plans (newest first)."""
    plans = db.query(MealPlanModel).order_by(MealPlanModel.week_start.desc()).all()
    return MealPlanListResponse(plans=[_serialize_plan(p) for p in plans], total=len(plans))


@router.get("/meal-plans/{plan_id}", response_model=MealPlanResponse)
async def get_meal_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.query(MealPlanModel).filter(MealPlanModel.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return _serialize_plan(plan)


@router.post("/meal-plans", response_model=MealPlanResponse, status_code=201)
async def create_meal_plan(payload: MealPlanCreate, db: Session = Depends(get_db)):
    plan = MealPlanModel(week_start=payload.week_start, name=payload.name)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _serialize_plan(plan)


@router.put("/meal-plans/{plan_id}", response_model=MealPlanResponse)
async def update_meal_plan(plan_id: str, payload: MealPlanCreate, db: Session = Depends(get_db)):
    plan = db.query(MealPlanModel).filter(MealPlanModel.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    plan.week_start = payload.week_start
    plan.name = payload.name
    db.commit()
    db.refresh(plan)
    return _serialize_plan(plan)


@router.delete("/meal-plans/{plan_id}", status_code=204)
async def delete_meal_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.query(MealPlanModel).filter(MealPlanModel.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    db.delete(plan)
    db.commit()
    return None


# ── Entries ──────────────────────────────────────────────────────────

@router.post("/meal-plans/{plan_id}/entries", response_model=MealPlanEntryResponse, status_code=201)
async def add_meal_plan_entry(plan_id: str, payload: MealPlanEntryInput, db: Session = Depends(get_db)):
    plan = db.query(MealPlanModel).filter(MealPlanModel.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    recipe = db.query(RecipeModel).filter(RecipeModel.id == payload.recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    entry = MealPlanEntryModel(
        meal_plan_id=plan.id,
        plan_date=payload.plan_date,
        meal_type=payload.meal_type,
        recipe_id=payload.recipe_id,
        servings_multiplier=payload.servings_multiplier,
        notes=payload.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return MealPlanEntryResponse(
        id=entry.id,
        plan_date=entry.plan_date,
        meal_type=entry.meal_type,
        recipe_id=entry.recipe_id,
        recipe_name=recipe.name,
        servings_multiplier=entry.servings_multiplier,
        notes=entry.notes,
    )


@router.delete("/meal-plans/entries/{entry_id}", status_code=204)
async def delete_meal_plan_entry(entry_id: str, db: Session = Depends(get_db)):
    entry = db.query(MealPlanEntryModel).filter(MealPlanEntryModel.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Meal plan entry not found")
    db.delete(entry)
    db.commit()
    return None


# ── Verification & shopping ──────────────────────────────────────────

def _aggregate_needs(plan: MealPlanModel, db: Session, min_confidence: float) -> tuple[list[dict], dict]:
    """Aggregate ingredient needs across all entries of a plan.

    Returns (items, summary) where each item is a plain dict:
      key: inventory_item_id (linked) or f"untracked:{name}" (free-text)
      name, quantity, inventory_item_id, inventory_item_name,
      required_units, available_units, missing_units, status, approx, sources,
      allergen_warnings
    """
    # Get all household members and their allergens for warning lookup
    member_allergens: dict[str, set[str]] = {}
    member_names: dict[str, str] = {}
    members = db.query(HouseholdMemberModel).all()
    for member in members:
        member_allergens[member.id] = set()
        member_names[member.id] = member.name
        for dr in member.restrictions:
            if dr.restriction_type == "allergen" and dr.allergen:
                member_allergens[member.id].add(dr.allergen.lower().strip())

    buckets: dict[str, dict] = {}

    for entry in plan.entries:
        recipe = entry.recipe
        if not recipe:
            continue
        mult = entry.servings_multiplier or 1
        for ing in (recipe.ingredients or []):
            value, approx = parse_quantity(ing.quantity)
            if ing.inventory_item_id:
                key = ing.inventory_item_id
                inv_name = ing.inventory_item.canonical_name if ing.inventory_item else ing.name
            else:
                key = f"untracked:{ing.name.strip().lower()}"
                inv_name = None

            bucket = buckets.setdefault(key, {
                "name": ing.name,
                "quantity": ing.quantity,
                "inventory_item_id": ing.inventory_item_id,
                "inventory_item_name": inv_name,
                "required_units": 0.0,
                "approx": approx,
                "sources": [],
                "allergen_warnings": None,
            })
            if value is None:
                # Unparseable (to taste, etc.) — count as 1 unit per use, approx
                bucket["required_units"] += 1.0 * mult
                bucket["approx"] = True
            else:
                bucket["required_units"] += value * mult
            bucket["approx"] = bucket["approx"] or approx
            bucket["sources"].append({
                "date": entry.plan_date.isoformat(),
                "meal_type": entry.meal_type,
                "recipe": recipe.name,
                "quantity": ing.quantity,
                "servings_multiplier": mult,
            })
            
            # Check for allergens in this ingredient
            if ing.inventory_item_id:
                # Query allergens for this inventory item
                allergens = db.query(ItemAllergenModel).filter(
                    ItemAllergenModel.inventory_item_id == ing.inventory_item_id,
                    ItemAllergenModel.is_present == True
                ).all()
                member_warnings = []
                for member_id, allergens_set in member_allergens.items():
                    for allergen in allergens:
                        if allergen.allergen.lower().strip() in allergens_set:
                            name = member_names.get(member_id, member_id)
                            member_warnings.append(f"Contains {allergen.allergen} — {name} is allergic")
                if member_warnings:
                    bucket["allergen_warnings"] = member_warnings

    # Resolve stock for linked items
    items = []
    summary = {"ok": 0, "short": 0, "not_tracked": 0, "total": 0}
    for key, bucket in buckets.items():
        if key.startswith("untracked:"):
            bucket["status"] = "not_tracked"
            bucket["available_units"] = None
            bucket["missing_units"] = math.ceil(bucket["required_units"]) or 1
            summary["not_tracked"] += 1
        else:
            item = db.query(InventoryItem).filter(InventoryItem.id == key).first()
            if item:
                available = sum(
                    st.count_estimate or 0
                    for st in item.states
                    if (st.confidence or 0) >= min_confidence
                )
                bucket["available_units"] = available
                required_ceil = math.ceil(bucket["required_units"]) or 0
                missing = max(0, required_ceil - available)
                bucket["missing_units"] = missing
                bucket["status"] = "short" if missing > 0 else "ok"
                summary["short" if missing > 0 else "ok"] += 1
            else:
                bucket["status"] = "not_tracked"
                bucket["available_units"] = None
                bucket["missing_units"] = math.ceil(bucket["required_units"]) or 1
                summary["not_tracked"] += 1
        items.append(bucket)
        summary["total"] += 1

    # Short + untracked first, then by name
    order = {"short": 0, "not_tracked": 1, "ok": 2}
    items.sort(key=lambda b: (order.get(b["status"], 9), b["name"].lower()))
    return items, summary


def _window_dates(start: str | None, end: str | None) -> tuple[date, date]:
    today = date.today()
    try:
        s = date.fromisoformat(start) if start else today
    except ValueError:
        raise HTTPException(status_code=422, detail="start must be ISO date (YYYY-MM-DD)")
    try:
        e = date.fromisoformat(end) if end else s + timedelta(days=6)  # rolling 7 days
    except ValueError:
        raise HTTPException(status_code=422, detail="end must be ISO date (YYYY-MM-DD)")
    if e < s:
        raise HTTPException(status_code=422, detail="end must be >= start")
    return s, e


@router.get("/meal-plans/{plan_id}/verify", response_model=MealPlanVerifyResponse)
async def verify_meal_plan(
    plan_id: str,
    start: str | None = None,
    end: str | None = None,
    min_confidence: float = 0.5,
    db: Session = Depends(get_db),
):
    """Aggregate all planned meals' ingredients vs pantry stock.

    Rolling 7 days by default (today → today+6); pass start/end to override.
    Only entries within the window are counted. min_confidence filters which
    inventory counts count as 'have it' (default 0.5, same as low-stock).
    """
    plan = db.query(MealPlanModel).filter(MealPlanModel.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    s, e = _window_dates(start, end)

    # Temporarily scope entries to the window for aggregation
    original_entries = plan.entries
    plan.entries = [x for x in original_entries if s <= x.plan_date <= e]
    try:
        items, summary = _aggregate_needs(plan, db, min_confidence)
    finally:
        plan.entries = original_entries

    return MealPlanVerifyResponse(
        plan_id=plan.id,
        week_start=plan.week_start,
        start=s,
        end=e,
        items=[MealPlanItemNeed(**i) for i in items],
        summary=summary,
        updated_at=datetime.utcnow(),
    )


@router.post("/meal-plans/{plan_id}/update-shopping", response_model=MealPlanUpdateShoppingResponse)
async def update_shopping_from_plan(
    plan_id: str,
    start: str | None = None,
    end: str | None = None,
    min_confidence: float = 0.5,
    db: Session = Depends(get_db),
):
    """Merge missing meal-plan ingredients into the shopping list.

    - Linked items that are short → shopping_list_items row (reason='meal plan')
    - Untracked items (salt, fresh produce...) → free-text row via item_name
      (item_id NULL) so they still land on the HEB order.
    - Dedupes by item (or item_name for untracked) + unresolved; keeps max needed.
    """
    plan = db.query(MealPlanModel).filter(MealPlanModel.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    s, e = _window_dates(start, end)

    original_entries = plan.entries
    plan.entries = [x for x in original_entries if s <= x.plan_date <= e]
    try:
        items, _ = _aggregate_needs(plan, db, min_confidence)
    finally:
        plan.entries = original_entries

    added = 0
    for item in items:
        if item["status"] == "ok":
            continue
        needed = item["missing_units"] or 1
        if item["inventory_item_id"]:
            # Upsert by item (any location) + unresolved
            row = (
                db.query(ShoppingListItemModel)
                .filter(
                    ShoppingListItemModel.item_id == item["inventory_item_id"],
                    ShoppingListItemModel.resolved_at.is_(None),
                )
                .first()
            )
            if row:
                row.needed = max(row.needed, needed)
                row.reason = "meal plan"
            else:
                db.add(ShoppingListItemModel(
                    item_id=item["inventory_item_id"],
                    item_name=item["inventory_item_name"],
                    needed=needed,
                    reason="meal plan",
                ))
            added += 1
        else:
            # Untracked — free-text row (item_id NULL)
            row = (
                db.query(ShoppingListItemModel)
                .filter(
                    ShoppingListItemModel.item_id.is_(None),
                    ShoppingListItemModel.item_name.ilike(item["name"].strip()),
                    ShoppingListItemModel.resolved_at.is_(None),
                )
                .first()
            )
            if row:
                row.needed = max(row.needed, needed)
                row.reason = "meal plan (untracked)"
            else:
                db.add(ShoppingListItemModel(
                    item_id=None,
                    item_name=item["name"].strip(),
                    needed=needed,
                    reason="meal plan (untracked)",
                ))
            added += 1

    db.commit()

    # Re-aggregate (post-write) for the response so statuses reflect the new list
    return MealPlanUpdateShoppingResponse(
        plan_id=plan.id,
        added=added,
        items=[MealPlanItemNeed(**i) for i in items],
        updated_at=datetime.utcnow(),
    )
