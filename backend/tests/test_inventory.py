"""Tests for inventory endpoints"""

from datetime import datetime
from app.db.models import InventoryItem, InventoryState

def test_get_empty_inventory(client):
    """Test getting inventory when empty"""
    response = client.get("/v1/inventory")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert "updated_at" in data

def test_get_inventory_with_items(client, db):
    """Test getting inventory with items"""
    # Create test items
    item1 = InventoryItem(canonical_name="peanut butter", brand="Jif")
    item2 = InventoryItem(canonical_name="pasta", brand="Barilla")
    db.add_all([item1, item2])
    db.flush()
    
    state1 = InventoryState(item_id=item1.id, count_estimate=3, confidence=0.9)
    state2 = InventoryState(item_id=item2.id, count_estimate=2, confidence=0.85)
    db.add_all([state1, state2])
    db.commit()
    
    response = client.get("/v1/inventory")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    
    # Check items are returned
    names = [item["canonical_name"] for item in data["items"]]
    assert "peanut butter" in names
    assert "pasta" in names

def test_inventory_override(client, db):
    """Test manual inventory override"""
    response = client.post(
        "/v1/inventory/override",
        json={
            "item_name": "peanut butter",
            "count_estimate": 5,
            "notes": "manually restocked"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "peanut butter" in data["message"]
    
    # Verify item was created/updated
    response = client.get("/v1/inventory")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["canonical_name"] == "peanut butter"
    assert data["items"][0]["count_estimate"] == 5
    assert data["items"][0]["is_manual"] is True

def test_inventory_history_empty(client):
    """Test inventory history when empty"""
    response = client.get("/v1/inventory/history?days=7")
    assert response.status_code == 200
    data = response.json()
    assert data["events"] == []
    assert data["total_events"] == 0
