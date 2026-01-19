# Phase 5 API Quick Reference

## Base URL
```
http://localhost:8000/v1
```

## Device Management API

### Register a Device
```bash
curl -X POST http://localhost:8000/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kitchen Pantry Camera",
    "device_id": "pantry-cam-001"
  }'

# Response:
{
  "id": "pantry-cam-001",
  "name": "Kitchen Pantry Camera",
  "device_token": "xxxxxxxxxxxxxxxxxxxxxxxx",  # Save this!
  "status": "inactive",
  "created_at": "2024-01-19T13:34:00"
}
```

### List All Devices
```bash
curl http://localhost:8000/v1/devices?skip=0&limit=100

# Response:
{
  "total": 5,
  "skip": 0,
  "limit": 100,
  "items": [
    {
      "id": "pantry-cam-001",
      "name": "Kitchen Pantry Camera",
      "status": "active",
      "battery_v": 3.95,
      "battery_pct": 42,
      "last_seen_at": "2024-01-19T13:30:00",
      "capture_count": 24
    }
  ]
}
```

### Get Device Details
```bash
curl http://localhost:8000/v1/devices/pantry-cam-001

# Response:
{
  "id": "pantry-cam-001",
  "name": "Kitchen Pantry Camera",
  "status": "active",
  "battery_v": 3.95,
  "battery_pct": 42,
  "rssi": -65,
  "last_seen_at": "2024-01-19T13:30:00",
  "total_captures": 24,
  "failed_captures": 1
}
```

### Get Device Health Metrics
```bash
curl http://localhost:8000/v1/devices/pantry-cam-001/health

# Response:
{
  "device_id": "pantry-cam-001",
  "is_healthy": true,
  "status": "active",
  "battery_v": 3.95,
  "battery_pct": 42,
  "rssi": -65,
  "last_seen_at": "2024-01-19T13:30:00",
  "captures_7d": 24,
  "success_rate_7d": 96,
  "captures_24h": 4,
  "success_rate_24h": 100
}
```

### Get Device Capture History
```bash
curl http://localhost:8000/v1/devices/pantry-cam-001/captures?days=7&status=complete

# Response:
{
  "device_id": "pantry-cam-001",
  "total": 24,
  "days": 7,
  "captures": [
    {
      "id": "cap-123",
      "trigger_type": "door",
      "captured_at": "2024-01-19T13:30:00",
      "status": "complete",
      "battery_v": 3.95,
      "rssi": -65
    }
  ]
}
```

### Update Device
```bash
curl -X PATCH http://localhost:8000/v1/devices/pantry-cam-001 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Camera Name"}'

# Response: Updated device object
```

### Delete Device
```bash
curl -X DELETE http://localhost:8000/v1/devices/pantry-cam-001

# Response:
{
  "success": true,
  "message": "Device deleted successfully"
}
```

---

## Advanced Inventory API

### Get Inventory Statistics
```bash
curl http://localhost:8000/v1/inventory/stats

# Response:
{
  "total_items": 47,
  "items_in_stock": 42,
  "items_out_of_stock": 5,
  "total_quantity": 156,
  "avg_confidence": 0.84,
  "confidence_breakdown": {
    "high": 40,
    "medium": 5,
    "low": 2
  }
}
```

### Get Item History
```bash
curl http://localhost:8000/v1/inventory/items/peanut%20butter/history?days=7

# Response:
{
  "item": {
    "canonical_name": "peanut butter",
    "brand": "Jif",
    "package_type": "jar"
  },
  "current": {
    "count": 2,
    "confidence": 0.92,
    "last_seen_at": "2024-01-19T13:30:00"
  },
  "history": [
    {
      "date": "2024-01-19T13:30:00",
      "count": 2,
      "event_type": "seen",
      "delta": 0
    }
  ],
  "total_events": 42
}
```

### Get Low Stock Items
```bash
curl http://localhost:8000/v1/inventory/low-stock?threshold=1

# Response:
{
  "threshold": 1,
  "item_count": 5,
  "items": [
    {
      "name": "milk",
      "brand": "Organic",
      "count": 0,
      "confidence": 0.88,
      "last_seen_at": "2024-01-18T10:00:00"
    }
  ]
}
```

### Get Stale Items
```bash
curl http://localhost:8000/v1/inventory/stale-items?days_threshold=7

# Response:
{
  "threshold_days": 7,
  "item_count": 3,
  "items": [
    {
      "name": "cereal",
      "last_seen_at": "2024-01-12T08:00:00",
      "days_since_seen": 7,
      "last_count": 1
    }
  ]
}
```

### Get Recent Changes
```bash
curl http://localhost:8000/v1/inventory/recent-changes?hours=24&event_type=seen

# Response:
{
  "hours": 24,
  "event_type_filter": "seen",
  "event_count": 12,
  "changes": [
    {
      "timestamp": "2024-01-19T13:30:00",
      "item_name": "pasta",
      "event_type": "seen",
      "delta": -1
    }
  ]
}
```

### Export Inventory (JSON)
```bash
curl http://localhost:8000/v1/inventory/export?format=json&include_history=true

# Response:
{
  "format": "json",
  "exported_at": "2024-01-19T13:34:00",
  "item_count": 47,
  "items": [
    {
      "name": "peanut butter",
      "brand": "Jif",
      "count": 2,
      "confidence": 0.92,
      "recent_events": [...]
    }
  ]
}
```

### Export Inventory (CSV)
```bash
curl http://localhost:8000/v1/inventory/export?format=csv

# Response: CSV content
# name,brand,package_type,count,confidence,last_seen,manual
# peanut butter,Jif,jar,2,0.92,2024-01-19T13:30:00,no
```

