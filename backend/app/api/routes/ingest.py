"""Ingest routes with structured logging."""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Device, Capture
from app.services.storage import get_storage_manager
from app.auth import TokenManager, get_current_device, security

logger = logging.getLogger("pantry-api.ingest")

router = APIRouter()


@router.post("/ingest")
async def ingest_image(
    request: Request,
    device_id: str = Form(...),
    token: str = Form(None),
    timestamp: str = Form(None),
    trigger_type: str = Form("manual"),
    captured_at: str = Form(None),
    battery_v: float = Form(None),
    rssi: int = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    authorization: HTTPAuthorizationCredentials = Depends(security),
):
    logger.info("Ingest request", extra={
        "device_id": device_id,
        "trigger_type": trigger_type,
        "upload_filename": image.filename,
        "image_size": 0,
    })

    # Verify device
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        logger.warning("Unknown device", extra={"device_id": device_id})
        raise HTTPException(status_code=401, detail="Device not found")

    auth_token = authorization.credentials if authorization else token
    if not auth_token or not TokenManager.verify_token(auth_token, db_device.token_hash):
        raise HTTPException(status_code=401, detail="Invalid token")

    capture_time = datetime.utcnow()
    timestamp_value = captured_at or timestamp
    if timestamp_value:
        try:
            capture_time = datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format")

    # Store image
    content = await image.read()
    if not content:
        logger.error("Empty image from ESP32", extra={"device_id": device_id})
        raise HTTPException(status_code=400, detail="Empty image payload")

    capture = Capture(
        device_id=db_device.id,
        trigger_type=trigger_type,
        captured_at=capture_time,
        image_path="pending",
        battery_v=battery_v,
        rssi=rssi,
        status="stored",
    )
    db.add(capture)
    db.flush()

    storage_mgr = get_storage_manager()
    capture.image_path = storage_mgr.save_image(
        device_id=db_device.id,
        capture_id=capture.id,
        image_data=content,
    )

    db_device.last_seen_at = datetime.utcnow()
    db_device.last_battery_v = battery_v
    db_device.last_rssi = rssi
    db.commit()

    logger.info("ESP32 capture stored", extra={
        "capture_id": capture.id,
        "device_id": device_id,
        "image_size": len(content),
        "battery_v": battery_v,
        "rssi": rssi,
    })

    try:
        from app.workers.celery_app import process_image_capture
        process_image_capture.delay(capture.id)
        logger.info("Capture queued from ESP32", extra={"capture_id": capture.id})
    except Exception as e:
        logger.error("Failed to queue ESP32 capture", extra={"capture_id": capture.id, "error": str(e)})
        capture.error_message = f"Analysis queue failed: {e}"
        db.commit()

    return {
        "status": "stored",
        "capture_id": capture.id,
        "message": "Image received and queued for analysis",
    }


@router.post("/ingest/barcode")
async def ingest_barcode(
    device_id: str = Form(...),
    barcode: str = Form(...),
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
):
    """Accept a barcode number from ESP32 (or other device) for product lookup.

    This endpoint allows an ESP32 with a connected barcode scanner module
    to submit barcode values directly. The system looks up the barcode and
    optionally auto-adds it to inventory.
    """
    logger.info("Barcode ingest from device", extra={
        "device_id": device_id,
        "barcode": barcode,
    })

    # Verify device
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=401, detail="Unknown device")

    from app.services.barcode import lookup_barcode
    from app.db.models import BarcodeLookup

    # Check cache first
    existing = db.query(BarcodeLookup).filter(
        BarcodeLookup.barcode == barcode.strip()
    ).first()

    if existing:
        existing.lookup_count = (existing.lookup_count or 1) + 1
        existing.last_lookup_at = datetime.utcnow()
        db.commit()

        logger.info("Barcode found in cache", extra={
            "barcode": barcode,
            "product": existing.product_name,
        })

        return {
            "status": "ok",
            "barcode": barcode,
            "product_name": existing.product_name,
            "brand": existing.brand,
            "in_inventory": existing.inventory_item_id is not None,
        }

    # External lookup
    try:
        product = lookup_barcode(barcode)
        if product.found:
            bl = BarcodeLookup(
                barcode=barcode.strip(),
                product_name=product.product_name,
                brand=product.brand,
                category=product.category,
                package_type=product.package_type,
                image_url=product.image_url,
                source=product.source,
            )
            db.add(bl)
            db.commit()

            logger.info("Barcode resolved from external lookup", extra={
                "barcode": barcode,
                "product": product.product_name,
            })

            return {
                "status": "ok",
                "barcode": barcode,
                "product_name": product.product_name,
                "brand": product.brand,
                "in_inventory": False,
            }

        logger.info("Barcode not found in lookup", extra={"barcode": barcode})
        return {
            "status": "not_found",
            "barcode": barcode,
            "product_name": None,
        }

    except Exception as e:
        logger.error("Barcode lookup failed", extra={
            "barcode": barcode,
            "error": str(e),
        })
        return {
            "status": "error",
            "barcode": barcode,
            "error": str(e),
        }
