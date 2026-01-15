"""Background job worker for processing captures"""

import logging
import os
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Capture, Observation
from app.services.vision import VisionAnalyzer
from app.services.inventory import InventoryManager
from app.exceptions import VisionAnalysisError
from datetime import datetime

logger = logging.getLogger(__name__)


class CaptureProcessor:
    """Process captures: analyze images and update inventory"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set - vision analysis will fail")
        self.analyzer = VisionAnalyzer(api_key) if api_key else None
    
    def process_capture(self, capture_id: str) -> bool:
        """
        Process a single capture: analyze image and update inventory.
        
        Args:
            capture_id: ID of the capture to process
            
        Returns:
            True if successful, False otherwise
        """
        db = SessionLocal()
        try:
            # Get capture
            capture = db.query(Capture).filter_by(id=capture_id).first()
            if not capture:
                logger.error(f"Capture not found: {capture_id}")
                return False
            
            # Check if already processing or complete
            if capture.status in ("analyzing", "complete"):
                logger.warning(f"Capture already {capture.status}: {capture_id}")
                return True
            
            # Mark as analyzing
            capture.status = "analyzing"
            db.commit()
            
            logger.info(f"Processing capture: {capture_id}")
            
            # Analyze image
            if not self.analyzer:
                raise VisionAnalysisError("Vision analyzer not initialized")
            
            vision_output = self.analyzer.analyze_image(capture.image_path)
            
            # Store raw observation
            observation = Observation(
                capture_id=capture_id,
                raw_json={
                    "scene_confidence": vision_output.scene_confidence,
                    "items": [item.dict() for item in vision_output.items],
                    "notes": vision_output.notes,
                },
                scene_confidence=vision_output.scene_confidence,
            )
            db.add(observation)
            db.flush()
            
            # Update inventory
            inventory_manager = InventoryManager(db)
            inventory_manager.process_observation(observation, vision_output)
            
            # Mark capture as complete
            capture.status = "complete"
            db.commit()
            
            logger.info(f"Successfully processed capture: {capture_id}")
            return True
            
        except VisionAnalysisError as e:
            logger.error(f"Vision analysis failed for {capture_id}: {str(e)}")
            capture.status = "failed"
            capture.error_message = str(e)
            db.commit()
            return False
        except Exception as e:
            logger.exception(f"Error processing capture {capture_id}: {str(e)}")
            capture.status = "failed"
            capture.error_message = str(e)
            db.commit()
            return False
        finally:
            db.close()
    
    def process_pending_captures(self, limit: int = 10) -> int:
        """
        Process all pending captures.
        
        Args:
            limit: Maximum number to process
            
        Returns:
            Number successfully processed
        """
        db = SessionLocal()
        try:
            pending = db.query(Capture).filter_by(status="stored").limit(limit).all()
            count = 0
            
            for capture in pending:
                if self.process_capture(capture.id):
                    count += 1
            
            logger.info(f"Processed {count}/{len(pending)} pending captures")
            return count
        finally:
            db.close()


# Singleton instance
_processor = None


def get_processor() -> CaptureProcessor:
    """Get or create the capture processor"""
    global _processor
    if _processor is None:
        _processor = CaptureProcessor()
    return _processor
