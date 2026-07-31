# Getting Started with Phase 2 Implementation

## Quick Start

### Prerequisites
```bash
# Python 3.9+
# pip (Python package manager)
# OpenAI API key
```

### One-Time Setup

```bash
# 1. Install dependencies
cd /home/brandon/projects/pantry-helper/backend
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env and add:
#   OPENAI_API_KEY=sk-your-key-here
#   DATABASE_URL=sqlite:///./pantry.db

# 3. Initialize database
python -m alembic upgrade head

# 4. Seed test data (optional)
python scripts/seed_db.py seed
```

### Running the System

```bash
# Terminal 1: Start backend API
cd /home/brandon/projects/pantry-helper/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start web UI (if desired)
cd /home/brandon/projects/pantry-helper/web
npm install  # First time only
npm run dev
```

The API will be available at `http://localhost:8000`  
API docs at `http://localhost:8000/docs`

## What You Can Do Now

### 1. Upload Images (from Device or Client)

```bash
curl -X POST http://localhost:8000/v1/ingest \
  -H "Authorization: Bearer your-device-token" \
  -F "image=@/path/to/pantry.jpg" \
  -F "trigger_type=door"
```

**Response** (image stored for later processing):
```json
{
  "capture_id": "cap-2026-01-15-abc123",
  "status": "stored",
  "timestamp": "2026-01-15T10:30:00Z"
}
```

### 2. Manually Process Images

```bash
# Process a specific image
curl -X POST http://localhost:8000/v1/admin/process-capture/cap-2026-01-15-abc123

# Response:
{
  "success": true,
  "capture_id": "cap-2026-01-15-abc123",
  "status": "complete",
  "items_found": 7,
  "observations": {
    "id": "obs-2026-01-15-xyz789",
    "items": [
      {"name": "milk", "quantity": 2, "confidence": 0.95},
      {"name": "eggs", "quantity": 1, "confidence": 0.89}
    ]
  }
}
```

### 3. Batch Process Pending Images

```bash
# Process up to 10 pending images
curl -X POST "http://localhost:8000/v1/admin/process-pending?limit=10"

# Response:
{
  "success": true,
  "processed": 10,
  "failed": 0,
  "skipped": 0
}
```

### 4. Check System Status

```bash
curl http://localhost:8000/v1/admin/stats

# Response:
{
  "devices": {"total": 2, "active": 1},
  "captures": {"total": 42, "pending": 3, "completed": 38, "failed": 1},
  "observations": {"total": 38},
  "inventory": {"items": 25, "last_update": "2026-01-15T10:45:00Z"}
}
```

### 5. View Current Inventory

```bash
curl http://localhost:8000/v1/inventory

# Response:
{
  "items": [
    {
      "id": "item-1",
      "name": "milk",
      "quantity": 2,
      "unit": "units",
      "last_seen": "2026-01-15T10:45:00Z",
      "confidence": 0.95
    },
    // ... more items
  ]
}
```

## Testing

### Run Unit Tests

```bash
# From backend directory
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_admin.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

### End-to-End Test

```bash
# 1. Create a test image (or use an existing one)
#    File should be: /tmp/test_pantry.jpg

# 2. Upload it
capture_id=$(curl -s -X POST http://localhost:8000/v1/ingest \
  -H "Authorization: Bearer device-token-123" \
  -F "image=@/tmp/test_pantry.jpg" \
  -F "trigger_type=door" | jq -r '.capture_id')

echo "Capture ID: $capture_id"

# 3. Process it
curl -X POST "http://localhost:8000/v1/admin/process-capture/$capture_id" | jq

# 4. Check inventory
curl http://localhost:8000/v1/inventory | jq
```

## Architecture Overview

### Data Flow

```
Image from Device
    ↓
POST /v1/ingest
    ↓
Capture Model (status: "stored")
    ↓
POST /v1/admin/process-capture/{id}  ← Manual trigger
    ↓
CaptureProcessor.process_capture()
    ↓
VisionAnalyzer.analyze_image()  (calls OpenAI Vision API)
    ↓
Extract JSON response
    ↓
Create Observation record
    ↓
InventoryManager.update_from_capture()
    ↓
Update InventoryItem quantities
    ↓
Create InventoryEvent (audit trail)
    ↓
