from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import ingest, inventory, admin, devices, advanced_inventory
from app.db.database import engine, Base
from app.exceptions import PantryException
from app.middleware.rate_limit import RateLimitMiddleware
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "status_code": exc.status_code,
            **({"details": exc.details} if exc.details else {})
        },
    )

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

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
