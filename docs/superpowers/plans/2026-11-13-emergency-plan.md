# 90-Day Emergency Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the supplied 90-day emergency food and water plan to Pantry Helper as a distinct, usable plan page without changing tracked inventory.

**Architecture:** Implement one React page using the existing router, sidebar, styling, and icon conventions. Keep plan data in the frontend and persist only checklist completion in browser localStorage; no backend, database migration, dependencies, or inventory writes.

**Tech Stack:** Existing React/Vite, Tailwind, lucide-react, and current frontend test/build setup.

**Spec:** Approved in Discord thread 1570920576191832245; source document `90-Day-Emergency-Food-Supply-Plan.md` supplied in that thread.

## Global Constraints

- Preserve the supplied plan's stated quantities, calories, exclusions, assumptions, safety instructions, and citations; identify food/calorie quantities as estimates.
- The page must not create or modify regular pantry inventory, shopping-list data, or server-side state.
- Save checkbox completion locally in the browser only; a first visit shows all checklist items incomplete.
- Match existing Pantry Helper visual identity; support desktop and phone widths and accessible labels/focus states.
- No new dependencies, schema/API/config changes, secrets, deployment, or external publication in this task.

## Review Focus

- A fresh browser/localStorage shows all controls unchecked; persisted progress restores only that browser's checklist.
- Calories and stages distinguish the 720,000 kcal minimum from the estimated 771,500 kcal inventory and its ~96 household-day estimate.
- Water milestones compute/display 12, 28, 56, 120, 240, and 360 gallons without conflating stored water with replenishment.
- Dietary exclusions remain visible and no listed ingredient silently reintroduces lentils, jasmine rice, milk/eggs, chicken, or turkey.
- Long lists, link text, focus rings, and navigation remain usable without horizontal overflow on mobile and desktop.

---

### Task 1: Build and verify the emergency-plan page

**Files:**
- Create: `web/src/pages/EmergencyPlan.jsx`
- Modify: `web/src/App.jsx`
- Test: existing frontend test location/pattern, or add the smallest matching test file if none covers page rendering and persistence.
- Update: `README.md` with the new page/feature and local progress behavior.

**Interfaces:**
- Route: `/emergency-plan`, sidebar label `Emergency Plan`.
- Local storage key: `pantry-helper-emergency-plan-v1`; store a set/list of checked checklist item IDs, tolerate malformed JSON by starting with all unchecked.
- No backend interfaces.

- [ ] Write tests for page content, first-visit unchecked state, localStorage persistence/reload, malformed saved state, and calorie/water milestone labels.
- [ ] Run the targeted tests and confirm the new behavior fails before implementation.
- [ ] Implement the page with sections for assumptions/dietary exclusions, inventory targets, no-cook allocation, weekly meal rotation, water milestones, storage/cooking safety, and phased build. Preserve source values and citations.
- [ ] Add the sidebar route and README feature entry.
- [ ] Run frontend tests and `npm run build`.
- [ ] Launch the actual app and inspect/capture desktop (1440px) and phone (390px) views; exercise the primary task, saved checklist state, and initial state. Check clipping, hierarchy, readability, keyboard focus, and link targets.
- [ ] Report exact changed files, test/build results, screenshots, and any limits. Do not deploy or publish from this task.
