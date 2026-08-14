# Meal Planning Feature — Audit + Implementation Plan

**Date:** 2026-08-14
**Repo:** brandongraves08/pantry-helper (CT202, live)
**Audit basis:** live API (`/v1/openapi.json`), live DB data, repo `main` @ 4c10ad4, `FEATURE_ARCHITECTURE.md`

---

## Part 1 — Audit: what exists today

### ✅ Already built (reuse, don't rebuild)

| Piece | Status | Details |
|---|---|---|
| **Recipes CRUD** | DONE | `/v1/recipes` GET/POST, `/v1/recipes/{id}` GET/PUT/DELETE. Model: name, description, source, servings, prep/cook time, instructions + `recipe_ingredients` (position, quantity string, name, note, optional `inventory_item_id` link). |
| **Recipe ingredient → inventory link** | DONE | Ingredients can link to an `inventory_item`; serializer exposes `inventory_item_id` + `inventory_item_name`. |
| **Per-recipe pantry verify** | DONE | `GET /v1/recipes/{id}/shopping-needs` — per ingredient: `ok` / `below_par` / `no_par` / `not_tracked` with count + par_level. |
| **Shopping list** | DONE | `GET /v1/shopping-list` + `POST /v1/shopping-list/recompute`. Par-driven (`needed = par − count`), unresolved rows only, reason field. Discord notify via Celery. |
| **Recipes web page** | DONE | `web/src/pages/Recipes.jsx` — list, search, add/edit modal, delete, detail view w/ shopping-needs. Wired in App.jsx nav. |
| **HEB cart filler** | BUILT, BLOCKED | `/root/.hermes/scripts/heb_cart_filler.py` reads `/v1/shopping-list` → searches heb.com via camofox → adds to cart. **Blocked on Brandon's HEB login cookie handoff** into the `heb-order` camofox profile. |
| **HEB item map** | DONE | `ecommerce-cart-automation/references/heb-item-map.json` — pantry canonical name → HEB query + preferred product. |

### ❌ Missing (the actual gap)

1. **No meal plan / daily schedule.** No table, no API, no UI. `FEATURE_ARCHITECTURE.md` marks "Meal Planning Integration ❌".
2. **No multi-recipe aggregation.** `shopping-needs` is per-recipe only; nothing sums a week of recipes into one requirement list.
3. **Shopping list ignores planned meals.** It's par-level only — a recipe needing an item that's *above par* (but short for the meal) never lands on the list.
4. **No "verify plan against pantry" endpoint** for a date range / week.
5. **No flow from "missing" → HEB order.** The cart filler only sees the par shopping list; meal-driven needs don't reach it.

### ⚠️ Audit findings that affect the build (gotchas)

