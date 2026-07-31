#!/bin/bash
# Celery worker startup with OpenClaw gateway vision provider
cd /home/brandon/clawd/pantry-helper/backend
source venv/bin/activate

export VISION_PROVIDER="${VISION_PROVIDER:-openclaw}"
export OPENCLAW_VISION_URL="${OPENCLAW_VISION_URL:-http://172.16.1.1:18790/analyze}"
export OPENCLAW_GATEWAY_TOKEN_FILE="${OPENCLAW_GATEWAY_TOKEN_FILE:-/home/brandon/.openclaw/secrets/openclaw.gateway.token}"
export OPENCLAW_VISION_MODEL="${OPENCLAW_VISION_MODEL:-openai/gpt-5.4-mini}"
export OPENCLAW_TIMEOUT="${OPENCLAW_TIMEOUT:-120}"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"

exec celery -A app.workers.celery_app worker --loglevel=info
