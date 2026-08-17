"""Integration tests for recipe suggestions and allergen warnings.

Tests the /v1/recipes/suggest and /v1/meal-plans/{id}/verify allergen
warning functionality using the in-memory SQLite test database.
"""
import pytest
from datetime import date
from app.db.models import (
    InventoryItem, InventoryState, Recipe, RecipeIngredient,
    HouseholdMember, DietaryRestriction, ItemAllergen, MealPlan, MealPlanEntry,
)


def _create_inventory(db, name, count=2, par=4):
    """Helper: create an inventory item with stock."""
    item = InventoryItem(canonical_name=name)
    db.add(item)
    db.flush()
    state = InventoryState(
        item_id=item.id, count_estimate=count, confidence=1.0, par_level=par,
    )
    db.add(state)
    db.flush()
    return item


def _create_recipe(db, name, ingredients):
    """Helper: create a recipe with ingredients."""
    recipe = Recipe(name=name, servings=4)
    db.add(recipe)
    db.flush()
    for i, (ing_name, qty, inv_item) in enumerate(ingredients):
        db.add(RecipeIngredient(
            recipe_id=recipe.id, position=i, quantity=qty,
            name=ing_name, inventory_item_id=inv_item.id if inv_item else None,
        ))
    db.flush()
    return recipe


# ── Recipe Suggestions ────────────────────────────────────────────────

class TestRecipeSuggestions:
    def test_suggest_returns_all_recipes(self, client, db):
        """All recipes with linked ingredients appear in suggestions."""
        beef = _create_inventory(db, "Ground Beef", count=3)
        buns = _create_inventory(db, "Burger Buns", count=8)
        cheese = _create_inventory(db, "Cheddar", count=4)
        tomatoes = _create_inventory(db, "Canned Tomatoes", count=0)

        _create_recipe(db, "Burgers", [
            ("ground beef", "1 lb", beef),
            ("buns", "4", buns),
            ("cheese", "4 slices", cheese),
        ])
        _create_recipe(db, "Pasta", [
            ("tomatoes", "1 can", tomatoes),
            ("spaghetti", "1 box", None),  # untracked
        ])
        db.commit()

        resp = client.get("/v1/recipes/suggest")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["suggestions"]) == 2
        # Burgers should rank higher (3/3 linked in stock vs 0/1)
        assert data["suggestions"][0]["recipe"]["name"] == "Burgers"
        assert data["suggestions"][0]["match_pct"] == 1.0
        assert data["suggestions"][1]["match_pct"] == 0.0

    def test_suggest_exclude_empty_recipes(self, client, db):
        """Recipes with no ingredients are excluded."""
        _create_recipe(db, "Empty Recipe", [])
        db.commit()

        resp = client.get("/v1/recipes/suggest")
        assert resp.status_code == 200
        assert len(resp.json()["suggestions"]) == 0

    def test_suggest_untracked_not_counted_as_missing(self, client, db):
        """Untracked ingredients (no inventory_item_id) don't hurt the score."""
        beef = _create_inventory(db, "Ground Beef", count=3)
        _create_recipe(db, "Burgers", [
            ("ground beef", "1 lb", beef),
            ("salt", None, None),  # untracked — shouldn't count
        ])
        db.commit()

        resp = client.get("/v1/recipes/suggest")
        data = resp.json()
        assert data["suggestions"][0]["match_pct"] == 1.0
        assert data["suggestions"][0]["not_tracked"] == 1
        assert data["suggestions"][0]["missing"] == 0

    def test_suggest_sorted_by_match_pct(self, client, db):
        """Higher match_pct sorts first; ties broken by in_stock count."""
        beef = _create_inventory(db, "Ground Beef", count=3)
        buns = _create_inventory(db, "Buns", count=0)
        cheese = _create_inventory(db, "Cheese", count=4)

        _create_recipe(db, "Partial", [("beef", "1 lb", beef), ("buns", "4", buns)])
        _create_recipe(db, "Full", [("beef", "1 lb", beef), ("cheese", "2 slices", cheese)])
        db.commit()

        resp = client.get("/v1/recipes/suggest")
        names = [s["recipe"]["name"] for s in resp.json()["suggestions"]]
        assert names[0] == "Full"
        assert names[1] == "Partial"


# ── Allergen Warnings ─────────────────────────────────────────────────

