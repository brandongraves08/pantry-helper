from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.database import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    token_hash = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    last_battery_v = Column(Float, nullable=True)
    last_rssi = Column(Integer, nullable=True)

    captures = relationship("Capture", back_populates="device")

class Capture(Base):
    __tablename__ = "captures"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String, ForeignKey("devices.id"), nullable=False)
    trigger_type = Column(String, nullable=False)  # door, light, timer, manual
    captured_at = Column(DateTime(timezone=True), nullable=False)
    image_path = Column(String, nullable=False)
    battery_v = Column(Float, nullable=True)
    rssi = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default="stored")  # stored, analyzing, complete, failed
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    device = relationship("Device", back_populates="captures")
    observations = relationship("Observation", back_populates="capture")

class Observation(Base):
    __tablename__ = "observations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    capture_id = Column(String, ForeignKey("captures.id"), nullable=False)
    raw_json = Column(JSON, nullable=False)
    scene_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    capture = relationship("Capture", back_populates="observations")

class Location(Base):
    __tablename__ = "locations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    parent_id = Column(String, ForeignKey("locations.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parent = relationship("Location", remote_side=[id], backref="children")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_name = Column(String, nullable=False, unique=True)
    brand = Column(String, nullable=True)
    package_type = Column(String, nullable=True)
    category = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    states = relationship("InventoryState", back_populates="item")
    events = relationship("InventoryEvent", back_populates="item")

class InventoryState(Base):
    __tablename__ = "inventory_state"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = Column(String, ForeignKey("inventory_items.id"), nullable=False)
    location_id = Column(String, ForeignKey("locations.id"), nullable=True)

    count_estimate = Column(Integer, nullable=False, default=0)
    confidence = Column(Float, nullable=False, default=0.0)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    # Home inventory fields
    expires_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    par_level = Column(Integer, nullable=True)

    is_manual = Column(Boolean, nullable=False, default=False)
    notes = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    item = relationship("InventoryItem", back_populates="states")
    location = relationship("Location")

class InventoryEvent(Base):
    __tablename__ = "inventory_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = Column(String, ForeignKey("inventory_items.id"), nullable=False)
    capture_id = Column(String, ForeignKey("captures.id"), nullable=True)
    event_type = Column(String, nullable=False)  # seen, adjusted, manual_override
    delta = Column(Integer, nullable=False, default=0)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    item = relationship("InventoryItem", back_populates="events")


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = Column(String, ForeignKey("inventory_items.id"), nullable=False)
    location_id = Column(String, ForeignKey("locations.id"), nullable=True)
    needed = Column(Integer, nullable=False, default=0)
    reason = Column(String, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    item = relationship("InventoryItem")
    location = relationship("Location")


class InventoryReview(Base):
    __tablename__ = "inventory_reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    capture_id = Column(String, ForeignKey("captures.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending/approved/rejected
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    capture = relationship("Capture")
