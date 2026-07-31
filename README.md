# Pantry Inventory System

A battery-powered, event-driven pantry inventory system using ESP32 camera, OpenAI Vision or Google Gemini AI, and a Python backend.

> **Status:** ✅ Core system complete and ready for development
> 
> **Vision AI:** Supports both OpenAI GPT-4 Vision and Google Gemini
>
> See [BUILD_STATUS.md](BUILD_STATUS.md) for detailed progress and [VISION_PROVIDERS.md](VISION_PROVIDERS.md) for AI provider configuration.

## Overview

- **ESP32 Camera Node**: Wakes on trigger (door/light), captures images, uploads to backend
- **Backend API**: FastAPI-based service for image ingestion, vision analysis, inventory management
- **Vision AI**: Choose between OpenAI GPT-4 Vision or Google Gemini for image analysis
- **Database**: PostgreSQL (or SQLite for dev) storing devices, captures, observations, and inventory state
- **Web UI**: React dashboard for viewing current inventory, history, and manual corrections

## Quick Start

### Docker (Fastest)

```bash
# 1. Configure environment
cp .env.docker.example .env
# Edit .env with your API key (OPENAI_API_KEY or GEMINI_API_KEY)

# 2. Start all services
docker-compose up -d

# 3. Seed test data
docker-compose exec backend python scripts/seed_db.py seed

# 4. Access services
# - API: http://localhost:8000
# - Web UI: http://localhost:3000
# - API Docs: http://localhost:8000/docs
```

