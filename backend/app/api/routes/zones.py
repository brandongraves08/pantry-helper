"""Zone management API for spatial learning"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import Zone, Device
from app.services.zones import ZoneService

router = APIRouter(prefix="/zones", tags=["zones"])

class ZoneCreate(BaseModel):
    name: str
    x: float
    y: float
    width: float
    height: float
    expected_item_type: Optional[str] = None
    notes: Optional[str] = None

class ZoneResponse(BaseModel):
    id: str
    device_id: str
    name: str
    x: float
    y: float
    width: float
    height: float
    expected_item_type: Optional[str]
    notes: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True

class ZonePatternResponse(BaseModel):
    zone_id: str
    inventory_item_id: str
    item_name: str
    occurrence_count: int
    avg_quantity: Optional[float]
    confidence_score: float
    last_seen_at: Optional[str]

@router.post("/device/{device_id}", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(device_id: str, zone_data: ZoneCreate, db: Session = Depends(get_db)):
    """Create a new zone for a device"""
    # Verify device exists
    device = db.query(Device).filter_by(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    # Create zone
    zone_service = ZoneService(db)
    zone = zone_service.create_zone(
        device_id=device_id,
        name=zone_data.name,
        x=zone_data.x,
        y=zone_data.y,
        width=zone_data.width,
        height=zone_data.height,
        expected_item_type=zone_data.expected_item_type,
        notes=zone_data.notes
    )
    return zone

@router.get("/device/{device_id}", response_model=List[ZoneResponse])
def list_zones(device_id: str, db: Session = Depends(get_db)):
    """List all zones for a device"""
    zone_service = ZoneService(db)
    zones = zone_service.get_zones_for_device(device_id)
    return zones

@router.get("/{zone_id}/patterns", response_model=List[ZonePatternResponse])
def get_zone_patterns(zone_id: str, db: Session = Depends(get_db)):
    """Get learned patterns for a zone"""
    # Verify zone exists
    zone = db.query(Zone).filter_by(id=zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
    
    zone_service = ZoneService(db)
    patterns = zone_service.get_zone_patterns(zone_id)
    
    return [
        {
            "zone_id": p.zone_id,
            "inventory_item_id": p.inventory_item_id,
            "item_name": p.inventory_item.canonical_name if p.inventory_item else "Unknown",
            "occurrence_count": p.occurrence_count,
            "avg_quantity": p.avg_quantity,
            "confidence_score": p.confidence_score,
            "last_seen_at": p.last_seen_at.isoformat() if p.last_seen_at else None
        }
        for p in patterns
    ]

@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(zone_id: str, db: Session = Depends(get_db)):
    """Soft-delete a zone by marking inactive"""
    zone = db.query(Zone).filter_by(id=zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
    
    zone.is_active = False
    db.commit()
    return None
