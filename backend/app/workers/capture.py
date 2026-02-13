"""Background job worker for processing captures"""
import logging
import os
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Capture, Observation, InventoryItem
from app.services.vision import VisionAnalyzer
from app.services.inventory import InventoryManager
from app.exceptions import VisionAnalysisError
from datetime import datetime

logger = logging.getLogger(__name__)


class CaptureProcessor:
    """Process captures: analyze images and update inventory"""

    def __init__(self):
        provider = os.getenv("VISION_PROVIDER", "openai").lower()
        # In production-test mode we allow a mock provider that doesn't require API keys.
        if provider in ("mock", "none"):
            self.analyzer = VisionAnalyzer(api_key=None, provider="mock")
            return
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
        elif provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
        elif provider == "nvidia":
            api_key = os.getenv("NVIDIA_NIM_API_KEY")
        else:
            api_key = None
        if not api_key:
            logger.warning(f"{provider.upper()} API key not set - vision analysis will fail")
            self.analyzer = None
        else:
            self.analyzer = VisionAnalyzer(api_key=api_key, provider=provider)

    def _apply_zone_inference(self, db: Session, capture_id: str, observation: Observation, vision_output):
        """Apply zone-based inference to enhance low-confidence detections."""
        from app.services.zones import ZoneService
        zone_service = ZoneService(db)
        capture = db.query(Capture).filter_by(id=capture_id).first()
        if not capture:
            return

        zones = zone_service.get_zones_for_device(capture.device_id)
        if not zones:
            logger.debug(f"No zones defined for device {capture.device_id}")
            return

        logger.info(f"Processing {len(zones)} zones for zone-based inference")

        for item in vision_output.items:
            if item.confidence >= 0.7:
                continue
            for zone in zones:
                if zone.expected_item_type and item.package_type == zone.expected_item_type:
                    inferred = zone_service.infer_item_for_zone(zone.id, item.package_type)
                    if inferred:
                        inferred_item, inference_conf = inferred
                        logger.info(f"Zone inference: {item.name} -> {inferred_item.canonical_name} "
                                    f"(confidence: {inference_conf:.2f})")
                        if inference_conf >= 0.7:
                            original_name = item.name
                            item.name = inferred_item.canonical_name
                            if item.brand is None:
                                item.brand = inferred_item.brand
                            item.confidence = inference_conf
                            if observation.raw_json:
                                for raw_item in observation.raw_json.get("items", []):
                                    if raw_item.get("name") == original_name:
                                        raw_item["name"] = inferred_item.canonical_name
                                        raw_item["inferred_from_zone"] = zone.name
                                        raw_item["inference_confidence"] = inference_conf
                            db.commit()
                            break

    def process_capture(self, capture_id: str) -> bool:
        """Process a single capture: analyze image and update inventory."""
        db = SessionLocal()
        try:
            capture = db.query(Capture).filter_by(id=capture_id).first()
            if not capture:
                logger.error(f"Capture not found: {capture_id}")
                return False

            if capture.status in ("analyzing", "complete"):
                logger.warning(f"Capture already {capture.status}: {capture_id}")
                return True

            capture.status = "analyzing"
            db.commit()
            logger.info(f"Processing capture: {capture_id}")

            if not self.analyzer:
                raise VisionAnalysisError("Vision analyzer not initialized")

            image_path = capture.image_path
            if image_path and not os.path.isabs(image_path):
                from app.services.storage import get_storage_manager
                storage_mgr = get_storage_manager()
                image_path = str(storage_mgr.storage_path / image_path)

            vision_output = self.analyzer.analyze_image(image_path)

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

            try:
                self._apply_zone_inference(db, capture_id, observation, vision_output)
            except Exception as e:
                logger.warning(f"Zone inference failed (continuing): {e}")

            inventory_manager = InventoryManager(db)
            inventory_manager.process_observation(observation, vision_output)

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
        """Process all pending captures."""
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


_processor = None


def get_processor() -> CaptureProcessor:
    """Get or create the capture processor"""
    global _processor
    if _processor is None:
        _processor = CaptureProcessor()
    return _processor
