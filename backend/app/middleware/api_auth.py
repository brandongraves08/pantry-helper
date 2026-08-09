"""Shared API token enforcement middleware.

Requires a Bearer token equal to PANTRY_API_TOKEN on every WRITE request
(POST/PUT/PATCH/DELETE), except /v1/ingest* which uses its own device-token auth.

Behavior:
- If PANTRY_API_TOKEN is not set (dev mode), writes are allowed (backwards-compatible).
- If set, a write without a valid `Authorization: Bearer <token>` gets HTTP 401.
- GET/HEAD/OPTIONS are always allowed (read-only).
"""
import hashlib
import hmac
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger("pantry-api.api_auth")

# Optional token (may be None in dev)
_EXPECTED = settings.PANTRY_API_TOKEN

# Read-only-safe methods
_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths that do their own auth (ESP32 device token) — don't double-require
_EXEMPT_PREFIXES = ("/v1/ingest",)


def _extract_bearer(request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


class APIAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if _EXPECTED and request.method in _WRITE_METHODS:
            path = request.url.path
            if not path.startswith(_EXEMPT_PREFIXES):
                presented = _extract_bearer(request)
                if not presented or not hmac.compare_digest(presented, _EXPECTED):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Unauthorized: valid Bearer token required"},
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        return await call_next(request)
