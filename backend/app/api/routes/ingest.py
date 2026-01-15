import os
import uuid
from datetime import datetime
from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Device, Capture
from app.models.schemas import CaptureResponse
from app.auth import TokenManager
from app.exceptions import (
    DeviceNotFoundError,
    AuthenticationError,
    ValidationError,
    StorageError,
)

router = APIRouter()

# Configure storage path
IMAGES_DIR = os.getenv("IMAGES_DIR", "./storage/images")
os.makedirs(IMAGES_DIR, exist_ok=True)

@router.post("/ingest", response_model=CaptureResponse)
async def ingest_image(
    device_id: str = Form(...),
    timestamp: str = Form(...),
    trigger_type: str = Form(...),
    battery_v: float = Form(...),
    rssi: int = Form(...),
    token: str = Form(...),  # Device authentication token
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Ingest an image from ESP32 device.
    
    Expected multipart form data:
    - device_id: Device identifier
    - token: Device authentication token
    - timestamp: ISO 8601 timestamp
    - trigger_type: door, light, timer, or manual
    - battery_v: Battery voltage (float)
    - rssi: WiFi signal strength (dBm)
    - image: JPEG image file
    """
    
    try:
        # Authenticate device
        device = TokenManager.verify_device_token(db, device_id, token)
        if not device:
            raise AuthenticationError(f"Invalid device credentials for {device_id}")

        # Parse and validate timestamp
        try:
            captured_at = datetime.fromisoformat(timestamp)
        except ValueError:
            raise ValidationError("Invalid timestamp format. Use ISO 8601.", field="timestamp")

        # Validate trigger type
        valid_triggers = {"door", "light", "timer", "manual"}
        if trigger_type not in valid_triggers:
            raise ValidationError(
                f"Invalid trigger_type. Must be one of: {', '.join(valid_triggers)}",
                field="trigger_type"
            )

        # Validate battery voltage
        if not (0 < battery_v < 10):
            raise ValidationError("Battery voltage out of range (0-10V)", field="battery_v")

        # Validate RSSI
        if not (-120 <= rssi <= 0):
            raise ValidationError("RSSI out of range (-120 to 0 dBm)", field="rssi")

        # Save image
        try:
            image_filename = f"{uuid.uuid4()}.jpg"
            image_path = os.path.join(IMAGES_DIR, image_filename)
            
            content = await image.read()
            if len(content) == 0:
                raise ValidationError("Image file is empty", field="image")
            
            with open(image_path, "wb") as f:
                f.write(content)
        except IOError as e:
            raise StorageError(f"Failed to save image: {str(e)}")

        # Create capture record
        capture = Capture(
            device_id=device_id,
            trigger_type=trigger_type,
            captured_at=captured_at,
            image_path=image_path,
            battery_v=battery_v,
            rssi=rssi,
            status="stored",
        )
        db.add(capture)
        db.flush()

        # Update device last seen
        device.last_seen_at = datetime.utcnow()
        device.last_battery_v = battery_v
        device.last_rssi = rssi

        db.commit()

        return CaptureResponse(
            capture_id=capture.id,
            status="stored",
            message="Image received and queued for analysis",
        )

    except Exception as e:
        db.rollback()
        # Re-raise our custom exceptions
        if isinstance(e, (DeviceNotFoundError, AuthenticationError, ValidationError, StorageError)):
            raise
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in ingest: {str(e)}", exc_info=True)
        raise
