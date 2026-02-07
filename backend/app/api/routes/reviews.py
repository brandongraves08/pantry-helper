from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Capture, InventoryReview
from app.models.schemas import ReviewRequest, ReviewResponse

router = APIRouter()


@router.post("/reviews", response_model=ReviewResponse)
async def create_review(req: ReviewRequest, db: Session = Depends(get_db)):
    """Create a manual verification task for a given capture (camera check)."""
    cap = db.query(Capture).filter(Capture.id == req.capture_id).first()
    if not cap:
        raise HTTPException(status_code=404, detail="Capture not found")

    review = InventoryReview(capture_id=req.capture_id, status="pending", notes=req.notes)
    db.add(review)
    db.commit()
    db.refresh(review)

    return ReviewResponse(
        id=review.id,
        capture_id=review.capture_id,
        status=review.status,
        notes=review.notes,
        created_at=review.created_at,
        resolved_at=review.resolved_at,
    )


@router.get("/reviews/pending", response_model=list[ReviewResponse])
async def list_pending_reviews(db: Session = Depends(get_db)):
    rows = (
        db.query(InventoryReview)
        .filter(InventoryReview.status == "pending")
        .order_by(InventoryReview.created_at.asc())
        .all()
    )
    return [
        ReviewResponse(
            id=r.id,
            capture_id=r.capture_id,
            status=r.status,
            notes=r.notes,
            created_at=r.created_at,
            resolved_at=r.resolved_at,
        )
        for r in rows
    ]


@router.post("/reviews/{review_id}/{action}", response_model=ReviewResponse)
async def resolve_review(review_id: str, action: str, db: Session = Depends(get_db)):
    """Resolve a manual check.

    - approve: queues processing for the capture (best-effort) and marks review approved.
    - reject: marks review rejected.
    """
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Action must be approve|reject")

    review = db.query(InventoryReview).filter(InventoryReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if action == "approve":
        # Best-effort: queue the capture for processing so "approve" actually does something.
        # If Celery/broker is down, we still mark approved.
        task_id = None
        try:
            from app.workers.celery_app import process_image_capture

            task = process_image_capture.delay(review.capture_id)
            task_id = getattr(task, "id", None)
        except Exception:
            task_id = None

        if task_id:
            review.notes = (review.notes or "") + ("\n" if review.notes else "") + f"queued task: {task_id}"

        review.status = "approved"
    else:
        review.status = "rejected"

    review.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(review)

    return ReviewResponse(
        id=review.id,
        capture_id=review.capture_id,
        status=review.status,
        notes=review.notes,
        created_at=review.created_at,
        resolved_at=review.resolved_at,
    )
