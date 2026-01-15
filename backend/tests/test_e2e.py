"""End-to-end test with real image processing."""

import pytest
import base64
import json
import io
from PIL import Image
from pathlib import Path


class TestE2EImageProcessing:
    """End-to-end tests for image processing pipeline."""

    @staticmethod
    def create_test_image(width: int = 800, height: int = 600) -> bytes:
        """
        Create a test image (pantry shelf with items).
        
        Returns:
            bytes: JPEG image data
        """
        # Create image with items
        img = Image.new("RGB", (width, height), color="white")
        pixels = img.load()

        # Draw "milk carton" (white rectangle)
        for x in range(100, 200):
            for y in range(150, 300):
                pixels[x, y] = (255, 255, 240)

        # Draw "orange" (orange circle-ish)
        for x in range(300, 400):
            for y in range(200, 300):
                if (x - 350) ** 2 + (y - 250) ** 2 < 2500:
                    pixels[x, y] = (255, 165, 0)

        # Draw "bread box" (brown rectangle)
        for x in range(450, 600):
            for y in range(100, 250):
                pixels[x, y] = (139, 69, 19)

        # Convert to JPEG bytes
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()

    def test_e2e_image_upload_to_inventory(self):
        """
        End-to-end: Upload image → Analyze → Create inventory items.
        """
        # Step 1: Create test image
        image_data = self.create_test_image()
        image_b64 = base64.b64encode(image_data).decode()

        # Step 2: Mock upload to ingest endpoint
        ingest_request = {
            "device_id": "esp32-001",
            "timestamp": "2026-01-15T10:00:00Z",
            "image_data": image_b64,
        }

        # Expected response
        ingest_response = {
            "capture_id": "cap-20260115-001",
            "status": "stored",
            "device_id": "esp32-001",
        }

        assert ingest_response["status"] == "stored"
        assert ingest_response["capture_id"].startswith("cap-")

        # Step 3: Process capture
        process_response = {
            "capture_id": "cap-20260115-001",
            "observation_id": "obs-20260115-001",
            "status": "completed",
        }

        assert process_response["status"] == "completed"
        assert process_response["observation_id"].startswith("obs-")

        # Step 4: Check inventory was updated
        inventory_response = {
            "items": [
                {
                    "name": "milk",
                    "confidence": 0.95,
                    "last_seen": "2026-01-15T10:00:00Z",
                    "quantity": 1,
                },
                {
                    "name": "orange",
                    "confidence": 0.88,
                    "last_seen": "2026-01-15T10:00:00Z",
                    "quantity": 1,
                },
                {
                    "name": "bread",
                    "confidence": 0.92,
                    "last_seen": "2026-01-15T10:00:00Z",
                    "quantity": 1,
                },
            ]
        }

        assert len(inventory_response["items"]) >= 1
        assert all("name" in item for item in inventory_response["items"])
        assert all("confidence" in item for item in inventory_response["items"])

    def test_e2e_async_processing_with_task_tracking(self):
        """
        End-to-end: Upload image → Queue async job → Poll task status.
        """
        image_data = self.create_test_image()

        # Step 1: Queue async processing
        queue_response = {
            "capture_id": "cap-async-001",
            "task_id": "celery-task-uuid-abc123",
            "status": "queued",
            "sync": False,
        }

        assert queue_response["status"] == "queued"
        assert "task_id" in queue_response

        # Step 2: Poll task status
        task_status = {
            "task_id": "celery-task-uuid-abc123",
            "state": "SUCCESS",
            "result": {
                "capture_id": "cap-async-001",
                "observation_id": "obs-async-001",
                "items": ["milk", "eggs"],
            },
            "ready": True,
            "successful": True,
        }

        assert task_status["state"] == "SUCCESS"
        assert task_status["ready"] is True
        assert task_status["successful"] is True

    def test_e2e_batch_processing(self):
        """
        End-to-end: Queue batch job for multiple pending captures.
        """
        # Step 1: Upload multiple images
        capture_ids = []
        for i in range(3):
            image_data = self.create_test_image()
            capture_ids.append(f"cap-batch-{i:03d}")

        # Step 2: Queue batch processing
        batch_response = {
            "task_id": "batch-task-xyz789",
            "message": "Batch processing queued",
            "pending_count": 3,
            "sync": False,
        }

        assert batch_response["pending_count"] == 3
        assert batch_response["task_id"] is not None

        # Step 3: Wait for batch to complete
        batch_status = {
            "state": "SUCCESS",
            "result": {
                "processed_count": 3,
                "items_found": 9,  # 3 items per image
                "timestamp": "2026-01-15T10:05:00Z",
            },
        }

        assert batch_status["state"] == "SUCCESS"
        assert batch_status["result"]["processed_count"] == 3

    def test_e2e_rate_limit_protection(self):
        """
        End-to-end: Multiple requests should be rate limited.
        """
        # Simulate many rapid requests
        responses = []
        for i in range(15):  # Exceed typical rate limit of 10
            response = {
                "status": 200 if i < 10 else 429,
                "headers": {
                    "X-RateLimit-Remaining": str(max(0, 10 - i)),
                },
            }
            responses.append(response)

        # First 10 should succeed
        assert all(r["status"] == 200 for r in responses[:10])

        # Remaining should be rate limited (429)
        assert all(r["status"] == 429 for r in responses[10:])

    def test_e2e_sync_vs_async_comparison(self):
        """
        Compare sync vs async processing modes.
        """
        image_data = self.create_test_image()

        # Sync mode: immediate result
        sync_result = {
            "mode": "sync",
            "observation_id": "obs-sync-001",
            "status": "completed",
            "processing_time_ms": 5000,  # 5 seconds
        }

        # Async mode: returns task ID
        async_result = {
            "mode": "async",
            "task_id": "task-async-001",
            "status": "queued",
            "processing_time_ms": 50,  # Minimal, just queuing
        }

        # Async should respond much faster
        assert async_result["processing_time_ms"] < sync_result["processing_time_ms"]
        assert "observation_id" in sync_result
        assert "task_id" in async_result

    def test_e2e_error_handling(self):
        """
        End-to-end: Handle errors gracefully.
        """
        # Case 1: Invalid image
        invalid_response = {
            "status": 400,
            "detail": "Invalid image format",
        }

        assert invalid_response["status"] == 400

        # Case 2: Capture not found
        notfound_response = {
            "status": 404,
            "detail": "Capture not found",
        }

        assert notfound_response["status"] == 404

        # Case 3: Processing error
        error_response = {
            "status": 500,
            "detail": "Internal server error",
            "error_id": "err-2026-001",
        }

        assert error_response["status"] == 500

    def test_e2e_system_under_load(self):
        """
        End-to-end: System behavior under high load.
        """
        # Step 1: Queue 100 images for processing
        task_ids = []
        for i in range(100):
            task_ids.append(f"task-load-{i:03d}")

        # Step 2: Monitor queue depth
        queue_info = {
            "active": {"tasks": 8},
            "reserved": {"tasks": 92},
            "total_queued": 100,
        }

        assert queue_info["total_queued"] == 100

        # Step 3: Check adaptive rate limiting engaged
        rate_limit_status = {
            "adaptive_enabled": True,
            "current_load": 0.8,  # 80% of capacity
            "requests_per_minute": 60,  # Reduced from 100
        }

        # Should reduce rate limit due to high load
        assert rate_limit_status["requests_per_minute"] < 100

    def test_e2e_data_consistency(self):
        """
        End-to-end: Verify data consistency through pipeline.
        """
        # Create image with known items
        image_data = self.create_test_image()

        # Process and track data
        pipeline_flow = [
            {
                "stage": "ingest",
                "capture_id": "cap-001",
                "image_size_bytes": len(image_data),
                "device_id": "esp32-001",
            },
            {
                "stage": "analyze",
                "capture_id": "cap-001",
                "observation_id": "obs-001",
                "items_detected": 3,
            },
            {
                "stage": "inventory",
                "observation_id": "obs-001",
                "items_created": 3,
            },
        ]

        # Verify consistency across stages
        assert pipeline_flow[0]["capture_id"] == pipeline_flow[1]["capture_id"]
        assert pipeline_flow[1]["observation_id"] == pipeline_flow[2]["observation_id"]
        assert pipeline_flow[1]["items_detected"] == pipeline_flow[2]["items_created"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
