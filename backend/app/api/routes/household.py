"""Household member management API"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.db.database import get_db
from app.db.models import HouseholdMember, DietaryRestriction, NutritionTarget

router = APIRouter(prefix="/household", tags=["household"])


class MemberCreate(BaseModel):
    name: str
    relationship: Optional[str] = Field(None, description="self, spouse, child, etc")
    birth_date: Optional[date] = None


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    birth_date: Optional[date] = None
    is_active: Optional[bool] = None


class RestrictionCreate(BaseModel):
    restriction_type: str = Field(..., description="allergy, intolerance, preference, medical")
    allergen: Optional[str] = None
    severity: Optional[str] = Field(None, description="mild, moderate, severe, life_threatening")
    notes: Optional[str] = None


class NutritionTargetCreate(BaseModel):
    daily_calories: Optional[int] = None
    daily_protein_g: Optional[float] = None
    daily_carbs_g: Optional[float] = None
    daily_fat_g: Optional[float] = None
    daily_fiber_g: Optional[float] = None
    notes: Optional[str] = None


def _member_dict(m: HouseholdMember) -> dict:
    return {
        "id": m.id,
        "name": m.name,
        "relationship": getattr(m, "member_relationship", None),
        "birth_date": str(m.birth_date) if m.birth_date else None,
        "is_active": m.is_active,
        "created_at": str(m.created_at),
    }


def _restriction_dict(r: DietaryRestriction) -> dict:
    return {
        "id": r.id,
        "member_id": r.member_id,
        "restriction_type": r.restriction_type,
        "allergen": r.allergen,
        "severity": r.severity,
        "notes": r.notes,
        "created_at": str(r.created_at),
    }


def _nutrition_dict(t: NutritionTarget) -> dict:
    return {
        "id": t.id,
        "member_id": t.member_id,
        "daily_calories": t.daily_calories,
        "daily_protein_g": t.daily_protein_g,
        "daily_carbs_g": t.daily_carbs_g,
        "daily_fat_g": t.daily_fat_g,
        "daily_fiber_g": t.daily_fiber_g,
        "notes": t.notes,
        "updated_at": str(t.updated_at),
    }


# Map Pydantic field names → SQLAlchemy column names
_FIELD_MAP = {"relationship": "member_relationship"}


@router.post("/members", status_code=status.HTTP_201_CREATED)
def create_member(member_data: MemberCreate, db: Session = Depends(get_db)):
    """Add a new household member"""
    member = HouseholdMember(
        name=member_data.name,
        member_relationship=member_data.relationship,
        birth_date=member_data.birth_date
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return _member_dict(member)


@router.get("/members")
def list_members(active_only: bool = True, db: Session = Depends(get_db)):
    """List all household members"""
    query = db.query(HouseholdMember)
    if active_only:
        query = query.filter(HouseholdMember.is_active == True)
    return [_member_dict(m) for m in query.all()]


@router.get("/members/{member_id}")
def get_member(member_id: str, db: Session = Depends(get_db)):
    """Get a specific household member"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return _member_dict(member)


@router.patch("/members/{member_id}")
def update_member(member_id: str, update_data: MemberUpdate, db: Session = Depends(get_db)):
    """Update household member details"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    for field, value in update_data.dict(exclude_unset=True).items():
        db_field = _FIELD_MAP.get(field, field)
        setattr(member, db_field, value)

    db.commit()
    db.refresh(member)
    return _member_dict(member)


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_member(member_id: str, db: Session = Depends(get_db)):
    """Soft-delete a household member"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.is_active = False
    db.commit()
    return None


@router.post("/members/{member_id}/restrictions")
def add_restriction(member_id: str, restriction_data: RestrictionCreate, db: Session = Depends(get_db)):
    """Add a dietary restriction/allergy for a member"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    restriction = DietaryRestriction(
        member_id=member_id,
        restriction_type=restriction_data.restriction_type,
        allergen=restriction_data.allergen,
        severity=restriction_data.severity,
        notes=restriction_data.notes
    )
    db.add(restriction)
    db.commit()
    db.refresh(restriction)
    return _restriction_dict(restriction)


@router.get("/members/{member_id}/restrictions")
def list_restrictions(member_id: str, db: Session = Depends(get_db)):
    """List dietary restrictions for a member"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return [_restriction_dict(r) for r in member.restrictions]


@router.post("/members/{member_id}/nutrition")
def set_nutrition_target(member_id: str, target_data: NutritionTargetCreate, db: Session = Depends(get_db)):
    """Set nutrition targets for a household member"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.nutrition_target:
        for field, value in target_data.dict(exclude_unset=True).items():
            setattr(member.nutrition_target, field, value)
    else:
        target = NutritionTarget(member_id=member_id, **target_data.dict())
        db.add(target)

    db.commit()
    db.refresh(member.nutrition_target)
    return _nutrition_dict(member.nutrition_target)


@router.get("/members/{member_id}/nutrition")
def get_nutrition_target(member_id: str, db: Session = Depends(get_db)):
    """Get nutrition targets for a household member"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if not member.nutrition_target:
        raise HTTPException(status_code=404, detail="No nutrition target set")
    return _nutrition_dict(member.nutrition_target)
