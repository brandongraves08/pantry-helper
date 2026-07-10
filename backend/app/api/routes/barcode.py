"""Barcode scanning routes.

Look up product info from barcodes via Open Food Facts,
link barcodes to inventory items, and add scanned items to inventory.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import BarcodeLookup, InventoryItem, InventoryState, InventoryEvent
from app.models.schemas import (
    BarcodeLookupResult,
    BarcodeLookupNutrition,
    BarcodeLinkRequest,
    BarcodeLinkResponse,
    BarcodeAddToInventoryRequest,
)
from app.services.barcode import lookup_barcode

logger = logging.getLogger("pantry-api.barcode")

router = APIRouter()


@router.get("/barcode/{barcode}", response_model=BarcodeLookupResult)
async def scan_barcode(barcode: str, db: Session = Depends(get_db)):
    """Look up a barcode and return product information.

    Checks the local cache first, then falls back to Open Food Facts.
    Also indicates if the barcode is already linked to an inventory item.
    """
    logger.info("Barcode lookup", extra={"barcode": barcode})

    # Check local cache first
    cached = db.query(BarcodeLookup).filter(
        BarcodeLookup.barcode == barcode.strip()
    ).first()

    if cached:
        logger.info("Barcode found in local cache", extra={"barcode": barcode})
        # Bump lookup count
        cached.lookup_count = (cached.lookup_count or 1) + 1
        cached.last_lookup_at = datetime.utcnow()
        db.commit()

        nutrition = None
        if cached.nutrition_json:
            nutrition = BarcodeLookupNutrition(**cached.nutrition_json)

        return BarcodeLookupResult(
            barcode=cached.barcode,
            found=True,
            product_name=cached.product_name,
            brand=cached.brand,
            category=cached.category,
            package_type=cached.package_type,
            image_url=cached.image_url,
            quantity=cached.quantity_label,
            serving_size=cached.serving_size,
            nutrition=nutrition,
            allergens=cached.allergens_json or [],
            ingredients_text=cached.ingredients_text,
            already_in_inventory=cached.inventory_item_id is not None,
            existing_item_name=cached.inventory_item.canonical_name if cached.inventory_item else None,
            source=cached.source or "cache",
        )

    # External lookup
    result = lookup_barcode(barcode)

    if not result.found:
        return BarcodeLookupResult(barcode=barcode, found=False)

    # Cache result in DB
    cached = BarcodeLookup(
        barcode=barcode.strip(),
        product_name=result.product_name,
        brand=result.brand,
        category=result.category,
        package_type=result.package_type,
        image_url=result.image_url,
        quantity_label=result.quantity,
        serving_size=result.serving_size,
        nutrition_json=result.nutrition if result.nutrition else None,
        allergens_json=result.allergens if result.allergens else None,
        ingredients_text=result.ingredients_text,
        source=result.source,
    )
    db.add(cached)
    db.commit()

    nutrition = None
    if result.nutrition:
        nutrition = BarcodeLookupNutrition(**{k: v for k, v in result.nutrition.items() if v is not None})

    return BarcodeLookupResult(
        barcode=result.barcode,
        found=True,
        product_name=result.product_name,
        brand=result.brand,
        category=result.category,
        package_type=result.package_type,
        image_url=result.image_url,
        quantity=result.quantity,
        serving_size=result.serving_size,
        nutrition=nutrition,
        allergens=result.allergens,
        ingredients_text=result.ingredients_text,
        source=result.source,
    )


@router.post("/barcode/link", response_model=BarcodeLinkResponse)
async def link_barcode_to_item(
    request: BarcodeLinkRequest,
    db: Session = Depends(get_db),
):
    """Link a barcode to an existing inventory item.

    This allows subsequent scans of the same barcode to reference the item.
    """
    logger.info("Barcode link requested", extra={
        "barcode": request.barcode,
        "item_name": request.inventory_item_name,
    })

    # Find or create the inventory item
    item = db.query(InventoryItem).filter(
        InventoryItem.canonical_name == request.inventory_item_name
    ).first()

    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Inventory item '{request.inventory_item_name}' not found. "
                   f"Add it to inventory first, or use the add-to-inventory endpoint.",
        )

    # Find or create the barcode lookup entry
    barcode_entry = db.query(BarcodeLookup).filter(
        BarcodeLookup.barcode == request.barcode.strip()
    ).first()

    if not barcode_entry:
        # Try to look up the barcode first
        result = lookup_barcode(request.barcode)
        barcode_entry = BarcodeLookup(
            barcode=request.barcode.strip(),
            product_name=result.product_name,
            brand=result.brand,
            category=result.category,
            package_type=result.package_type,
            source=result.source,
        )
        db.add(barcode_entry)
        db.flush()

    barcode_entry.inventory_item_id = item.id
    barcode_entry.lookup_count = (barcode_entry.lookup_count or 1) + 1
    barcode_entry.last_lookup_at = datetime.utcnow()
    db.commit()

    logger.info("Barcode linked to inventory item", extra={
        "barcode": request.barcode,
        "item_id": item.id,
    })

    return BarcodeLinkResponse(
        success=True,
        barcode=request.barcode,
        inventory_item_name=item.canonical_name,
        message=f"Barcode {request.barcode} linked to {item.canonical_name}",
    )


@router.post("/barcode/add-to-inventory")
async def add_barcode_to_inventory(
    request: BarcodeAddToInventoryRequest,
    db: Session = Depends(get_db),
):
    """Add a barcode-scanned product directly to inventory.

    Creates or updates an inventory item from barcode scan data.
    """
    logger.info("Add barcode to inventory", extra={
        "barcode": request.barcode,
        "product_name": request.product_name,
    })

    # Find or create inventory item
    item = db.query(InventoryItem).filter(
        InventoryItem.canonical_name == request.product_name
    ).first()

    if not item:
        item = InventoryItem(
            canonical_name=request.product_name,
            brand=request.brand,
            package_type=request.package_type,
            category=request.category,
        )
        db.add(item)
        db.flush()
        logger.info("Created new inventory item from barcode", extra={
            "item_id": item.id, "product": request.product_name,
        })

    # Update existing item metadata if not already set
    if request.brand and not item.brand:
        item.brand = request.brand
    if request.category and not item.category:
        item.category = request.category
    if request.package_type and not item.package_type:
        item.package_type = request.package_type

    # Update/create inventory state
    state = db.query(InventoryState).filter(
        InventoryState.item_id == item.id
    ).first()

    if state:
        delta = request.quantity_estimate - (state.count_estimate or 0)
        state.count_estimate = request.quantity_estimate
        state.confidence = 1.0
        state.is_manual = True
        state.last_seen_at = datetime.utcnow()
        if request.par_level is not None:
            state.par_level = request.par_level
        if request.expires_at is not None:
            state.expires_at = request.expires_at
    else:
        state = InventoryState(
            item_id=item.id,
            count_estimate=request.quantity_estimate,
            confidence=1.0,
            is_manual=True,
            last_seen_at=datetime.utcnow(),
            par_level=request.par_level,
            expires_at=request.expires_at,
        )
        db.add(state)
        delta = request.quantity_estimate

    # Record inventory event
    event = InventoryEvent(
        item_id=item.id,
        event_type="manual_override",
        delta=delta,
        details={
            "source": "barcode_scan",
            "barcode": request.barcode,
        },
    )
    db.add(event)

    # Link barcode to this item
    barcode_entry = db.query(BarcodeLookup).filter(
        BarcodeLookup.barcode == request.barcode.strip()
    ).first()

    if barcode_entry:
        barcode_entry.inventory_item_id = item.id
        barcode_entry.lookup_count = (barcode_entry.lookup_count or 1) + 1
        barcode_entry.last_lookup_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "item_id": item.id,
        "item_name": item.canonical_name,
        "count": request.quantity_estimate,
        "message": f"Added {request.quantity_estimate}x {request.product_name} to inventory",
    }
