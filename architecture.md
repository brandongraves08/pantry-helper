Here’s an **Architecture Document** you can drop straight into your repo as `ARCHITECTURE.md` and start building with Copilot in VS Code. Because apparently we can’t just look at shelves with our eyes anymore.

````markdown
# Pantry Inventory (ESP32 + Camera + OpenAI) Architecture

## 1) Goal
Build a battery-powered pantry inventory system that:
- Wakes on a trigger (door open OR pantry light turns on)
- Captures one or more images
- Sends images to an API for classification (OpenAI vision)
- Updates and serves an inventory (what, count, confidence, last_seen)
- Runs reliably with low power consumption and minimal maintenance

Non-goals (for v1):
- Perfect counting of stacked items
- OCR-heavy label parsing
- Real-time video streaming
- Multi-room synchronization

---

## 2) High-level System Overview

### Components
1. **ESP32 Camera Node** (battery powered)
   - Deep sleep most of the time
   - Triggered wake via:
     - Door sensor (reed switch)
     - Light sensor (phototransistor / LDR comparator / BH1750)
   - Captures image(s)
   - Connects Wi-Fi briefly
   - Uploads images to backend
   - Receives ACK + optional “next actions” (take another photo, adjust exposure, etc.)

2. **Backend API**
   - Authenticates device
   - Stores images + metadata
   - Sends images to OpenAI Vision
   - Parses results into structured inventory deltas
   - Updates database
   - Exposes inventory UI/API

3. **Database**
   - Inventory items (canonical + variants)
   - Observations (per capture event)
   - Deltas (add/remove/adjust counts)
   - Device health telemetry (battery %, RSSI, wake reason, errors)

4. **Web UI (optional but recommended)**
   - Current inventory list
   - History (what changed and when)
   - Manual corrections (human overrides are inevitable)

---

## 3) Data Flow

### Event-driven capture flow (happy path)
1. Trigger occurs (door open or light on)
2. ESP32 wakes from deep sleep
3. ESP32 powers/initializes camera
4. Captures image(s)
5. ESP32 connects Wi-Fi
6. ESP32 uploads to backend:
   - Image bytes (JPEG)
   - Metadata: device_id, timestamp, trigger_type, battery_voltage, RSSI
7. Backend stores image, queues analysis
8. Backend calls OpenAI Vision with instructions to return JSON results
9. Backend writes observation + inventory delta
10. Backend responds to ESP32 with:
   - success/failure
   - optional instructions (retry, capture another angle, etc.)
11. ESP32 goes back to deep sleep

### Failure paths
- No Wi-Fi: store image to SD (if present) or discard; retry next trigger
- Upload fails: retry N times then sleep
- Vision call fails: inventory not updated but image stored for later reprocessing

---

## 4) ESP32 Node Design

### Responsibilities
- Ultra-low-power operation
- Accurate trigger wake
- Reliable image capture
- Secure upload to backend

### Hardware interfaces
- Camera: ESP32-CAM style module or ESP32-S3 camera dev board
- Trigger inputs:
  - Door: reed switch -> GPIO (wakeup capable)
  - Light: sensor -> GPIO/ADC (wakeup via external comparator OR timer wake with “check light”)
- Optional:
  - microSD storage for offline buffering
  - Battery measurement via ADC divider

### Firmware modules
- `power/`:
  - deep sleep control
  - wake reason handling
  - brownout detection
- `sensors/`:
  - door sensor handler
  - light sensor handler
  - debounce + “ignore repeated triggers within X seconds”
- `camera/`:
  - init, capture JPEG
  - exposure/brightness presets
- `net/`:
  - Wi-Fi connect with timeout
  - NTP time sync (optional)
- `upload/`:
  - HTTPS POST image + metadata
  - device auth token
  - retry logic
- `config/`:
  - Wi-Fi creds (provisioning)
  - device_id + API endpoint
  - thresholds (light threshold, quiet period)

### Power strategy
- Default: deep sleep, wake on GPIO (door) or external wake (light comparator)
- Keep wake time short:
  - Capture -> Wi-Fi -> upload -> sleep
- Set strict timeouts:
  - Wi-Fi connect: 10–15s max
  - Upload: 15–20s max
- Optional “multi-shot”:
  - Take 2–3 photos quickly (different exposure) before Wi-Fi to reduce radio-on time

---

## 5) Backend Architecture

### Suggested stack (simple + Copilot-friendly)
- API: **FastAPI (Python)** or **Node/Express**
- Queue: lightweight background worker (RQ/Celery) or simple in-process task for v1
- DB: **Postgres** (or SQLite for prototype)
- Storage: local disk or S3-compatible bucket
- Auth: per-device token

### Services
1. **Ingest API**
   - `POST /v1/ingest`
   - Accepts multipart form:
     - `image` (jpeg)
     - JSON metadata fields
   - Validates token
   - Stores image
   - Creates “capture event”
   - Enqueues analysis job
   - Returns `{capture_id, status}`

