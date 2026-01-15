#!/bin/bash
# Quick start script for Pantry Inventory development

set -e

echo "🥫 Pantry Inventory - Quick Start"
echo "================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Install from https://python.org"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required. Install from https://nodejs.org"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "❌ pip is required. Usually comes with Python."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm is required. Usually comes with Node.js."
    exit 1
fi

echo "✓ Python 3: $(python3 --version)"
echo "✓ Node.js: $(node --version)"
echo "✓ npm: $(npm --version)"
echo ""

# Install dependencies
echo "Installing dependencies..."
make all 2>&1 | tail -5
echo "✓ Dependencies installed"
echo ""

# Configure backend
echo "Configuring backend..."
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "✓ Created backend/.env (update with your OpenAI API key)"
else
    echo "✓ backend/.env already exists"
fi
echo ""

# Initialize database
echo "Initializing database..."
cd backend && python scripts/seed_db.py seed 2>&1 | tail -10
cd ..
echo "✓ Database initialized with test devices"
echo ""

# Summary
echo "================================="
echo "✓ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Update backend/.env with your OpenAI API key:"
echo "   export OPENAI_API_KEY=sk-..."
echo ""
echo "2. Start the backend API (Terminal 1):"
echo "   make backend-run"
echo ""
echo "3. Start the web UI (Terminal 2):"
echo "   make web-dev"
echo ""
echo "4. Open the web UI:"
echo "   http://localhost:5173"
echo ""
echo "5. View API docs:"
echo "   http://localhost:8000/docs"
echo ""
echo "For more info, see DEVELOPMENT.md"
