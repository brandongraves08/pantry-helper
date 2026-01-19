#!/bin/bash

# Pantry Helper - Setup Script
# This script sets up the development environment for the pantry inventory system

set -e

echo "🥫 Pantry Helper - Setup Script"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Check Python version
info "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
info "Found Python ${PYTHON_VERSION}"

# Check if pip is available
info "Checking pip installation..."
if ! python3 -m pip --version &> /dev/null; then
    warning "pip not found, installing pip..."
    
    # Try to install pip using ensurepip
    if python3 -m ensurepip --version &> /dev/null; then
        python3 -m ensurepip --default-pip
        success "pip installed via ensurepip"
    else
        # Download and install pip manually
        info "Downloading pip installer..."
        curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
        python3 /tmp/get-pip.py --user
        rm /tmp/get-pip.py
        success "pip installed manually"
    fi
else
    success "pip is available"
fi

# Check if we're in the right directory
if [ ! -f "Makefile" ] || [ ! -d "backend" ]; then
    error "Please run this script from the project root directory"
    exit 1
fi

success "Project root detected"

# Setup Python virtual environment
info "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "Virtual environment created"
else
    info "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
success "Virtual environment activated"

# Upgrade pip
info "Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel -q
success "pip upgraded"

# Install backend dependencies
info "Installing backend dependencies..."
cd backend
python -m pip install -r requirements.txt -q
cd ..
success "Backend dependencies installed"

# Setup environment file
info "Setting up environment configuration..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    success "Created backend/.env from example"
    warning "Please edit backend/.env and add your API key:"
    warning "  - For OpenAI: Set OPENAI_API_KEY=sk-..."
    warning "  - For Gemini: Set GEMINI_API_KEY=... and VISION_PROVIDER=gemini"
else
    info "backend/.env already exists"
fi

# Create storage directory
info "Creating storage directories..."
mkdir -p storage/images
success "Storage directories created"

# Initialize database
info "Initializing database..."
cd backend
python -m alembic upgrade head 2>/dev/null || {
    warning "Alembic migrations not found, creating tables directly"
    python -c "from app.db.database import engine, Base; from app.db.models import *; Base.metadata.create_all(bind=engine)"
}
cd ..
success "Database initialized"

# Seed test data
info "Seeding test devices..."
cd backend
python scripts/seed_db.py seed 2>/dev/null || warning "Seed script not available or already run"
cd ..

# Check for Node.js
info "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    warning "Node.js is not installed. Web UI setup will be skipped."
    warning "Install Node.js 16+ to enable web UI development"
else
    NODE_VERSION=$(node -v)
    info "Found Node ${NODE_VERSION}"
    
    # Install web dependencies
    info "Installing web UI dependencies..."
    cd web
    npm install
    cd ..
    success "Web UI dependencies installed"
fi

# Check for PlatformIO (optional)
info "Checking PlatformIO installation..."
if ! command -v pio &> /dev/null; then
    warning "PlatformIO CLI not found. Firmware development will be unavailable."
    warning "Install with: pip install platformio"
else
    success "PlatformIO CLI found"
fi

echo ""
echo "================================"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "================================"
echo ""
echo "Next steps:"configure your Vision AI provider:"
echo ""
echo "   For OpenAI (default):"
echo -e "   ${BLUE}VISION_PROVIDER=openai${NC}"
echo -e "   ${BLUE}OPENAI_API_KEY='sk-your-key-here'${NC}"
echo ""
echo "   For Google Gemini:"
echo -e "   ${BLUE}VISION_PROVIDER=gemini${NC}"
echo -e "   ${BLUE}GEMINI_API_KEY='your-gemini-key-here'${NC}"
echo ""
echo "2. Start the backend API:"
echo -e "   ${BLUE}make backend-run${NC}"
echo "   API will be available at http://localhost:8000"
echo "   API docs at http://localhost:8000/docs"
echo ""
echo "3. Start the web UI (in another terminal):"
echo -e "   ${BLUE}make web-dev${NC}"
echo "   UI will be available at http://localhost:5173"
echo ""
echo "4. Test devices created:"
echo "   - pantry-cam-001 (Kitchen Pantry)"
echo "   - pantry-cam-002 (Garage Storage)"
echo ""
echo "For detailed documentation, see:"
echo "  - README.md - Quick start guide"
echo "  - ARCHITECTURE.md - System design"
echo "  - BUILD_STATUS.md - Current statu
echo "  - ARCHITECTURE.md - System design"
echo "  - DEVELOPMENT.md - Development workflows"
echo ""

# Deactivate venv for now
deactivate 2>/dev/null || true
