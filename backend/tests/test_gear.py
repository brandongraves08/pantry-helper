def test_gear_crud_and_defaults(client):
    created = client.post(
        "/v1/gear",
        json={
            "name": "Camp stove",
            "category": "Outdoor cooking / DIY",
            "quantity": 1,
            "location": "Garage shelf",
            "notes": "Backup kit",
        },
    )
    assert created.status_code == 201
    item = created.json()
    assert item["name"] == "Camp stove"
    assert item["category"] == "Outdoor cooking / DIY"
    assert item["quantity"] == 1
    assert item["location"] == "Garage shelf"
    assert item["notes"] == "Backup kit"
    assert item["condition"] == "Unknown"
    assert item["unit"] is None

    listed = client.get("/v1/gear")
    assert listed.status_code == 200
    assert listed.json() == {"items": [item], "total": 1}

    category = "Field repairs / improvised kit"
    category_updated = client.patch(
        f"/v1/gear/{item['id']}", json={"category": category}
    )
    assert category_updated.status_code == 200
    assert category_updated.json()["category"] != item["category"]
    assert category_updated.json()["category"] == category
    assert client.get("/v1/gear").json()["items"][0]["category"] == category

    updated = client.patch(
        f"/v1/gear/{item['id']}",
        json={
            "quantity": 2,
            "unit": "¾-inch NPT fittings / Wh·h",
            "location": "Basement bin",
            "condition": "Needs attention",
            "notes": "Checked and ready",
        },
    )
    assert updated.status_code == 200
    assert (
        client.patch(f"/v1/gear/{item['id']}", json={"quantity": None}).status_code
        == 422
    )
    assert (
        client.patch(f"/v1/gear/{item['id']}", json={"condition": None}).status_code
        == 422
    )
    assert (
        client.patch(f"/v1/gear/{item['id']}", json={"quantity": "NaN"}).status_code
        == 422
    )
    assert (
        client.patch(f"/v1/gear/{item['id']}", json={"condition": "Broken"}).status_code
        == 422
    )
    assert (
        client.patch(f"/v1/gear/{item['id']}", json={"quantity": -1}).status_code == 422
    )
    unchanged = client.get("/v1/gear").json()["items"][0]
    assert unchanged == updated.json()
    assert updated.json()["quantity"] == 2
    assert updated.json()["unit"] == "¾-inch NPT fittings / Wh·h"
    assert updated.json()["location"] == "Basement bin"
    assert updated.json()["notes"] == "Checked and ready"
    assert updated.json()["condition"] == "Needs attention"
    assert updated.json()["name"] == "Camp stove"
    good = client.patch(f"/v1/gear/{item['id']}", json={"condition": "Good"})
    assert good.status_code == 200
    assert good.json()["condition"] == "Good"
    reloaded = client.get("/v1/gear").json()["items"][0]
    assert reloaded["location"] == "Basement bin"
    assert reloaded["notes"] == "Checked and ready"
    assert reloaded["unit"] == "¾-inch NPT fittings / Wh·h"

    deleted = client.delete(f"/v1/gear/{item['id']}")
    assert deleted.status_code == 204
    assert client.get("/v1/gear").json() == {"items": [], "total": 0}


def test_gear_rejects_invalid_input_and_missing_ids(client):
    assert (
        client.post(
            "/v1/gear", json={"name": "   ", "category": "Fuel", "quantity": 1}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/v1/gear",
            json={"name": "Fuel canister", "category": "Fuel", "quantity": -1},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/v1/gear",
            json={
                "name": "Fuel canister",
                "category": "Fuel",
                "quantity": 1,
                "condition": "Broken",
            },
        ).status_code
        == 422
    )
    assert client.patch("/v1/gear/missing", json={"name": "Nope"}).status_code == 404
    assert client.delete("/v1/gear/missing").status_code == 404


def test_gear_unit_is_optional_free_text_across_create_edit_and_reload(client):
    optional = client.post(
        "/v1/gear", json={"name": "Fuel canister", "category": "Fuel", "quantity": 1}
    )
    assert optional.status_code == 201
    assert optional.json()["unit"] is None

    label = "¾-inch NPT fittings / Wh·h"
    created = client.post(
        "/v1/gear",
        json={"name": "Adapter kit", "category": "DIY", "quantity": 1, "unit": label},
    )
    assert created.status_code == 201
    assert created.json()["unit"] == label

    edited_label = "scoops / pinches (hand-measured)"
    updated = client.patch(
        f"/v1/gear/{created.json()['id']}", json={"unit": edited_label}
    )
    assert updated.status_code == 200
    assert updated.json()["unit"] == edited_label
    reloaded = {item["id"]: item for item in client.get("/v1/gear").json()["items"]}
    assert reloaded[created.json()["id"]]["unit"] == edited_label
    assert reloaded[optional.json()["id"]]["unit"] is None


def test_gear_crud_does_not_mutate_food_inventory(client, db):
    from app.db.models import InventoryItem, InventoryState

    food = InventoryItem(canonical_name="black beans", brand="Example")
    db.add(food)
    db.flush()
    db.add(InventoryState(item_id=food.id, count_estimate=7, confidence=0.9))
    db.commit()

    def food_snapshot():
        return (
            [
                (row.id, row.canonical_name, row.brand, row.category, row.unit)
                for row in db.query(InventoryItem).all()
            ],
            [
                (row.id, row.item_id, row.count_estimate, row.confidence)
                for row in db.query(InventoryState).all()
            ],
        )

    before = food_snapshot()

    created = client.post(
        "/v1/gear", json={"name": "Camp stove", "category": "Cooking", "quantity": 1}
    )
    assert created.status_code == 201
    gear_id = created.json()["id"]
    assert client.patch(f"/v1/gear/{gear_id}", json={"quantity": 2}).status_code == 200
    assert client.delete(f"/v1/gear/{gear_id}").status_code == 204

    assert food_snapshot() == before
