"""Logging and exception handling utilities"""

import logging
import os
from typing import Any, Dict

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

class PantryException(Exception):
    """Base exception for Pantry Inventory service"""
    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class DeviceNotFoundError(PantryException):
    """Device not found in database"""
    def __init__(self, device_id: str):
        super().__init__(
            f"Device {device_id} not found",
            status_code=404,
            details={"device_id": device_id}
        )

class AuthenticationError(PantryException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class ValidationError(PantryException):
    """Validation error"""
    def __init__(self, message: str, field: str = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(message, status_code=400, details=details)

class StorageError(PantryException):
    """File storage error"""
    def __init__(self, message: str):
        super().__init__(f"Storage error: {message}", status_code=500)

class VisionAnalysisError(PantryException):
    """Vision API analysis error"""
    def __init__(self, message: str):
        super().__init__(f"Vision analysis failed: {message}", status_code=500)