2. **Vision Analyzer Worker**
   - Pull capture_id
   - Loads image
   - Calls OpenAI Vision with strict JSON schema expectations
   - Produces structured observation
   - Computes inventory delta
   - Writes to DB

3. **Inventory API**
   - `GET /v1/inventory`
   - `GET /v1/inventory/history`
   - `POST /v1/inventory/override` (manual corrections)

---

## 6) OpenAI Vision Prompting Contract

### Output requirements
Return **machine-parseable JSON** with:
- `items`: list of recognized pantry items
- Each item:
  - `name` (canonical-ish)
  - `brand` (optional)
  - `package_type` (box, can, jar, bag)
  - `quantity_estimate` (int, optional)
  - `confidence` (0–1)
- `scene_confidence` (0–1)
- `notes` (optional)

### Example output
```json
{
  "scene_confidence": 0.82,
  "items": [
    {"name":"peanut butter","brand":"Jif","package_type":"jar","quantity_estimate":1,"confidence":0.88},
    {"name":"pasta","brand":"Barilla","package_type":"box","quantity_estimate":2,"confidence":0.74}
  ],
  "notes":"Some items partially occluded."
}
````

### Inventory delta logic (v1)

* If item appears with confidence >= threshold (ex: 0.70):

  * mark as `last_seen = now`
  * increment/adjust count conservatively
* If item not seen for N days:

  * mark as `stale` (don’t delete automatically)
* Manual override always wins

---

## 7) Data Model (DB)

### Tables

**devices**

* id (uuid)
* name
* token_hash
* created_at
* last_seen_at
* last_battery_v
* last_rssi

**captures**

* id (uuid)
* device_id
* trigger_type (door|light|timer|manual)
* captured_at
* image_path
* battery_v
* rssi
* status (stored|analyzing|complete|failed)
* error_message

**observations**

* id (uuid)
* capture_id
* raw_json (jsonb)
* scene_confidence
* created_at

**inventory_items**

* id (uuid)
* canonical_name
* brand (nullable)
* package_type (nullable)

**inventory_state**

* id (uuid)
* item_id
* count_estimate (int)
* confidence (float)
* last_seen_at
* is_manual (bool)
* notes

**inventory_events**

* id (uuid)
* item_id
* capture_id (nullable)
* event_type (seen|adjusted|manual_override)
* delta (int)
* created_at
* details (jsonb)

---

## 8) Security

### Device authentication

* Each device has a pre-shared token
* ESP32 includes `Authorization: Bearer <token>`
* Backend stores hashed tokens

### Transport

* HTTPS only
* Certificate pinning optional (hard on embedded, but doable)

### Data privacy

* Pantry images are sensitive-ish (people store meds, addresses on boxes, etc.)
* Store minimal images; allow auto-delete after X days
* Never log raw images in request logs

---

## 9) Repository Layout (recommended)

```
pantry-inventory/
  ARCHITECTURE.md
  README.md

  firmware/
    platformio.ini
    src/
      main.cpp
      camera/
      power/
      sensors/
      net/
      upload/
    include/
    test/

  backend/
    app/
      main.py
      routes/
      services/
      workers/
      models/
      db/
    tests/
    Dockerfile
    docker-compose.yml (optional)

  web/
    (optional UI)
```

---

## 10) MVP Milestones

### Milestone 1: Capture + Upload

* ESP32 wakes on trigger, takes photo, uploads to backend
* Backend saves image + capture metadata

### Milestone 2: Vision + Parse

* Worker calls OpenAI
* Store observation JSON

### Milestone 3: Inventory View

* Inventory endpoint returns current inferred items
* Add basic web page or JSON-only

### Milestone 4: Reliability + Power

* Retry/backoff
* Sleep tuning
* Battery voltage reporting + dashboard

---

## 11) Testing Plan

### Firmware

* Wake reason correctness (door vs light)
* Debounce works (no rapid fire)
* Camera capture success rate
* Wi-Fi connect timeout behavior
* Upload retries + graceful sleep

### Backend

* Auth reject/accept
* Upload handles large payloads
* Vision JSON schema validation
* Inventory delta correctness
* Reprocess capture endpoint (for improving prompts)

---

## 12) Config & Environment

### Backend env vars

* `OPENAI_API_KEY`
* `DATABASE_URL`
* `STORAGE_PATH` or `S3_BUCKET`
* `DEVICE_TOKEN_SALT`
* `VISION_MODEL` (if configurable)
* `INVENTORY_CONFIDENCE_THRESHOLD` (default 0.70)

### Firmware config

* Wi-Fi SSID/password
* `API_BASE_URL`
* `DEVICE_ID`
* `DEVICE_TOKEN`
* Thresholds (light threshold, retry counts)

---

## 13) Future Improvements (after MVP)

* Multiple angles (two nodes or PTZ)
* On-device prefiltering (skip upload if image too dark)
* Better counting with temporal smoothing
* Barcode recognition
* Household “consumption” predictions
* Notifications: “low on peanut butter” (society is doomed)