Response success to client
```

### File Organization

```
backend/
├── app/
│   ├── main.py                      ← FastAPI app
│   ├── api/
│   │   └── routes/
│   │       ├── ingest.py            ← Image upload
│   │       ├── inventory.py         ← Inventory endpoints
│   │       └── admin.py            ← NEW: Admin endpoints
│   ├── services/
│   │   ├── vision.py               ← NEW: OpenAI integration
│   │   ├── inventory.py            ← Inventory logic
│   │   └── ...
│   ├── workers/
│   │   ├── capture.py              ← NEW: Background processor
│   │   └── __init__.py             ← NEW: Package marker
│   ├── db/
│   │   ├── models.py               ← Database models
│   │   └── ...
│   └── ...
├── tests/
│   ├── test_admin.py               ← NEW: Admin endpoint tests
│   ├── test_workers.py             ← NEW: Worker tests
│   └── ...
└── requirements.txt
```

## Configuration

### Environment Variables (.env)

```bash
# Required
OPENAI_API_KEY=sk-...your-key-here...

# Database (default: SQLite)
DATABASE_URL=sqlite:///./pantry.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/pantry

# Logging (default: INFO)
LOG_LEVEL=DEBUG  # or INFO, WARNING, ERROR

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Device Setup

Each device needs:
1. A unique device ID
2. A pre-shared token (hashed as SHA256)

```python
# Generated during setup
device_id = "kitchen-camera-001"
device_token = "device-token-abc123xyz"
device_token_hash = hashlib.sha256(device_token.encode()).hexdigest()
```

## Common Tasks

### Upload Multiple Images

```bash
for img in /path/to/images/*.jpg; do
  curl -X POST http://localhost:8000/v1/ingest \
    -H "Authorization: Bearer device-token-123" \
    -F "image=@$img" \
    -F "trigger_type=door"
  echo "Uploaded: $img"
done
```

### Process All Pending

```bash
# Keep processing until none pending
while true; do
  result=$(curl -s -X POST "http://localhost:8000/v1/admin/process-pending?limit=50")
  processed=$(echo $result | jq '.processed')
  
  if [ "$processed" -eq 0 ]; then
    echo "No more pending captures"
    break
  fi
  
  echo "Processed $processed captures"
done
```

### Monitor Processing

```bash
# Watch for changes (requires watch command)
watch -n 5 'curl -s http://localhost:8000/v1/admin/stats | jq'

# Or without watch - check repeatedly
for i in {1..10}; do
  curl -s http://localhost:8000/v1/admin/stats | jq '.captures'
  sleep 5
done
```

### Export Inventory

```bash
# Export to JSON
curl -s http://localhost:8000/v1/inventory | jq > inventory.json

# Export to CSV
curl -s http://localhost:8000/v1/inventory | jq -r \
  '.items[] | [.name, .quantity, .unit, .last_seen] | @csv' > inventory.csv
```

## Troubleshooting

### OpenAI API Not Working

```bash
# Check your API key
echo $OPENAI_API_KEY  # Should not be empty

# Test connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | jq '.data | length'
```

### Database Connection Issues

```bash
# Check database file exists
ls -lh pantry.db  # Should show file

# Run migrations
python -m alembic upgrade head

# Seed test data
python scripts/seed_db.py seed
```

### Image Upload Failing

```bash
# Check file exists and is valid
file /path/to/image.jpg  # Should say "JPEG image data"

# Check device token
curl -X POST http://localhost:8000/v1/ingest \
  -H "Authorization: Bearer invalid-token" \
  -F "image=@/path/to/image.jpg"
# Should return 401 Unauthorized
```

### Processing Hangs

```bash
# Check if OpenAI API is rate limited
# Look for:
#   "error": {"type": "rate_limit_error"}

# Wait a minute and retry
sleep 60
curl -X POST http://localhost:8000/v1/admin/process-pending
```

## Next Steps for Production

### 1. Add Task Queue
```python
# Use Celery for async processing
from celery import Celery
from app.workers.capture import get_processor

celery = Celery('pantry')

@celery.task
def process_capture_async(capture_id):
    return get_processor().process_capture(capture_id)
```

### 2. Add Rate Limiting
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/v1/admin/process-pending")
@limiter.limit("10/minute")
async def process_pending():
    ...
```

### 3. Add Request Authentication
```python
# Validate device tokens more strictly
# Add API key management for web clients
# Implement JWT tokens with expiration
```

### 4. Setup Monitoring
```python
# Add Prometheus metrics
# Setup Sentry for error tracking
# Configure structured logging (JSON)
```

## Getting Help

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Logs
```bash
# From backend directory
tail -f *.log  # Application logs
python -m pytest tests/ -v --tb=short  # Test output
```

### Status Files
- `STATUS.txt` - Project status and statistics
- `PHASE_2_SUMMARY.md` - What was implemented in Phase 2
- `IMPLEMENTATION_PHASE_2.md` - Detailed technical documentation
- `INDEX.md` - Navigation guide for all docs

---

**Ready to test?** Start with "Running the System" above, then work through "Common Tasks".
