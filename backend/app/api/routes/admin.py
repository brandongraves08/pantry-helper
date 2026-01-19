"""Admin control endpoints for manual processing and system monitoring."""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import (
    Capture,
    Device,
    Observation,
    InventoryEvent,
)
from app.workers.celery_app import (
    process_image_capture,
    process_pending_captures,
    celery_app,
)
from app.middleware.rate_limit import rate_limit_store
import logging
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()



@router.get("/admin/stats")
async def get_system_stats():
    """Get system statistics and job queue status."""
    db = SessionLocal()
    try:
        # Database stats
        device_count = db.query(Device).count()
        capture_count = db.query(Capture).count()
        observation_count = db.query(Observation).count()
        event_count = db.query(InventoryEvent).count()

        # Capture status breakdown
        pending = db.query(Capture).filter(
            Capture.status == CaptureStatus.PENDING
        ).count()
        processing = db.query(Capture).filter(
            Capture.status == CaptureStatus.PROCESSING
        ).count()
        completed = db.query(Capture).filter(
            Capture.status == CaptureStatus.COMPLETED
        ).count()
        failed = db.query(Capture).filter(
            Capture.status == CaptureStatus.FAILED
        ).count()

        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active() or {}
        reserved_tasks = inspect.reserved() or {}
        
        total_active = sum(len(tasks) for tasks in active_tasks.values())
        total_reserved = sum(len(tasks) for tasks in reserved_tasks.values())

        return {
            "devices": device_count,
            "captures": {
                "total": capture_count,
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
            },
            "observations": observation_count,
            "events": event_count,
            "queue": {
                "active_jobs": total_active,
                "reserved_jobs": total_reserved,
                "total_queued": total_active + total_reserved,
            },
            "rate_limits": {
                "enabled": True,
                "total_tracked": len(rate_limit_store.requests),
            },
        }
    finally:
        db.close()


@router.post("/admin/process-capture/{capture_id}")
async def process_capture(capture_id: str, sync: bool = Query(False)):
    """
    Process a single image capture.
    
    Args:
        capture_id: ID of capture to process
        sync: If True, wait for result; if False, queue asynchronously (default)
    """
    db = SessionLocal()
    try:
        capture = db.query(Capture).filter(Capture.id == capture_id).first()
        if not capture:
            raise HTTPException(status_code=404, detail="Capture not found")

        if sync:
            # Process synchronously
            try:
                from app.services.vision import VisionAnalyzer

                analyzer = VisionAnalyzer()
                result = analyzer.analyze_image(capture.image_data)

                # Create observation
                observation = Observation(
                    capture_id=capture.id,
                    device_id=capture.device_id,
                    raw_json=result,
                )
                db.add(observation)
                capture.status = CaptureStatus.COMPLETED
                db.commit()

                return {
                    "capture_id": capture_id,
                    "observation_id": observation.id,
                    "status": "completed",
                    "sync": True,
                }
            except Exception as e:
                capture.status = CaptureStatus.FAILED
                db.commit()
                logger.error(f"Sync processing failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        else:
            # Queue async job
            task = process_image_capture.delay(capture_id)
            return {
                "capture_id": capture_id,
                "task_id": task.id,
                "status": "queued",
                "sync": False,
            }
    finally:
        db.close()


@router.post("/admin/process-pending")
async def process_pending(sync: bool = Query(False)):
    """
    Process all pending captures.
    
    Args:
        sync: If True, process synchronously; if False, queue batch job
    """
    db = SessionLocal()
    try:
        pending = db.query(Capture).filter(
            Capture.status == CaptureStatus.PENDING
        ).all()

        if not pending:
            return {
                "message": "No pending captures",
                "processed": 0,
                "sync": sync,
            }

        if sync:
            # Process synchronously
            processed = 0
            try:
                from app.services.vision import VisionAnalyzer

                analyzer = VisionAnalyzer()
                for capture in pending:
                    try:
                        result = analyzer.analyze_image(capture.image_data)
                        observation = Observation(
                            capture_id=capture.id,
                            device_id=capture.device_id,
                            raw_json=result,
                        )
                        db.add(observation)
                        capture.status = CaptureStatus.COMPLETED
                        processed += 1
                    except Exception as e:
                        logger.error(f"Failed to process {capture.id}: {e}")
                        capture.status = CaptureStatus.FAILED

                db.commit()
                return {
                    "message": "Batch processing completed",
                    "processed": processed,
                    "sync": True,
                }
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        else:
            # Queue batch job
            task = process_pending_captures.delay()
            return {
                "task_id": task.id,
                "message": "Batch processing queued",
                "pending_count": len(pending),
                "sync": False,
            }
    finally:
        db.close()


@router.get("/admin/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a queued processing task."""
    from celery.result import AsyncResult

    task = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "state": task.state,
        "result": task.result if task.ready() else None,
        "ready": task.ready(),
        "successful": task.successful() if task.ready() else None,
        "failed": task.failed() if task.ready() else None,
    }


@router.post("/admin/cancel-task/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running or queued task."""
    celery_app.control.revoke(task_id, terminate=True)
    
    return {
        "task_id": task_id,
        "status": "cancelled",
    }


@router.get("/admin/queue-info")
async def get_queue_info():
    """Get detailed information about the job queue."""
    try:
        inspect = celery_app.control.inspect()
        
        active = inspect.active() or {}
        reserved = inspect.reserved() or {}
        stats = inspect.stats() or {}

        return {
            "active": {
                "tasks": sum(len(tasks) for tasks in active.values()),
                "by_worker": {w: len(tasks) for w, tasks in active.items()},
            },
            "reserved": {
                "tasks": sum(len(tasks) for tasks in reserved.values()),
                "by_worker": {w: len(tasks) for w, tasks in reserved.items()},
            },
            "workers": list(stats.keys()),
            "pool_size": len(stats),
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
