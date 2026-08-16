from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

class IngestRequest(BaseModel):
    """Ingest request from ESP32"""
    device_id: str
    timestamp: datetime
    trigger_type: str  # door, light, timer, manual
    battery_v: float
    rssi: int
    # Image is handled as multipart form data

class CaptureResponse(BaseModel):
    """Response to ingest request"""
    capture_id: str
    status: str
    message: Optional[str] = None


class CaptureDetail(BaseModel):
    id: str
    device_id: str
    trigger_type: str
    captured_at: datetime
    status: str
    error_message: Optional[str] = None
    image_path: str

    latest_observation: Optional[dict] = None

class InventoryItem(BaseModel):
    """Inventory item representation"""
    item_id: Optional[str] = None
    canonical_name: str
    brand: Optional[str] = None
    package_type: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None

    count_estimate: int
    confidence: float
    expiry_date: Optional[str] = None  # ISO date extracted from label
    last_seen_at: datetime

    # Home inventory fields
    location: Optional[str] = None
    expires_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    par_level: Optional[int] = None

    # Brand rating / favorite
    rating: Optional[float] = None
    is_favorite: bool = False

    # HEB enrichment
    heb_product_name: Optional[str] = None
    heb_url: Optional[str] = None
    heb_price: Optional[float] = None
    heb_image_url: Optional[str] = None
    heb_status: Optional[str] = "pending"

    is_manual: bool = False
    notes: Optional[str] = None
    image_url: Optional[str] = None

class InventoryResponse(BaseModel):
    """Full inventory response"""
    items: List[InventoryItem]
    updated_at: datetime
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    has_more: Optional[bool] = None

class ObservationItem(BaseModel):
    """Parsed observation item from OpenAI Vision"""
    name: str
    brand: Optional[str] = None
    package_type: Optional[str] = None
    quantity_estimate: Optional[int] = None
    confidence: float
    expiry_date: Optional[str] = None  # ISO date extracted from label

class VisionOutput(BaseModel):
    scene_type: Optional[str] = None
    """OpenAI Vision API response structure"""
    scene_confidence: float
    items: List[ObservationItem]
    notes: Optional[str] = None

class InventoryOverride(BaseModel):
    """Manual inventory correction"""
    item_name: str
    count_estimate: int
    notes: Optional[str] = None
    location: Optional[str] = None
    expires_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    par_level: Optional[int] = None
    brand: Optional[str] = None
    rating: Optional[float] = None
    is_favorite: Optional[bool] = None


class InventoryVerifyRequest(BaseModel):
    """User-confirmed count for an inventory item."""
    count_estimate: int
    notes: Optional[str] = None


class HebEnrichmentPayload(BaseModel):
    """HEB product info pulled from heb.com for an inventory item."""
    product_name: Optional[str] = None
    url: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None


class FlagCreate(BaseModel):
    """User-reported issue on an inventory item."""
    field: Optional[str] = None  # image | brand | count | name | other
    reason: str


class VoiceShoppingAdd(BaseModel):
    """Add an item to the shopping list by name (Alexa/voice path)."""
    item_name: str
    quantity: int = 1


class FlagResolve(BaseModel):
    """Mark a flag resolved (after the agent/admin fixed the underlying issue)."""
    resolution_note: Optional[str] = None


class FlagResponse(BaseModel):
    """An inventory flag as returned by the API."""
    id: str
    item_id: str
    canonical_name: Optional[str] = None
    field: Optional[str] = None
    reason: str
    status: str  # open | resolved
    resolution_note: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class ShoppingListItem(BaseModel):
    item_name: str
    needed: int
    reason: Optional[str] = None
    location: Optional[str] = None


class ShoppingListResponse(BaseModel):
    items: List[ShoppingListItem]
    updated_at: datetime


class ReviewRequest(BaseModel):
    capture_id: str
    notes: Optional[str] = None


class ReviewResponse(BaseModel):
    id: str
    capture_id: str
    status: str
    notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

# Barcode Schemas

class BarcodeLookupRequest(BaseModel):
    """Request to look up a barcode."""
    barcode: str


class BarcodeLookupNutrition(BaseModel):
    energy_kcal: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_g: Optional[float] = None
    sugars_g: Optional[float] = None


class BarcodeLookupResult(BaseModel):
    """Result of a barcode lookup."""
    barcode: str
    found: bool = False
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    package_type: Optional[str] = None
    image_url: Optional[str] = None
    quantity: Optional[str] = None
    serving_size: Optional[str] = None
    nutrition: Optional[BarcodeLookupNutrition] = None
    allergens: list[str] = []
    ingredients_text: Optional[str] = None
    already_in_inventory: bool = False
    existing_item_name: Optional[str] = None
    source: str = "openfoodfacts"


class BarcodeLinkRequest(BaseModel):
    """Link a barcode to an inventory item."""
    barcode: str
    inventory_item_name: str


class BarcodeLinkResponse(BaseModel):
    """Response after linking barcode to an item."""
    success: bool
    barcode: str
    inventory_item_name: str
    message: str


class BarcodeAddToInventoryRequest(BaseModel):
    """Add a barcode-scanned product directly to inventory."""
    barcode: str
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    package_type: Optional[str] = None
    quantity_estimate: int = 1
    par_level: Optional[int] = None
    expires_at: Optional[datetime] = None


