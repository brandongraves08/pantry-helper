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


class MemberResponse(BaseModel):
    id: str
    name: str
    relationship: Optional[str]
    birth_date: Optional[str]
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class RestrictionCreate(BaseModel):
    restriction_type: str = Field(..., description="allergy, intolerance, preference, medical")
    allergen: Optional[str] = None
    severity: Optional[str] = Field(None, description="mild, moderate, severe, life_threatening")
    notes: Optional[str] = None


class RestrictionResponse(BaseModel):
    id: str
    member_id: str
    restriction_type: str
    allergen: Optional[str]
    severity: Optional[str]
    notes: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class NutritionTargetCreate(BaseModel):
    daily_calories: Optional[int] = None
    daily_protein_g: Optional[float] = None
    daily_carbs_g: Optional[float] = None
    daily_fat_g: Optional[float] = None
    daily_fiber_g: Optional[float] = None
    notes: Optional[str] = None


class NutritionTargetResponse(BaseModel):
    id: str
    member_id: str
    daily_calories: Optional[int]
    daily_protein_g: Optional[float]
    daily_carbs_g: Optional[float]
    daily_fat_g: Optional[float]
    daily_fiber_g: Optional[float]
    notes: Optional[str]
    updated_at: str

    class Config:
        from_attributes = True


@router.post("/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def create_member(member_data: MemberCreate, db: Session = Depends(get_db)):
    """Add a new household member"""
    member = HouseholdMember(
        name=member_data.name,
        relationship=member_data.relationship,
        birth_date=member_data.birth_date
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get("/members", response_model=List[MemberResponse])
def list_members(active_only: bool = True, db: Session = Depends(get_db)):
    """List all household members"""
    query = db.query(HouseholdMember)
    if active_only:
        query = query.filter(HouseholdMember.is_active == True)
    return query.all()


@router.get("/members/{member_id}", response_model=MemberResponse)
def get_member(member_id: str, db: Session = Depends(get_db)):
    """Get a specific household member"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.patch("/members/{member_id}", response_model=MemberResponse)
def update_member(member_id: str, update_data: MemberUpdate, db: Session = Depends(get_db)):
    """Update household member details"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(member, field, value)

    db.commit()
    db.refresh(member)
    return member


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_member(member_id: str, db: Session = Depends(get_db)):
    """Soft-delete a household member"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.is_active = False
    db.commit()
    return None


@router.post("/members/{member_id}/restrictions", response_model=RestrictionResponse)
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
    return restriction


@router.get("/members/{member_id}/restrictions", response_model=List[RestrictionResponse])
def list_restrictions(member_id: str, db: Session = Depends(get_db)):
    """List dietary restrictions for a member"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member.restrictions


@router.post("/members/{member_id}/nutrition", response_model=NutritionTargetResponse)
def set_nutrition_target(member_id: str, target_data: NutritionTargetCreate, db: Session = Depends(get_db)):
    """Set nutrition targets for a household member"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Update existing or create new
    if member.nutrition_target:
        for field, value in target_data.dict(exclude_unset=True).items():
            setattr(member.nutrition_target, field, value)
    else:
        target = NutritionTarget(member_id=member_id, **target_data.dict())
        db.add(target)

    db.commit()
    db.refresh(member.nutrition_target)
    return member.nutrition_target


@router.get("/members/{member_id}/nutrition", response_model=NutritionTargetResponse)
def get_nutrition_target(member_id: str, db: Session = Depends(get_db)):
    """Get nutrition targets for a household member"""
    member = db.query(HouseholdMember).filter_by(id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if not member.nutrition_target:
        raise HTTPException(status_code=404, detail="No nutrition target set")
    return member.nutrition_target
