# Pantry Helper — Roadmap

> **Last Updated:** 2026-08-16
> **Status:** 🟢 Live on CT202 (`pantry-helper.thelab.lan`, .202) — FastAPI + Postgres + Redis + Celery + React (Docker Compose)
> **Repo:** `github.com/brandongraves08/pantry-helper` (PUBLIC, MIT) — no GitHub Actions (banned repo-wide); deploys are git pull + compose build on CT202.
> **Feature truth:** `FEATURE_ARCHITECTURE.md` (kept current) + the `pantry-app-development` skill. This file is the prioritized next-steps plan.

---

## ✅ Live Now (verified 2026-08-16)

- **Full stack** on CT202: `pantry-api`, `pantry-db` (postgres:15), `pantry-redis`, `pantry-worker` (Celery + beat), `pantry-web` (React/Vite PWA), `pantry-flower`, `pantry-promtail`. Health check `/health` covers DB/Redis/storage.
- **Inventory** — items, locations, par levels, expiry dates, counts, notes, brand/rating/favorite, product images (OFF backfill + HEB images), search/filter/sort in UI. `POST /v1/inventory/override` for add/edit. 57 items live.
- **Auth & hardening** — write routes Bearer-protected (`PANTRY_API_TOKEN`), Redis rate limiting, CORS locked to the LAN origins, DB indexes applied.
- **Vision pipeline** — image ingest → Celery → vision provider (`hermes` is the default per Brandon; openclaw legacy only). 2 legacy captures in DB are `failed` (initial camera test, not the active flow).
- **Verification queue** — `GET /v1/inventory/unverified` (confidence < 0.5), `POST /v1/inventory/{id}/verify`. Daily 6pm cron drives the loop in chat (pantry-verification-loop skill).
- **HEB enrichment** — every new item starts `heb_status=pending`; camofox automator searches heb.com (the only path past Imperva), posts product name/url/price/image; daily 4am cron runs silently. 63 shopping-list rows live.
- **Meal planning** — weekly plans (Mon–Sun grid, 4 slots/day), recipes w/ ingredients, `GET /v1/meal-plans/{id}/verify` (rolling 7-day window vs stock, `min_confidence=0.5`), `POST /v1/meal-plans/{id}/update-shopping` merges missing + untracked items into the HEB order. 3 recipes, 1 plan live.
- **Recipes** — CRUD + rating/favorite + per-recipe shopping needs. Ingredient→inventory linking.
- **Flag & feedback (built 2026-08-16)** — per-item Flag button in UI (field picker image/brand/count/name/other + free-text reason) → `inventory_flags` table → `GET /v1/inventory/flags` for Hermes to fix → `POST /v1/inventory/flags/{id}/resolve`. Amber highlight + badge on flagged rows.
- **Review Queue UI (built 2026-08-16)** — `/reviews` page surfaces the pending manual-review queue with Approve/Reject; failed captures hidden; header badge shows pending count.
- **Confidence-aware low-stock** — `GET /v1/inventory/low-stock?min_confidence=` (default 0.5) excludes unverified items from shopping recs; pagination on inventory.
- **Barcode, nutrition lookup** (Open Food Facts), **household members** (backend CRUD + basic UI), **devices/zones** (zones are schema-ready; pattern learning inert).
- **Observability** — Nagios checks, Loki dashboard + alert rules, PBS daily backups, image retention via Celery beat (daily 03:00 UTC).
- **PWA** — iPhone home-screen installable, service worker, icons.

---

## 📋 Next Steps (prioritized — the actual plan)

### P1 — High value, low effort (do first)

| # | Item | Why | Rough effort |
|---|------|-----|--------------|
| 1 | **Expiry/low-stock alerts to Discord** | `expires_at` + low-stock data already live; UI shows badges but nothing pushes. A small watcher (Hermes cron, no_agent) pings #alerts when items cross 7d-to-expiry or go below par. No app code needed. | S (script + cron) |
| 2 | **Meal-plan allergen & nutrition warnings** | Household member routes exist (backend) but the UI is a stub and nothing checks a planned meal against a member's allergens/restrictions. Wire the verify response to warn "contains peanut — wife is allergic." Real family value, uses existing tables. | M (backend verify + UI) |
| 3 | **Recipe suggestions from stock** | Recipes + inventory both live; "what can I cook with what I have" is the natural next pull. `GET /v1/recipes/suggest?match=on_hand` — score recipes by % ingredients in stock. | M |

