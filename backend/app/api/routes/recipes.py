from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Recipe as RecipeModel, RecipeIngredient as RecipeIngredientModel, InventoryItem
from app.models.schemas import (
    RecipeCreate,
    Recipe as RecipeSchema,
    RecipeListResponse,
    RecipeIngredient as RecipeIngredientSchema,
    RecipeSuggestion,
    RecipeSuggestResponse,
)

router = APIRouter()


def _serialize(recipe: RecipeModel) -> RecipeSchema:
    ingredients = [
        RecipeIngredientSchema(
            id=ing.id,
            position=ing.position,
            quantity=ing.quantity,
            name=ing.name,
            note=ing.note,
            inventory_item_id=ing.inventory_item_id,
            inventory_item_name=(ing.inventory_item.canonical_name if ing.inventory_item else None),
        )
        for ing in (recipe.ingredients or [])
    ]
    return RecipeSchema(
        id=recipe.id,
        name=recipe.name,
        description=recipe.description,
        source=recipe.source,
        servings=recipe.servings,
        prep_time_min=recipe.prep_time_min,
        cook_time_min=recipe.cook_time_min,
        instructions=recipe.instructions,
        rating=recipe.rating,
        is_favorite=recipe.is_favorite,
        ingredients=ingredients,
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
    )


@router.get("/recipes", response_model=RecipeListResponse)
async def list_recipes(
    search: str | None = None,
    db: Session = Depends(get_db),
):
    """List all recipes, optionally filtered by name search."""
    q = db.query(RecipeModel).order_by(RecipeModel.created_at.desc())
    if search:
        q = q.filter(RecipeModel.name.ilike(f"%{search}%"))
    recipes = q.all()
    return RecipeListResponse(
        recipes=[_serialize(r) for r in recipes],
        total=len(recipes),
    )


@router.get("/recipes/suggest", response_model=RecipeSuggestResponse)
async def suggest_recipes(
    min_stock: int = 1,
    db: Session = Depends(get_db),
):
    """Suggest recipes ranked by what you can cook tonight.

    Scores each recipe by the percentage of its linked ingredients that are
    in stock (count_estimate >= min_stock). Unlinked/untracked ingredients
    count as neither in-stock nor missing — they're a separate bucket.
    Returns recipes sorted by match_pct descending.
    """
    # Pre-compute which inventory items are in stock
    in_stock: set[str] = set()
    all_items = db.query(InventoryItem).all()
    for item in all_items:
        if item.states:
            total = sum(s.count_estimate or 0 for s in item.states)
            if total >= min_stock:
                in_stock.add(item.id)

    recipes = db.query(RecipeModel).all()
    suggestions = []
    for recipe in recipes:
        ings = recipe.ingredients or []
        if not ings:
            continue
        total = len(ings)
        stocked = 0
        missing = 0
        untracked = 0
        for ing in ings:
            if not ing.inventory_item_id:
                untracked += 1
            elif ing.inventory_item_id in in_stock:
                stocked += 1
            else:
                missing += 1

        # Score = in-stock / (in-stock + missing); untracked are excluded from denominator
        tracked = stocked + missing
        match_pct = stocked / tracked if tracked > 0 else 1.0

        suggestions.append(RecipeSuggestion(
            recipe=_serialize(recipe),
            total_ingredients=total,
            in_stock=stocked,
            missing=missing,
            not_tracked=untracked,
            match_pct=round(match_pct, 2),
        ))

    suggestions.sort(key=lambda s: (-s.match_pct, -s.in_stock, s.recipe.name))
    return RecipeSuggestResponse(
        suggestions=suggestions,
        inventory_items=len(all_items),
    )


@router.get("/recipes/{recipe_id}", response_model=RecipeSchema)
async def get_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """Get a single recipe by ID."""
    recipe = db.query(RecipeModel).filter(RecipeModel.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return _serialize(recipe)


@router.post("/recipes", response_model=RecipeSchema, status_code=201)
async def create_recipe(payload: RecipeCreate, db: Session = Depends(get_db)):
    """Create a new recipe."""
    recipe = RecipeModel(
        name=payload.name,
        description=payload.description,
        source=payload.source,
        servings=payload.servings,
        prep_time_min=payload.prep_time_min,
        cook_time_min=payload.cook_time_min,
        instructions=payload.instructions,
        rating=payload.rating,
        is_favorite=payload.is_favorite or False,
    )
    db.add(recipe)
    db.flush()

    for i, ing in enumerate(payload.ingredients or []):
        recipe.ingredients.append(RecipeIngredientModel(
            recipe_id=recipe.id,
            position=i,
            quantity=ing.quantity,
            name=ing.name,
            note=ing.note,
            inventory_item_id=ing.inventory_item_id,
        ))

    db.commit()
    db.refresh(recipe)
    return _serialize(recipe)


@router.put("/recipes/{recipe_id}", response_model=RecipeSchema)
async def update_recipe(recipe_id: str, payload: RecipeCreate, db: Session = Depends(get_db)):
    """Update an existing recipe (replaces ingredients)."""
    recipe = db.query(RecipeModel).filter(RecipeModel.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    recipe.name = payload.name
    recipe.description = payload.description
    recipe.source = payload.source
    recipe.servings = payload.servings
    recipe.prep_time_min = payload.prep_time_min
    recipe.cook_time_min = payload.cook_time_min
    recipe.instructions = payload.instructions
    if payload.rating is not None:
        recipe.rating = payload.rating
    if payload.is_favorite is not None:
        recipe.is_favorite = payload.is_favorite

    # Replace ingredients
    recipe.ingredients.clear()
    db.flush()
    for i, ing in enumerate(payload.ingredients or []):
        recipe.ingredients.append(RecipeIngredientModel(
            recipe_id=recipe.id,
            position=i,
            quantity=ing.quantity,
            name=ing.name,
            note=ing.note,
            inventory_item_id=ing.inventory_item_id,
        ))

    db.commit()
    db.refresh(recipe)
    return _serialize(recipe)


@router.delete("/recipes/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """Delete a recipe."""
    recipe = db.query(RecipeModel).filter(RecipeModel.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    db.delete(recipe)
    db.commit()
    return None


@router.get("/recipes/{recipe_id}/shopping-needs")
async def recipe_shopping_needs(recipe_id: str, db: Session = Depends(get_db)):
    """List recipe ingredients that are low/missing from inventory (below par or absent)."""
    recipe = db.query(RecipeModel).filter(RecipeModel.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    needs = []
    for ing in (recipe.ingredients or []):
        if not ing.inventory_item:
            needs.append({
                "ingredient": ing.name,
                "quantity": ing.quantity,
                "note": ing.note,
                "in_inventory": False,
                "count": 0,
                "par_level": None,
                "status": "not_tracked",
            })
            continue
        state = ing.inventory_item.states[0] if ing.inventory_item.states else None
        count = state.count_estimate if state else 0
        par = state.par_level if state else None
        if par is not None and count < par:
            status = "below_par"
        elif par is None:
            status = "no_par"
        else:
            status = "ok"
        needs.append({
            "ingredient": ing.name,
            "quantity": ing.quantity,
            "note": ing.note,
            "in_inventory": True,
            "item_name": ing.inventory_item.canonical_name,
            "inventory_item_id": ing.inventory_item.id,
            "count": count,
            "par_level": par,
            "status": status,
        })

    return {"recipe_id": recipe.id, "recipe_name": recipe.name, "needs": needs}