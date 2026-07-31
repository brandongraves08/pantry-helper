#!/usr/bin/env bash
# Pantry Helper — Setup Script
# Usage: ./setup.sh [--docker]

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "🍅 Pantry Helper Setup"
echo "━━━━━━━━━━━━━━━━━━━━"

if [[ "${1:-}" == "--docker" ]]; then
    echo "🐳 Setting up with Docker..."
    
    # Check .env
    if [ ! -f .env ]; then
        cp .env.docker.example .env
        echo "⚠️  Created .env from .env.docker.example — configure your API keys"
    fi
    
    echo "Starting Docker services..."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    echo "✅ Services running!"
    echo "   API:   http://localhost:8000"
    echo "   Web:   http://localhost:3000"
    echo "   Docs:  http://localhost:8000/docs"
    echo ""
    echo "Next: create a test device:"
    echo "  docker compose exec backend python register_device.py --name pantry-cam-001"
    exit 0
fi

echo "📦 Setting up for local development..."

# Backend
echo ""
echo "→ Backend (Python)"
cd "$ROOT_DIR/backend"

if [ ! -d venv ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

# Copy .env if needed
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Created backend/.env from .env.example — configure your API keys"
fi

# Check for DB
if [ ! -f pantry.db ]; then
    echo "   Creating SQLite database..."
    python3 -c "from app.db.database import engine, Base; Base.metadata.create_all(bind=engine)" 2>/dev/null || true
fi

cd "$ROOT_DIR"

# Web UI
echo ""
echo "→ Web UI"
cd "$ROOT_DIR/web"
if [ ! -d node_modules ]; then
    npm install
fi

cd "$ROOT_DIR"

echo ""
echo "✅ Local setup complete!"
echo ""
echo "To start, run in three terminals:"
echo "  Terminal 1:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "  Terminal 2:  cd web && npm run dev"
echo ""
echo "Or use the API directly:"
echo "  curl http://localhost:8000/health"
