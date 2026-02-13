# Pantry Inventory Helper - Feature Architecture

## Current Status: MVP Working ✅

### Legend
| Status | Meaning |
|--------|---------|
| ✅ | Complete/Working |
| 🔄 | In Progress |
| ⏳ | Planned |
| ❌ | Not Started |
| 🔴 | Blocked |

---

## CORE FEATURES

### 1. Vision Processing Pipeline

| Component | Status | Details |
|-----------|--------|---------|
| Image Upload (`/v1/ingest`) | ✅ | JPEG/PNG, multipart form |
| Async Processing | ✅ | Celery + Redis queue |
| Vision Analysis | ✅ | NVIDIA NIM (LLaMA 3.2 11B) |
| Text Fallback Parser | ✅ | Extracts items from natural language |
| Storage | ✅ | Local filesystem + metadata in DB |

### Vision Models Available

| Model | Parameters | Status | Notes |
|-------|-----------|--------|-------|
| **meta/llama-3.2-11b-vision-instruct** | 11B | ✅ Active | ~9s response, 83 items extracted |
| meta/llama-3.2-90b-vision-instruct | 90B | ⏳ Available | More accurate, slower, more expensive |
| microsoft/phi-3-vision-128k-instruct | 4.2B | ⏳ Available | Microsoft, potentially cheaper/faster |
| microsoft/phi-3.5-vision-instruct | ~4B | ⏳ Available | Updated version |

**Pricing**: NVIDIA NIM currently free tier (no cost data available via API)

| Provider | Status | Model | Issue |
|----------|--------|-------|-------|
| OpenAI | 🔴 Quota Exceeded | gpt-5 | insufficient_quota |
| Gemini | 🔴 Quota Exceeded | gemini-2.0-flash | free_tier_requests limit 0 |
| Ollama (Local) | ⏳ Not Enabled | llava | Can add later |

---

### 2. Spatial Learning (Zones)

| Feature | Status | Details |
|---------|--------|---------|
| Zone CRUD API | ✅ | POST/GET/DELETE `/v1/zones/` |
| Zone Coordinate System | ✅ | Normalized 0.0-1.0 (x,y,width,height) |
| Expected Item Types | ✅ | Can tag zones with "can", "box", etc. |
| Pattern Learning | ⚠️ | DB schema ready, inference runs but no patterns yet |
| Zone Inference | ✅ | Processes zones during capture (needs learned patterns) |
| YOLOv8 Detection | ⏳ | Stub created, needs `pip install ultralytics` |

**Zone Workflow:**
1. User creates zone: `POST /v1/zones/device/pantry-cam-001`
2. After high-confidence detections, system learns patterns per zone
3. Next capture with low-confidence items → queries learned patterns
4. Infers: "4 cans in Zone A → likely tomatoes (85% confidence)"

### 3. Inventory Management

| Feature | Status | Endpoint |
|---------|--------|----------|
| Item Inventory State | ✅ | `/v1/inventory` |
| Locations | ✅ | `/v1/locations` |
| Par Levels | ✅ | `par_level` field in inventory_state |
| Expiration Tracking | ✅ | `expires_at`, `opened_at` fields |
| Shopping List Generation | ✅ | `/v1/shopping` |
| Manual Override | ⚠️ | Partial - Review queue exists |

### 4. Review Queue

| Feature | Status | Notes |
|---------|--------|-------|
| Review List API | ✅ | `/v1/reviews/pending` |
| Approve/Reject | ⚠️ | API exists, UI needs work |
| "Approve & Apply" Workflow | ⏳ | Planned for web UI |

---

## HARDWARE INTEGRATION

### 1. Pi Zero 2 W Client

| Component | Status | Path |
|-----------|--------|------|
| Capture Script | ⏳ | `hardware/pi-zero-2w/capture_and_upload.py` |
| Systemd Service | ⏳ | `hardware/pi-zero-2w/pantry-capture.service` |
| Setup Script | ⏳ | `hardware/pi-zero-2w/setup.sh` |
| README | ⏳ | `hardware/pi-zero-2w/README.md` |

**Current Test Device:** `pantry-cam-001` (Virtual/Local)

### 2. RTSP Camera Support (Future)

| Feature | Status | Notes |
|---------|--------|-------|
| RTSP Stream Support | ❌ | TCP connection fix complete, but no capture client yet |
| ONVIF Discovery | ❌ | Future |

---

## DEPLOYMENT

| Component | Status | Notes |
|-----------|--------|-------|
| Docker Compose | ⏳ | Files exist but Docker not installed |
| Production Deployment | 🔴 | Requires sudo for Docker |
| Database Migrations | ⚠️ | Alembic config issue (no .ini) |
| Environment Variables | ✅ | Uses .env, config.py |
| Health Check | ✅ | `/health` endpoint working |

