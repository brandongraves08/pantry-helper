"""Device management endpoints for pantry cameras."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Device, Capture, InventoryEvent
from app.models.schemas import (
    DeviceResponse,
    DeviceCreate,
    DeviceUpdate,
    DeviceHealthResponse,
    DeviceListResponse,
)
from app.auth import TokenManager
from app.exceptions import DeviceNotFoundError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/devices", response_model=DeviceListResponse)
async def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    List all registered devices with pagination.
    
    Query Parameters:
    - skip: Number of devices to skip (default: 0)
    - limit: Maximum devices to return (default: 100, max: 1000)
    """
    logger.info(f"Listing devices (skip={skip}, limit={limit})")
    
    # Get total count
    total = db.query(Device).count()
    
    # Get paginated results
    devices = db.query(Device).offset(skip).limit(limit).all()
    
    device_responses = []
    for device in devices:
        # Count captures and failures
        total_captures = db.query(Capture).filter(
            Capture.device_id == device.id
        ).count()
        
        failed_uploads = db.query(Capture).filter(
            Capture.device_id == device.id,
            Capture.status == "failed"
        ).count()
        
        device_responses.append(
            DeviceResponse(
                id=device.id,
                name=device.name,
                created_at=device.created_at,
                last_seen_at=device.last_seen_at,
                battery_v=device.last_battery_v,
                battery_pct=_calculate_battery_percentage(device.last_battery_v),
                rssi=device.last_rssi,
                total_captures=total_captures,
                failed_uploads=failed_uploads,
                status=_get_device_status(device),
            )
        )
    
    return DeviceListResponse(
        items=device_responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific device.
    
    Path Parameters:
    - device_id: The unique device identifier
    
    Returns:
    - Device information with current status, battery level, and capture statistics
    """
    logger.info(f"Getting device: {device_id}")
    
    device = db.query(Device).filter_by(id=device_id).first()
    if not device:
        logger.warning(f"Device not found: {device_id}")
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    # Count captures and failures
    total_captures = db.query(Capture).filter(
        Capture.device_id == device.id
    ).count()
    
    failed_uploads = db.query(Capture).filter(
        Capture.device_id == device.id,
        Capture.status == "failed"
    ).count()
    
    return DeviceResponse(
        id=device.id,
        name=device.name,
        created_at=device.created_at,
        last_seen_at=device.last_seen_at,
        battery_v=device.last_battery_v,
        battery_pct=_calculate_battery_percentage(device.last_battery_v),
        rssi=device.last_rssi,
        total_captures=total_captures,
        failed_uploads=failed_uploads,
        status=_get_device_status(device),
    )


@router.get("/devices/{device_id}/health", response_model=DeviceHealthResponse)
async def get_device_health(
    device_id: str,
    db: Session = Depends(get_db),
):
    """
    Get detailed health metrics for a device.
    
    Returns:
    - Battery percentage and voltage
    - WiFi signal strength (RSSI)
    - Last seen timestamp
    - Upload success rate
    - Recent capture statistics
    """
    logger.info(f"Getting health for device: {device_id}")
    
    device = db.query(Device).filter_by(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    # Get last 7 days of captures
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_captures = db.query(Capture).filter(
        Capture.device_id == device.id,
        Capture.created_at >= week_ago,
    ).all()
    
    # Calculate statistics
    total_recent = len(recent_captures)
    successful = len([c for c in recent_captures if c.status == "complete"])
    failed = len([c for c in recent_captures if c.status == "failed"])
    analyzing = len([c for c in recent_captures if c.status == "analyzing"])
    
    success_rate = (successful / total_recent * 100) if total_recent > 0 else 0
    
    # Get last 24 hours
    day_ago = datetime.utcnow() - timedelta(days=1)
    captures_24h = len([c for c in recent_captures if c.created_at >= day_ago])
    
    is_healthy = (
        device.last_seen_at and
        (datetime.utcnow() - device.last_seen_at) < timedelta(hours=1) and
        success_rate > 90
    )
    
    return DeviceHealthResponse(
        device_id=device.id,
        is_healthy=is_healthy,
        battery_v=device.last_battery_v,
        battery_pct=_calculate_battery_percentage(device.last_battery_v),
        rssi=device.last_rssi,
        last_seen_at=device.last_seen_at,
        last_seen_ago_seconds=int(
            (datetime.utcnow() - device.last_seen_at).total_seconds()
        ) if device.last_seen_at else None,
        total_captures=db.query(Capture).filter(
            Capture.device_id == device.id
        ).count(),
        captures_7d=total_recent,
        captures_24h=captures_24h,
        successful_7d=successful,
        failed_7d=failed,
        analyzing_7d=analyzing,
        success_rate_7d=success_rate,
    )


@router.post("/devices", response_model=DeviceResponse)
async def create_device(
    request: DeviceCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new device.
    
    Request Body:
    - name: Human-readable device name
    - device_id: Optional custom device ID (generated if not provided)
    
    Returns:
    - DeviceResponse with generated device_id and authentication token
    
    Note: The device token must be saved by the caller and provided in future requests.
    """
    logger.info(f"Creating new device: {request.name}")
    
    # Use provided device_id or generate one
    device_id = request.device_id or f"device-{TokenManager.generate_token()[:16]}"
    
    # Check if device already exists
    existing = db.query(Device).filter_by(id=device_id).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Device {device_id} already exists",
        )
    
    # Generate device token and hash it
    device_token = TokenManager.generate_token()
    token_hash = TokenManager.hash_token(device_token)
    
    # Create device
    device = Device(
        id=device_id,
        name=request.name,
        token_hash=token_hash,
    )
    
    db.add(device)
    db.commit()
    
    logger.info(f"Created device: {device_id}")
    
    return DeviceResponse(
        id=device.id,
        name=device.name,
        created_at=device.created_at,
        last_seen_at=device.last_seen_at,
        battery_v=device.last_battery_v,
        battery_pct=_calculate_battery_percentage(device.last_battery_v),
        rssi=device.last_rssi,
        total_captures=0,
        failed_uploads=0,
        status="inactive",
        device_token=device_token,  # Return token once during creation
    )


