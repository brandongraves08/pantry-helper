"""Celery task queue configuration with structured logging."""
from app.log_config import setup_logging

logger = setup_logging("pantry-worker")

from celery import Celery, Task
from app.config import Settings

settings = Settings()

# Initialize Celery app
celery_app = Celery(
    "pantry_inventory",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.JOB_TIMEOUT,
    task_soft_time_limit=settings.JOB_TIMEOUT - 30,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,
)


class DatabaseTask(Task):
    """Task with database session management."""

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning("Task retrying", extra={
            "task_id": task_id,
            "error": str(exc),
            "retry_count": self.request.retries,
        })
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error("Task failed", extra={
            "task_id": task_id,
            "error": str(exc),
        })
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        logger.info("Task completed", extra={
            "task_id": task_id,
            "result": retval,
        })
        super().on_success(retval, task_id, args, kwargs)


@celery_app.task(bind=True, base=DatabaseTask, max_retries=settings.MAX_RETRIES)
def process_image_capture(self, capture_id: str) -> dict:
    """Process a single image capture asynchronously."""
    from app.db.session import SessionLocal
    from app.db.models import Capture
    from app.workers.capture import CaptureProcessor

    logger.info("Processing capture", extra={"capture_id": capture_id})
    db = None
    try:
        db = SessionLocal()
        processor = CaptureProcessor()
        success = processor.process_capture(capture_id)

        if success:
            logger.info("Capture processed successfully", extra={"capture_id": capture_id})
            return {"capture_id": capture_id, "status": "completed"}
        else:
            raise ValueError(f"Processing failed for capture {capture_id}")

    except Exception as exc:
        logger.error("Error processing capture", extra={
            "capture_id": capture_id,
            "error": str(exc),
        })
        if db:
            try:
                capture = db.query(Capture).filter(Capture.id == capture_id).first()
                if capture:
                    capture.status = "failed"
                    capture.error_message = str(exc)
                    db.commit()
            except Exception:
                pass
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries, 600))

    finally:
        if db:
            db.close()


@celery_app.task(bind=True, base=DatabaseTask, max_retries=settings.MAX_RETRIES)
def process_pending_captures(self) -> dict:
    """Process all pending image captures in batch."""
    from app.db.session import SessionLocal
    from app.db.models import Capture

    db = None
    try:
        db = SessionLocal()
        pending = db.query(Capture).filter(Capture.status == "stored").all()
        processed_count = 0
        for capture in pending:
            try:
                process_image_capture.delay(capture.id)
                processed_count += 1
            except Exception as e:
                logger.error("Failed to queue capture", extra={
                    "capture_id": capture.id,
                    "error": str(e),
                })
        logger.info("Batch queued", extra={"queued": processed_count})
        return {"queued_count": processed_count, "status": "queued"}
    except Exception as exc:
        logger.error("Batch processing error", extra={"error": str(exc)})
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries, 600))
    finally:
        if db:
            db.close()


@celery_app.task
def cleanup_old_captures() -> dict:
    """Clean up old capture records."""
    from app.db.session import SessionLocal
    from app.db.models import Capture
    from datetime import datetime, timedelta

    try:
        db = SessionLocal()
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        deleted = db.query(Capture).filter(Capture.created_at < cutoff_date).delete()
        db.commit()
        logger.info("Cleanup complete", extra={"deleted": deleted})
        return {"deleted_count": deleted, "status": "completed"}
    except Exception as exc:
        logger.error("Cleanup error", extra={"error": str(exc)})
        return {"status": "error", "error": str(exc)}
    finally:
        db.close()
