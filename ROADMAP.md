# Pantry Helper — Roadmap

> **Last Updated:** 2026-07-19
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

### Phase 1: Hardening & Infrastructure ✅ *(2026-07-10)*
- [x] PBS backup configured and verified
- [x] Nagios monitoring via NCPA (5 checks)
- [x] .env consistency between local and LXC
- [x] Secret audit (OpenAI/NVIDIA keys, gateway token mount)

### Phase 2: Code & Config Maturity ✅ *(2026-07-10)*
- [x] All uncommitted code committed and pushed
- [x] docker-compose.yml / override.yml drift resolved
- [x] .gitignore covers all sensitive files
- [x] ROADMAP rewritten from stale January version

### Phase 3: Docker Image Optimization ✅ *(2026-07-10)*
- [x] Multi-stage build optimized with `--no-install-recommends`
- [x] Removed ImageMagick dependency, stripped gcc from builder
- [x] Split test deps into requirements-dev.txt
- [x] Added explicit Dockerfile targets: `runtime`, `prod`, `dev`
- **Result:** 565MB → **355MB** per backend image (37% reduction)

### Phase 4: Monitoring & Observability ✅ *(2026-07-10)*
- [x] Enhanced `/health` endpoint (DB + Redis + storage)
- [x] Nagios: 5 active checks verified
- [x] Grafana/Loki dashboard: `/d/dfrpmw7636328d/pantry-helper-logs-and-health`
- [x] Loki alert rules: high error rate, critical errors, no recent logs

### Phase 5: Mobile & Client Experience ✅ *(2026-07-19)*
- [x] **PWA support** — iPhone home-screen installable client
  - vite-plugin-pwa with Workbox service worker (19 precached entries, API caching)
  - PWA manifest with standalone display, 6 icon sizes
  - iOS meta tags: apple-mobile-web-app-capable, status-bar, touch icons (120/152/180)
  - Blue can icon at 8 sizes (72-512px)
  - Deployed and verified on LXC 202

## 📋 Current Focus — Phase 6: Core Software Polish

| Task | Priority | Status |
|------|----------|--------|
| **Confidence tuning** — vision prompts & thresholds per category | 🔥 High | Pending |
| Expiry tracking via OCR — parse dates from labels | Medium | Pending |
| User authentication — login/logout, roles | Low | Pending |
| Service layer tests (backend — pytest) | Medium | Pending |
| Frontend component tests (React Testing Library) | Low | Pending |
| Rate limiting on API endpoints | Low | Pending |
| Operational runbook & family quick-reference card | Medium | Pending |

## 📋 Lower Priority

- **Mobile responsiveness** — Full audit of all pages for mobile layout, touch targets
- **Push notifications** — Evaluate web push API for expiring/low-stock alerts
- **Web UI theme system** — Remove hardcoded colors
- **CORS** — Verify production CORS config
- **E2E tests** (Playwright)
- **Load test API endpoints**

## 🔧 Technical Debt

- **Secrets management** — Gateway token via docker secret mount is working, full audit pending
- **Docker images at 355MB** — Under 500MB target, no further action needed

## 🔌 ESP32 Hardware — Separate Plan

ESP32 hardware has been moved to its own project plan:
**`projects/pantry-helper-hardware/plan.json`** — on hold.

When ready to pick up: device registration, camera firmware (OV2640), WiFi + HTTPS upload,
power management (deep sleep), OTA updates, field test. Not in scope for current software focus.

## 📊 Success Metrics

- ✅ Nagios-monitored: 5 checks
- ✅ PBS-backed-up: daily job
- ✅ Config-consistent dev/prod
- ✅ Docker images <500MB: 355MB
- ✅ Loki dashboard + alert rules
- ✅ PWA deployed (iPhone home-screen)
- ✅ Code committed: all tracked
- ➖ Confidence tuning: pending
- ➖ Expiry OCR: pending
- ➖ Test coverage: pending
