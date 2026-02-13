#!/bin/bash
# Celery worker startup with NVIDIA vision provider
cd /home/brandon/clawd/pantry-helper/backend
source venv/bin/activate

export VISION_PROVIDER=nvidia
export NVIDIA_NIM_API_KEY="${NVIDIA_NIM_API_KEY:-$1}"
export NVIDIA_MODEL="${NVIDIA_MODEL:-meta/llama-3.2-11b-vision-instruct}"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"

exec celery -A app.workers.celery_app worker --loglevel=info
