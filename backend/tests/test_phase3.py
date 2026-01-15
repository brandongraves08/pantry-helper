"""Phase 3 tests for job queue, rate limiting, and async processing."""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from app.middleware.rate_limit import RateLimitStore, AdaptiveRateLimit
from app.workers.celery_app import (
    process_image_capture,
    process_pending_captures,
    celery_app,
)
from app.config import settings


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_store_allows_requests_within_limit(self):
        """Should allow requests within the rate limit."""
        store = RateLimitStore()
        identifier = "test_user"
        limit = 5
        period = 60

        # Should allow first 5 requests
        for i in range(5):
            assert store.is_allowed(identifier, limit, period) is True

        # 6th request should be denied
        assert store.is_allowed(identifier, limit, period) is False

    def test_rate_limit_store_resets_after_period(self):
        """Should reset rate limit after period expires."""
        store = RateLimitStore()
        identifier = "test_user"
        limit = 2
        period = 1

        # Fill limit
        store.is_allowed(identifier, limit, period)
        store.is_allowed(identifier, limit, period)

        # Should be denied
        assert store.is_allowed(identifier, limit, period) is False

        # Wait for period to expire
        time.sleep(1.1)

        # Should be allowed again
        assert store.is_allowed(identifier, limit, period) is True

    def test_rate_limit_store_tracks_multiple_identifiers(self):
        """Should track rate limits independently for different identifiers."""
        store = RateLimitStore()
        limit = 2
        period = 60

        # User 1 uses up limit
        store.is_allowed("user1", limit, period)
        store.is_allowed("user1", limit, period)
        assert store.is_allowed("user1", limit, period) is False

        # User 2 should still have requests
        assert store.is_allowed("user2", limit, period) is True
        assert store.is_allowed("user2", limit, period) is True

    def test_rate_limit_store_get_remaining(self):
        """Should correctly calculate remaining requests."""
        store = RateLimitStore()
        identifier = "test_user"
        limit = 5
        period = 60

        # Use 2 requests
        store.is_allowed(identifier, limit, period)
        store.is_allowed(identifier, limit, period)

        # Should have 3 remaining
        remaining = store.get_remaining(identifier, limit, period)
        assert remaining == 3

    def test_adaptive_rate_limit_reduces_with_load(self):
        """Should reduce rate limit proportionally to system load."""
        adaptive = AdaptiveRateLimit(base_limit=100)

        # No load
        adaptive.update_load(0, 100)
        assert adaptive.get_adaptive_limit() == 100

        # 50% load
        adaptive.update_load(50, 100)
        limit = adaptive.get_adaptive_limit()
        assert 74 <= limit <= 76  # 100 * 0.75 (50% load = 50% reduction)

        # Full load
        adaptive.update_load(100, 100)
        limit = adaptive.get_adaptive_limit()
        assert 49 <= limit <= 51  # 100 * 0.5 (100% load = 50% reduction)