---

## WEB UI

| Feature | Status | Path |
|---------|--------|------|
| React Frontend | ⏳ | `web/` exists but not deployed |
| Inventory List | ⚠️ | `InventoryList.jsx` exists |
| Review Queue | ⚠️ | `ReviewQueue.jsx` exists |
| Manual Override | ⚠️ | `ManualOverride.jsx` exists |
| Shopping List | ⚠️ | `ShoppingList.jsx` exists |
| API Client | ⚠️ | `api.js` stub exists |

---

## MODEL COMPARISON FRAMEWORK

To compare models (when credits available):

```python
# Test harness needed
models = [
    ("nvidia", "meta/llama-3.2-11b-vision-instruct"),
    ("nvidia", "meta/llama-3.2-90b-vision-instruct"),  # Larger
    ("nvidia", "microsoft/phi-3-vision-128k-instruct"),
    ("nvidia", "microsoft/phi-3.5-vision-instruct"),
]

metrics = ["response_time", "items_detected", "accuracy_score", "cost"]
```

**Current Status:** Only NVIDIA models available (OpenAI/Gemini blocked)

---

## PRIORITY BACKLOG

### P0 - Critical (Blocking Usage)
1. ❌ **Pi Zero 2 W Client** - Hardware firmware
2. ✅ ~~Vision Pipeline~~ - FIXED (NVIDIA NIM working)
3. ⏳ **Docker Deployment** - Need sudo to install Docker

### P1 - Feature Complete MVP
4. ⏳ **Pattern Learning** - Built but needs filled patterns
5. ⏳ **YOLOv8 Integration** - Bounding box detection
6. ⏳ **Web UI Deployment** - Integrate with backend
7. ⏳ **Review Queue UI** - Approve/reject flow

### P2 - Enhanced Experience
8. ⏳ **Model Comparison Tests** - Need OpenAI/Gemini credits
9. ⏳ **ML Accuracy Metrics** - Track detection quality over time
10. ⏳ **RTSP Camera Support** - For network cameras
11. ⏳ **Mobile Notifications** - Pushover integration

### P2 - Enhanced Experience (Continued)
12. ⏳ **Household Member Profiles** - Nutrition needs, allergies, preferences
13. ⏳ **Nutrition Database** - Per-item nutrition facts
14. ⏳ **Allergen Tracking** - Cross-contamination warnings
15. ⏳ **Supply Forecasting** - Days of food remaining based on consumption
16. ❌ **Family Member Tracking** - Who took what
17. ❌ **Recipe Integration** - Suggest recipes based on stock
18. ❌ **Expiry Alerts** - Push notifications for expiring items
19. ❌ **Shopping Integration** - Order from Instacart/etc

---

## HOUSEHOLD & NUTRITION FEATURES

### 1. Household Member Profiles
| Feature | Status | Notes |
|---------|--------|-------|
| Member CRUD | ❌ | Name, age, dietary restrictions |
| Allergy Profiles | ❌ | Peanuts, dairy, gluten, etc. |
| Nutrition Targets | ❌ | Daily calories, macros, micros |
| Preferences | ❌ | Vegetarian, keto, halal, etc. |

### 2. Nutrition Database
| Feature | Status | Notes |
|---------|--------|-------|
| USDA Integration | ❌ | Auto-lookup nutrition facts |
| Manual Entry | ❌ | Per-item nutrition override |
| Barcode Scan | ❌ | Integration with OpenFoodFacts |
| Serving Sizes | ❌ | Standardize portions |

### 3. Allergen Management
| Feature | Status | Notes |
|---------|--------|-------|
| Allergen List Per Item | ❌ | Big 9 + custom |
| Cross-Contamination Warnings | ❌ | "May contain..." |
| Safe/Unsafe Inventory Views | ❌ | Filter by household member |
| Emergency Contact | ❌ | If allergen detected |

### 4. Supply Forecasting
| Feature | Status | Notes |
|---------|--------|-------|
| Consumption Tracking | ❌ | Track what gets used when |
| Depletion Estimates | ❌ | "7 days of cereal remaining" |
| Restock Recommendations | ❌ | Buy before you run out |
| Meal Planning Integration | ❌ | Factor in planned meals |

---

## RUNNING STATE

**Backend:**
- API Server: `http://localhost:8000` ✅
- Celery Worker: Processing ✅
- Redis Queue: `localhost:6379` ✅

**Active Capture:** `d6c7572a-484b-4dc3-a05c-99d6c1f32654` ✅
**Active Zone:** `shelf_3_left` ✅

---

Last Updated: 2026-02-11
