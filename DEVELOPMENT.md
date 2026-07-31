# Pantry Inventory - Development Guide

This guide covers development workflows, debugging, and contributing to the Pantry Inventory project.

## Table of Contents
1. [Development Environment Setup](#development-environment-setup)
2. [Running Services](#running-services)
3. [Testing](#testing)
4. [Debugging](#debugging)
5. [Common Development Tasks](#common-development-tasks)
6. [Code Organization](#code-organization)

## Development Environment Setup

### 1. Clone and Initialize

```bash
git clone <repository>
cd pantry-helper
```

### 2. Install All Dependencies

```bash
make all
```

This installs:
- Backend Python dependencies
- Web UI Node dependencies
- Sets up the database

### 3. Configure Environment

#### Backend Configuration

```bash
cp backend/.env.example backend/.env
```

**Development `.env` template:**

```env
# Database - use SQLite for local development
DATABASE_URL=sqlite:///./pantry.db

# OpenAI - get key from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-key-here

# Storage
IMAGES_DIR=./storage/images

# Logging
LOG_LEVEL=DEBUG

# Server
HOST=0.0.0.0
PORT=8000
```

#### Firmware Configuration

Edit `firmware/src/config/config.cpp`:

```cpp
// Replace with your WiFi network
char ssid[64] = "YOUR_SSID";
char password[64] = "YOUR_PASSWORD";

// Device identifier - must match backend
char device_id[64] = "pantry-cam-001";

// Backend endpoint
char api_endpoint[256] = "http://192.168.1.100:8000/v1/ingest";

// Device token from `make backend-seed`
char api_token[256] = "your-token-here";
```

### 4. Seed Test Data

```bash
make backend-seed
```

This creates two test devices with tokens:
- `pantry-cam-001` (Kitchen Pantry)
- `pantry-cam-002` (Garage Storage)

Tokens are printed to console - save them for firmware config.

## Running Services

### Run Everything (Development)

```bash
# Terminal 1 - Backend API
make backend-run
# API at http://localhost:8000
# Docs at http://localhost:8000/docs

# Terminal 2 - Web UI
make web-dev
# UI at http://localhost:5173
```

### Individual Services

```bash
make backend-run    # FastAPI server (port 8000)
make web-dev        # React dev server (port 5173)
make firmware-build # Compile ESP32 firmware
make firmware-upload # Upload to device
make firmware-monitor # View serial output
```

## Testing

### Run All Tests

```bash
make backend-test
```

### Run Specific Test File

```bash
cd backend
python -m pytest tests/test_ingest.py -v
```

### Run Test with Coverage

```bash
cd backend
python -m pytest tests/ --cov=app --cov-report=html
```

### Test Without Mocking (Integration Tests)

```bash
cd backend
python -m pytest tests/ -v -m integration
```

## Debugging

### Backend Debugging

#### 1. Enable Debug Logging

Add to `backend/.env`:
```env
LOG_LEVEL=DEBUG
```

#### 2. View Live Logs

```bash
make backend-run
```

Logs appear in the terminal.

#### 3. Use Interactive Debugger (PyCharm/VS Code)

Set a breakpoint in your code:

```python
import pdb; pdb.set_trace()
```

Or use your IDE's debugger:
- **VS Code**: Install Python extension, set breakpoints, press F5
- **PyCharm**: Set breakpoints, click Debug button

#### 4. Inspect Database State

```python
from app.db.database import SessionLocal
from app.db.models import Device, Capture

db = SessionLocal()
devices = db.query(Device).all()
for device in devices:
    print(f"Device: {device.id}, Last seen: {device.last_seen_at}")
db.close()
```

### Firmware Debugging

#### 1. Serial Monitor

```bash
make firmware-monitor
```

This shows ESP32 serial output:
```
[PANTRY] Starting Pantry Camera System
[CONFIG] Using default settings
[POWER] Initialized
[SENSORS] Initialized
[CAMERA] Initialized
```

#### 2. Add Debug Logging

```cpp
Serial.printf("[DEBUG] Battery voltage: %.2f V\n", Battery::read_voltage());
```

#### 3. Test Locally Without Hardware

Modify `firmware/src/main.cpp` to simulate triggers:

```cpp
void loop() {
    // Simulate trigger every 10 seconds
    static unsigned long last_trigger = 0;
    if (millis() - last_trigger > 10000) {
        Serial.println("[TEST] Simulating door trigger");
        handle_capture_event("door");
        last_trigger = millis();
    }
}
```

### Web UI Debugging

#### 1. Browser DevTools

- **Chrome/Firefox**: Press F12
- **Console tab**: View JavaScript errors
- **Network tab**: Inspect API calls
- **React DevTools**: Install browser extension

#### 2. Enable Debug Output

Add to `web/src/App.jsx`:

```javascript
useEffect(() => {
  console.debug('Inventory updated:', inventory)
}, [inventory])
```

#### 3. Inspect API Requests

```bash
# Terminal where web-dev is running will show:
# GET /v1/inventory 200 (from vite proxy logs)
```

## Common Development Tasks

### Add a New API Endpoint

1. Create route file: `backend/app/api/routes/my_route.py`

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello"}
```

2. Include in `backend/app/main.py`:

```python
from app.api.routes import my_route
app.include_router(my_route.router, prefix="/v1", tags=["my_route"])
```

3. Test with:

```bash
curl http://localhost:8000/v1/my-endpoint
```

### Add a New Database Model

1. Create in `backend/app/db/models.py`:

```python
class MyModel(Base):
    __tablename__ = "my_models"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

2. Create migration:

```bash
cd backend
python -m alembic revision --autogenerate -m "Add MyModel table"
python -m alembic upgrade head
```

### Add a New React Component

1. Create file: `web/src/components/MyComponent.jsx`

```javascript
function MyComponent({ prop1 }) {
  return <div>{prop1}</div>
}

export default MyComponent
```

2. Import in `web/src/App.jsx`:

```javascript
import MyComponent from './components/MyComponent'

function App() {
  return <MyComponent prop1="value" />
}
```

### Test an API Endpoint Manually

```bash
# Ingest an image
curl -X POST http://localhost:8000/v1/ingest \
  -F "device_id=pantry-cam-001" \
  -F "token=<your-token-from-seed>" \
  -F "timestamp=$(date -u +%Y-%m-%dT%H:%M:%S)" \
  -F "trigger_type=door" \
  -F "battery_v=4.2" \
  -F "rssi=-45" \
  -F "image=@test_image.jpg"

# View inventory
curl http://localhost:8000/v1/inventory | python -m json.tool

# Override an item
curl -X POST http://localhost:8000/v1/inventory/override \
  -H "Content-Type: application/json" \
  -d '{"item_name":"peanut butter","count_estimate":3}'
```

### Generate a New Device Token

```bash
cd backend
python scripts/auth_utils.py generate-token
```

Output:
```
New token: abc123...xyz789
Hash:      abc123...xyz789_hash
```

Register in database:

```bash
cd backend
python scripts/seed_db.py add-device my-device "My Device" --token "abc123...xyz789"
```

## Code Organization

### Backend Structure

```
backend/
├── app/
│   ├── api/routes/
│   │   ├── ingest.py      # Image upload endpoint
│   │   └── inventory.py    # Inventory endpoints
│   ├── services/
│   │   ├── vision.py       # OpenAI Vision integration
│   │   └── inventory.py    # Inventory delta logic
│   ├── db/
│   │   ├── database.py     # SQLAlchemy setup
│   │   └── models.py       # Database models
│   ├── models/
│   │   └── schemas.py      # Pydantic request/response schemas
│   ├── auth.py             # Device authentication
│   ├── exceptions.py        # Custom exceptions
│   └── main.py             # FastAPI app
├── scripts/
│   ├── seed_db.py          # Initialize database
│   └── auth_utils.py       # Token utilities
├── tests/
│   ├── conftest.py         # Pytest fixtures
│   ├── test_health.py
│   ├── test_ingest.py
│   └── test_inventory.py
└── requirements.txt
```

### Key Design Patterns

#### 1. Exception Handling

All business logic errors use custom exceptions:

```python
from app.exceptions import ValidationError, AuthenticationError

try:
    # Business logic
except Exception as e:
    raise ValidationError("User-friendly message", field="field_name")
```

#### 2. Database Session Management

```python
from app.db.database import get_db

@router.get("/path")
async def endpoint(db: Session = Depends(get_db)):
    # DB session is automatically cleaned up
    result = db.query(SomeModel).filter(...).first()
    return result
```

#### 3. Pydantic Schemas for API

```python
class MyRequest(BaseModel):
    field1: str
    field2: int

class MyResponse(BaseModel):
    id: str
    created_at: datetime
```

## Performance Tips

### Backend

1. **Index frequently queried columns**
   ```python
   device_id = Column(String, ForeignKey(...), index=True)
   ```

2. **Use pagination for large result sets**
   ```python
   @router.get("/items")
   async def get_items(skip: int = 0, limit: int = 100):
       items = db.query(Item).offset(skip).limit(limit).all()
   ```

3. **Cache expensive operations**
   ```python
   @cache_result(ttl=60)  # Cache for 60 seconds
   def expensive_operation():
       ...
   ```

### Frontend

1. **Use React.memo for expensive components**
   ```javascript
   const MyComponent = React.memo(function MyComponent(props) {
       ...
   })
   ```

2. **Lazy load routes**
   ```javascript
   const LazyComponent = React.lazy(() => import('./Heavy'))
   ```

3. **Optimize API calls**
   - Use request debouncing
   - Implement infinite scroll instead of loading all data

## Troubleshooting Development Issues

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>

# Check database connection
cd backend && python -c "from app.db.database import SessionLocal; db = SessionLocal(); print('DB OK')"
```

### Web dev server won't connect to backend
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS is configured (should be automatic)
# If issues, add to backend/.env: CORS_ORIGINS=["http://localhost:5173"]
```

### Tests fail with "database is locked"
```bash
# Close other connections to test database
pkill -f pytest

# Or use in-memory database (tests/conftest.py already does this)
make backend-test
```

### Firmware won't upload
```bash
# List USB devices
ls /dev/ttyUSB* 
# or on macOS
ls /dev/tty.SLAB_USBtoUART

# Manually specify port in platformio.ini:
# upload_port = /dev/ttyUSB0

# Try verbose mode
cd firmware && pio run -e esp32-cam -t upload -v
```

## Next Steps

1. **Read ARCHITECTURE.md** for system design details
2. **Check existing tests** in `backend/tests/` for patterns
3. **Review copilot-instructions.md** for AI agent guidelines
4. **Start building!** Pick a task from GitHub issues or create your own

Happy coding! 🎉
