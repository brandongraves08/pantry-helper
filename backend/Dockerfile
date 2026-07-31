# =============================================================
# Pantry Helper Backend — Multi-stage Dockerfile
#   Builder : install pip packages (no gcc needed — all wheels)
#   Runtime : slim image with only runtime apt deps
# =============================================================

# ---- Builder Stage ----
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# libzbar0 headers not needed at build time (pyzbar uses ctypes at runtime)
# but needed so pyzbar can verify the .so exists during install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Runtime Stage (prod target) ----
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Runtime deps only — no build tools, no recommends (avoids ImageMagick pull)
# libzbar0 Recommends: libmagickcore (huge) — stripped with --no-install-recommends
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzbar0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 10001 appuser

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create persistent data and logs directories
RUN mkdir -p /data/storage logs && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default: uvicorn (dev mode — reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---- Prod target (gunicorn, no reload) ----
FROM runtime AS prod

# Override with production entrypoint — no reload
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

# ---- Dev target (includes test deps) ----
FROM runtime AS dev

USER root
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
