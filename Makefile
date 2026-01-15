.PHONY: help backend-install backend-run backend-test backend-migrate firmware-build firmware-upload web-install web-dev clean

help:
	@echo "Pantry Inventory - Available targets:"
	@echo ""
	@echo "Backend:"
	@echo "  make backend-install     Install backend dependencies"
	@echo "  make backend-run         Run backend API server"
	@echo "  make backend-test        Run backend tests"
	@echo "  make backend-migrate     Run database migrations"
	@echo "  make backend-seed        Seed test devices and data"
	@echo ""
	@echo "Firmware:"
	@echo "  make firmware-build      Build ESP32 firmware"
	@echo "  make firmware-upload     Upload firmware to device"
	@echo ""
	@echo "Web UI:"
	@echo "  make web-install         Install web dependencies"
	@echo "  make web-dev             Run web dev server"
	@echo "  make web-build           Build web for production"
	@echo ""
	@echo "General:"
	@echo "  make clean               Clean build artifacts"
	@echo "  make all                 Install all dependencies"

# Backend targets
backend-install:
	cd backend && pip install -r requirements.txt

backend-run:
	cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	cd backend && python -m pytest tests/ -v

backend-migrate:
	cd backend && python -m alembic upgrade head

backend-migrate-down:
	cd backend && python -m alembic downgrade -1

backend-seed:
	cd backend && python scripts/seed_db.py seed

# Firmware targets
firmware-build:
	cd firmware && pio run -e esp32-cam

firmware-upload:
	cd firmware && pio run -e esp32-cam -t upload

firmware-monitor:
	cd firmware && pio device monitor -e esp32-cam

# Web UI targets
web-install:
	cd web && npm install

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build

web-preview:
	cd web && npm run preview

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	cd backend && rm -rf .pytest_cache dist build *.egg-info || true
	cd firmware && rm -rf .pio build || true
	cd web && rm -rf node_modules dist .next || true

install: backend-install web-install

run: backend-run

dev:
	@echo "Starting all services..."
	@echo "Backend will start on http://localhost:8000"
	@echo "Web UI will start on http://localhost:5173"
	@echo "API docs available at http://localhost:8000/docs"
	make backend-run

build: firmware-build web-build

all: backend-install web-install
	@echo "All dependencies installed!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure backend/.env with database and OpenAI API key"
	@echo "2. Run 'make backend-seed' to create test devices"
	@echo "3. Run 'make backend-run' to start the API server"
	@echo "4. Run 'make web-dev' to start the web UI"
