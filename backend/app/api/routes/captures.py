from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.db.database import get_db
from app.db.models import Capture, Observation
from app.models.schemas import CaptureDetail
from app.services.storage import get_storage_manager

router = APIRouter()


@router.get("/captures/{capture_id}", response_model=CaptureDetail)
async def get_capture(capture_id: str, db: Session = Depends(get_db)):
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
    """Serve the stored image for a capture.

    Note: This is intentionally simple for on-prem/LAN mode.
    Later we should add auth.
    """
    cap = db.query(Capture).filter(Capture.id == capture_id).first()
    if not cap:
        raise HTTPException(status_code=404, detail="Capture not found")

    image_path = cap.image_path
    if not image_path:
        raise HTTPException(status_code=404, detail="Image not found")

    # Resolve relative paths against STORAGE_PATH
    if not os.path.isabs(image_path):
        storage_mgr = get_storage_manager()
        image_path = str(storage_mgr.storage_path / image_path)

    # Final sanity check
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file missing")

    return FileResponse(image_path, media_type="image/jpeg")
