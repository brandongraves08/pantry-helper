"""Tests for supply forecast and consumption endpoints."""
import pytest
from datetime import datetime, timedelta, date
from app.db.models import (
    InventoryItem, InventoryState, ConsumptionEvent, HouseholdMember,
)


def _create_item(db, name, count=5, par=10):
    item = InventoryItem(canonical_name=name)
    db.add(item)
    db.flush()
    state = InventoryState(
        item_id=item.id, count_estimate=count, confidence=1.0, par_level=par,
    )
    db.add(state)
    db.flush()
    return item


def _create_member(db, name="Wife"):
    member = HouseholdMember(name=name, member_relationship="spouse")
    db.add(member)
    db.flush()
    return member


class TestRecordConsumption:
    def test_record_consumption(self, client, db):
        item = _create_item(db, "Milk")
        member = _create_member(db)
        db.commit()

        resp = client.post("/v1/consumption", json={
            "member_id": member.id,
            "inventory_item_id": item.id,
            "quantity_used": 1.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["quantity_used"] == 1.0
        assert data["member_id"] == member.id

    def test_record_consumption_with_date(self, client, db):
        item = _create_item(db, "Milk")
        member = _create_member(db)
        db.commit()

        resp = client.post("/v1/consumption", json={
            "member_id": member.id,
            "inventory_item_id": item.id,
            "quantity_used": 2.0,
            "consumed_at": "2026-08-01T12:00:00",
            "notes": "breakfast",
        })
        assert resp.status_code == 200
        assert resp.json()["notes"] == "breakfast"

    def test_record_consumption_missing_fields(self, client, db):
        resp = client.post("/v1/consumption", json={"member_id": "x"})
        assert resp.status_code == 422

    def test_record_consumption_bad_member(self, client, db):
        item = _create_item(db, "Milk")
        db.commit()
        resp = client.post("/v1/consumption", json={
            "member_id": "nonexistent",
            "inventory_item_id": item.id,
            "quantity_used": 1.0,
        })
        assert resp.status_code == 404


class TestSupplyForecast:
    def test_forecast_no_data(self, client, db):
        """Items with no consumption events show status=no_data."""
        _create_item(db, "Milk", count=5)
        db.commit()

        resp = client.get("/v1/inventory/supply-forecast")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_items"] == 1
        assert data["forecasts"][0]["status"] == "no_data"

    def test_forecast_with_consumption(self, client, db):
        """Consumption events calculate daily rate and days_left."""
        item = _create_item(db, "Milk", count=10, par=20)
        member = _create_member(db)
        db.commit()

        # Record 2 consumption events: 1 unit each, 10 days ago and now
        for days_ago in [10, 0]:
            client.post("/v1/consumption", json={
                "member_id": member.id,
                "inventory_item_id": item.id,
                "quantity_used": 1.0,
                "consumed_at": (datetime.utcnow() - timedelta(days=days_ago)).isoformat(),
            })

        resp = client.get("/v1/inventory/supply-forecast?window_days=30")
        data = resp.json()
        forecast = data["forecasts"][0]
        assert forecast["status"] in ("depleting", "low", "critical")
        assert forecast["daily_rate"] > 0
        assert forecast["days_left"] is not None
        assert forecast["days_left"] > 0
        assert forecast["consumption_events"] == 2

    def test_forecast_critical_status(self, client, db):
        """Items with <=7 days left show critical status."""
        item = _create_item(db, "Milk", count=2, par=20)
        member = _create_member(db)
        db.commit()

        # Record 10 units consumed over 10 days = 1/day, 2 left = 2 days
        for i in range(10):
            client.post("/v1/consumption", json={
                "member_id": member.id,
                "inventory_item_id": item.id,
                "quantity_used": 1.0,
                "consumed_at": (datetime.utcnow() - timedelta(days=10 - i)).isoformat(),
            })

        resp = client.get("/v1/inventory/supply-forecast")
        forecast = resp.json()["forecasts"][0]
        assert forecast["status"] == "critical"
        assert forecast["days_left"] <= 7

    def test_forecast_sorted_by_urgency(self, client, db):
        """Critical items sort before stable ones."""
        milk = _create_item(db, "Milk", count=2, par=20)
        cereal = _create_item(db, "Cereal", count=10, par=5)
        member = _create_member(db)
        db.commit()

        # Milk: heavy consumption (critical)
        for i in range(10):
            client.post("/v1/consumption", json={
                "member_id": member.id,
                "inventory_item_id": milk.id,
                "quantity_used": 1.0,
                "consumed_at": (datetime.utcnow() - timedelta(days=10 - i)).isoformat(),
            })

        resp = client.get("/v1/inventory/supply-forecast")
        statuses = [f["status"] for f in resp.json()["forecasts"]]
        assert statuses.index("critical") < statuses.index("no_data")

    def test_forecast_reorder_suggestion(self, client, db):
        """Items below par with data get a reorder_by date."""
        item = _create_item(db, "Milk", count=3, par=10)
        member = _create_member(db)
        db.commit()

        for i in range(5):
            client.post("/v1/consumption", json={
                "member_id": member.id,
                "inventory_item_id": item.id,
                "quantity_used": 1.0,
                "consumed_at": (datetime.utcnow() - timedelta(days=5 - i)).isoformat(),
            })

        resp = client.get("/v1/inventory/supply-forecast")
        forecast = resp.json()["forecasts"][0]
        assert forecast["reorder_by"] is not None