@router.patch("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    request: DeviceUpdate,
    db: Session = Depends(get_db),
):
    """
    Update device settings.
    
    Path Parameters:
    - device_id: The unique device identifier
    
    Request Body (all optional):
    - name: Update device name
    - enabled: Enable/disable device
    
    Returns:
    - Updated DeviceResponse
    """
    logger.info(f"Updating device: {device_id}")
    
    device = db.query(Device).filter_by(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    # Update fields if provided
    if request.name is not None:
        device.name = request.name
        logger.info(f"Updated device name to: {request.name}")
    
    db.commit()
    
    # Count captures
    total_captures = db.query(Capture).filter(
        Capture.device_id == device.id
    ).count()
    
    failed_uploads = db.query(Capture).filter(
        Capture.device_id == device.id,
        Capture.status == "failed"
    ).count()
    
    return DeviceResponse(
        id=device.id,
        name=device.name,
        created_at=device.created_at,
        last_seen_at=device.last_seen_at,
        battery_v=device.last_battery_v,
        battery_pct=_calculate_battery_percentage(device.last_battery_v),
        rssi=device.last_rssi,
        total_captures=total_captures,
        failed_uploads=failed_uploads,
        status=_get_device_status(device),
    )


@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: str,
    db: Session = Depends(get_db),
):
    """
    Deregister a device and optionally delete its data.
    
    Path Parameters:
    - device_id: The unique device identifier
    
    Returns:
    - Success message
    
    Note: This removes the device from the registry. Associated captures and data
    can be configured to remain in the database for historical analysis.
    """
    logger.info(f"Deleting device: {device_id}")
    
    device = db.query(Device).filter_by(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    device_name = device.name
    
    # Delete device
    db.delete(device)
    db.commit()
    
    logger.info(f"Deleted device: {device_id}")
    
    return {
        "success": True,
        "message": f"Device '{device_name}' ({device_id}) has been deregistered",
    }


@router.get("/devices/{device_id}/captures")
async def get_device_captures(
    device_id: str,
    days: int = Query(7, ge=1, le=90),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get capture history for a device.
    
    Path Parameters:
    - device_id: The unique device identifier
    
    Query Parameters:
    - days: Number of days of history (1-90, default: 7)
    - status: Filter by capture status (stored, analyzing, complete, failed)
    
    Returns:
    - List of captures with timestamps and status
    """
    logger.info(f"Getting captures for device {device_id} (last {days} days)")
    
    device = db.query(Device).filter_by(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    # Build query
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = db.query(Capture).filter(
        Capture.device_id == device_id,
        Capture.created_at >= cutoff,
    )
    
    # Filter by status if provided
    if status:
        query = query.filter(Capture.status == status)
    
    captures = query.order_by(Capture.created_at.desc()).all()
    
    return {
        "device_id": device_id,
        "days": days,
        "status_filter": status,
        "total": len(captures),
        "captures": [
            {
                "id": c.id,
                "captured_at": c.captured_at,
                "status": c.status,
                "trigger_type": c.trigger_type,
                "battery_v": c.battery_v,
                "rssi": c.rssi,
                "error": c.error_message,
            }
            for c in captures
        ],
    }


# Helper functions

def _calculate_battery_percentage(voltage: Optional[float]) -> Optional[float]:
    """Calculate battery percentage from voltage (LiPo 2S: 7.4V)."""
    if voltage is None:
        return None
    
    # LiPo 2S: 6.0V (0%) to 8.4V (100%)
    MIN_V = 6.0
    MAX_V = 8.4
    
    if voltage < MIN_V:
        return 0.0
    if voltage > MAX_V:
        return 100.0
    
    percentage = ((voltage - MIN_V) / (MAX_V - MIN_V)) * 100.0
    return round(percentage, 1)


def _get_device_status(device: Device) -> str:
    """Determine device status based on last seen time."""
    if not device.last_seen_at:
        return "inactive"
    
    now = datetime.utcnow()
    time_diff = now - device.last_seen_at
    
    if time_diff < timedelta(hours=1):
        return "active"
    elif time_diff < timedelta(days=1):
        return "idle"
    elif time_diff < timedelta(days=7):
        return "inactive"
    else:
        return "offline"
