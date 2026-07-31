"""Authentication utilities for ESP32 device tokens."""
import hashlib
import hmac
import secrets
import logging
from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Device

logger = logging.getLogger("pantry-api.auth")

security = HTTPBearer(auto_error=False)


class TokenManager:
    """Manage device authentication tokens."""

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token for device registration."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for storage using SHA-256."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def verify_token(token: str, token_hash: str) -> bool:
        """Constant-time comparison of token against stored hash."""
        return hmac.compare_digest(
            TokenManager.hash_token(token), token_hash
        )


def get_current_device(
    authorization: HTTPAuthorizationCredentials = Depends(security),
    device_id: str = Header(None, alias="X-Device-ID"),
    db: Session = Depends(get_db),
) -> Device:
    """Authenticate a device using Bearer token + optional X-Device-ID header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.credentials

    if device_id:
        device = db.query(Device).filter(Device.id == device_id).first()
    else:
        # Try to find device by trying all token hashes
        devices = db.query(Device).all()
        for device in devices:
            if TokenManager.verify_token(token, device.token_hash):
                return device
        raise HTTPException(status_code=401, detail="Invalid token")

    if not device:
        raise HTTPException(status_code=401, detail="Device not found")

    if not TokenManager.verify_token(token, device.token_hash):
        raise HTTPException(status_code=401, detail="Invalid token")

    return device


def authenticate_device(
    token: str,
    device_id: str = None,
    db: Session = None,
) -> Device:
    """Direct authentication for non-FastAPI contexts."""
    if not db:
        from app.db.database import SessionLocal
        db = SessionLocal()

    try:
        if device_id:
            device = db.query(Device).filter(Device.id == device_id).first()
        else:
            devices = db.query(Device).all()
            for device in devices:
                if TokenManager.verify_token(token, device.token_hash):
                    return device
            return None

        if device and TokenManager.verify_token(token, device.token_hash):
            return device
        return None
    finally:
        db.close()
