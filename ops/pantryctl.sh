#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DC=(docker compose)
COMPOSE_FILES=(-f docker-compose.yml)

MODE=${PANTRY_MODE:-dev}
if [[ "${2:-}" == "--prod" ]] || [[ "${1:-}" == *"prod"* ]]; then
  MODE=prod
  COMPOSE_FILES+=(-f docker-compose.prod.yml)
fi

cmd=${1:-status}
shift || true

urls() {
  echo "Web UI:       http://localhost:3000"
  echo "API:          http://localhost:8000"
  echo "API Docs:     http://localhost:8000/docs"
  echo "Flower:       http://localhost:5555"
}

case "$cmd" in
  up|up-prod|start|start-prod)
    "${DC[@]}" "${COMPOSE_FILES[@]}" up -d --build
    echo "\nServices up ($MODE)."
    urls
    ;;
  down|stop)
    "${DC[@]}" "${COMPOSE_FILES[@]}" down
    ;;
  restart)
    "${DC[@]}" "${COMPOSE_FILES[@]}" restart
    ;;
  ps|status)
    "${DC[@]}" "${COMPOSE_FILES[@]}" ps
    echo ""
    urls
    ;;
  logs)
    "${DC[@]}" "${COMPOSE_FILES[@]}" logs -f "${1:-}"
    ;;
  shell)
    svc=${1:-backend}
    "${DC[@]}" "${COMPOSE_FILES[@]}" exec "$svc" /bin/sh
    ;;
  migrate)
    "${DC[@]}" "${COMPOSE_FILES[@]}" exec -T backend alembic upgrade head
    ;;
  seed)
    "${DC[@]}" "${COMPOSE_FILES[@]}" exec -T backend python scripts/seed_db.py
    ;;
  health)
    curl -fsS http://localhost:8000/health && echo
    ;;
  *)
    echo "Usage: ops/pantryctl.sh {up|up-prod|down|restart|status|logs [svc]|shell [svc]|migrate|seed|health}"
    exit 1
    ;;
esac
