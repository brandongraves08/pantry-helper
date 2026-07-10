"""Request/response logging middleware for FastAPI.

Logs every HTTP request with method, path, status, duration, client IP,
and a unique request ID. Health-check requests are logged at DEBUG level
to avoid noise.
"""

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

import logging

# Get the structured JSON logger without reconfiguring root.
# The root handler is already set up by main.py setup_logging().
# We set level to DEBUG so health-check quiet-path logs still emit.
logger = logging.getLogger("pantry-api.request_log")
logger.setLevel(logging.DEBUG)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests and responses with timing."""

    # Path prefixes to suppress to DEBUG (reduce health-check noise)
    QUIET_PREFIXES: tuple = ("/health", "/flower", "/metrics")

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        path = request.url.path
        method = request.method
        query = str(request.url.query) if request.url.query else None
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        # Determine log level based on path
        quiet = path.startswith(self.QUIET_PREFIXES)
        log = logger.debug if quiet else logger.info

        start = time.monotonic()

        # Log incoming request
        log("Request started", extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "query": query,
            "client_ip": client_ip,
            "user_agent": user_agent[:200],
        })

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            logger.exception("Request failed", extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "error": str(exc),
            })
            raise

        duration_ms = (time.monotonic() - start) * 1000

        # Log response with appropriate severity
        extra = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "query": query,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
        }
        if status_code >= 500:
            logger.error("Request completed with server error", extra=extra)
        elif status_code >= 400:
            logger.warning("Request completed with client error", extra=extra)
        elif quiet:
            logger.debug("Health check completed", extra=extra)
        else:
            logger.info("Request completed", extra=extra)

        return response
