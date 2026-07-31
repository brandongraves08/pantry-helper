"""Background worker for image retention policy enforcement."""

import logging
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import Capture
from app.services.storage import get_storage_manager
from app.config import settings

logger = logging.getLogger(__name__)


class RetentionPolicyEnforcer:
    """Enforces image retention policies and cleanup."""
    
    # Default retention in days - can be overridden via env
    DEFAULT_RETENTION_DAYS = int(os.getenv("IMAGE_RETENTION_DAYS", "30"))
    
    def __init__(self):
        """Initialize retention policy enforcer."""
        self.storage_manager = get_storage_manager()
        self.retention_days = self.DEFAULT_RETENTION_DAYS
        
        logger.info(f"Retention policy enforcer initialized (retention: {self.retention_days} days)")
    
    def enforce_retention(self) -> dict:
        """
        Enforce image retention policy by deleting expired captures.
        
        Returns:
            Dictionary with stats: deleted_count, freed_mb, errors
        """
        logger.info(f"Starting retention policy enforcement (retention: {self.retention_days} days)...")
        
        db = SessionLocal()
        deleted_count = 0
        freed_bytes = 0
        errors = 0
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            
            logger.info(f"Deleting captures before {cutoff_date.isoformat()}")
            
            # Find captures older than retention period
            old_captures = db.query(Capture).filter(
                Capture.captured_at < cutoff_date
            ).all()
            
            logger.info(f"Found {len(old_captures)} captures to process")
            
            for capture in old_captures:
                try:
                    # Get image size before deletion
                    image_size = self.storage_manager.get_image_size(capture.image_path)
                    
                    # Delete image file
                    if self.storage_manager.delete_image(capture.image_path):
                        freed_bytes += image_size
                        deleted_count += 1
                    
                    # Note: Don't delete the Capture record itself, just the image
                    # This preserves audit history and metadata
                    capture.image_path = None  # Mark as image deleted
                    db.add(capture)
                    
                except Exception as e:
                    logger.error(f"Error processing capture {capture.id}: {str(e)}")
                    errors += 1
                    continue
            
            # Commit all changes
            if deleted_count > 0:
                db.commit()
            
            freed_mb = freed_bytes / (1024 * 1024)
            
            logger.info(
                f"Retention enforcement complete: "
                f"{deleted_count} images deleted, {freed_mb:.2f} MB freed, {errors} errors"
            )
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "freed_mb": freed_mb,
                "errors": errors,
                "cutoff_date": cutoff_date.isoformat(),
            }
            
        except Exception as e:
            logger.exception(f"Error during retention enforcement: {str(e)}")
            return {
                "success": False,
                "deleted_count": deleted_count,
                "freed_mb": freed_bytes / (1024 * 1024),
                "errors": errors + 1,
                "error": str(e),
            }
        
        finally:
            db.close()
    
    def cleanup_failed_captures(self, days: int = 7) -> dict:
        """
        Clean up images from failed captures (status='failed') older than X days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Dictionary with stats
        """
        logger.info(f"Cleaning up failed captures older than {days} days...")
        
        db = SessionLocal()
        deleted_count = 0
        freed_bytes = 0
        errors = 0
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Find failed captures older than threshold
            failed_captures = db.query(Capture).filter(
                Capture.status == "failed",
                Capture.created_at < cutoff_date,
            ).all()
            
            logger.info(f"Found {len(failed_captures)} failed captures to clean")
            
            for capture in failed_captures:
                try:
                    if capture.image_path:
                        image_size = self.storage_manager.get_image_size(capture.image_path)
                        if self.storage_manager.delete_image(capture.image_path):
                            freed_bytes += image_size
                            deleted_count += 1
                        
                        capture.image_path = None
                        db.add(capture)
                    
                except Exception as e:
                    logger.error(f"Error cleaning capture {capture.id}: {str(e)}")
                    errors += 1
                    continue
            
            if deleted_count > 0:
                db.commit()
            
            freed_mb = freed_bytes / (1024 * 1024)
            
            logger.info(
                f"Failed capture cleanup complete: "
                f"{deleted_count} images deleted, {freed_mb:.2f} MB freed"
            )
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "freed_mb": freed_mb,
                "errors": errors,
            }
            
        except Exception as e:
            logger.exception(f"Error cleaning failed captures: {str(e)}")
            return {
                "success": False,
                "deleted_count": deleted_count,
                "freed_mb": freed_bytes / (1024 * 1024),
                "errors": errors + 1,
                "error": str(e),
            }
        
        finally:
            db.close()
    
    def check_storage_quota(self, max_storage_mb: int = 5000) -> dict:
        """
        Check if storage usage exceeds quota and clean up if needed.
        
        Args:
            max_storage_mb: Maximum storage in MB
            
        Returns:
            Dictionary with stats and cleanup result
        """
        logger.info(f"Checking storage quota (limit: {max_storage_mb} MB)...")
        
        # Get current storage stats
        stats = self.storage_manager.get_storage_stats()
        current_size_mb = stats["total_size_mb"]
        
        logger.info(f"Current storage: {current_size_mb:.2f} MB / {max_storage_mb} MB")
        
        if current_size_mb <= max_storage_mb:
            return {
                "over_quota": False,
                "current_size_mb": current_size_mb,
                "limit_mb": max_storage_mb,
                "cleanup_needed": False,
            }
        
        # Over quota - trigger cleanup
        logger.warning(f"Storage over quota! Cleaning up...")
        cleanup_result = self.enforce_retention()
        
        # Get new stats
        new_stats = self.storage_manager.get_storage_stats()
        new_size_mb = new_stats["total_size_mb"]
        
        return {
            "over_quota": True,
            "previous_size_mb": current_size_mb,
            "current_size_mb": new_size_mb,
            "limit_mb": max_storage_mb,
            "cleanup_result": cleanup_result,
            "freed_mb": current_size_mb - new_size_mb,
        }


# Global instance
_enforcer = None


def get_retention_enforcer() -> RetentionPolicyEnforcer:
    """Get or create retention policy enforcer singleton."""
    global _enforcer
    if _enforcer is None:
        _enforcer = RetentionPolicyEnforcer()
    return _enforcer
