# Pantry Helper Custom Barcode Labels Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users create locally stored Code 128 pantry labels for repackaged foods and scan them back into Pantry Helper.

**Architecture:** Add one authenticated FastAPI endpoint that creates a local barcode mapping and updates the existing inventory state in one database transaction. Extend the existing Barcode Scanner page with a custom-label form, SVG preview, and print action; use the existing local-cache-first lookup path for scans.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, existing React/Vite app and Vitest, `JsBarcode` for Code 128 SVG generation, existing Tailwind styles.

**Spec:** `docs/superpowers/specs/2026-11-20-pantry-custom-barcode-labels-design.md`

## Global Constraints

- Keep writes in Pantry Helper's existing inventory database; do not merge, migrate, or modify Offline Prepper stores.
- Custom identifiers use the `PH-` prefix plus a UUID hex value; do not create UPC/EAN values.
- Use existing `InventoryItem`, `InventoryState`, `InventoryEvent`, and `BarcodeLookup` tables; no database migration.
- Scanning a saved label is lookup-only and must not change inventory count.
- Preserve retail barcode lookup and Open Food Facts fallback behavior.
- Protect the new write route with the existing API auth middleware.
- Do not create or deploy a rice record as part of the code change; the user enters the exact package description.
- Preserve the current visual system and document the feature in README with screenshots from a running app.

## Review Focus

- Blank/whitespace item names and nonpositive counts must be rejected without partial inventory writes; cover in the API validation test.
- A generated code collision must not overwrite an existing mapping; handle the uniqueness failure safely and cover collision behavior.
- Existing item state must increment by the requested package count, not be reset; cover existing-item API test.
- Scanning an internal code while external lookup is unavailable must still return the local item and leave stock unchanged; cover local-cache API test.
- Long names/package descriptions and narrow viewports must not clip the printed barcode label; exercise desktop and phone-sized print preview.

---

## Files to change

- Modify `backend/app/models/schemas.py` — label-create request/response and optional label creation timestamp in barcode lookup response.
- Modify `backend/app/api/routes/barcode.py` — authenticated create-label transaction and local lookup timestamp.
- Create `backend/tests/test_barcode_labels.py` — validation, inventory update, collision, and local-scan behavior.
- Modify `web/src/api/client.js` — typed-in-shape API function following existing client conventions.
- Modify `web/src/pages/BarcodeScan.jsx` — label form, saved-label preview, barcode scan continuity, and print control.
- Modify `web/src/index.css` — print-only label styling; leave the on-screen design intact.
- Modify `web/package.json` and `web/package-lock.json` — add `jsbarcode` without an exact direct-dependency pin.
- Create `web/src/test/BarcodeScan.test.jsx` — creation and error states plus print action.
- Modify `README.md` — how to create/scan/print locally generated pantry labels and limitations.
- Create `docs/screenshots/barcode-labels/desktop.png` and `phone.png` — capture the real feature at both sizes.

## Task 1: Backend create-label API and local lookup

**Interfaces:**
- `BarcodeLabelCreateRequest`: `product_name: str`, `package_description: Optional[str] = None`, `quantity_estimate: int = 1` (must be ≥1).
- `BarcodeLabelCreateResponse`: `barcode: str`, `item_id: str`, `item_name: str`, `package_description: Optional[str]`, `quantity_estimate: int`, `label_created_at: datetime`.
- `BarcodeLookupResult.label_created_at: Optional[datetime] = None`; return it only for locally generated entries.
- `POST /v1/barcode/create-label` accepts the request and returns the response.

- [ ] Write `backend/tests/test_barcode_labels.py` tests for: new item saves count and mapping; existing item count increments; empty name/count 0 are rejected without creating rows; generated identifiers match `^PH-[0-9a-f]{32}$` and collisions do not overwrite; a later `GET /v1/barcode/{barcode}` is served from local cache without external lookup or stock change.
- [ ] Run `cd backend && pytest -q tests/test_barcode_labels.py`; confirm expected failures because the request/route are not implemented.
- [ ] Implement the schema and route in the files above. Generate the code server-side with `uuid.uuid4().hex`; write item/state/event/BarcodeLookup changes in one transaction; handle a unique collision by rolling back and returning a safe server error rather than replacing another row. For existing inventory items, add `quantity_estimate` to the current count. Set `source="manual"` and store `package_description` as the barcode quantity label.
- [ ] Re-run the focused backend test and full `cd backend && .venv312/bin/pytest -q`; all pass.
- [ ] Commit the backend slice with `git add backend/app/models/schemas.py backend/app/api/routes/barcode.py backend/tests/test_barcode_labels.py && git commit -m "feat: create internal pantry barcode labels"`.

## Task 2: Barcode label UI, print, docs, and visual QA

**Interfaces:**
- Add `createBarcodeLabel(payload)` in `web/src/api/client.js`, posting to `/v1/barcode/create-label`.
- On success, `BarcodeScan` receives `barcode`, `item_name`, `package_description`, `quantity_estimate`, and `label_created_at`; render that exact value using JsBarcode `CODE128` in an SVG.

- [ ] Write `web/src/test/BarcodeScan.test.jsx` to verify the label form submits the entered item/quantity, shows a generated Code 128 SVG and print control, and shows backend validation/network errors. Verify scanning-related paths continue to call the existing lookup API.
- [ ] Run `cd web && npm test -- --reporter=dot`; confirm the new feature tests fail for missing UI/API wiring.
- [ ] Add `jsbarcode` and implement the API client and UI form, label preview, and `window.print()` action. Include a print stylesheet that prints only the label with readable product/package/date text and barcode value; keep existing screen behavior intact.
- [ ] Update `README.md` with concise instructions for generating and scanning internal labels, plus the limit that codes are Pantry Helper-local rather than retail UPCs.
- [ ] Run the new frontend tests, the full web test suite, and `npm run build`.
- [ ] Launch the app with a test backend; exercise create → preview/print → scan by camera/manual lookup at desktop and phone sizes. Check empty, invalid, success, API-error and print states; inspect screenshots for clipping, hierarchy, keyboard focus, and tap targets.
- [ ] Save desktop and phone captures of the real feature to the planned screenshot paths after visual inspection; commit the frontend, README, tests, and screenshots with `git add README.md web/package.json web/package-lock.json web/src/api/client.js web/src/pages/BarcodeScan.jsx web/src/index.css web/src/test/BarcodeScan.test.jsx docs/screenshots/barcode-labels && git commit -m "feat: add printable pantry barcode labels"`.

## Baseline before implementation

- Clean feature worktree: `/root/pantry-helper-barcode-labels` on `feat/pantry-barcode-labels`, based on `origin/main`.
- `cd web && npm ci --no-audit --no-fund` completed.
- Baseline web suite: 3 files, 29 tests passed. Existing Vite/esbuild deprecation warnings are present.
- Baseline backend suite: 148 passed, 103 existing deprecation warnings, using Python 3.12 in `backend/.venv312`. The system Python 3.14 cannot build the repository's pinned `psycopg2-binary==2.9.9` (no wheel; local `pg_config` absent), so use the validated Python 3.12 environment for backend tests.
