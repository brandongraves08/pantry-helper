"""Nutrition lookup and management routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import InventoryItem, NutritionFact
from app.services.nutrition import search_by_name

logger = __import__("logging").getLogger("pantry-api.nutrition")

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────


class NutritionSearchResult(BaseModel):
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    serving_size: Optional[str] = None
    image_url: Optional[str] = None
    nutrition: dict = {}
    allergens: list = []
    ingredients_text: Optional[str] = None
    source: str = "openfoodfacts"


class NutritionSearchResponse(BaseModel):
    query: str
    count: int
    results: list[NutritionSearchResult]


class SaveNutritionRequest(BaseModel):
    source: Optional[str] = "manual"
    serving_size: Optional[str] = None
    calories_per_serving: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    sugar_g: Optional[float] = None


class NutritionInfoResponse(BaseModel):
    item_id: str
    item_name: str
    has_nutrition: bool
    serving_size: Optional[str] = None
    calories_per_serving: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    sugar_g: Optional[float] = None
    source: Optional[str] = None
    updated_at: Optional[str] = None


# ── Routes ─────────────────────────────────────────────────────────────


@router.get("/nutrition/lookup", response_model=NutritionSearchResponse)
async def lookup_nutrition(
    q: str = Query(..., min_length=2, description="Item name to search for"),
    limit: int = Query(5, ge=1, le=20),
):
    """Search Open Food Facts for nutrition info by product name."""
    results = search_by_name(q, limit=limit)
    return NutritionSearchResponse(
        query=q,
        count=len(results),
        results=[
            NutritionSearchResult(
                product_name=r.product_name,
                brand=r.brand,
                category=r.category,
                barcode=r.barcode,
                serving_size=r.serving_size,
                image_url=r.image_url,
                nutrition=r.nutrition,
                allergens=r.allergens,
                ingredients_text=r.ingredients_text,
                source=r.source,
            )
            for r in results
        ],
    )


@router.get("/inventory/{item_id}/nutrition", response_model=NutritionInfoResponse)
async def get_item_nutrition(item_id: str, db: Session = Depends(get_db)):
    """Get nutrition info for an inventory item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    nf = db.query(NutritionFact).filter(
        NutritionFact.inventory_item_id == item.id
    ).first()

    return NutritionInfoResponse(
        item_id=item.id,
        item_name=item.canonical_name or "",
        has_nutrition=nf is not None,
        serving_size=nf.serving_size if nf else None,
        calories_per_serving=nf.calories_per_serving if nf else None,
        protein_g=nf.protein_g if nf else None,
        carbs_g=nf.carbs_g if nf else None,
        fat_g=nf.fat_g if nf else None,
        fiber_g=nf.fiber_g if nf else None,
        sodium_mg=nf.sodium_mg if nf else None,
        sugar_g=nf.sugar_g if nf else None,
        source=nf.source if nf else None,
        updated_at=nf.updated_at.isoformat() if nf and nf.updated_at else None,
    )


@router.post("/inventory/{item_id}/nutrition", response_model=NutritionInfoResponse)
async def save_item_nutrition(
    item_id: str,
    req: SaveNutritionRequest,
    db: Session = Depends(get_db),
):
    """Save or update nutrition info for an inventory item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    nf = db.query(NutritionFact).filter(
        NutritionFact.inventory_item_id == item.id
    ).first()

    if nf:
        # Update existing
        nf.source = req.source or nf.source
        nf.serving_size = req.serving_size or nf.serving_size
        if req.calories_per_serving is not None:
            nf.calories_per_serving = req.calories_per_serving
        if req.protein_g is not None:
            nf.protein_g = req.protein_g
        if req.carbs_g is not None:
            nf.carbs_g = req.carbs_g
        if req.fat_g is not None:
            nf.fat_g = req.fat_g
        if req.fiber_g is not None:
            nf.fiber_g = req.fiber_g
        if req.sodium_mg is not None:
            nf.sodium_mg = req.sodium_mg
        if req.sugar_g is not None:
            nf.sugar_g = req.sugar_g
    else:
        nf = NutritionFact(
            inventory_item_id=item.id,
            source=req.source or "manual",
            serving_size=req.serving_size,
            calories_per_serving=req.calories_per_serving,
            protein_g=req.protein_g,
            carbs_g=req.carbs_g,
            fat_g=req.fat_g,
            fiber_g=req.fiber_g,
            sodium_mg=req.sodium_mg,
            sugar_g=req.sugar_g,
        )
        db.add(nf)

    db.commit()
    db.refresh(nf)

    return NutritionInfoResponse(
        item_id=item.id,
        item_name=item.canonical_name or "",
        has_nutrition=True,
        serving_size=nf.serving_size,
        calories_per_serving=nf.calories_per_serving,
        protein_g=nf.protein_g,
        carbs_g=nf.carbs_g,
        fat_g=nf.fat_g,
        fiber_g=nf.fiber_g,
        sodium_mg=nf.sodium_mg,
        sugar_g=nf.sugar_g,
        source=nf.source,
        updated_at=nf.updated_at.isoformat() if nf.updated_at else None,
    )
