"""Advanced inventory query endpoints for analytics and reporting."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import InventoryItem, InventoryState, InventoryEvent, Capture
from app.models.schemas import (
    InventoryItem as InventoryItemSchema,
    InventoryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/inventory/stats")
async def get_inventory_statistics(db: Session = Depends(get_db)):
    """
    Get comprehensive inventory statistics and metrics.
    
    Returns:
    - Total items tracked
    - Items with stock
    - Items out of stock
    - Total quantity tracked
    - Average confidence
    """
    logger.info("Getting inventory statistics...")
    
    try:
        # Total items
        total_items = db.query(InventoryItem).count()
        
        # Items by stock status
        states = db.query(InventoryState).all()
        items_in_stock = len([s for s in states if s.count_estimate > 0])
        items_out_of_stock = len([s for s in states if s.count_estimate == 0])
        
        # Aggregate metrics
        total_quantity = sum(s.count_estimate or 0 for s in states)
        avg_confidence = sum(s.confidence for s in states) / len(states) if states else 0.0
        
        # Items by confidence level
        high_confidence = len([s for s in states if s.confidence >= 0.8])
        medium_confidence = len([s for s in states if 0.5 <= s.confidence < 0.8])
        low_confidence = len([s for s in states if s.confidence < 0.5])
        
        return {
            "total_items": total_items,
            "items_in_stock": items_in_stock,
            "items_out_of_stock": items_out_of_stock,
            "total_quantity": total_quantity,
            "avg_confidence": round(avg_confidence, 2),
            "confidence_breakdown": {
                "high": high_confidence,
                "medium": medium_confidence,
                "low": low_confidence,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting inventory stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/items/{item_name}/history")
async def get_item_history(
    item_name: str,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """
    Get detailed history of an inventory item.
    
    Parameters:
    - item_name: Name of the item to track
    - days: Historical data to retrieve (default: 7 days)
    
    Returns:
    - Item metadata
    - Count history over time
    - Confidence trends
    - Recent events
    """
    logger.info(f"Getting history for item: {item_name}")
    
    try:
        # Get item
        item = db.query(InventoryItem).filter_by(
            canonical_name=item_name
        ).first()
        
        if not item:
            raise HTTPException(status_code=404, detail=f"Item not found: {item_name}")
        
        # Get current state
        current_state = db.query(InventoryState).filter_by(
            item_id=item.id
        ).first()
        
        # Get recent events
        cutoff = datetime.utcnow() - timedelta(days=days)
        events = db.query(InventoryEvent).filter(
            InventoryEvent.item_id == item.id,
            InventoryEvent.created_at >= cutoff,
        ).order_by(InventoryEvent.created_at.desc()).all()
        
        # Build history timeline
        timeline = []
        running_count = current_state.count_estimate if current_state else 0
        
        for event in reversed(events):
            running_count -= event.delta  # Reverse to get historical value
            timeline.append({
                "date": event.created_at.isoformat(),
                "count": running_count,
                "event_type": event.event_type,
                "delta": event.delta,
                "details": event.details,
            })
        
        return {
            "item": {
                "id": item.id,
                "canonical_name": item.canonical_name,
                "brand": item.brand,
                "package_type": item.package_type,
            },
            "current": {
                "count": current_state.count_estimate if current_state else 0,
                "confidence": current_state.confidence if current_state else 0.0,
                "last_seen_at": current_state.last_seen_at.isoformat() if current_state and current_state.last_seen_at else None,
                "is_manual": current_state.is_manual if current_state else False,
            },
            "history": timeline,
            "total_events": len(events),
            "days_tracked": days,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting item history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/low-stock")
async def get_low_stock_items(
    threshold: int = Query(1, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get items with stock at or below threshold.
    
    Parameters:
    - threshold: Stock level threshold (default: 1)
    
    Returns:
    - List of low-stock items with current counts
    """
    logger.info(f"Getting low-stock items (threshold={threshold})...")
    
    try:
        low_stock = db.query(InventoryState).filter(
            InventoryState.count_estimate <= threshold
        ).all()
        
        items = []
        for state in low_stock:
            if state.item:
                items.append({
                    "name": state.item.canonical_name,
                    "brand": state.item.brand,
                    "count": state.count_estimate,
                    "confidence": state.confidence,
                    "last_seen_at": state.last_seen_at.isoformat() if state.last_seen_at else None,
                })
        
        return {
            "threshold": threshold,
            "item_count": len(items),
            "items": items,
        }
    except Exception as e:
        logger.error(f"Error getting low-stock items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/stale-items")
