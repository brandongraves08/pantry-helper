# Pantry Project — Full Audit Report

**Date:** 2026-08-09
**Scope:** Backend API, database, frontend, vision/ML, deploy/ops, data quality, docs.
**Method:** Code review of `brandongraves08/pantry-helper` @ `9032876`, live DB/API inspection on CT202.

---

## Summary

Project is **functional** (core inventory + shopping + recipes all work, deployed and healthy). The most urgent issues are **security** — the API is effectively unauthenticated with an unsafe CORS config — followed by **dead UI** and a **stale feature doc**. Findings are P0 (act now), P1 (this sprint), P2 (nice-to-have).

---

## P0 — Critical (fix now)

### P0-1. No authentication on the API (except ingest)
- **Where:** `app/api/routes/*.py` — only `ingest.py` requires `get_current_device`. Every other route (inventory, override, reviews, recipes, shopping, devices, admin, agent) is unauthenticated.
- **Impact:** Anyone on the network can overwrite inventory, approve/reject reviews, add/delete recipes, register/delete devices, and hit admin process endpoints. The `agent` endpoints (used by Discord digest) are read-only, but write routes are wide open.
- **Fix:** Require `get_current_device` (or a bearer token) on all write routes; keep read routes optionally open or token-gated. This is a homelab on 192.168.2.x, so blast radius is LAN-only — but LAN-only is still "trusts LAN, no auth" per existing setup note.

### P0-2. Unsafe CORS: `allow_origins=["*"]` + `allow_credentials=True`
- **Where:** `app/main.py:53-59`
- **Impact:** Wildcard origins with credentials is rejected by browsers / treated as insecure; enables cross-site requests to carry cookies. Also defeats the trust model.
- **Fix:** Restrict to the actual web origin(s): `allow_origins=["http://pantry-helper.thelab.lan:3000", "http://localhost:3000"]`.

### P0-3. Alembic not wired — migrations can't actually run
- **Where:** repo has `backend/migrations/versions/*.py` and `script.py.mako`, but **no `alembic.ini`** and no `alembic/env.py`.
- **Impact:** `alembic upgrade head` cannot run. Tables only exist because `Base.metadata.create_all` on startup creates them. Any schema change that needs a real migration (index/column alter) has no path; and the `create_all` vs migration race is fragile.
- **Fix:** Add `alembic.ini` + `env.py`, OR decide it's fine to rely on `create_all` (works for add-model) and document that that's the mechanism — but remove the broken "run alembic" steps from the deploy plan/skill.

### P0-4. Stale feature doc misleads
- **Where:** `FEATURE_ARCHITECTURE.md`
- **Impact:** Claims "React Frontend ⏳ not deployed", "Docker not installed", "Pi Zero 2 W Client ❌", "Barcode Scan ❌" — all **false** (web is deployed & live, Docker runs the stack, barcode works). A doc that says production isn't deployed when it is causes wrong decisions.
- **Fix:** Correct the stale status flags (see details below).

---

## P1 — Should fix this sprint

### P1-1. Dead buttons in Inventory UI
- **Where:** `web/src/pages/Inventory.jsx` — the **Add Item**, **Filter**, **Sort**, and **Edit** buttons have **no `onClick` handler**.
- **Impact:** Core inventory-management actions look enabled but do nothing. The app's primary UI has no way to add/edit an item from the list; only the "Nutrition" button works.
- **Fix:** Wire Add/Edit to the override API (`POST /v1/inventory/override`), implement filter/sort over `filteredItems`, or hide the inert buttons until implemented.

### P1-2. Rate limiter is in-memory + only covers 3 paths
- **Where:** `app/middleware/rate_limit.py` — `RateLimitStore` is a plain dict (no Redis), and `RATE_LIMITED_PATHS` only lists `/v1/ingest`, `/v1/admin/process-capture`, `/v1/admin/process-pending`.
- **Impact:** The override/review/recipe write endpoints have **no rate limit**; a misbehaving client can hammer them. Also, an in-memory store means limits reset on every worker restart and don't scale across the 2 workers.
- **Fix:** Gate all write routes for rate limiting; move the store to Redis (already available).

### P1-3. Missing DB indexes on hot FK columns
- **Where:** `app/db/models.py` — indexes exist only on `barcode_lookups.barcode`. No index on `inventory_events.item_id`, `inventory_state.item_id`, `captures.device_id`, `inventory_state.location_id`, `captures.status`.
- **Impact:** As `inventory_events`/`captures` grow, the item-history and capture queries (which filter by these) degrade to full scans. Note: alembic must work (P0-3) before adding indexes cleanly.
- **Fix:** Add indexes on FK/query columns.

