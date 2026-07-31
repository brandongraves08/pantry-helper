# Pantry Inventory - Quick Reference

## Essential Commands

### First Time Setup
```bash
make all                  # Install all dependencies
make backend-seed         # Create test database with devices
cp backend/.env.example backend/.env  # Configure environment
# Edit backend/.env and add OPENAI_API_KEY
```

### Development (Run in Separate Terminals)

**Terminal 1 - Backend API:**
```bash
make backend-run
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Terminal 2 - Web UI:**
```bash
make web-dev
# UI: http://localhost:5173
```

### Testing
```bash
make backend-test         # Run all tests
cd backend && python -m pytest tests/test_ingest.py -v  # Single file
```

### Database
```bash
make backend-seed         # Initialize and populate with test data
cd backend && python scripts/seed_db.py add-device pantry-cam-003 "My Device"  # Add device
```

### Firmware
```bash
make firmware-build       # Compile for ESP32-CAM
make firmware-upload      # Upload to connected device
make firmware-monitor     # View serial output
```

### Cleanup
```bash
make clean               # Remove build artifacts
```

## API Endpoints

### Test API Health
```bash
curl http://localhost:8000/health
```

### View API Docs (Interactive)
```bash
# Open in browser:
http://localhost:8000/docs
```

### Get Current Inventory
```bash
curl http://localhost:8000/v1/inventory | jq .
```

### Get Inventory History (Last 7 Days)
```bash
curl "http://localhost:8000/v1/inventory/history?days=7" | jq .
```

### Add/Update Inventory Item Manually
```bash
curl -X POST http://localhost:8000/v1/inventory/override \
  -H "Content-Type: application/json" \
  -d '{
    "item_name": "peanut butter",
    "count_estimate": 3,
    "notes": "refilled"
  }'
```

### Upload Image (ESP32 Simulation)
```bash
# First, get a token from `make backend-seed` output

curl -X POST http://localhost:8000/v1/ingest \
  -F "device_id=pantry-cam-001" \
  -F "token=<YOUR_TOKEN_HERE>" \
  -F "timestamp=$(date -u +%Y-%m-%dT%H:%M:%S)" \
  -F "trigger_type=door" \
  -F "battery_v=4.2" \
  -F "rssi=-45" \
  -F "image=@test_image.jpg"
```

## File Locations

### Important Config Files
- `backend/.env` - Backend environment variables (DATABASE_URL, OPENAI_API_KEY, etc.)
- `firmware/src/config/config.cpp` - ESP32 WiFi credentials and API endpoint
- `web/src/api.js` - Web UI API endpoint configuration

### Key Implementation Files
- `backend/app/main.py` - FastAPI application setup
- `backend/app/services/vision.py` - OpenAI Vision integration (needs implementation)
- `backend/app/services/inventory.py` - Inventory delta calculation
- `firmware/src/main.cpp` - ESP32 main event loop
- `web/src/App.jsx` - React main component

### Documentation
- `README.md` - Project overview and quick start
- `ARCHITECTURE.md` - System design and data models
- `DEVELOPMENT.md` - Development workflows and debugging
- `BUILD_SUMMARY.md` - What's been built (this session)

## Key Concepts

### Device Authentication
- Each ESP32 has a unique token (pre-shared secret)
- Tokens are hashed in database with SHA256
- Device sends token in `POST /v1/ingest` request
- Invalid tokens rejected with 401 Unauthorized

### Inventory Delta Logic
- Confidence threshold: 0.70 (70%)
- Items below threshold are ignored
- Items not seen for 7 days marked stale
- Manual overrides always win
- All changes tracked in `inventory_events` table

### Data Files Structure
```
Images: ./storage/images/           (UUID-named JPEG files)
Database: ./pantry.db               (SQLite in dev, or PostgreSQL)
Logs: stdout (make backend-run)
```

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Check database connection
cd backend && python -c "from app.db.database import SessionLocal; db = SessionLocal(); print('OK')"

# Enable debug logging
# Edit backend/.env: LOG_LEVEL=DEBUG
```

