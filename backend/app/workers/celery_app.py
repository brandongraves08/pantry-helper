"""Celery task queue configuration and task definitions."""

from celery import Celery, Task
from app.config import Settings
import logging

logger = logging.getLogger(__name__)

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
    result_expires=3600,  # 1 hour
)


class DatabaseTask(Task):
    """Task with database session management."""

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(f"Task {task_id} retrying after error: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info(f"Task {task_id} completed successfully")
        super().on_success(retval, task_id, args, kwargs)


@celery_app.task(bind=True, base=DatabaseTask, max_retries=settings.MAX_RETRIES)
def process_image_capture(self, capture_id: str) -> dict:
    """
    Process a single image capture asynchronously.
    
    Args:
        capture_id: The capture record ID to process
        
    Returns:
        dict: Processing result with observation_id and status
    """
    from app.db.session import SessionLocal
    from app.db.models import Capture
    from app.workers.capture import CaptureProcessor

    db = None
    try:
        db = SessionLocal()
        processor = CaptureProcessor()
        success = processor.process_capture(capture_id)
        
        if success:
            logger.info(f"Processed capture {capture_id} successfully")
            return {
                "capture_id": capture_id,
                "status": "completed",
            }
        else:
            raise ValueError(f"Processing failed for capture {capture_id}")

    except Exception as exc:
        logger.error(f"Error processing capture {capture_id}: {exc}")
        
        # Mark capture as failed
        if db:
            try:
                capture = db.query(Capture).filter(Capture.id == capture_id).first()
                if capture:
                    capture.status = "failed"
                    capture.error_message = str(exc)
                    db.commit()
            except:
                pass
        
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries, 600))

    finally:
        if db:
            db.close()


@celery_app.task(bind=True, base=DatabaseTask, max_retries=settings.MAX_RETRIES)
def process_pending_captures(self) -> dict:
    """
    Process all pending image captures in batch.
    
    Returns:
        dict: Summary of processed captures
    """
    from app.db.session import SessionLocal
    from app.db.models import Capture

    db = None
    try:
        db = SessionLocal()
        
        # Find pending captures
        pending = db.query(Capture).filter(
            Capture.status == "stored"
        ).all()

        processed_count = 0
        for capture in pending:
            try:
                # Chain task for each capture
                process_image_capture.delay(capture.id)
                processed_count += 1
            except Exception as e:
                logger.error(f"Failed to queue capture {capture.id}: {e}")

        logger.info(f"Queued {processed_count} captures for processing")
        return {
            "queued_count": processed_count,
            "status": "queued",
        }

    except Exception as exc:
        logger.error(f"Error in batch processing: {exc}")
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries, 600))

    finally:
        if db:
            db.close()


@celery_app.task
def cleanup_old_captures() -> dict:
    """
    Clean up old capture records to maintain database performance.
    
    Returns:
        dict: Cleanup statistics
    """
    from app.db.session import SessionLocal
    from app.db.models import Capture
    from datetime import datetime, timedelta

    try:
        db = SessionLocal()
        
        # Delete captures older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        deleted = db.query(Capture).filter(
            Capture.created_at < cutoff_date
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {deleted} old capture records")
        
        return {
            "deleted_count": deleted,
            "status": "completed",
        }

    except Exception as exc:
        logger.error(f"Error in cleanup: {exc}")
        return {
            "status": "error",
            "error": str(exc),
        }

    finally:
        db.close()
