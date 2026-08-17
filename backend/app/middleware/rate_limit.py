"""Rate limiting middleware (Redis-backed with in-memory fallback).

Applies a per-client-IP limit to all WRITE requests (POST/PUT/PATCH/DELETE),
including the previously-unprotected override/review/recipe/device routes, plus
a tighter limit on ingest/admin processing endpoints.

Uses Redis (INCR + EXPIRE, fixed-window) when available; falls back to an
in-process dict store so the stack still functions if Redis is down.
"""
import logging
import time
import hashlib

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger("pantry-api.rate_limit")

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Tighter per-endpoint limits for heavy/expensive ops.
# Keyed by path prefix → (limit, period_seconds).
TIGHT_LIMITS = {
    "/v1/ingest": (10, 60),
    "/v1/admin/process-capture": (20, 60),
    "/v1/admin/process-pending": (5, 60),
    "/v1/admin": (30, 60),
    "/v1/captures/manual": (10, 60),
}

# Default write limit
DEFAULT_WRITE_LIMIT = 60
DEFAULT_WRITE_PERIOD = 60  # seconds


class RateLimitStore:
    """Redis-backed store with an in-memory fallback."""

    def __init__(self):
        self._redis = None
        self._mem: dict = {}
        self._redis_attempted = False

    def _get_redis(self):
        if self._redis_attempted:
            return self._redis
        self._redis_attempted = True
        try:
            import redis
            self._redis = redis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=2,
                socket_timeout=2,
                decode_responses=True,
            )
            self._redis.ping()
        except Exception as e:
            logger.warning("Redis rate-limit store unavailable, using in-memory fallback", extra={"error": str(e)})
            self._redis = None
        return self._redis

    def incr(self, key: str, period: int, limit: int):
        """Increment counter for key; return (count, approved)."""
        r = self._get_redis()
        if r:
            try:
                full_key = f"ratelimit:{key}"
                count = r.incr(full_key)
                if count == 1:
                    r.expire(full_key, period)
                return count, count <= limit
            except Exception as e:
                logger.warning("Redis rate-limit incr failed, falling back", extra={"error": str(e)})
        # in-memory fallback (fixed window)
        now = time.time()
        rec = self._mem.get(key)
        if rec is None or now >= rec[1]:
            self._mem[key] = [now, now + period, 1]
            return 1, 1 <= limit
        self._mem[key][2] += 1
        return self._mem[key][2], self._mem[key][2] <= limit


rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        method = request.method
        path = request.url.path

        limited = False
        limit = DEFAULT_WRITE_LIMIT
        period = DEFAULT_WRITE_PERIOD

        if method in _WRITE_METHODS:
            limited = True
            # check tight limits first (most specific path prefix wins)
            for prefix, (l, p) in TIGHT_LIMITS.items():
                if path.startswith(prefix):
                    limit, period = l, p
                    break

        if not limited:
            return await call_next(request)

        identifier = self._get_identifier(request)
        key = f"{path}|{identifier}"

        count, allowed = rate_limit_store.incr(key, period, limit)
        remaining = max(0, limit - count)
        retry_after = period

        if not allowed:
            logger.warning("Rate limit exceeded", extra={"identifier": identifier, "path": path, "count": count, "limit": limit})
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded", "remaining": remaining, "retry_after": period},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(remaining),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Period"] = str(period)
        return response

    def _get_identifier(self, request) -> str:
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0].strip()
        if request.client:
            return request.client.host
        return request.url.path


class AdaptiveRateLimit:
    """Adaptive rate limiting based on system load (kept for compatibility)."""

    def __init__(self, base_limit: int = settings.RATE_LIMIT_REQUESTS):
        self.base_limit = base_limit
        self.current_load = 0.0

    def update_load(self, queue_size: int, max_queue_size: int = 100):
        self.current_load = min(queue_size / max_queue_size, 1.0)

    def get_adaptive_limit(self) -> int:
        reduction_factor = 1.0 - (self.current_load * 0.5)
        return int(self.base_limit * reduction_factor)


adaptive_rate_limit = AdaptiveRateLimit()
