"""Zone-based spatial learning and detection service"""
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.models import Zone, ZonePattern, ZoneDetection, InventoryItem, Observation
from datetime import datetime

logger = logging.getLogger(__name__)

class ZoneService:
    """Manages shelf zones and spatial learning"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_zone(
        self, 
        device_id: str, 
        name: str, 
        x: float, y: float, 
        width: float, height: float,
        expected_item_type: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Zone:
        """Create a new zone on a shelf"""
        zone = Zone(
            device_id=device_id,
            name=name,
            x=x, y=y,
            width=width,
            height=height,
            expected_item_type=expected_item_type,
            notes=notes
        )
        self.db.add(zone)
        self.db.commit()
        self.db.refresh(zone)
        logger.info(f"Created zone {name} for device {device_id}")
        return zone
    
    def get_zones_for_device(self, device_id: str) -> List[Zone]:
        """Get all active zones for a device"""
        return self.db.query(Zone).filter(
            Zone.device_id == device_id,
            Zone.is_active == True
        ).all()
    
    def get_zone_at_location(
        self, 
        device_id: str, 
        x: float, 
        y: float
    ) -> Optional[Zone]:
        """Find which zone contains a point (x,y)"""
        zones = self.get_zones_for_device(device_id)
        for zone in zones:
            if (zone.x <= x <= zone.x + zone.width and 
                zone.y <= y <= zone.y + zone.height):
                return zone
        return None
    
    def update_pattern(
        self, 
        zone_id: str, 
        item_id: str, 
        quantity: int = 1,
        confidence: float = 1.0
    ) -> ZonePattern:
        """Update learned pattern for a zone+item combination"""
        pattern = self.db.query(ZonePattern).filter(
            ZonePattern.zone_id == zone_id,
            ZonePattern.inventory_item_id == item_id
        ).first()
        
        if pattern:
            # Update existing
            pattern.occurrence_count += 1
            pattern.last_seen_at = datetime.utcnow()
            # Weighted average
            old_avg = pattern.avg_quantity or 0
            pattern.avg_quantity = (old_avg * (pattern.occurrence_count - 1) + quantity) / pattern.occurrence_count
            pattern.confidence_score = min(0.95, pattern.confidence_score + 0.05)
        else:
            # Create new
            pattern = ZonePattern(
                zone_id=zone_id,
                inventory_item_id=item_id,
                occurrence_count=1,
                avg_quantity=quantity,
                confidence_score=confidence * 0.5,  # Start lower
                last_seen_at=datetime.utcnow()
            )
            self.db.add(pattern)
        
        self.db.commit()
        self.db.refresh(pattern)
        return pattern
    
    def get_zone_patterns(self, zone_id: str) -> List[ZonePattern]:
        """Get all learned patterns for a zone, sorted by confidence"""
        return self.db.query(ZonePattern).filter(
            ZonePattern.zone_id == zone_id
        ).order_by(ZonePattern.confidence_score.desc()).all()
    
    def infer_item_for_zone(
        self, 
        zone_id: str, 
        detected_class: str
    ) -> Optional[Tuple[InventoryItem, float]]:
        """Infer what item is likely in this zone based on patterns"""
        patterns = self.get_zone_patterns(zone_id)
        
        if not patterns:
            return None
        
        # Get top pattern
        top_pattern = patterns[0]
        
        # High confidence threshold for inference
        if top_pattern.confidence_score >= 0.7:
            item = self.db.query(InventoryItem).filter(
                InventoryItem.id == top_pattern.inventory_item_id
            ).first()
            return (item, top_pattern.confidence_score)
        
        return None
    
    def create_detection(
        self,
        observation_id: str,
        detected_class: str,
        confidence: float,
        bbox: Tuple[float, float, float, float],  # x, y, w, h
        zone_id: Optional[str] = None,
        inferred_item_id: Optional[str] = None,
        inference_confidence: Optional[float] = None
    ) -> ZoneDetection:
        """Record a detection with optional zone/inference info"""
        detection = ZoneDetection(
            observation_id=observation_id,
            zone_id=zone_id,
            detected_class=detected_class,
            confidence=confidence,
            bbox_x=bbox[0],
            bbox_y=bbox[1],
            bbox_w=bbox[2],
            bbox_h=bbox[3],
            inferred_item_id=inferred_item_id,
            inference_confidence=inference_confidence
        )
        self.db.add(detection)
        self.db.commit()
        self.db.refresh(detection)
        return detection
    
    def get_detections_for_observation(self, observation_id: str) -> List[ZoneDetection]:
        """Get all zone-linked detections for an observation"""
        return self.db.query(ZoneDetection).filter(
            ZoneDetection.observation_id == observation_id
        ).all()