### Web UI won't connect to API
```bash
# Ensure backend is running
curl http://localhost:8000/health

# Check web UI is proxy-ing correctly
# Should see requests in backend terminal
```

### Tests fail
```bash
# Clear pytest cache
cd backend && rm -rf .pytest_cache
make backend-test

# Run verbose mode
cd backend && python -m pytest tests/ -vv
```

### Firmware upload fails
```bash
# List USB ports
ls /dev/ttyUSB*    # Linux
ls /dev/tty.*      # macOS

# Try upload with verbose output
cd firmware && pio run -e esp32-cam -t upload -v
```

## Development Workflow

1. **Start**: `make backend-run` + `make web-dev`
2. **Edit code** in your IDE
3. **Test changes**: 
   - Backend auto-reloads (Uvicorn reload mode)
   - Web auto-reloads (Vite HMR)
4. **Run tests**: `make backend-test`
5. **View results**: Browser at http://localhost:5173

## Database Operations

### View Database Contents (SQLite)
```bash
# Connect to SQLite database
sqlite3 pantry.db

# List tables
.tables

# View devices
SELECT id, name, last_seen_at FROM devices;

# View inventory
SELECT * FROM inventory_items;

# Exit
.quit
```

### Reset Database
```bash
rm pantry.db                    # Delete SQLite file
make backend-seed              # Recreate with fresh data
```

### Add New Device Programmatically
```bash
cd backend
python -c "
from scripts.seed_db import create_test_device, generate_token, SessionLocal
db = SessionLocal()
token = generate_token()
create_test_device(db, 'pantry-cam-999', 'Test Device', token)
"
```

## Performance Tuning

### Speed Up Tests
```bash
cd backend
# Run tests in parallel (requires pytest-xdist)
python -m pytest tests/ -n auto

# Skip slow tests
python -m pytest tests/ -m "not slow"
```

### Reduce API Response Time
- Add database indexes on frequently queried columns
- Implement pagination for large result sets
- Cache OpenAI Vision results
- Use pagination in `/v1/inventory/history`

## Monitoring

### Backend Logs
```bash
# Already visible in terminal running `make backend-run`
# Enable debug mode in backend/.env:
LOG_LEVEL=DEBUG
```

### Request Tracing
```bash
# Use browser DevTools Network tab (F12)
# Or use httpie for pretty-printed requests:
pip install httpie
http GET http://localhost:8000/v1/inventory
```

### Database Metrics
```bash
# View database file size (SQLite)
ls -lh pantry.db

# Count items in inventory
sqlite3 pantry.db "SELECT COUNT(*) FROM inventory_items;"
```

## Git Workflow

```bash
git status                      # See changes
git add .                       # Stage all
git commit -m "Description"     # Commit
git log --oneline              # View history
```

## Where to Go From Here

### Learn the System
1. Read `ARCHITECTURE.md` for system design
2. Check `BUILD_SUMMARY.md` for what's been built
3. Look at test files in `backend/tests/` for usage examples

### Implement Features
1. **Vision Analysis**: Complete `backend/app/services/vision.py`
2. **Async Jobs**: Add Celery/RQ for background processing
3. **Firmware**: Implement `firmware/src/camera/` and `firmware/src/upload/`
4. **UI Enhancements**: Add filters, search, analytics to web UI

### Deploy
1. Set up PostgreSQL database
2. Configure `backend/.env` for production
3. Build Docker container or deploy to cloud
4. Point ESP32 devices to production API endpoint

## Contact / Questions

Check `DEVELOPMENT.md` for more detailed guides on:
- Debugging strategies
- Adding new API endpoints
- Creating database migrations
- Testing patterns
- Code organization

---

**Happy Building!** 🚀

Last updated: 2026-01-13