async def get_stale_items(
    days_threshold: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """
    Get items not seen for N days (potentially missing or used up).
    
    Parameters:
    - days_threshold: Days since last seen (default: 7)
    
    Returns:
    - List of stale items with last seen date
    """
    logger.info(f"Getting stale items (threshold={days_threshold} days)...")
    
    try:
        cutoff = datetime.utcnow() - timedelta(days=days_threshold)
        
        stale_states = db.query(InventoryState).filter(
            InventoryState.last_seen_at < cutoff
        ).all()
        
        items = []
        for state in stale_states:
            if state.item:
                days_ago = (datetime.utcnow() - state.last_seen_at).days if state.last_seen_at else None
                items.append({
                    "name": state.item.canonical_name,
                    "brand": state.item.brand,
                    "last_count": state.count_estimate,
                    "last_seen_at": state.last_seen_at.isoformat() if state.last_seen_at else None,
                    "days_since_seen": days_ago,
                    "confidence": state.confidence,
                })
        
        return {
            "threshold_days": days_threshold,
            "item_count": len(items),
            "items": sorted(items, key=lambda x: x["days_since_seen"] or 999, reverse=True),
        }
    except Exception as e:
        logger.error(f"Error getting stale items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/recent-changes")
async def get_recent_changes(
    hours: int = Query(24, ge=1, le=168),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get recent inventory changes with timeline.
    
    Parameters:
    - hours: Historical window (default: 24 hours)
    - event_type: Filter by type (seen, adjusted, manual_override, or None for all)
    
    Returns:
    - Timeline of recent inventory events
    """
    logger.info(f"Getting recent changes (hours={hours}, type={event_type})...")
    
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(InventoryEvent).filter(
            InventoryEvent.created_at >= cutoff
        )
        
        if event_type:
            query = query.filter(InventoryEvent.event_type == event_type)
        
        events = query.order_by(InventoryEvent.created_at.desc()).all()
        
        changes = []
        for event in events:
            changes.append({
                "timestamp": event.created_at.isoformat(),
                "item_name": event.item.canonical_name if event.item else None,
                "event_type": event.event_type,
                "delta": event.delta,
                "details": event.details,
                "capture_id": event.capture_id,
            })
        
        return {
            "hours": hours,
            "event_type_filter": event_type,
            "event_count": len(changes),
            "changes": changes,
        }
    except Exception as e:
        logger.error(f"Error getting recent changes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/export")
async def export_inventory(
    format: str = Query("json", regex="^(json|csv)$"),
    include_history: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Export inventory in various formats.
    
    Parameters:
    - format: Output format (json or csv)
    - include_history: Include full event history
    
    Returns:
    - Inventory data in requested format
    """
    logger.info(f"Exporting inventory (format={format}, history={include_history})...")
    
    try:
        states = db.query(InventoryState).all()
        
        if format == "json":
            items = []
            for state in states:
                item_data = {
                    "name": state.item.canonical_name if state.item else None,
                    "brand": state.item.brand if state.item else None,
                    "package_type": state.item.package_type if state.item else None,
                    "count": state.count_estimate,
                    "confidence": state.confidence,
                    "last_seen": state.last_seen_at.isoformat() if state.last_seen_at else None,
                    "is_manual": state.is_manual,
                }
                
                if include_history:
                    events = db.query(InventoryEvent).filter_by(
                        item_id=state.item_id
                    ).order_by(InventoryEvent.created_at.desc()).limit(10).all()
                    item_data["recent_events"] = [
                        {
                            "date": e.created_at.isoformat(),
                            "type": e.event_type,
                            "delta": e.delta,
                        }
                        for e in events
                    ]
                
                items.append(item_data)
            
            return {
                "format": "json",
                "exported_at": datetime.utcnow().isoformat(),
                "item_count": len(items),
                "items": items,
            }
        
        elif format == "csv":
            # Return CSV as string
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=["name", "brand", "package_type", "count", "confidence", "last_seen", "manual"]
            )
            writer.writeheader()
            
            for state in states:
                writer.writerow({
                    "name": state.item.canonical_name if state.item else "",
                    "brand": state.item.brand if state.item else "",
                    "package_type": state.item.package_type if state.item else "",
                    "count": state.count_estimate,
                    "confidence": round(state.confidence, 2),
                    "last_seen": state.last_seen_at.isoformat() if state.last_seen_at else "",
                    "manual": "yes" if state.is_manual else "no",
                })
            
            return {
                "format": "csv",
                "content": output.getvalue(),
                "item_count": len(states),
            }
    
    except Exception as e:
        logger.error(f"Error exporting inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
