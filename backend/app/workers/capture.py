"""Capture processing pipeline with structured logging."""
import json
import logging
import os
from app.models.schemas import VisionOutput
from app.exceptions import VisionAnalysisError
from app.services.vision import VisionAnalyzer
from app.services.barcode_detector import detect_barcodes
from app.services.barcode import lookup_barcode

logger = logging.getLogger("pantry-worker")


class CaptureProcessor:
    """Process a captured image through the vision pipeline."""

    def __init__(self):
        try:
            self.vision = VisionAnalyzer()
        except ValueError as e:
            if os.getenv("PYTEST_CURRENT_TEST"):
                logger.warning("Vision analyzer unavailable in test context", extra={"error": str(e)})
                self.vision = VisionAnalyzer(provider="mock")
            else:
                raise

    def process_capture(self, capture_id: str) -> bool:
        from app.db.session import SessionLocal
        from app.db.models import Capture, Observation, InventoryItem, InventoryState, InventoryEvent

        logger.info("Starting capture processing", extra={"capture_id": capture_id})

        db = SessionLocal()
        try:
            capture = db.query(Capture).filter(Capture.id == capture_id).first()
            if not capture:
                logger.error("Capture not found", extra={"capture_id": capture_id})
                return False

            capture.status = "analyzing"
            db.commit()

            image_path = capture.image_path
            if not os.path.isabs(image_path):
                from app.services.storage import get_storage_manager
                mgr = get_storage_manager()
                image_path = str(mgr.storage_path / image_path)

            if not os.path.exists(image_path):
                logger.error("Image file not found", extra={
                    "capture_id": capture_id,
                    "image_path": image_path,
                })
                capture.status = "failed"
                capture.error_message = f"Image file not found: {image_path}"
                db.commit()
                return False

            # Run barcode detection on the image
            barcodes = detect_barcodes(image_path)
            if barcodes:
                logger.info("Barcode(s) detected in capture image", extra={
                    "capture_id": capture_id,
                    "count": len(barcodes),
                    "codes": [b.data for b in barcodes],
                })
                # Look up each detected barcode and create/update barcode lookup records
                for bc in barcodes:
                    try:
                        product = lookup_barcode(bc.data)
                        if product.found:
                            logger.info("Barcode resolved to product", extra={
                                "barcode": bc.data,
                                "product": product.product_name,
                            })
                            # Check if item already in inventory
                            from app.db.models import BarcodeLookup
                            existing = db.query(BarcodeLookup).filter(
                                BarcodeLookup.barcode == bc.data
                            ).first()
                            if not existing:
                                bl = BarcodeLookup(
                                    barcode=bc.data,
                                    product_name=product.product_name,
                                    brand=product.brand,
                                    category=product.category,
                                    package_type=product.package_type,
                                    image_url=product.image_url,
                                    source=product.source,
                                )
                                db.add(bl)
                                db.commit()
                    except Exception as bc_err:
                        logger.warning("Barcode product lookup failed", extra={
                            "barcode": bc.data,
                            "error": str(bc_err),
                        })

            # Run vision analysis
            logger.info("Running vision analysis", extra={
                "capture_id": capture_id,
                "provider": self.vision.provider,
                "image_path": image_path,
            })
            result: VisionOutput = self.vision.analyze_image(image_path)

            # Store observation
            observation = Observation(
                capture_id=capture.id,
                raw_json=result.model_dump(mode="json"),
                scene_confidence=result.scene_confidence,
            )
            db.add(observation)
            db.flush()

            # Update inventory
            items_updated = 0
            for item_data in result.items:
                name = (item_data.name or "").strip()
                if not name:
                    continue
                qty = item_data.quantity_estimate or 1
                conf = item_data.confidence or 0.5
                if conf < 0.7:
                    logger.info("Skipping low-confidence item", extra={
                        "capture_id": capture_id,
                        "item": name,
                        "confidence": conf,
                    })
                    continue

                canonical = name.lower().replace("  ", " ").strip()
                inv_item = db.query(InventoryItem).filter(
                    InventoryItem.canonical_name == canonical
                ).first()

                if not inv_item:
                    inv_item = InventoryItem(
                        canonical_name=canonical,
                        brand=item_data.brand,
                        package_type=item_data.package_type or "other",
                    )
                    db.add(inv_item)
                    db.flush()

                # Propagate the capture image to the inventory item
                # Always update to the latest capture so the photo stays fresh
                inv_item.image_path = capture.image_path

                state = db.query(InventoryState).filter(
                    InventoryState.item_id == inv_item.id
                ).first()

                if state:
                    delta = qty - (state.count_estimate or 0)
                    state.count_estimate = qty
                    state.confidence = conf
                    state.last_seen_at = capture.captured_at
                else:
                    delta = qty
                    state = InventoryState(
                        item_id=inv_item.id,
                        count_estimate=qty,
                        confidence=conf,
                        last_seen_at=capture.captured_at,
                    )
                    db.add(state)

                event = InventoryEvent(
                    item_id=inv_item.id,
                    capture_id=capture.id,
                    event_type="seen",
                    delta=delta,
                    details={
                        "confidence": conf,
                        "trigger_type": capture.trigger_type,
                    },
                )
                db.add(event)
                items_updated += 1

            # Update capture status
            capture.status = "complete"
            db.commit()

            logger.info("Capture processed", extra={
                "capture_id": capture_id,
                "items_found": len(result.items),
                "items_updated": items_updated,
                "scene_confidence": result.scene_confidence,
            })
            return True

        except VisionAnalysisError as e:
            logger.error("Vision analysis failed", extra={
                "capture_id": capture_id,
                "error": str(e),
            })
            capture.status = "failed"
            capture.error_message = f"Vision analysis error: {e}"
            db.commit()
            return False

        except Exception as e:
            logger.exception("Unexpected processing error", extra={
                "capture_id": capture_id,
                "error": str(e),
            })
            try:
                capture.status = "failed"
                capture.error_message = str(e)
                db.commit()
            except Exception:
                pass
            return False

        finally:
            db.close()

    def process_pending_captures(self, limit: int = 50) -> int:
        """Process stored captures synchronously, mainly for maintenance/tests."""
        from app.db.session import SessionLocal
        from app.db.models import Capture

        db = SessionLocal()
        try:
            captures = (
                db.query(Capture)
                .filter(Capture.status == "stored")
                .order_by(Capture.created_at.asc())
                .limit(limit)
                .all()
            )
            capture_ids = [capture.id for capture in captures]
        finally:
            db.close()

        processed = 0
        for capture_id in capture_ids:
            if self.process_capture(capture_id):
                processed += 1
        return processed
