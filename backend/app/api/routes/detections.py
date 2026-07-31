"""Detection review — per-item approval/rejection of vision pipeline results."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import (
    Capture,
    InventoryItem,
    InventoryState,
    Observation,
)
from app.models.schemas import ObservationItem

logger = __import__("logging").getLogger("pantry-api.detections")

router = APIRouter()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Request / Response models ──────────────────────────────────────────


class DetectionItem(BaseModel):
    """One detected item from an observation, enriched with inventory status."""

    index: int  # position in the observation items list
    observation_id: str
    capture_id: str
    name: str
    brand: Optional[str] = None
    package_type: Optional[str] = None
    quantity_estimate: Optional[int] = None
    confidence: float
    in_inventory: bool = False
    inventory_item_id: Optional[str] = None
    inventory_state_id: Optional[str] = None
    current_count: Optional[int] = None
    current_par: Optional[int] = None


class DetectionsResponse(BaseModel):
    capture_id: str
    capture_status: str
    detection_count: int
    items: list[DetectionItem]


class ApproveDetectionRequest(BaseModel):
    """Optional overrides when approving a detection."""
    name: Optional[str] = None
    brand: Optional[str] = None
    package_type: Optional[str] = None
    quantity_estimate: Optional[int] = None
    count: Optional[int] = None
    par_level: Optional[int] = None
    expires_at: Optional[str] = None  # ISO date


class EditDetectionRequest(BaseModel):
    name: str
    brand: Optional[str] = None
    package_type: Optional[str] = None
    quantity_estimate: Optional[int] = None
    count: int = 1
    par_level: Optional[int] = None
    expires_at: Optional[str] = None


class DetectionActionResponse(BaseModel):
    success: bool
    message: str
    detection_index: int
    capture_id: str


# ── Helpers ────────────────────────────────────────────────────────────


def _find_existing_item(db: Session, name: str, brand: Optional[str] = None) -> Optional[InventoryItem]:
    """Find an inventory item matching name (and brand if given)."""
    q = db.query(InventoryItem).filter(InventoryItem.canonical_name.ilike(name.strip()))
    if brand:
        q = q.filter(InventoryItem.brand.ilike(brand.strip()))
    return q.first()


def _add_to_inventory(
    db: Session,
    capture: Capture,
    name: str,
    brand: Optional[str] = None,
    package_type: Optional[str] = None,
    quantity_estimate: Optional[int] = None,
    count: int = 1,
    par_level: Optional[int] = None,
    expires_at: Optional[str] = None,
) -> tuple[InventoryItem, InventoryState]:
    """Add an item to inventory from a detection."""
    item = _find_existing_item(db, name, brand)
    if not item:
        item = InventoryItem(
            canonical_name=name.strip().title(),
            brand=brand.strip().title() if brand else None,
            package_type=package_type or "other",
        )
        db.add(item)
        db.flush()

    state = db.query(InventoryState).filter(
        InventoryState.item_id == item.id,
    ).first()

    if state:
        state.count_estimate = count
        state.confidence = 1.0
        state.is_manual = True
        if par_level is not None:
            state.par_level = par_level
    else:
        state = InventoryState(
            item_id=item.id,
            count_estimate=count,
            par_level=par_level or 0,
            confidence=1.0,
            is_manual=True,
        )
        db.add(state)
        db.flush()

    if expires_at:
        try:
            state.expires_at = datetime.fromisoformat(expires_at)
        except ValueError:
            pass

    if quantity_estimate:
        state.count_estimate = quantity_estimate

    db.commit()
    db.refresh(item)
    db.refresh(state)
    return item, state


def _remove_from_inventory(db: Session, capture: Capture, name: str, brand: Optional[str] = None) -> bool:
    """Remove an item from inventory that was added from this capture."""
    item = _find_existing_item(db, name, brand)
    if not item:
        return False

    state = db.query(InventoryState).filter(
        InventoryState.item_id == item.id,
        InventoryState.capture_id == capture.id,
        InventoryState.is_manual == False,
    ).first()

    if state:
        db.delete(state)
        db.commit()
        return True

    # Fallback: remove any state with this name
    state = db.query(InventoryState).filter(
        InventoryState.item_id == item.id,
    ).first()
    if state:
        db.delete(state)
        db.commit()
        return True

    return False


# ── Routes ─────────────────────────────────────────────────────────────


@router.get("/captures/{capture_id}/detections", response_model=DetectionsResponse)
async def list_detections(capture_id: str, db: Session = Depends(get_db)):
    """Return all detected items from a capture's observations, enriched with inventory status."""
    capture = db.query(Capture).filter(Capture.id == capture_id).first()
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")

    obs_list = (
        db.query(Observation)
        .filter(Observation.capture_id == capture_id)
        .order_by(Observation.created_at.desc())
        .all()
    )

    items: list[DetectionItem] = []
    seen_names: set[str] = set()

    for obs in obs_list:
        if not obs.raw_json:
            continue

        raw = obs.raw_json
        item_list = []
        if isinstance(raw, dict):
            item_list = raw.get("items", [])
        elif isinstance(raw, list):
            item_list = raw

        for idx, detected in enumerate(item_list):
            if not isinstance(detected, dict):
                continue

            name = (detected.get("name") or "").strip()
            if not name:
                continue

            # Deduplicate
            key = name.lower()
            if key in seen_names:
                continue
            seen_names.add(key)

            brand = detected.get("brand")
            confidence = detected.get("confidence", 0)

            # Check if already in inventory
            existing_item = _find_existing_item(db, name, brand)
            in_inventory = False
            state_id = None
            item_id = None
            current_count = None
            current_par = None

            if existing_item:
                state = db.query(InventoryState).filter(
                    InventoryState.item_id == existing_item.id
                ).first()
                if state and state.confidence > 0:
                    in_inventory = True
                    state_id = state.id
                    item_id = existing_item.id
                    current_count = state.count_estimate
                    current_par = state.par_level

            items.append(DetectionItem(
                index=idx,
                observation_id=obs.id,
                capture_id=capture_id,
                name=name,
                brand=brand,
                package_type=detected.get("package_type"),
                quantity_estimate=detected.get("quantity_estimate"),
                confidence=confidence,
                in_inventory=in_inventory,
                inventory_item_id=item_id,
                inventory_state_id=state_id,
                current_count=current_count,
                current_par=current_par,
            ))

    items.sort(key=lambda x: x.confidence, reverse=True)
    for i, item in enumerate(items):
        item.index = i

    return DetectionsResponse(
        capture_id=capture_id,
        capture_status=capture.status,
        detection_count=len(items),
        items=items,
    )