### P2 — Next tier (after P1)

| # | Item | Why | Rough effort |
|---|------|-----|--------------|
| 4 | **Supply forecasting** | `consumption_events` table exists but nothing writes it. Hook verify/meal-plan consumption → depletion estimates ("~7 days of cereal"). | L (data model + writes + UI) |
| 5 | **Backend test suite (pytest)** | Zero backend tests today; the parse_quantity + verify math are the riskiest code. Lock the heuristics down before more features stack on them. | M |
| 6 | **Expiry OCR** | Vision pipeline could parse dates off labels; currently expiry is manual. Nice-to-have while the camera flow is dormant. | M |

### P3 — Parked / separate tracks

| # | Item | Why it's parked |
|---|------|-----------------|
| 7 | **YOLOv8 + pattern learning** | Stub exists, `ultralytics` not installed; zone/spatial inference inert. Documented as unbuilt — revisit only if the camera/ESP32 path comes back. |
| 8 | **ESP32 / Pi Zero camera hardware** | Separate project (`projects/pantry-helper-hardware`), on hold. The software side doesn't need it. |
| 9 | **Full login/roles, E2E (Playwright), load tests, theme system** | Bearer-token write auth is adequate for LAN; polish items, low urgency. |
| 10 | **Model comparison harness** | Needs OpenAI/NVIDIA credits; revisit when the vision pipeline is active again. |

---

## ⚠️ Known Debt & Gotchas (must-know for any dev session)

- **`create_all` races alembic** — new tables auto-create on backend restart, then `alembic upgrade head` DuplicateTable-fails. Fix: `alembic stamp <NNN>`, never re-run upgrade for new tables. Column-alter/index changes need a real migration or hand SQL (create_all won't alter existing tables). Live DB is at **010**.
- **Stale-image trap** — a failed `git pull` on CT202 leaves the old code but compose build still succeeds; `/health` lies. Always verify the running container has your symbol (`docker exec pantry-api grep -c ...`).
- **CT202 pulls need the token URL** — `https://x-access-token:<TOKEN>@github.com/brandongraves08/pantry-helper.git`; bare `git pull` fails. Checkout also had root-owned git objects once — chown to brandon if pull permission errors appear.
- **CT202 local compose mods** — keep TZ/`restart: always` lines; don't `git reset --hard` or clobber `docker-compose*.yml`, `deploy.sh`, `.env*`.
- **Pydantic schema gaps** — a route can set a field the response schema doesn't declare; FastAPI silently drops it. Schema + route must BOTH change.
- **`override` hardcodes confidence=1.0** — photo/vision-derived items must be re-flagged to the low band in DB; they then count as unverified.
- **GitHub Actions BANNED** — all repos, workflows purged. Deploys are pull + compose only.

---

## 📊 Success Metrics (live)

- ✅ Nagios checks on API/Web/Flower + system
- ✅ PBS daily backups
- ✅ Docker images < 500MB (355MB backend)
- ✅ Loki dashboard + alert rules
- ✅ PWA installed (iPhone)
- ✅ Auth on writes + rate limiting
- ✅ Meal planning → HEB order flow (the flagship feature)
- ✅ Flag & feedback loop closed (08-16)
- ➖ Tests (0 backend) — P2
- ➖ Expiry OCR — P2
- ➖ Push alerts — P1 #1

---

## 🗓 Cadence

- **Daily 6pm CT** — pantry verification loop (Hermes cron) — working through unverified items.
- **Daily 4am CT** — HEB enrichment automator (silent when nothing pending).
- **Weekly** — check `GET /v1/inventory/flags` open queue + pending HEB items; work the plan above on-demand.
