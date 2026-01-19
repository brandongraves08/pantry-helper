# Phase 5 Roadmap - Backend APIs & Polish

**Status:** Ready to Start  
**Estimated Duration:** 2-3 days  
**Priority:** High - Needed before full system testing

---

## Phase 5: Backend API Enhancements

### What Phase 5 Will Add

#### 1. Device Management API
**Files to Create/Modify:**
- `backend/app/api/routes/devices.py` (NEW - 150 lines)
- `backend/app/models/schemas.py` (Update - +50 lines)

**New Endpoints:**
```
GET  /v1/devices                      # List all devices
GET  /v1/devices/{device_id}          # Get device details
PATCH /v1/devices/{device_id}         # Update device settings
DELETE /v1/devices/{device_id}        # Deregister device
GET  /v1/devices/{device_id}/health   # Get device health metrics
```

**Response Example:**
```json
{
  "id": "pantry-cam-001",
  "name": "Kitchen Pantry Camera",
  "created_at": "2026-01-19T12:00:00Z",
  "last_seen_at": "2026-01-19T14:30:00Z",
  "battery_v": 3.95,
  "battery_pct": 78.1,
  "rssi": -65,
  "total_captures": 156,
  "failed_uploads": 2,
  "status": "active"
}
```

---

#### 2. Image Retention Policy
**Files to Create/Modify:**
- `backend/app/services/storage.py` (NEW - 100 lines)
- `backend/app/workers/retention.py` (NEW - 80 lines)

**Features:**
- Auto-delete images older than X days
- Keep observation data indefinitely
- Configurable retention periods
- Scheduled cleanup job
- Dry-run capability for testing

**Configuration:**
```python
# backend/.env
IMAGE_RETENTION_DAYS=30           # Delete images after 30 days
IMAGE_CLEANUP_CRON="0 2 * * *"    # Run at 2 AM daily
ENABLE_IMAGE_RETENTION=true       # Toggle feature
```

---

#### 3. Advanced Inventory Queries
**Files to Modify:**
- `backend/app/api/routes/inventory.py` (+100 lines)

**New Endpoints:**
```
GET /v1/inventory/history?start_date=2026-01-01&end_date=2026-01-31
GET /v1/inventory/export?format=csv    # Export to CSV
GET /v1/inventory/stats                 # Consumption analytics
GET /v1/inventory/items/{name}/history # Item-specific history
```

**Query Capabilities:**
- Filter by date range
- Export to CSV/JSON
- Consumption rate analysis
- Trend detection

---

#### 4. Enhanced Admin Endpoints
**Files to Modify:**
- `backend/app/api/routes/admin.py` (+80 lines)

**New Features:**
- System diagnostics endpoint
- Database statistics
- Cache status
- Worker metrics
- Cleanup triggers

```
GET  /v1/admin/diagnostics     # System health check
GET  /v1/admin/db-stats        # Database metrics
POST /v1/admin/cleanup-images  # Manual cleanup trigger
GET  /v1/admin/workers         # Worker status
```

---

## Implementation Order

### Day 1: Device Management
1. Create `backend/app/api/routes/devices.py`
2. Add device-related schemas
3. Implement device endpoints
4. Add tests for device API

### Day 2: Image Retention
1. Create storage service
2. Implement retention logic
3. Add Celery cleanup task
4. Add configuration options

### Day 3: Advanced Queries & Polish
1. Enhance inventory endpoints
2. Add export functionality
3. Implement admin diagnostics
4. Complete testing

---

## Key Considerations

### Database Changes
- No new migrations needed (using existing tables)
- Add indexes on common queries
- Consider partitioning for large image tables

### Error Handling
- Graceful degradation for missing devices
- Rollback on cleanup failures
- Detailed error logging

### Security
- Validate device_id on all operations
- Rate limit device list endpoint
- Audit device deletions

### Performance
- Cache device list (5-minute TTL)
- Batch image deletion queries
- Use async cleanup jobs

---

## Files & Estimated Lines

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Device API | `devices.py` | 150 | TODO |
| Retention Service | `storage.py` | 100 | TODO |
| Cleanup Job | `retention.py` | 80 | TODO |
| Enhanced Admin | `admin.py` | +80 | TODO |
| Tests | `test_devices.py` | 150 | TODO |
| **Total** | | **560** | |

---

## Example: Device Management Implementation

### Schema (Pydantic)
```python
class DeviceResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    last_seen_at: Optional[datetime]
    battery_v: Optional[float]
    battery_pct: Optional[float]
    rssi: Optional[int]
    total_captures: int
    failed_uploads: int
    status: str  # active, inactive, error

class DeviceUpdate(BaseModel):
    name: Optional[str]
    enabled: Optional[bool]
```

### Route
```python
@router.get("/devices")
async def list_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return [DeviceResponse.from_orm(d) for d in devices]

@router.get("/devices/{device_id}")
async def get_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter_by(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceResponse.from_orm(device)
```

---

## Testing Strategy

### Unit Tests
- Device CRUD operations
- Image cleanup logic
- Query filters

### Integration Tests
- Full device lifecycle
- Cleanup with actual DB
- API endpoint flows

### E2E Tests
- Device registration → images → cleanup
- Export and reimport

---

## Configuration Template

```python
# backend/app/config.py - Add to Settings class

class Settings(BaseSettings):
    # Image retention
    IMAGE_RETENTION_DAYS: int = 30
    IMAGE_CLEANUP_ENABLED: bool = True
    IMAGE_CLEANUP_CRON: str = "0 2 * * *"
    
    # Device management
    DEVICE_INACTIVITY_DAYS: int = 7
    MARK_INACTIVE_AFTER_DAYS: int = 14
    
    # Query limits
    MAX_HISTORY_RESULTS: int = 10000
    MAX_EXPORT_SIZE: int = 100000  # rows
```

---

## Migration Checklist

Before moving to Phase 6:

- [ ] Device management API complete
- [ ] Image retention working
- [ ] Export functionality tested
- [ ] Admin endpoints enhanced
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Code reviewed

---

## What Phase 6 Will Require

Once Phase 5 is complete:
- Frontend needs to call device API
- WebSocket updates for device status
- Export button in web UI
- Settings panel for retention config

---

**Next Action:** Start Phase 5 device management implementation

**Estimated Completion:** 2-3 days

**Then Proceed To:** Phase 6 - Web UI & WebSocket Features