**See [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for more commands**

### Automated Setup (Recommended)

```bash
# One-command setup - installs dependencies, creates venv, initializes database
./setup.sh

# Activate the virtual environment
source venv/bin/activate

# Add your Vision AI API key to backend/.env
# For OpenAI (default):
echo "VISION_PROVIDER=openai" >> backend/.env
echo "OPENAI_API_KEY=sk-your-key-here" >> backend/.env

# OR for Google Gemini:
echo "VISION_PROVIDER=gemini" >> backend/.env
echo "GEMINI_API_KEY=your-gemini-key-here" >> backend/.env

# Start the backend (Terminal 1)
make backend-run

# Start the web UI (Terminal 2)
make web-dev

# Run the demo to test everything (Terminal 3)
python demo.py
```

### Vision AI Provider Setup

The system supports two AI providers:

**Option 1: OpenAI GPT-4 Vision (Default)**
- Get API key from https://platform.openai.com/api-keys
- Cost: ~$0.01 per image
- Best accuracy for complex scenes

**Option 2: Google Gemini**
- Get API key from https://makersuite.google.com/app/apikey  
- Free tier available (60 requests/minute)
- Faster, cost-effective

See [VISION_PROVIDERS.md](VISION_PROVIDERS.md) for detailed comparison and configuration.

### Manual Setup

Prerequisites:
- Python 3.9+
- Node.js 16+ (for web UI)
- PostgreSQL (optional; SQLite works for development)
- Redis (for Celery workers)
- PlatformIO CLI (for firmware)

### 1. Backend Setup

```bash
# Install dependencies
make backend-install

# Copy environment file and configure
cp backend/.env.example backend/.env
# Edit backend/.env with:
# - DATABASE_URL: Your database connection string
# - OPENAI_API_KEY: Your OpenAI API key
# - IMAGES_DIR: Where to store uploaded images (default: ./storage/images)

# Initialize database and seed test data
make backend-seed

# Start API server
make backend-run
```

The API will be available at `http://localhost:8000`. Visit `/docs` for interactive API documentation (Swagger UI).

**Test devices created:**
- `pantry-cam-001` - Kitchen Pantry
- `pantry-cam-002` - Garage Storage

Tokens are generated and displayed by `make backend-seed`. Keep them secret!

### 2. Web UI Setup

```bash
# Install dependencies
make web-install

# Start development server
make web-dev
```

The web UI will be available at `http://localhost:5173` and proxy API calls to the backend.

### 3. Firmware Setup (ESP32)

```bash
# Build firmware for ESP32-CAM
make firmware-build

# Upload to device (ensure device is connected via USB)
make firmware-upload

# Monitor serial output
make firmware-monitor
```

Edit `firmware/src/config/config.cpp` with:
- WiFi SSID and password
- Device ID (must match registered device in backend)
- API endpoint (e.g., `https://your-backend.com/v1/ingest`)
- API token (from device seeding)

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed component descriptions, data models, and design decisions.

## API Endpoints

### Image Ingestion
- **POST** `/v1/ingest` - Upload image from ESP32
  ```bash
  curl -X POST http://localhost:8000/v1/ingest \
    -F "device_id=pantry-cam-001" \
    -F "token=<device-token>" \
    -F "timestamp=$(date -u +%Y-%m-%dT%H:%M:%S)" \
    -F "trigger_type=door" \
    -F "battery_v=4.2" \
    -F "rssi=-45" \
    -F "image=@test_image.jpg"
  ```

### Inventory
- **GET** `/v1/inventory` - Get current inventory state
  ```bash
  curl http://localhost:8000/v1/inventory | jq .
  ```
  
- **GET** `/v1/inventory/history?days=7` - Get inventory change history
  ```bash
  curl "http://localhost:8000/v1/inventory/history?days=7" | jq .
  ```
  
- **POST** `/v1/inventory/override` - Manually correct an item count
  ```bash
  curl -X POST http://localhost:8000/v1/inventory/override \
    -H "Content-Type: application/json" \
    -d '{"item_name":"peanut butter","count_estimate":3,"notes":"refilled"}'
  ```

### Health
- **GET** `/health` - Health check

## Project Structure

```
pantry-helper/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/routes/        # Ingest and inventory endpoints
│   │   ├── services/          # Vision analyzer, inventory manager
│   │   ├── workers/           # Celery background tasks
│   │   ├── models/            # Pydantic schemas
│   │   ├── db/                # Database models and config
│   │   ├── auth.py            # Token management
│   │   └── exceptions.py      # Custom exceptions
│   ├── tests/                 # Pytest test suite
│   ├── migrations/            # Alembic database migrations
│   └── requirements.txt
├── firmware/                   # ESP32-CAM firmware (C++)
│   └── src/
│       ├── camera/            # Camera module
│       ├── net/               # WiFi and HTTP upload
│       ├── power/             # Deep sleep management
│       └── sensors/           # Door/light triggers
├── web/                       # React web UI
│   └── src/
│       ├── components/        # Dashboard, charts, forms
│       └── api.js             # API client
├── .github/
│   └── copilot-instructions.md  # AI coding agent guide
├── setup.sh                   # Automated setup script
├── demo.py                    # Test/demo script
├── Makefile                   # Build commands
├── docker-compose.yml         # Full stack deployment
└── BUILD_STATUS.md            # Detailed build status
```

## Helpful Commands

### Development
```bash
make help              # Show all available commands
make backend-run       # Start API server
make web-dev           # Start web UI dev server
make backend-test      # Run test suite
python demo.py         # Run demo/test
```

### Database
```bash
make backend-migrate        # Apply migrations
make backend-migrate-down   # Rollback migration
make backend-seed           # Create test devices
```

### Firmware
```bash
make firmware-build    # Compile ESP32 code
make firmware-upload   # Flash to device
make firmware-monitor  # Serial console
```

### Docker
```bash
docker-compose up -d              # Start all services
docker-compose logs -f backend    # View logs
docker-compose down               # Stop services
```

## Testing

Run the comprehensive test suite:

```bash
cd backend
pytest tests/ -v
```

Or use the demo script to test the full flow:

```bash
python demo.py
```

This will:
1. Check API health
2. Upload a test image
3. Wait for vision processing
4. Display inventory results
│   │   └── main.py            # FastAPI app
│   ├── scripts/               # Utilities (seed_db, auth_utils)
│   ├── tests/                 # Pytest test suite
│   ├── migrations/            # Alembic database migrations
│   └── requirements.txt
├── firmware/                   # ESP32 C++ firmware
│   ├── src/
│   │   ├── main.cpp           # Entry point
│   │   ├── power/             # Sleep and power management
│   │   ├── sensors/           # Door/light trigger logic
│   │   ├── camera/            # Image capture
│   │   ├── net/               # WiFi management
│   │   ├── upload/            # HTTPS image upload
│   │   └── config/            # Device configuration
│   └── platformio.ini
├── web/                        # React web UI
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── App.jsx            # Main app component
│   │   ├── api.js             # Axios client
│   │   └── index.css          # Styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── ARCHITECTURE.md            # System architecture document
├── README.md
├── Makefile                   # Build automation
└── .gitignore