@router.post("/captures/{capture_id}/detections/{index}/approve", response_model=DetectionActionResponse)
async def approve_detection(
    capture_id: str,
    index: int,
    req: Optional[ApproveDetectionRequest] = None,
    db: Session = Depends(get_db),
):
    """Approve a detected item — add it to inventory with optional overrides."""
    capture = db.query(Capture).filter(Capture.id == capture_id).first()
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")

    obs = (
        db.query(Observation)
        .filter(Observation.capture_id == capture_id)
        .order_by(Observation.created_at.desc())
        .first()
    )
    if not obs or not obs.raw_json:
        raise HTTPException(status_code=404, detail="No observations found for this capture")

    raw = obs.raw_json
    item_list = []
    if isinstance(raw, dict):
        item_list = raw.get("items", [])
    elif isinstance(raw, list):
        item_list = raw

    if index < 0 or index >= len(item_list):
        raise HTTPException(status_code=400, detail=f"Detection index {index} out of range (0-{len(item_list)-1})")

    detected = item_list[index]
    name = (req.name if req and req.name else detected.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Item name is required")

    count = req.count if req and req.count is not None else detected.get("quantity_estimate", 1)
    _add_to_inventory(
        db, capture,
        name=name,
        brand=req.brand if req and req.brand else detected.get("brand"),
        package_type=req.package_type if req and req.package_type else detected.get("package_type"),
        quantity_estimate=detected.get("quantity_estimate"),
        count=count,
        par_level=req.par_level if req else None,
        expires_at=req.expires_at if req else None,
    )

    return DetectionActionResponse(
        success=True,
        message=f"Approved '{name}' — added to inventory",
        detection_index=index,
        capture_id=capture_id,
    )


@router.post("/captures/{capture_id}/detections/{index}/reject", response_model=DetectionActionResponse)
async def reject_detection(
    capture_id: str,
    index: int,
    db: Session = Depends(get_db),
):
    """Reject a detected item — remove from inventory if it was auto-added."""
    capture = db.query(Capture).filter(Capture.id == capture_id).first()
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")

    obs = (
        db.query(Observation)
        .filter(Observation.capture_id == capture_id)
        .order_by(Observation.created_at.desc())
        .first()
    )
    if not obs or not obs.raw_json:
        raise HTTPException(status_code=404, detail="No observations found for this capture")

    raw = obs.raw_json
    item_list = []
    if isinstance(raw, dict):
        item_list = raw.get("items", [])
    elif isinstance(raw, list):
        item_list = raw

    if index < 0 or index >= len(item_list):
        raise HTTPException(status_code=400, detail=f"Detection index {index} out of range")

    detected = item_list[index]
    name = (detected.get("name") or "").strip()
    brand = detected.get("brand")

    _remove_from_inventory(db, capture, name, brand)

    return DetectionActionResponse(
        success=True,
        message=f"Rejected '{name}' — removed from inventory",
        detection_index=index,
        capture_id=capture_id,
    )


@router.post("/captures/{capture_id}/detections/{index}/edit", response_model=DetectionActionResponse)
async def edit_detection(
    capture_id: str,
    index: int,
    req: EditDetectionRequest,
    db: Session = Depends(get_db),
):
    """Edit a detected item with corrected info and add it to inventory."""
    capture = db.query(Capture).filter(Capture.id == capture_id).first()
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")

    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Item name is required")

    _add_to_inventory(
        db, capture,
        name=req.name,
        brand=req.brand,
        package_type=req.package_type,
        quantity_estimate=req.quantity_estimate,
        count=req.count,
        par_level=req.par_level,
        expires_at=req.expires_at,
    )

    return DetectionActionResponse(
        success=True,
        message=f"Edited and approved '{req.name}' — updated in inventory",
        detection_index=index,
        capture_id=capture_id,
    )
