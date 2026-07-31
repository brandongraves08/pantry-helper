"""Storage management and image retention policies."""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages image storage and retention policies."""
    
    # Default retention in days
    DEFAULT_RETENTION_DAYS = 30
    MIN_RETENTION_DAYS = 1
    MAX_RETENTION_DAYS = 365
    
    def __init__(self):
        """Initialize storage manager."""
        self.storage_path = Path(settings.STORAGE_PATH or "./storage")
        self.images_path = self.storage_path / "images"
        
        # Ensure directories exist
        self.images_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Storage manager initialized at {self.storage_path}")
    
    @staticmethod
    def get_image_filename(device_id: str, capture_id: str) -> str:
        """
        Generate standardized image filename.
        
        Args:
            device_id: Device identifier
            capture_id: Capture identifier
            
        Returns:
            Filename without path
        """
        return f"{device_id}_{capture_id}.jpg"
    
    def get_image_path(self, device_id: str, capture_id: str) -> Path:
        """
        Get full path to image file.
        
        Args:
            device_id: Device identifier
            capture_id: Capture identifier
            
        Returns:
            Full Path object
        """
        filename = self.get_image_filename(device_id, capture_id)
        return self.images_path / filename
    
    def save_image(
        self,
        device_id: str,
        capture_id: str,
        image_data: bytes,
    ) -> str:
        """
        Save image to storage.
        
        Args:
            device_id: Device identifier
            capture_id: Capture identifier
            image_data: Image bytes (JPEG)
            
        Returns:
            Relative path to image
            
        Raises:
            IOError: If save fails
        """
        try:
            image_path = self.get_image_path(device_id, capture_id)
            
            # Write image
            with open(image_path, "wb") as f:
                f.write(image_data)
            
            # Return relative path for storage in DB
            relative_path = f"images/{self.get_image_filename(device_id, capture_id)}"
            logger.info(f"Saved image: {relative_path} ({len(image_data)} bytes)")
            
            return relative_path
            
        except Exception as e:
            logger.error(f"Failed to save image {device_id}/{capture_id}: {str(e)}")
            raise IOError(f"Failed to save image: {str(e)}")
    
    def delete_image(self, image_path: str) -> bool:
        """
        Delete image file.
        
        Args:
            image_path: Relative path to image
            
        Returns:
            True if deleted, False if not found
        """
        try:
            full_path = self.storage_path / image_path
            
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Deleted image: {image_path}")
                return True
            else:
                logger.warning(f"Image not found for deletion: {image_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete image {image_path}: {str(e)}")
            return False
    
    def get_image_size(self, image_path: str) -> int:
        """
        Get image file size in bytes.
        
        Args:
            image_path: Relative path to image
            
        Returns:
            File size in bytes, 0 if not found
        """
        try:
            full_path = self.storage_path / image_path
            
            if full_path.exists():
                return full_path.stat().st_size
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to get image size {image_path}: {str(e)}")
            return 0
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with total_size, file_count, oldest_file, newest_file
        """
        try:
            total_size = 0
            file_count = 0
            oldest_time = None
            newest_time = None
            
            for image_file in self.images_path.glob("*.jpg"):
                try:
                    file_size = image_file.stat().st_size
                    file_mtime = datetime.fromtimestamp(image_file.stat().st_mtime)
                    
                    total_size += file_size
                    file_count += 1
                    
                    if oldest_time is None or file_mtime < oldest_time:
                        oldest_time = file_mtime
                    if newest_time is None or file_mtime > newest_time:
                        newest_time = file_mtime
                        
                except Exception as e:
                    logger.warning(f"Error reading file stats: {str(e)}")
                    continue
            
            return {
                "total_size_mb": total_size / (1024 * 1024),
                "file_count": file_count,
                "oldest_file": oldest_time.isoformat() if oldest_time else None,
                "newest_file": newest_time.isoformat() if newest_time else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {
                "total_size_mb": 0,
                "file_count": 0,
                "oldest_file": None,
                "newest_file": None,
            }
    
    def cleanup_orphaned_images(self) -> int:
        """
        Delete images that don't have corresponding DB records.
        
        This scans the image directory and removes files that are not
        referenced in the database. Useful for cleaning up after failed uploads
        or manual database maintenance.
        
        Returns:
            Number of orphaned images deleted
        """
        # Import here to avoid circular dependency
        from sqlalchemy.orm import Session
        from app.db.database import SessionLocal
        from app.db.models import Capture
        
        deleted_count = 0
        
        try:
            db = SessionLocal()
            
            # Get all image files
            image_files = list(self.images_path.glob("*.jpg"))
            logger.info(f"Scanning {len(image_files)} image files for orphans...")
            
            for image_file in image_files:
                filename = image_file.name
                
                # Check if this image exists in DB
                capture = db.query(Capture).filter(
                    Capture.image_path.like(f"%{filename}")
                ).first()
                
                if not capture:
                    logger.warning(f"Orphaned image found: {filename}")
                    self.delete_image(f"images/{filename}")
                    deleted_count += 1
            
            logger.info(f"Cleanup complete: {deleted_count} orphaned images deleted")
            
        except Exception as e:
            logger.error(f"Error during orphan cleanup: {str(e)}")
        finally:
            db.close()
        
        return deleted_count


# Global instance
_storage_manager = None


def get_storage_manager() -> StorageManager:
    """Get or create storage manager singleton."""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
    return _storage_manager
