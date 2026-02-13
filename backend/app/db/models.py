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
    zones = relationship("Zone", back_populates="device")

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
    zone_detections = relationship("ZoneDetection", back_populates="observation")

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

class Zone(Base):
    """Spatial zones on shelves for ML learning"""
    __tablename__ = "zones"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String, ForeignKey("devices.id"), nullable=False)
    name = Column(String, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    expected_item_type = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    device = relationship("Device", back_populates="zones")

class ZonePattern(Base):
    """Learned patterns per zone"""
    __tablename__ = "zone_patterns"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    inventory_item_id = Column(String, ForeignKey("inventory_items.id"), nullable=False)
    occurrence_count = Column(Integer, default=0)
    avg_quantity = Column(Float, nullable=True)
    confidence_score = Column(Float, default=0.0)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ZoneDetection(Base):
    """Detections linked to specific zones"""
    __tablename__ = "zone_detections"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    observation_id = Column(String, ForeignKey("observations.id"), nullable=False)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=True)
    detected_class = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    bbox_x = Column(Float, nullable=False)
    bbox_y = Column(Float, nullable=False)
    bbox_w = Column(Float, nullable=False)
    bbox_h = Column(Float, nullable=False)
    inferred_item_id = Column(String, ForeignKey("inventory_items.id"), nullable=True)
    inference_confidence = Column(Float, nullable=True)
    is_manual_override = Column(Boolean, default=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    observation = relationship("Observation", back_populates="zone_detections")
    zone = relationship("Zone")
    inferred_item = relationship("InventoryItem")

class HouseholdMember(Base):
    """Household member profiles for nutrition/allergen tracking"""
    __tablename__ = "household_members"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    member_relationship = Column(String, nullable=True)  # self, spouse, child, etc
    birth_date = Column(DateTime(timezone=True), nullable=True)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    restrictions = relationship("DietaryRestriction", back_populates="member")
    nutrition_target = relationship("NutritionTarget", back_populates="member", uselist=False)
    consumption_events = relationship("ConsumptionEvent", back_populates="member")


class DietaryRestriction(Base):
    """Allergies, intolerances, preferences per member"""
    __tablename__ = "dietary_restrictions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id = Column(String, ForeignKey("household_members.id"), nullable=False)
    restriction_type = Column(String, nullable=False)  # allergy, intolerance, preference, medical
    allergen = Column(String, nullable=True)  # peanuts, dairy, gluten, etc
    severity = Column(String, nullable=True)  # mild, moderate, severe, life_threatening
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    member = relationship("HouseholdMember", back_populates="restrictions")


class NutritionTarget(Base):
    """Daily nutrition targets per member"""
    __tablename__ = "nutrition_targets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id = Column(String, ForeignKey("household_members.id"), nullable=False)
    daily_calories = Column(Integer, nullable=True)
    daily_protein_g = Column(Float, nullable=True)
    daily_carbs_g = Column(Float, nullable=True)
    daily_fat_g = Column(Float, nullable=True)
    daily_fiber_g = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    member = relationship("HouseholdMember", back_populates="nutrition_target")


class NutritionFact(Base):
    """Nutrition facts per inventory item"""
    __tablename__ = "nutrition_facts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    inventory_item_id = Column(String, ForeignKey("inventory_items.id"), nullable=False)
    source = Column(String, nullable=True)  # usda, manual, barcode
    serving_size = Column(String, nullable=True)
    calories_per_serving = Column(Integer, nullable=True)
    protein_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)
    fiber_g = Column(Float, nullable=True)
    sodium_mg = Column(Float, nullable=True)
    sugar_g = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    item = relationship("InventoryItem", back_populates="nutrition_facts", uselist=False)


class ItemAllergen(Base):
    """Allergens present in inventory items (Big 9 + custom)"""
    __tablename__ = "item_allergens"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    inventory_item_id = Column(String, ForeignKey("inventory_items.id"), nullable=False)
    allergen = Column(String, nullable=False)  # peanuts, tree_nuts, milk, eggs, fish, shellfish, wheat, soy, sesame
    is_present = Column(Boolean, default=True)  # True=contains, False=may_contain
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    item = relationship("InventoryItem", back_populates="allergens")


class ConsumptionEvent(Base):
    """Track what household members consume (for supply forecasting)"""
    __tablename__ = "consumption_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id = Column(String, ForeignKey("household_members.id"), nullable=False)
    inventory_item_id = Column(String, ForeignKey("inventory_items.id"), nullable=False)
    quantity_used = Column(Float, nullable=False)  # servings consumed
    consumed_at = Column(DateTime(timezone=True), nullable=False)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(String, nullable=True)  # e.g., "breakfast"
    
    member = relationship("HouseholdMember", back_populates="consumption_events")
    item = relationship("InventoryItem", back_populates="consumption_events")


# Add relationship to InventoryItem
InventoryItem.nutrition_facts = relationship("NutritionFact", back_populates="item", uselist=False)
InventoryItem.allergens = relationship("ItemAllergen", back_populates="item")
InventoryItem.consumption_events = relationship("ConsumptionEvent", back_populates="item")
