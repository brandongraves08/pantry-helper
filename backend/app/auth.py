"""Authentication utilities for device token verification"""

import hashlib
import secrets
from typing import Optional
from sqlalchemy.orm import Session
from app.db.models import Device

class TokenManager:
    """Manage device token generation and verification"""
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a device token using SHA256"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def generate_token() -> str:
        """Generate a random secure device token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_device_token(
        db: Session,
        device_id: str,
        token: str,
    ) -> Optional[Device]:
        """
        Verify a device token and return the device if valid.
        
        Args:
            db: Database session
            device_id: Device ID
            token: Device token (unhashed)
            
        Returns:
            Device object if token is valid, None otherwise
        """
        device = db.query(Device).filter_by(id=device_id).first()
        
        if not device:
            return None
        
        # Constant-time comparison to prevent timing attacks
        expected_hash = TokenManager.hash_token(token)
        if secrets.compare_digest(expected_hash, device.token_hash):
            return device
        
        return None
