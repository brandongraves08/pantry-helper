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

# Device Management Schemas

class DeviceCreate(BaseModel):
    """Request to create a new device"""
    name: str
    device_id: Optional[str] = None  # Auto-generated if not provided


class DeviceUpdate(BaseModel):
    """Request to update device settings"""
    name: Optional[str] = None
    enabled: Optional[bool] = None


class DeviceResponse(BaseModel):
    """Device information response"""
    id: str
    name: str
    created_at: datetime
    last_seen_at: Optional[datetime] = None
    battery_v: Optional[float] = None
    battery_pct: Optional[float] = None
    rssi: Optional[int] = None
    total_captures: int = 0
    failed_uploads: int = 0
    status: str  # active, idle, inactive, offline
    device_token: Optional[str] = None  # Only returned on creation


class DeviceListResponse(BaseModel):
    """Paginated list of devices"""
    items: List[DeviceResponse]
    total: int
    skip: int
    limit: int


class DeviceHealthResponse(BaseModel):
    """Detailed device health metrics"""
    device_id: str
    is_healthy: bool
    battery_v: Optional[float] = None
    battery_pct: Optional[float] = None
    rssi: Optional[int] = None
    last_seen_at: Optional[datetime] = None
    last_seen_ago_seconds: Optional[int] = None
    total_captures: int
    captures_7d: int
    captures_24h: int
    successful_7d: int
    failed_7d: int
    analyzing_7d: int
    success_rate_7d: float