# Copilot Instructions for Pantry Inventory Project

## System Architecture

**Battery-powered pantry inventory using ESP32 camera + OpenAI Vision + FastAPI backend**

Components:
- **ESP32 Firmware** (`firmware/`): C++, PlatformIO. Deep sleep, wakes on door/light trigger, captures JPEG, uploads to backend
- **Backend API** (`backend/`): FastAPI + SQLAlchemy + Celery. Device auth via SHA256 tokens, async image processing
- **Database**: PostgreSQL (prod) / SQLite (dev). See [backend/app/db/models.py](../backend/app/db/models.py) for schema: `Device` → `Capture` → `Observation` → `InventoryItem`/`InventoryState`
- **Web UI** (`web/`): React + Vite. Inventory dashboard with manual overrides

**Critical data flow:**
1. ESP32 wakes → captures image → uploads to `/v1/ingest` with device_id + token
2. Backend stores image, queues Celery job
3. Worker calls OpenAI Vision API with structured JSON prompt ([backend/app/services/vision.py](../backend/app/services/vision.py))
4. InventoryManager updates state based on vision output ([backend/app/services/inventory.py](../backend/app/services/inventory.py))

## Developer Workflows

**First time setup:**
```bash
make backend-install && make web-install  # Install deps
cp backend/.env.example backend/.env      # Configure OPENAI_API_KEY, DATABASE_URL
make backend-seed                         # Creates test devices + generates tokens
make backend-run                          # API at :8000, docs at /docs
make web-dev                              # UI at :5173
```

**Testing:**
- Backend: `make backend-test` or `cd backend && pytest tests/ -v`
- Tests use in-memory SQLite + TestClient ([backend/tests/conftest.py](../backend/tests/conftest.py))
- Test device `test-device-001` with token `test-token` auto-created in fixtures

**Firmware (ESP32):**
- `make firmware-build` - Compile with PlatformIO
- `make firmware-upload` - Flash via USB
- `make firmware-monitor` - Serial debug output
- Config in [firmware/src/config/config.cpp](../firmware/src/config/config.cpp) (WiFi, device_id, API endpoint)

**Database migrations:**
- Alembic: `make backend-migrate` (up), `make backend-migrate-down` (down)
- Migration files in [backend/migrations/versions/](../backend/migrations/versions/)

**Docker deployment:**
- `docker-compose up` runs db + redis + backend + celery worker + flower
- Uses [docker-compose.yml](../docker-compose.yml) with health checks and auto-restart

## Critical Patterns & Conventions

**Authentication:**
- Device tokens are SHA256-hashed ([backend/app/auth.py](../backend/app/auth.py))
- Use `secrets.compare_digest()` for constant-time comparison (prevent timing attacks)
- Tokens generated via `secrets.token_urlsafe(32)`

**Error handling:**
- Custom `PantryException` with status codes ([backend/app/exceptions.py](../backend/app/exceptions.py))
- FastAPI exception handler returns JSON with `detail` + `status_code`
- Vision errors wrapped in `VisionAnalysisError`

**Async processing:**
- Image upload returns immediately; Celery worker processes in background
- Capture status: `stored` → `analyzing` → `complete` or `failed`
- Check status via `/v1/captures/{capture_id}` (see [backend/app/api/routes/inventory.py](../backend/app/api/routes/inventory.py))

**Vision API integration:**
- Supports both OpenAI GPT-4 Vision and Google Gemini
- Provider selected via `VISION_PROVIDER` env var (`openai` or `gemini`)
- Model: `gpt-4-vision-preview` (OpenAI) or `gemini-1.5-flash` (Gemini), configurable in [backend/app/config.py](../backend/app/config.py)
- Multi-provider implementation in [backend/app/services/vision.py](../backend/app/services/vision.py)
- Prompt in `VisionAnalyzer._build_prompt()` expects JSON response: `{"scene_confidence": 0.85, "items": [{"name": "...", "count": 2, "confidence": 0.9}]}`
- Images base64-encoded (OpenAI) or PIL Image object (Gemini)
- Markdown code block parsing for both providers

**Database UUIDs:**
- All models use `uuid.uuid4()` string IDs, not auto-increment
- Foreign keys: Device → Capture → Observation → InventoryItem

**Code style:**
- Python: snake_case, type hints, docstrings
- JavaScript: camelCase, ESLint
- C++: PascalCase for classes/namespaces, snake_case for functions

## Key Files Reference

- [architecture.md](../architecture.md) - Full system design, failure modes, power optimization
- [Makefile](../Makefile) - All build/run commands
- [backend/app/main.py](../backend/app/main.py) - FastAPI app setup, middleware order: rate limit → CORS
- [backend/app/workers/capture.py](../backend/app/workers/capture.py) - Celery job: analyze image + update inventory
- [firmware/src/main.cpp](../firmware/src/main.cpp) - Main loop: check triggers → capture → upload → deep sleep