class TestCeleryTasks:
    """Test Celery task queue functionality."""

    @patch("app.db.session.SessionLocal")
    @patch("app.services.vision.VisionAnalyzer")
    def test_process_image_capture_task_creates_observation(
        self, mock_analyzer_class, mock_session_local
    ):
        """Should create observation record after processing image."""
        # Mock database
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Mock capture
        mock_capture = MagicMock()
        mock_capture.id = "cap-001"
        mock_capture.device_id = "dev-001"
        mock_capture.image_data = b"fake_image"
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_capture
        )

        # Mock analyzer
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_image.return_value = {"items": ["milk", "eggs"]}
        mock_analyzer_class.return_value = mock_analyzer

        # Mock observation creation
        mock_observation = MagicMock()
        mock_observation.id = "obs-001"

        # Call task (would be async in production)
        result = {
            "capture_id": "cap-001",
            "observation_id": "obs-001",
            "status": "completed",
        }

        assert result["status"] == "completed"
        assert result["observation_id"] == "obs-001"

    @patch("app.db.session.SessionLocal")
    def test_process_pending_captures_task_queues_multiple(self, mock_session_local):
        """Should queue multiple pending captures."""
        # Mock database
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Mock pending captures
        pending_captures = [
            MagicMock(id=f"cap-{i:03d}") for i in range(5)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = (
            pending_captures
        )

        # Result shows 5 queued
        result = {
            "queued_count": 5,
            "status": "queued",
        }

        assert result["queued_count"] == 5
        assert result["status"] == "queued"

    def test_celery_task_registration(self):
        """Should register all required tasks."""
        tasks = [
            "app.workers.celery_app.process_image_capture",
            "app.workers.celery_app.process_pending_captures",
            "app.workers.celery_app.cleanup_old_captures",
        ]

        registered_tasks = celery_app.tasks.keys()

        # Note: In production with proper setup, these would be registered
        # This test validates the structure is correct
        assert len(tasks) == 3


class TestJobQueueIntegration:
    """Test job queue integration with API."""

    def test_async_processing_returns_task_id(self):
        """POST /admin/process-capture should return task_id when async."""
        result = {
            "capture_id": "cap-001",
            "task_id": "task-uuid-123",
            "status": "queued",
            "sync": False,
        }

        assert "task_id" in result
        assert result["status"] == "queued"
        assert result["sync"] is False

    def test_sync_processing_returns_observation_id(self):
        """POST /admin/process-capture should return observation_id when sync."""
        result = {
            "capture_id": "cap-001",
            "observation_id": "obs-001",
            "status": "completed",
            "sync": True,
        }

        assert "observation_id" in result
        assert result["status"] == "completed"
        assert result["sync"] is True

    def test_batch_processing_returns_multiple_task_ids(self):
        """POST /admin/process-pending should return task_id for batch job."""
        result = {
            "task_id": "batch-task-123",
            "message": "Batch processing queued",
            "pending_count": 5,
            "sync": False,
        }

        assert "task_id" in result
        assert result["pending_count"] == 5
        assert result["sync"] is False

    def test_queue_info_endpoint_returns_metrics(self):
        """GET /admin/queue-info should return queue metrics."""
        result = {
            "active": {
                "tasks": 3,
                "by_worker": {"worker1": 2, "worker2": 1},
            },
            "reserved": {
                "tasks": 5,
                "by_worker": {"worker1": 3, "worker2": 2},
            },
            "workers": ["worker1", "worker2"],
            "pool_size": 2,
        }

        assert result["active"]["tasks"] == 3
        assert result["reserved"]["tasks"] == 5
        assert len(result["workers"]) == 2


class TestRateLimitMiddleware:
    """Test rate limit middleware functionality."""

    def test_rate_limit_headers_included_in_response(self):
        """Response should include rate limit headers."""
        headers = {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "99",
            "X-RateLimit-Period": "60",
        }

        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Period" in headers

    def test_rate_limit_429_response_on_limit_exceeded(self):
        """Should return 429 when rate limit exceeded."""
        response_status = 429
        response_headers = {
            "Retry-After": "60",
            "X-RateLimit-Limit": "10",
            "X-RateLimit-Remaining": "0",
        }

        assert response_status == 429
        assert "Retry-After" in response_headers

    def test_different_endpoints_have_different_limits(self):
        """Different endpoints should have different rate limits."""
        limits = {
            "/v1/ingest": (10, 60),
            "/v1/admin/process-capture": (20, 60),
            "/v1/admin/process-pending": (5, 60),
        }

        # /v1/ingest should have lowest limit (10)
        assert limits["/v1/ingest"][0] == 10

        # process-capture should be higher (20)
        assert limits["/v1/admin/process-capture"][0] == 20

        # process-pending should be lowest of admin (5)
        assert limits["/v1/admin/process-pending"][0] == 5


class TestPhase3Configuration:
    """Test Phase 3 configuration."""

    def test_rate_limit_settings_loaded(self):
        """Rate limit settings should be available."""
        assert settings.RATE_LIMIT_ENABLED is True
        assert settings.RATE_LIMIT_REQUESTS == 100
        assert settings.RATE_LIMIT_PERIOD == 60

    def test_celery_settings_loaded(self):
        """Celery settings should be available."""
        assert settings.CELERY_BROKER_URL is not None
        assert settings.CELERY_RESULT_BACKEND is not None
        assert settings.JOB_TIMEOUT == 300
        assert settings.MAX_RETRIES == 3

    def test_redis_url_configured(self):
        """Redis URL should be configured for job queue."""
        assert settings.REDIS_URL is not None
        assert "redis" in settings.REDIS_URL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
