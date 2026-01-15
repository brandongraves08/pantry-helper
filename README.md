# Pantry Inventory System

A battery-powered, event-driven pantry inventory system using ESP32 camera, OpenAI Vision, and a Python backend.

## Overview

- **ESP32 Camera Node**: Wakes on trigger (door/light), captures images, uploads to backend
- **Backend API**: FastAPI-based service for image ingestion, vision analysis, inventory management
- **Database**: PostgreSQL (or SQLite for dev) storing devices, captures, observations, and inventory state
- **Web UI**: React dashboard for viewing current inventory, history, and manual corrections

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+ (for web UI)
- PostgreSQL (optional; SQLite works for development)
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
│   │   ├── models/            # Pydantic schemas
│   │   ├── db/                # Database models and config
│   │   ├── auth.py            # Token management
│   │   ├── exceptions.py       # Custom exceptions
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
