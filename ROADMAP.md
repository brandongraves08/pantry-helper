# Pantry Helper — Roadmap

> **Last Updated:** 2026-07-10
> **Status:** 🟢 Production-deployed on LXC 202 (pantry-helper.thelab.lan)
> **Stack:** FastAPI + PostgreSQL + Celery + Redis + React (Docker Compose)

## ✅ Complete (Deployed & Operational)

- **Docker Compose stack** — FastAPI backend, Celery worker, PostgreSQL, Redis, React web UI, Flower monitoring
- **Production LXC deployment** — LXC 202 at 192.168.2.202, Docker Compose with production overrides
- **Vision analysis** — OpenClaw vision provider (`openai/gpt-5.4-mini`), working detection pipeline
- **Background job queue** — Celery + Redis for async image analysis
- **Device registration API** — Token-based device management
- **Inventory management** — Locations, expiry dates, par levels, shopping list
- **Barcode scanning** — Detection routes in vision service
- **Nutrition tracking** — Routes for nutrition data from detections
- **Structured logging** — Across the entire stack
- **Nagios monitoring** — 3 HTTP checks (API, Web, Flower) + 2 NCPA system checks (CPU, Memory)
- **PBS backup** — Daily automatic backup of LXC 202
- **Cloudflare ingress** — Traefik routes via `*.homelab.graveystudios.com` when mapped

## ✅ Recently Complete

### Phase 3: Docker Image Optimization ✅ *(2026-07-10)*
- [x] Multi-stage build already existed — optimized with `--no-install-recommends`
- [x] Removed ImageMagick dependency (libzbar0 Recommends → stripped)
- [x] Removed unnecessary gcc from builder stage (all packages ship wheels)
- [x] Split test deps into requirements-dev.txt (pytest, httpx)
- [x] Added explicit Dockerfile targets: `runtime`, `prod` (gunicorn), `dev` (with test deps)
- [x] Added `target: runtime` to docker-compose.yml for api/worker/flower
- **Result:** 565MB → **355MB** per backend image (37% reduction, under 500MB target)

### Phase 4: Monitoring & Observability
- [ ] Create Grafana/Loki dashboard for pantry-helper logs
- [ ] Add Loki alert rules (5xx errors, service down, high latency)
- [ ] Verify all health endpoints cover DB + Redis from Nagios

### Phase 5: ESP32 Hardware Onboarding
- [ ] Test device registration flow with real or simulated ESP32
- [ ] End-to-end capture → vision analysis → inventory update test
- [ ] Build and verify ESP32 firmware
- [ ] Camera module implementation
- [ ] WiFi + HTTPS upload
- [ ] Power management (deep sleep, GPIO wake)

## 📋 Medium Priority

- **Image retention policy** — Auto-delete images older than X days
- **Confidence tuning** — Fine-tune vision prompts & thresholds per category
- **Inventory history queries** — Advanced filtering, CSV export
- **Device management UI** — Health metrics, settings, de-registration
- **Mobile responsiveness** — Current: partially responsive
- **User auth** — Login/logout, user roles (if needed beyond single-family)
- **Expiry tracking via OCR** — Parse expiry dates from labels

## 🔧 Technical Debt

- **Firmware is still stubs** — Camera, upload, power, and sensor modules need real implementation
- **Web UI has some hardcoded colors** — Needs theme system
- **CORS** — Verify production CORS config
- **Rate limiting** — Add to API endpoints
- **Secrets management** — Gateway token via docker secret mount is working, full audit needed
- **Docker images ~840MB** — Multi-stage build targets <500MB

## 🧪 Testing

- [ ] Service layer tests (backend)
- [ ] Frontend component tests (React Testing Library)
- [ ] E2E tests (Playwright)
- [ ] Firmware unit tests
- [ ] Load test API endpoints

## 📚 Documentation Needs

- Current docs (architecture.md, DEPLOY_GUIDE.md, etc.) are comprehensive but from initial build
- Needs: operational runbook (backup restore, service restart, troubleshooting)
- Needs: ESP32 hardware setup guide
- Needs: quick-reference card for family use

## 📊 Success Metrics

- Nagios-monitored: ✅ (5 checks)
- PBS-backed-up: ✅ (daily job)
- Config-consistent dev/prod: ✅
- Docker images <500MB: ❌ (next phase)
- ESP32 connected: ❌ (next phase)
- Loki dashboard: ❌ (next phase)
- Code committed: ✅ (all changes tracked)
