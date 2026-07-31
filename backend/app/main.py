import os

import redis as sync_redis
from sqlalchemy import text

from app.log_config import setup_logging

logger = setup_logging("pantry-api")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import ingest, inventory, admin, devices, advanced_inventory, agent
from app.api.routes import shopping, reviews, captures, zones, household, barcode, detections, nutrition
from app.config import settings
from app.db.database import engine, Base
from app.exceptions import PantryException
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_log import RequestLogMiddleware

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pantry Inventory API",
    version="1.0.0",
    description="Event-driven pantry inventory system with ESP32 camera integration"
)

# Exception handler for PantryException
@app.exception_handler(PantryException)
async def pantry_exception_handler(request, exc: PantryException):
    logger.error("PantryException", extra={
        "status_code": exc.status_code,
        "detail": exc.message,
    })
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "status_code": exc.status_code,
            **({"details": exc.details} if exc.details else {})
        },
    )

# Request logging middleware (outermost — captures all requests including rate-limited ones)
app.add_middleware(RequestLogMiddleware)

# Rate limiting middleware (must be added before CORS)
app.add_middleware(RateLimitMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, prefix="/v1", tags=["ingest"])
app.include_router(inventory.router, prefix="/v1", tags=["inventory"])
app.include_router(advanced_inventory.router, prefix="/v1", tags=["advanced_inventory"])
app.include_router(devices.router, prefix="/v1", tags=["devices"])
app.include_router(admin.router, prefix="/v1", tags=["admin"])
app.include_router(shopping.router, prefix="/v1", tags=["shopping"])
app.include_router(reviews.router, prefix="/v1", tags=["reviews"])
app.include_router(captures.router, prefix="/v1", tags=["captures"])
app.include_router(zones.router, prefix="/v1", tags=["zones"])
app.include_router(household.router, prefix="/v1", tags=["household"])
app.include_router(barcode.router, prefix="/v1", tags=["barcode"])
app.include_router(agent.router, prefix="/v1", tags=["agent"])
app.include_router(detections.router, prefix="/v1", tags=["detections"])
app.include_router(nutrition.router, prefix="/v1", tags=["nutrition"])

@app.get("/health")
async def health_check():
    """
    Health check endpoint with dependency verification.

    Returns:
        HTTP 200 + status "ok" when all checks pass.
        HTTP 200 + status "degraded" when non-critical checks fail (Redis, storage).
        HTTP 503 + status "critical" when critical checks fail (database).
    """
    logger.info("Health check requested")

    health = {
        "status": "ok",
        "version": "1.0.0",
        "checks": {},
    }

    # ── Database check (critical) ──
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health["checks"]["database"] = {"status": "ok"}
    except Exception as e:
        logger.error("Health check: database unreachable", extra={"error": str(e)})
        health["checks"]["database"] = {"status": "error", "detail": str(e)}
        health["status"] = "critical"

    # ── Redis check (non-critical — API can serve cached data without it) ──
    try:
        r = sync_redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=3,
        )
        r.ping()
        r.close()
        health["checks"]["redis"] = {"status": "ok"}
    except Exception as e:
        health["checks"]["redis"] = {"status": "unavailable", "detail": str(e)}
        if health["status"] == "ok":
            health["status"] = "degraded"

    # ── Storage check (non-critical) ──
    try:
        storage_path = settings.STORAGE_PATH
        if storage_path and os.path.exists(storage_path):
            stat = os.statvfs(storage_path)
            avail = stat.f_frsize * stat.f_bavail
            total = stat.f_frsize * stat.f_blocks
            used_pct = round((1 - stat.f_bavail / stat.f_blocks) * 100, 1)
            health["checks"]["storage"] = {
                "status": "ok",
                "free_bytes": avail,
                "total_bytes": total,
                "used_pct": used_pct,
            }
            if used_pct > 90:
                health["checks"]["storage"]["status"] = "warning"
        else:
            health["checks"]["storage"] = {"status": "unavailable"}
    except Exception as e:
        health["checks"]["storage"] = {"status": "error", "detail": str(e)}

    # ── Response ──
    if health["status"] == "critical":
        return JSONResponse(status_code=503, content=health)

    return health

@app.on_event("startup")
async def startup_event():
    logger.info("Pantry API started", extra={
        "version": "1.0.0",
        "providers": {
            "vision": os.getenv("VISION_PROVIDER", "not set"),
            "db": os.getenv("DATABASE_URL", "not set")[:30] + "...",
        }
    })