- **`not_tracked` ingredients get silently skipped.** Current `shopping-needs` returns `not_tracked` for unlinked ingredients (salt, pepper, fresh herbs, lettuce — pantry intentionally doesn't track them). For meal planning these are exactly what you'd want on the HEB order. Decision needed (see below).
- **Quantity is a free-text string** (`"1½ lb"`, `"½ cup"`, `"4 slices"`) vs inventory `count_estimate` integer. Verification must decide: count-based items compare counts; weight/volume items need a "units per use" heuristic.
- **Live shopping list has duplicate canonical names** (e.g. 3 Black Beans rows, Bush's beans ×2) — multiple `inventory_items` share a canonical name. The merge must dedupe by canonical name or it'll double-order.
- **Confidence matters.** 41/54 live inventory items sit at 0.30 confidence (unverified photo stocktake). Verification should respect `min_confidence` (0.5 default, same as low-stock) or the plan will claim "have it" on unconfirmed counts.
- **Deploy gotchas (known):** new tables → `create_all` races alembic → `alembic stamp 007`; CT202 pulls need the token URL; always verify the running container actually has your code (`docker exec pantry-api grep`); preserve CT202 local compose mods.

---

## Part 2 — Feature plan: Meal Planning

### Goal
Save recipes → schedule what's made each day → verify ingredients against pantry → anything missing lands on the shopping list → flows to the HEB order.

### Data model (migration `007_meal_plans.py`)

```python
class MealPlan(Base):
    __tablename__ = "meal_plans"
    id          = Column(String, primary_key=True, default=uuid4)
    week_start  = Column(Date, nullable=False, index=True)   # Monday of plan week
    name        = Column(String, nullable=True)              # "Week of 8/17", optional
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class MealPlanEntry(Base):
    __tablename__ = "meal_plan_entries"
    id            = Column(String, primary_key=True, default=uuid4)
    meal_plan_id  = Column(String, ForeignKey("meal_plans.id"), nullable=False, index=True)
    plan_date     = Column(Date, nullable=False, index=True)   # the actual day
    meal_type     = Column(String, nullable=False)             # breakfast | lunch | dinner | snack
    recipe_id     = Column(String, ForeignKey("recipes.id"), nullable=False)
    servings_multiplier = Column(Integer, nullable=False, default=1)  # 1x recipe = 4 servings etc.
    notes         = Column(String, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
```

One `MealPlan` per week (Mon–Sun) keeps it simple; entries carry the actual date so you can schedule across the week. Reuse of `recipes.id` means ingredients come for free.

### Backend API (`backend/app/api/routes/meal_plans.py`)

| Endpoint | Purpose |
|---|---|
| `GET /v1/meal-plans?start=&end=` | List plans/entries in a date range (with recipe + ingredient detail) |
| `POST /v1/meal-plans` | Create a week plan |
| `PUT /v1/meal-plans/{id}` | Rename/reschedule week |
| `DELETE /v1/meal-plans/{id}` | Delete plan (cascade entries) |
| `POST /v1/meal-plans/{id}/entries` | Schedule a recipe: `{plan_date, meal_type, recipe_id, servings_multiplier}` |
| `DELETE /v1/meal-plans/entries/{entry_id}` | Remove a scheduled meal |
| `GET /v1/meal-plans/{id}/verify` | **The core:** aggregate all entries' ingredients vs pantry → per item: `have`, `need_total`, `missing`, `status` (ok/short/not_tracked), `confidence`-filtered |
| `POST /v1/meal-plans/{id}/update-shopping` | Merge `missing` items into shopping list (`reason="meal plan"`), deduped by canonical name |

**Verify algorithm (per planned meal, × servings_multiplier):**
1. For each ingredient linked to an inventory item: sum required across entries (parsed quantity → units, see decision D2). Count available = `count_estimate` for states with `confidence >= 0.5`.
2. `missing = max(0, required − available)` → status `ok` / `short`.
3. Unlinked ingredients → `not_tracked`; **default: include on the order** unless the recipe marks them as pantry-staples (D1).
4. Merge into `shopping_list_items` with `reason='meal plan'`, dedupe by canonical name, don't clobber existing `below par` rows (keep the max needed).

### Web UI (`web/src/pages/MealPlans.jsx` + nav)

- **Week view** (Mon–Sun columns, 4 meal slots per day). Pick a recipe per slot via search dropdown (reuses recipe list).
- Each slot shows servings multiplier + small ingredient-count badge.
- **Verify banner** per day/week: "3 of 7 ingredients short — 2 on HEB order" with expandable per-item list (have X / need Y).
- **"Add missing to HEB order"** button → calls `update-shopping`, then hands off to the cart filler (Phase 3).
- Nav: `MealPlans` item, `BookOpen`/`CalendarDays` icon.

### HEB order integration (Phase 3)

- Reuse `heb_cart_filler.py` unchanged — it reads `/v1/shopping-list`, so meal-plan items (reason `meal plan`) ride along automatically.
- **Blocker:** HEB login cookie handoff into camofox `heb-order` profile (Brandon signs in once, pastes cookie header — 2 min).
- Extend `heb-item-map.json` for any new canonical names the recipes introduce.

---

## Part 3 — Build order (phases)

### Phase 1 — Backend core (the engine)
1. Models + migration `007_meal_plans.py` (watch the `create_all` race → `alembic stamp 007`).
2. `meal_plans.py` router: CRUD + entries + `verify` + `update-shopping`.
3. Schemas in `schemas.py` (MealPlan, MealPlanEntry, MealPlanVerifyResponse, MealPlanItemNeed).
4. Wire router in `main.py`; py_compile + throwaway-venv import test.
5. Deploy to CT202 (token-URL pull, build backend, verify container has symbols).

### Phase 2 — Web UI
6. `MealPlans.jsx` week planner + verify badges + "add to HEB" button; `client.js` API fns; nav route.
7. `npm run build` must pass; deploy web container; verify asset hash.

### Phase 3 — HEB flow
8. Confirm cart filler picks up meal-plan items; refresh `heb-item-map.json`.
9. **Needs Brandon:** HEB login cookie handoff → cart filler dry-run → live add-to-cart.

---

## Part 4 — Decisions I need from you

**D1 — Untracked ingredients (salt, fresh herbs, lettuce, pickle juice):**
- (a) **Default: add to HEB order** unless recipe marks them "pantry staple" — recommended, because fresh produce IS an HEB item.
- (b) Always skip untracked — keep pantry philosophy (they're assumed stocked).
- (c) Per-recipe flag at save time.

**D2 — Quantity math:** recipe quantities are strings (`"1½ lb"`, `"½ cup"`). For MVP I'll parse numerics (`1½`, `½`, `4`, `2`) and compare against integer counts with a "1 unit per use" heuristic for weight/volume items, flagged as `approx` in the verify output. Good enough to catch "out of ground beef," wrong for "exactly 0.8 lb left." Acceptable?

**D3 — Verify window:** current week only, or rolling 7 days from today (so Friday planning catches Monday)? Recommend **rolling 7 days**.

**D4 — Auto vs manual HEB push:** after `update-shopping`, auto-run the cart filler (needs login handoff first), or just stage the list and ping you? Recommend **stage + ping until login is done, then auto.**

---

## Deliverables when done
- Recipes you can save (already live) → plan the week in the UI → one click verifies against real pantry counts → missing items in the shopping list → HEB cart filler adds them to your order. End-to-end.

*Plan file: docs/MEAL_PLANNING_PLAN.md (this doc).*