class TestAllergenWarnings:
    def test_warning_when_member_allergic(self, client, db):
        """Verify returns allergen_warnings when a member is allergic to an item."""
        beef = _create_inventory(db, "Ground Beef", count=3)
        recipe = _create_recipe(db, "Burgers", [("beef", "1 lb", beef)])

        # Create member with peanut allergy
        member = HouseholdMember(name="Wife", member_relationship="spouse")
        db.add(member)
        db.flush()
        db.add(DietaryRestriction(
            member_id=member.id, restriction_type="allergen",
            allergen="peanuts", severity="severe",
        ))

        # Add peanut allergen to Ground Beef
        db.add(ItemAllergen(
            inventory_item_id=beef.id, allergen="peanuts", is_present=True,
        ))

        # Create meal plan
        plan = MealPlan(week_start=date(2026, 8, 17), name="Test Week")
        db.add(plan)
        db.flush()
        db.add(MealPlanEntry(
            meal_plan_id=plan.id, plan_date=date(2026, 8, 17),
            meal_type="dinner", recipe_id=recipe.id,
        ))
        db.commit()

        resp = client.get(f"/v1/meal-plans/{plan.id}/verify")
        assert resp.status_code == 200
        items = resp.json()["items"]
        beef_item = next(i for i in items if i["inventory_item_id"] == beef.id)
        assert beef_item["allergen_warnings"] is not None
        assert len(beef_item["allergen_warnings"]) == 1
        assert "peanuts" in beef_item["allergen_warnings"][0]
        assert "Wife" in beef_item["allergen_warnings"][0]

    def test_no_warning_when_not_allergic(self, client, db):
        """No warning when member has a different allergy."""
        beef = _create_inventory(db, "Ground Beef", count=3)
        recipe = _create_recipe(db, "Burgers", [("beef", "1 lb", beef)])

        member = HouseholdMember(name="Wife", member_relationship="spouse")
        db.add(member)
        db.flush()
        db.add(DietaryRestriction(
            member_id=member.id, restriction_type="allergen",
            allergen="gluten", severity="moderate",
        ))
        db.add(ItemAllergen(
            inventory_item_id=beef.id, allergen="peanuts", is_present=True,
        ))

        plan = MealPlan(week_start=date(2026, 8, 17), name="Test")
        db.add(plan)
        db.flush()
        db.add(MealPlanEntry(
            meal_plan_id=plan.id, plan_date=date(2026, 8, 17),
            meal_type="dinner", recipe_id=recipe.id,
        ))
        db.commit()

        resp = client.get(f"/v1/meal-plans/{plan.id}/verify")
        items = resp.json()["items"]
        beef_item = next(i for i in items if i["inventory_item_id"] == beef.id)
        assert beef_item["allergen_warnings"] is None

    def test_no_warning_when_no_members(self, client, db):
        """No warnings when no household members exist."""
        beef = _create_inventory(db, "Ground Beef", count=3)
        recipe = _create_recipe(db, "Burgers", [("beef", "1 lb", beef)])
        db.add(ItemAllergen(
            inventory_item_id=beef.id, allergen="peanuts", is_present=True,
        ))

        plan = MealPlan(week_start=date(2026, 8, 17), name="Test")
        db.add(plan)
        db.flush()
        db.add(MealPlanEntry(
            meal_plan_id=plan.id, plan_date=date(2026, 8, 17),
            meal_type="dinner", recipe_id=recipe.id,
        ))
        db.commit()

        resp = client.get(f"/v1/meal-plans/{plan.id}/verify")
        items = resp.json()["items"]
        beef_item = next(i for i in items if i["inventory_item_id"] == beef.id)
        assert beef_item["allergen_warnings"] is None


# ── Household Member API ──────────────────────────────────────────────

class TestHouseholdMembers:
    def test_create_member(self, client, db):
        resp = client.post("/v1/household/members", json={
            "name": "Wife", "relationship": "spouse",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Wife"
        assert data["relationship"] == "spouse"
        assert data["is_active"] is True

    def test_list_members(self, client, db):
        client.post("/v1/household/members", json={"name": "Wife"})
        client.post("/v1/household/members", json={"name": "Kid"})
        resp = client.get("/v1/household/members")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_add_restriction(self, client, db):
        resp = client.post("/v1/household/members", json={"name": "Wife"})
        member_id = resp.json()["id"]
        resp = client.post(f"/v1/household/members/{member_id}/restrictions", json={
            "restriction_type": "allergen", "allergen": "peanuts", "severity": "severe",
        })
        assert resp.status_code == 200
        assert resp.json()["allergen"] == "peanuts"

    def test_delete_member(self, client, db):
        resp = client.post("/v1/household/members", json={"name": "Wife"})
        member_id = resp.json()["id"]
        resp = client.delete(f"/v1/household/members/{member_id}")
        assert resp.status_code == 204
        # Should be hidden from active list
        resp = client.get("/v1/household/members")
        assert len(resp.json()) == 0