### P1-4. Vision/ML fallback gap (YOLO stub)
- **Where:** `app/services/object_detection.py` — `ultralytics` is not installed; `detect()` always returns `[]` (adds no value), and the capture pipeline never actually runs zone object detection.
- **Impact:** The spatial-learning/zone-inference feature is effectively inert despite being marked semi-working in the doc.
- **Fix:** Either install `ultralytics` + a weights file and wire it into `capture.py`, or (recommended) remove/degate the YOLO path from the doc to "not implemented" until it's genuinely needed. Given "off-the-shelf only, no custom scripts" and cost-consciousness, **recommend documenting it as unbuilt** rather than adding a heavy dependency.

### P1-5. Two captures both failed (old data)
- **Where:** DB — `SELECT status, count(*) FROM captures` → 2 rows, both `failed` for device `pantry-cam-001`, `error_message = "Processing failed for capture ..."` (generic — worker did not record a detail).
- **Impact:** Both ingested captures errored during processing. This is legacy data from the initial camera test, not the current active flow — but it shows the worker's failure path logs no actionable error, so future failures are hard to diagnose.
- **Fix:** Add the worker exception detail to `captures.error_message` (capture.py already logs it in some paths — make it persist to DB). Whether the two historical captures need re-processing or should be cleaned up is a data-hygiene call.

---

## P2 — Enhancements

### P2-1. Inventory items unverified & missing images
- 41/54 items are confidence 0.30 (unverified from the 08-09 stocktake); 5 items have no image (Ground Beef, Bush's Texas Style, Korean BBQ Baked Beans, Wet Ones, Freezer Bags surefresh).
- **N/A** — already flagged; awaiting product photo or manual correction. Ties to the planned "Flag Incorrect Info" feature.

### P2-2. low-stock ignores confidence
- `advanced_inventory.py` low-stock filters only on `count_estimate <= threshold`, not confidence. Unverified/unconfirmed items still appear in low-stock/shopping recs. Add a `confidence >= 0.5` filter (small change) once you want unverified items excluded.

### P2-3. Health/storage retention config
- `IMAGE_RETENTION_DAYS` defaults 30, `MAX_STORAGE_MB` 5000; no retention worker config observed in the docker compose `command` for the worker. Confirm `retention.py` worker runs or the images dir grows unbounded.

### P2-4. `_low_stock_rows` loads all states into memory
- `agent.py` `_low_stock_rows` and `_expiring_rows` do `db.query(...).all()` then filter in Python. Fine at 54 items; won't scale. Prefer SQL-side filtering when volume grows.

### P2-5. No search-sort-pagination on inventory endpoint
- `GET /v1/inventory` returns everything; no `?search=/sort=`/`page=` params. Fine for 54 items; add pagination before the list grows.

---

## Fix list (mapped to plan + skills)

| # | Item | Severity | Effort | Backlog entry |
|---|------|----------|--------|---------------|
| 1 | Add auth to write routes + CORS restrict | P0 | M | (new — security) |
| 2 | Wire alembic OR document create_all as the migration mechanism | P0 | M | (new — db hygiene) |
| 3 | Correct stale FEATURE_ARCHITECTURE statuses | P0 | S | "Full Project Audit" deliverable 3 |
| 4 | Wire/hide dead Inventory buttons (Add/Edit/Filter/Sort) | P1 | M | "Web UI Deployment" / "Review Queue UI" |
| 5 | Rate-limit write routes + Redis-backed store | P1 | M | (new — hardening) |
| 6 | Add DB indexes on FK/query columns | P1 | S | (new — perf) |
| 7 | Resolve failed captures (vision config) | P1 | M | (new — ops) |
| 8 | Document YOLO as unbuilt (or wire it) | P1 | S | "YOLOv8 Integration" |
| 9 | low-stock confidence filter | P2 | S | "Flag Incorrect Info" / data hygiene |
| 10 | Pagination on inventory list | P2 | M | (new — perf) |

---

## Doc corrections needed (FEATURE_ARCHITECTURE.md)
Confirm-and-fix these stale lines during the same pass:
- React Frontend: ⏳ → ✅ deployed
- Docker Deployment / Production Deployment: → ✅ running on CT202
- Pi Zero 2 W Client: ❌ → still ⏳/not shipped (keep, it's genuinely not built)
- Barcode Scan / Nutrition Database / Recipe Integration: → ✅ works (barcode + recipes are live)
- "Database Migrations ⚠️ Alembic config issue" → accurate (see P0-3)

---

*Report generated 2026-08-09. Findings verified against live code + DB on CT202.*
