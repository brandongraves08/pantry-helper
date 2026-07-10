"""Capture routes with structured logging."""
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging
import os

from app.db.database import get_db
from app.db.models import Capture, Device, Observation
from app.models.schemas import CaptureDetail, CaptureResponse
from app.services.storage import get_storage_manager
from app.auth import TokenManager

logger = logging.getLogger("pantry-api.captures")

router = APIRouter()


@router.get("/captures")
async def list_captures(
    limit: int = 25,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    logger.info("Listing captures", extra={"limit": limit, "skip": skip})
    limit = max(1, min(limit, 100))
    skip = max(0, skip)
    total = db.query(Capture).count()
    captures = (
        db.query(Capture)
        .order_by(Capture.captured_at.desc(), Capture.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {
        "captures": [
            {
                "id": cap.id,
                "device_id": cap.device_id,
                "trigger_type": cap.trigger_type,
                "captured_at": cap.captured_at,
                "status": cap.status,
                "error_message": cap.error_message,
                "image_url": f"/v1/captures/{cap.id}/image",
            }
            for cap in captures
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/captures/manual", response_model=CaptureResponse)
async def create_manual_capture(
    device_id: str | None = Form(None),
    notes: str | None = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    logger.info("Manual capture initiated", extra={
        "device_id": device_id,
        "upload_filename": image.filename,
        "content_type": image.content_type,
    })

    device = None
    if device_id:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            logger.warning("Device not found", extra={"device_id": device_id})
            raise HTTPException(status_code=404, detail="Device not found")
    else:
        device = db.query(Device).order_by(Device.created_at.asc()).first()

    if not device:
        token = TokenManager.generate_token()
        device = Device(
            id="dashboard-manual",
            name="Dashboard Manual Capture",
            token_hash=TokenManager.hash_token(token),
        )
        db.add(device)
        db.flush()
        logger.info("Created auto-device for manual capture", extra={"device_id": device.id})

    content = await image.read()
    if not content:
        logger.error("Empty image file")
        raise HTTPException(status_code=400, detail="Image file is empty")

    capture = Capture(
        device_id=device.id,
        trigger_type="manual",
        captured_at=datetime.utcnow(),
        image_path="pending",
        battery_v=None,
        rssi=None,
        status="stored",
    )
    db.add(capture)
    db.flush()

    storage_mgr = get_storage_manager()
    capture.image_path = storage_mgr.save_image(
        device_id=device.id,
        capture_id=capture.id,
        image_data=content,
    )
    device.last_seen_at = datetime.utcnow()
    db.commit()

    logger.info("Capture stored", extra={
        "capture_id": capture.id,
        "image_size": len(content),
        "image_path": capture.image_path,
    })

    try:
        from app.workers.celery_app import process_image_capture
        process_image_capture.delay(capture.id)
        logger.info("Capture queued for analysis", extra={"capture_id": capture.id})
    except Exception as task_err:
        logger.error("Failed to queue analysis task", extra={
            "capture_id": capture.id,
            "error": str(task_err),
        })
        capture.error_message = f"Queued capture but failed to start analysis: {task_err}"
        db.commit()

    return CaptureResponse(
        capture_id=capture.id,
        status=capture.status,
        message="Photo received and queued for inventory analysis",
    )


@router.get("/captures/{capture_id}", response_model=CaptureDetail)
async def get_capture(capture_id: str, db: Session = Depends(get_db)):
    logger.info("Fetching capture", extra={"capture_id": capture_id})
    cap = db.query(Capture).filter(Capture.id == capture_id).first()
    if not cap:
        raise HTTPException(status_code=404, detail="Capture not found")
    obs = (
        db.query(Observation)
        .filter(Observation.capture_id == cap.id)
        .order_by(Observation.created_at.desc())
        .first()
    )
    return CaptureDetail(
        id=cap.id,
        device_id=cap.device_id,
        trigger_type=cap.trigger_type,
        captured_at=cap.captured_at,
        status=cap.status,
        error_message=cap.error_message,
        image_path=cap.image_path,
        latest_observation=obs.raw_json if obs else None,
    )


@router.get("/captures/{capture_id}/image")
async def get_capture_image(capture_id: str, db: Session = Depends(get_db)):
    cap = db.query(Capture).filter(Capture.id == capture_id).first()
    if not cap:
        raise HTTPException(status_code=404, detail="Capture not found")
    image_path = cap.image_path
    if not image_path:
        raise HTTPException(status_code=404, detail="Image not found")
    if not os.path.isabs(image_path):
        storage_mgr = get_storage_manager()
        image_path = str(storage_mgr.storage_path / image_path)
    if not os.path.exists(image_path):
        logger.warning("Image file missing", extra={"capture_id": capture_id, "path": image_path})
        raise HTTPException(status_code=404, detail="Image file missing")
    return FileResponse(image_path, media_type="image/jpeg")