# Recipe Schemas

class RecipeIngredientInput(BaseModel):
    """An ingredient line in a recipe."""
    quantity: Optional[str] = None
    name: str
    note: Optional[str] = None
    inventory_item_id: Optional[str] = None


class RecipeCreate(BaseModel):
    """Request to create or update a recipe."""
    name: str
    description: Optional[str] = None
    source: Optional[str] = None
    servings: Optional[int] = None
    prep_time_min: Optional[int] = None
    cook_time_min: Optional[int] = None
    instructions: Optional[str] = None
    rating: Optional[float] = None
    is_favorite: Optional[bool] = False
    ingredients: Optional[List[RecipeIngredientInput]] = []


class RecipeIngredient(BaseModel):
    """An ingredient line as returned in a recipe."""
    id: str
    position: int
    quantity: Optional[str] = None
    name: str
    note: Optional[str] = None
    inventory_item_id: Optional[str] = None
    inventory_item_name: Optional[str] = None


class Recipe(BaseModel):
    """A saved recipe."""
    id: str
    name: str
    description: Optional[str] = None
    source: Optional[str] = None
    servings: Optional[int] = None
    prep_time_min: Optional[int] = None
    cook_time_min: Optional[int] = None
    instructions: Optional[str] = None
    rating: Optional[float] = None
    is_favorite: Optional[bool] = False
    ingredients: List[RecipeIngredient] = []
    created_at: datetime
    updated_at: datetime


class RecipeListResponse(BaseModel):
    """List of recipes."""
    recipes: List[Recipe]
    total: int


# Device Management Schemas

class DeviceCreate(BaseModel):
    """Request to create a new device"""
    name: str
    device_id: Optional[str] = None  # Auto-generated if not provided


class DeviceUpdate(BaseModel):
    """Request to update device settings"""
    name: Optional[str] = None
    enabled: Optional[bool] = None


class DeviceResponse(BaseModel):
    """Device information response"""
    id: str
    name: str
    created_at: datetime
    last_seen_at: Optional[datetime] = None
    battery_v: Optional[float] = None
    battery_pct: Optional[float] = None
    rssi: Optional[int] = None
    total_captures: int = 0
    failed_uploads: int = 0
    status: str  # active, idle, inactive, offline
    device_token: Optional[str] = None  # Only returned on creation


class DeviceListResponse(BaseModel):
    """Paginated list of devices"""
    items: List[DeviceResponse]
    total: int
    skip: int
    limit: int


class DeviceHealthResponse(BaseModel):
    """Detailed device health metrics"""
    device_id: str
    is_healthy: bool
    battery_v: Optional[float] = None
    battery_pct: Optional[float] = None
    rssi: Optional[int] = None
    last_seen_at: Optional[datetime] = None
    last_seen_ago_seconds: Optional[int] = None
    total_captures: int
    captures_7d: int
    captures_24h: int
    successful_7d: int
    failed_7d: int
    analyzing_7d: int
    success_rate_7d: float


# ── Meal Plan Schemas ────────────────────────────────────────────────

class MealPlanCreate(BaseModel):
    """Create a weekly meal plan."""
    week_start: date  # Monday of the plan week
    name: Optional[str] = None


class MealPlanEntryInput(BaseModel):
    """Schedule a recipe on a specific day/meal slot."""
    plan_date: date
    meal_type: str  # breakfast | lunch | dinner | snack
    recipe_id: str
    servings_multiplier: int = 1
    notes: Optional[str] = None


class MealPlanEntryResponse(BaseModel):
    """A single scheduled meal."""
    id: str
    plan_date: date
    meal_type: str
    recipe_id: str
    recipe_name: Optional[str] = None
    servings_multiplier: int = 1
    notes: Optional[str] = None


class MealPlanResponse(BaseModel):
    """A meal plan with its entries."""
    id: str
    week_start: date
    name: Optional[str] = None
    entries: List[MealPlanEntryResponse] = []
    created_at: datetime
    updated_at: datetime


class MealPlanListResponse(BaseModel):
    """List of meal plans."""
    plans: List[MealPlanResponse]
    total: int


class MealPlanItemNeed(BaseModel):
    """One ingredient's stock status across all planned meals."""
    name: str
    quantity: Optional[str] = None
    inventory_item_id: Optional[str] = None
    inventory_item_name: Optional[str] = None
    required_units: Optional[float] = None
    available_units: Optional[float] = None
    missing_units: Optional[float] = None
    status: str  # ok | short | not_tracked
    approx: bool = False  # True when quantity math is a heuristic (weight/volume units)
    sources: List[dict] = []  # [{date, meal_type, recipe, quantity, servings_multiplier}]


class MealPlanVerifyResponse(BaseModel):
    """Aggregated verification of a meal plan against pantry stock."""
    plan_id: str
    week_start: date
    start: date
    end: date
    items: List[MealPlanItemNeed]
    summary: dict  # {ok, short, not_tracked, total}
    updated_at: datetime


class MealPlanUpdateShoppingResponse(BaseModel):
    """Result of merging missing meal-plan items into the shopping list."""
    plan_id: str
    added: int
    items: List[MealPlanItemNeed]
    updated_at: datetime