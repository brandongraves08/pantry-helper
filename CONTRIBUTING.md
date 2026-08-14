# Contributing to Pantry Helper

Thanks for wanting to help! This is a self-hosted pantry inventory + meal planning system. Here's how to contribute without stepping on anyone's toes.

## Getting started

1. **Fork** the repo and clone your fork.
2. **Run it locally:** `docker compose up -d --build` (backend on :8000, web on :3000). See `README.md` for the full setup.
3. Create a feature branch: `git checkout -b feat/your-thing`.

## What we're looking for

- Bug fixes with a failing test or repro description.
- New features that fit the existing architecture (`backend/app/api/routes/<feature>.py` router + `web/src/pages/<Feature>.jsx` page).
- Docs improvements, especially for self-hosting and ESP32 setup.

## Development notes

- **Backend:** FastAPI + SQLAlchemy + Postgres. New tables go in `backend/app/db/models.py` + an alembic migration in `backend/migrations/versions/`.
  - ⚠️ Known quirk: `Base.metadata.create_all` runs on startup and races alembic. For brand-new tables expect `DuplicateTable` during `alembic upgrade` — use `alembic stamp <revision>` to align history. See `pantry-app-development` notes in the repo docs.
- **Web:** React + Vite + Tailwind. `npm run build` must pass before opening a PR.
- **API auth:** Write routes require `Authorization: Bearer <PANTRY_API_TOKEN>` (env). The web app sends it automatically via `VITE_PANTRY_API_TOKEN`.

## Before opening a PR

- [ ] No secrets: run a grep for tokens/keys (`ghp_`, `sk-`, `AIza`, `PANTRY_API_TOKEN=`) over your branch.
- [ ] Backend changes: `python3 -m py_compile` on changed files.
- [ ] Web changes: `npm run build` succeeds.
- [ ] Update `FEATURE_ARCHITECTURE.md` if you add or remove a feature.

## Code of conduct

Be kind. Assume good faith. This is a homelab project that became public — the maintainer runs it for real, so breaking changes need a real reason.
