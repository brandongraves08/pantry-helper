"""Rate limiting middleware and utilities."""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import hashlib
from typing import Dict, Tuple
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimitStore:
    """In-memory rate limit store (can be extended to Redis)."""

    def __init__(self):
        self.requests: Dict[str, list] = {}

    def is_allowed(
        self,
        identifier: str,
        limit: int = settings.RATE_LIMIT_REQUESTS,
        period: int = settings.RATE_LIMIT_PERIOD,
    ) -> bool:
        """
        Check if request is allowed under rate limit.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            limit: Number of requests allowed
            period: Time period in seconds
            
        Returns:
            bool: True if request is allowed
        """
        now = time.time()
        
        # Initialize request list if needed
        if identifier not in self.requests:
            self.requests[identifier] = []

        # Remove old requests outside the period
        self.requests[identifier] = [
            req_time
            for req_time in self.requests[identifier]
            if now - req_time < period
        ]

        # Check if limit exceeded
        if len(self.requests[identifier]) >= limit:
            return False

        # Record new request
        self.requests[identifier].append(now)
        return True

    def get_remaining(
        self,
        identifier: str,
        limit: int = settings.RATE_LIMIT_REQUESTS,
        period: int = settings.RATE_LIMIT_PERIOD,
    ) -> int:
        """Get remaining requests for identifier."""
        now = time.time()
        
        if identifier not in self.requests:
            return limit

        # Remove old requests
        self.requests[identifier] = [
            req_time
            for req_time in self.requests[identifier]
            if now - req_time < period
        ]

        return max(0, limit - len(self.requests[identifier]))


# Global rate limit store
rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for API rate limiting."""

    # Endpoints that are rate limited
    RATE_LIMITED_PATHS = {
        "/v1/ingest": (10, 60),  # 10 requests per minute
        "/v1/admin/process-capture": (20, 60),  # 20 per minute
        "/v1/admin/process-pending": (5, 60),  # 5 per minute
    }

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to request."""
        
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Check if path is rate limited
        path = request.url.path
        rate_limit_config = None
        
        for limited_path, config in self.RATE_LIMITED_PATHS.items():
            if path.startswith(limited_path):
                rate_limit_config = config
                break

        if not rate_limit_config:
            return await call_next(request)

        # Get identifier (IP address for now)
        identifier = self._get_identifier(request)
        limit, period = rate_limit_config

        # Check rate limit
        if not rate_limit_store.is_allowed(identifier, limit, period):
            remaining = rate_limit_store.get_remaining(identifier, limit, period)
            logger.warning(f"Rate limit exceeded for {identifier} on {path}")
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "remaining": remaining,
                    "retry_after": period,
                },
                headers={
                    "Retry-After": str(period),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(remaining),
                },
            )

        # Add rate limit headers to response
        response = await call_next(request)
        remaining = rate_limit_store.get_remaining(identifier, limit, period)
        
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Period"] = str(period)

        return response

    def _get_identifier(self, request: Request) -> str:
        """Extract unique identifier from request."""
        # Try X-Forwarded-For header first (for proxied requests)
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Fall back to client IP
        if request.client:
            return request.client.host
        
        # Use request path as fallback
        return request.url.path


class AdaptiveRateLimit:
    """Adaptive rate limiting based on system load."""

    def __init__(self, base_limit: int = settings.RATE_LIMIT_REQUESTS):
        self.base_limit = base_limit
        self.current_load = 0.0

    def update_load(self, queue_size: int, max_queue_size: int = 100):
        """Update current system load."""
        self.current_load = min(queue_size / max_queue_size, 1.0)

    def get_adaptive_limit(self) -> int:
        """Get rate limit adjusted for current load."""
        # Reduce limit proportionally to load
        reduction_factor = 1.0 - (self.current_load * 0.5)  # Max 50% reduction
        return int(self.base_limit * reduction_factor)


adaptive_rate_limit = AdaptiveRateLimit()
