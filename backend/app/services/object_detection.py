"""Object detection service (YOLOv8 wrapper)"""
import logging
import os
from typing import List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Detection:
    """A single object detection"""
    class_name: str
    confidence: float
    x: float  # normalized 0-1
    y: float  # normalized 0-1
    width: float  # normalized 0-1
    height: float  # normalized 0-1

class ObjectDetector:
    """Wrapper for YOLOv8 or other object detection models"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path
        self._load_model()
    
    def _load_model(self):
        """Load YOLOv8 model (if available)"""
        try:
            from ultralytics import YOLO
            
            if self.model_path and os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
            else:
                # Use nano model for fast CPU inference
                self.model = YOLO('yolov8n.pt')
                
            logger.info(f"Loaded YOLOv8 model: {self.model}")
        except ImportError:
            logger.warning("Ultralytics not installed. Object detection disabled.")
            logger.warning("Install with: pip install ultralytics")
        except Exception as e:
            logger.error(f"Failed to load YOLOv8: {e}")
    
    def is_available(self) -> bool:
        """Check if YOLOv8 is available"""
        return self.model is not None
    
    def detect(self, image_path: str, conf_threshold: float = 0.3) -> List[Detection]:
        """
        Detect objects in image.
        Returns normalized coordinates (0-1 range).
        """
        if not self.model:
            logger.warning("YOLOv8 not available, skipping detection")
            return []
        
        try:
            import numpy as np
            from PIL import Image
            
            # Get image dimensions
            img = Image.open(image_path)
            img_w, img_h = img.size
            
            # Run YOLOv8
            results = self.model(image_path, conf=conf_threshold, verbose=False)
            
            detections = []
            
            for result in results:
                if result.boxes is None:
                    continue
                
                boxes = result.boxes.cpu().numpy()
                
                for box in boxes:
                    # YOLO returns xywh format
                    x, y, w, h = box.xywh[0]
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id]
                    
                    # Normalize to 0-1
                    detection = Detection(
                        class_name=class_name,
                        confidence=confidence,
                        x=float(x) / img_w,
                        y=float(y) / img_h,
                        width=float(w) / img_w,
                        height=float(h) / img_h
                    )
                    detections.append(detection)
            
            logger.info(f"YOLOv8 detected {len(detections)} objects")
            return detections
            
        except Exception as e:
            logger.error(f"YOLOv8 detection failed: {e}")
            return []
    
    def detect_zones_intersecting(
        self,
        image_path: str,
        zones: List,
        conf_threshold: float = 0.3
    ) -> List[Tuple[Detection, Optional[object]]]:
        """
        Detect objects and match them to zones.
        Returns list of (detection, zone) tuples.
        """
        detections = self.detect(image_path, conf_threshold)
        results = []
        
        for det in detections:
            # Find intersecting zone
            matched_zone = None
            for zone in zones:
                # Check if detection center is in zone
                det_center_x = det.x + det.width / 2
                det_center_y = det.y + det.height / 2
                
                if (zone.x <= det_center_x <= zone.x + zone.width and
                    zone.y <= det_center_y <= zone.y + zone.height):
                    matched_zone = zone
                    break
            
            results.append((det, matched_zone))
        
        return results

# Singleton instance
detector = ObjectDetector()

def get_detector() -> ObjectDetector:
    """Get the global detector instance"""
    return detector
