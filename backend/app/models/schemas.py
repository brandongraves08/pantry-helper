from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class IngestRequest(BaseModel):
    """Ingest request from ESP32"""
    device_id: str
    timestamp: datetime
    trigger_type: str  # door, light, timer, manual
    battery_v: float
    rssi: int
    # Image is handled as multipart form data

class CaptureResponse(BaseModel):
    """Response to ingest request"""
    capture_id: str
    status: str
    message: Optional[str] = None

class InventoryItem(BaseModel):
    """Inventory item representation"""
    canonical_name: str
    brand: Optional[str] = None
    package_type: Optional[str] = None
    count_estimate: int
    confidence: float
    last_seen_at: datetime
    is_manual: bool = False
    notes: Optional[str] = None

class InventoryResponse(BaseModel):
    """Full inventory response"""
    items: List[InventoryItem]
    updated_at: datetime

class ObservationItem(BaseModel):
    """Parsed observation item from OpenAI Vision"""
    name: str
    brand: Optional[str] = None
    package_type: Optional[str] = None
    quantity_estimate: Optional[int] = None
    confidence: float

class VisionOutput(BaseModel):
    """OpenAI Vision API response structure"""
    scene_confidence: float
    items: List[ObservationItem]
    notes: Optional[str] = None

class InventoryOverride(BaseModel):
    """Manual inventory correction"""
    item_name: str
    count_estimate: int
    notes: Optional[str] = None
