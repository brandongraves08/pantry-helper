from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import PreppingGear

router = APIRouter()


class GearCondition(str, Enum):
    GOOD = "Good"
    NEEDS_ATTENTION = "Needs attention"
    UNKNOWN = "Unknown"


class GearInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    quantity: float = Field(default=1, ge=0, allow_inf_nan=False)
    unit: Optional[str] = Field(default=None, max_length=50)
    location: Optional[str] = Field(default=None, max_length=200)
    condition: GearCondition = GearCondition.UNKNOWN
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("name", "category")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class GearPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    quantity: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    unit: Optional[str] = Field(default=None, max_length=50)
    location: Optional[str] = Field(default=None, max_length=200)
    condition: Optional[GearCondition] = None
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("name", "category")
    @classmethod
    def nonblank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            raise ValueError("must not be null")
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("quantity", "condition", mode="before")
    @classmethod
    def required_patch_values(cls, value):
        if value is None:
            raise ValueError("must not be null")
        return value


class GearResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    quantity: float
    unit: Optional[str]
    location: Optional[str]
    condition: str
    notes: Optional[str]


class GearListResponse(BaseModel):
    items: list[GearResponse]
    total: int


@router.get("/gear", response_model=GearListResponse)
def list_gear(db: Session = Depends(get_db)):
    items = db.query(PreppingGear).order_by(PreppingGear.name, PreppingGear.id).all()
    return {"items": items, "total": len(items)}


@router.post("/gear", response_model=GearResponse, status_code=201)
def create_gear(payload: GearInput, db: Session = Depends(get_db)):
    item = PreppingGear(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/gear/{gear_id}", response_model=GearResponse)
def update_gear(gear_id: str, payload: GearPatch, db: Session = Depends(get_db)):
    item = db.query(PreppingGear).filter(PreppingGear.id == gear_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gear item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/gear/{gear_id}", status_code=204)
def delete_gear(gear_id: str, db: Session = Depends(get_db)):
    item = db.query(PreppingGear).filter(PreppingGear.id == gear_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gear item not found")
    db.delete(item)
    db.commit()