---

## Admin Storage API

### Get Storage Statistics
```bash
curl http://localhost:8000/v1/admin/storage/stats

# Response:
{
  "status": "ok",
  "storage": {
    "total_size_mb": 1234.5,
    "file_count": 156,
    "oldest_file": "2023-12-20T10:00:00",
    "newest_file": "2024-01-19T13:34:00"
  }
}
```

### Enforce Image Retention
```bash
# Keep images newer than 30 days
curl -X POST http://localhost:8000/v1/admin/storage/cleanup?days=30

# Response:
{
  "status": "success",
  "result": {
    "success": true,
    "deleted_count": 12,
    "freed_mb": 45.2,
    "errors": 0,
    "cutoff_date": "2023-12-20T13:34:00"
  }
}
```

### Clean Failed Captures
```bash
# Delete images from failed captures older than 7 days
curl -X POST http://localhost:8000/v1/admin/storage/cleanup-failed?days=7

# Response:
{
  "status": "success",
  "result": {
    "success": true,
    "deleted_count": 3,
    "freed_mb": 8.1,
    "errors": 0
  }
}
```

### Check Storage Quota
```bash
# Check if over 5GB quota, cleanup if needed
curl -X POST http://localhost:8000/v1/admin/storage/check-quota?max_mb=5000

# Response if under quota:
{
  "status": "ok",
  "result": {
    "over_quota": false,
    "current_size_mb": 1234.5,
    "limit_mb": 5000,
    "cleanup_needed": false
  }
}

# Response if over quota (auto-cleanup triggered):
{
  "status": "ok",
  "result": {
    "over_quota": true,
    "previous_size_mb": 5234.5,
    "current_size_mb": 4800.2,
    "freed_mb": 434.3,
    "cleanup_result": {...}
  }
}
```

### Clean Orphaned Images
```bash
# Remove images without DB records
curl -X POST http://localhost:8000/v1/admin/storage/cleanup-orphans

# Response:
{
  "status": "success",
  "deleted_count": 2
}
```

---

## Common Workflows

### 1. Set Up a New Device
```bash
# 1. Register device
RESPONSE=$(curl -X POST http://localhost:8000/v1/devices \
  -H "Content-Type: application/json" \
  -d '{"name": "Kitchen Camera"}')

DEVICE_ID=$(echo $RESPONSE | jq -r '.id')
DEVICE_TOKEN=$(echo $RESPONSE | jq -r '.device_token')

echo "Device ID: $DEVICE_ID"
echo "Device Token: $DEVICE_TOKEN"

# 2. Configure ESP32 with these values in firmware/src/config/config.cpp
# 3. Flash firmware to device
# 4. Monitor health
curl http://localhost:8000/v1/devices/$DEVICE_ID/health
```

### 2. Check Inventory Status
```bash
# Get summary statistics
curl http://localhost:8000/v1/inventory/stats | jq .

# Find low stock items
curl http://localhost:8000/v1/inventory/low-stock?threshold=2 | jq .

# Find stale items (not seen in 7 days)
curl http://localhost:8000/v1/inventory/stale-items?days_threshold=7 | jq .
```

### 3. Audit Recent Activity
```bash
# Get all inventory changes in last 24 hours
curl http://localhost:8000/v1/inventory/recent-changes?hours=24 | jq '.changes | sort_by(.timestamp) | reverse'

# Get all device captures in last 7 days
curl http://localhost:8000/v1/devices/pantry-cam-001/captures?days=7 | jq '.captures'
```

### 4. Manage Storage
```bash
# Check current usage
STATS=$(curl http://localhost:8000/v1/admin/storage/stats | jq '.storage')
SIZE=$(echo $STATS | jq '.total_size_mb')
echo "Current storage: ${SIZE}MB"

# If approaching quota, cleanup old images
if (( $(echo "$SIZE > 4500" | bc -l) )); then
  curl -X POST http://localhost:8000/v1/admin/storage/cleanup?days=30
fi

# Remove orphaned files
curl -X POST http://localhost:8000/v1/admin/storage/cleanup-orphans
```

### 5. Export Inventory Data
```bash
# Export as JSON with full history
curl http://localhost:8000/v1/inventory/export?format=json&include_history=true > inventory.json

# Export as CSV for spreadsheet
curl http://localhost:8000/v1/inventory/export?format=csv > inventory.csv

# View in spreadsheet
open inventory.csv  # macOS
xdg-open inventory.csv  # Linux
start inventory.csv  # Windows
```

---

## Error Handling

### Standard Error Response
```json
{
  "detail": "Device not found",
  "status_code": 404
}
```

### Common Status Codes
- `200`: Success
- `400`: Bad request (invalid parameters)
- `404`: Not found (device/item doesn't exist)
- `409`: Conflict (duplicate device ID)
- `422`: Validation error (invalid data types)
- `500`: Server error

---

## Environment Variables

Create `backend/.env`:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/pantry

# Storage
STORAGE_PATH=./storage
IMAGE_RETENTION_DAYS=30
MAX_STORAGE_MB=5000

# Vision API
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

---

## Performance Tips

✅ **Pagination**: Always use `limit` for list endpoints  
✅ **Date Filters**: Use `days` parameter to limit history queries  
✅ **Cleanup**: Run retention policy weekly, not daily  
✅ **Exports**: Use CSV for large datasets  
✅ **Monitoring**: Check `health` endpoint periodically  

---

**Documentation Generated**: 2024-01-19  
**Version**: Phase 5 Complete
