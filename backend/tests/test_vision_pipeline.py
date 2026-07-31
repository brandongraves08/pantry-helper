"""Tests for vision pipeline improvements — confidence tuning and expiry OCR."""

from app.models.schemas import VisionOutput, ObservationItem


def test_observation_item_supports_expiry():
    """Test that ObservationItem schema accepts expiry_date field."""
    item = ObservationItem(
        name="milk",
        brand="Horizon",
        package_type="bottle",
        quantity_estimate=1,
        confidence=0.9,
        expiry_date="2026-07-30",
    )
    assert item.expiry_date == "2026-07-30"
    assert item.name == "milk"


def test_observation_item_expiry_optional():
    """Test that expiry_date is optional (null by default)."""
    item = ObservationItem(
        name="peanut butter",
        confidence=0.85,
    )
    assert item.expiry_date is None


def test_vision_output_supports_scene_type():
    """Test that VisionOutput accepts scene_type field."""
    items = [ObservationItem(name="yogurt", confidence=0.9, expiry_date="2026-07-25")]
    output = VisionOutput(
        scene_type="refrigerator",
        scene_confidence=0.85,
        items=items,
        notes="Fridge shelf",
    )
    assert output.scene_type == "refrigerator"
    assert output.items[0].expiry_date == "2026-07-25"


def test_vision_output_supports_expiry_in_items():
    """Test that VisionOutput items can carry expiry_date."""
    items = [
        ObservationItem(name="milk", confidence=0.95, expiry_date="2026-07-30"),
        ObservationItem(name="yogurt", confidence=0.85, expiry_date="2026-07-25"),
    ]
    output = VisionOutput(
        scene_type="refrigerator",
        scene_confidence=0.88,
        items=items,
    )
    assert len(output.items) == 2
    assert output.items[0].expiry_date == "2026-07-30"
    assert output.items[1].expiry_date == "2026-07-25"


def test_vision_output_serialize_deserialize():
    """Test that VisionOutput round-trips through JSON with all new fields."""
    items = [ObservationItem(name="milk", confidence=0.95, expiry_date="2026-07-30")]
    output = VisionOutput(
        scene_type="refrigerator",
        scene_confidence=0.88,
        items=items,
    )
    serialized = output.model_dump(mode="json")
    assert serialized["scene_type"] == "refrigerator"
    assert serialized["items"][0]["expiry_date"] == "2026-07-30"
    deserialized = VisionOutput(**serialized)
    assert deserialized.scene_type == "refrigerator"
    assert deserialized.items[0].expiry_date == "2026-07-30"


def test_vision_output_scene_type_default_none():
    """Test that scene_type defaults to None."""
    output = VisionOutput(scene_confidence=0.0, items=[])
    assert output.scene_type is None


def test_vision_prompt_contains_calibration():
    """Test that the vision prompt includes confidence calibration."""
    from app.services.vision import VisionAnalyzer
    analyzer = VisionAnalyzer(provider="mock")
    prompt = analyzer._build_prompt()
    assert "CONFIDENCE 0.9" in prompt
    assert "CONFIDENCE 0.7" in prompt
    assert "CONFIDENCE 0.4" in prompt
    assert "SCENE CONFIDENCE" in prompt
    assert "Never round confidence up" in prompt


def test_vision_prompt_contains_scene_type():
    """Test that the vision prompt includes scene_type."""
    from app.services.vision import VisionAnalyzer
    analyzer = VisionAnalyzer(provider="mock")
    prompt = analyzer._build_prompt()
    assert "scene_type" in prompt
    assert "pantry_shelf" in prompt
    assert "refrigerator" in prompt


def test_vision_prompt_contains_expiry():
    """Test that the vision prompt includes expiry date extraction."""
    from app.services.vision import VisionAnalyzer
    analyzer = VisionAnalyzer(provider="mock")
    prompt = analyzer._build_prompt()
    assert "expiry_date" in prompt
    assert "YYYY-MM-DD" in prompt


def test_vision_prompt_json_structure():
    """Test that the prompt describes a valid JSON structure matching our schema."""
    from app.services.vision import VisionAnalyzer
    analyzer = VisionAnalyzer(provider="mock")
    prompt = analyzer._build_prompt()
    fields = ["scene_type", "scene_confidence", "items", "name",
              "brand", "package_type", "quantity_estimate", "confidence",
              "expiry_date", "notes"]
    for field in fields:
        assert field in prompt, f"Prompt missing field: {field}"
