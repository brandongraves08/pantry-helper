import re
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.db.models import BarcodeLookup, InventoryEvent, InventoryItem, InventoryState
from app.main import app
from app.middleware import api_auth
from app.api.routes import barcode as barcode_routes


def test_create_label_creates_inventory_and_manual_barcode(client, db):
    response = client.post(
        "/v1/barcode/create-label",
        json={
            "product_name": "White rice",
            "package_description": "1 lb bag",
            "quantity_estimate": 2,
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert re.fullmatch(r"PH-[0-9a-f]{32}", result["barcode"])
    assert result["item_name"] == "White rice"
    assert result["package_description"] == "1 lb bag"
    assert result["quantity_estimate"] == 2
    assert result["label_created_at"]

    item = db.query(InventoryItem).filter_by(canonical_name="White rice").one()
    state = db.query(InventoryState).filter_by(item_id=item.id).one()
    code = db.query(BarcodeLookup).filter_by(barcode=result["barcode"]).one()
    event = db.query(InventoryEvent).filter_by(item_id=item.id).one()
    assert state.count_estimate == 2
    assert state.is_manual is True
    assert code.inventory_item_id == item.id
    assert code.source == "manual"
    assert code.quantity_label == "1 lb bag"
    assert event.delta == 2
    assert event.details["barcode"] == result["barcode"]


def test_create_label_increments_existing_item_count(client, db):
    item = InventoryItem(canonical_name="White rice", package_type="bag")
    db.add(item)
    db.flush()
    db.add(InventoryState(item_id=item.id, count_estimate=4, confidence=1.0, is_manual=True))
    db.commit()

    response = client.post(
        "/v1/barcode/create-label",
        json={"product_name": "White rice", "quantity_estimate": 2},
    )

    assert response.status_code == 200
    assert db.query(InventoryState).filter_by(item_id=item.id).one().count_estimate == 6
    assert db.query(InventoryItem).filter_by(canonical_name="White rice").count() == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"product_name": "", "quantity_estimate": 1},
        {"product_name": "   ", "quantity_estimate": 1},
        {"product_name": "White rice", "quantity_estimate": 0},
    ],
)
def test_invalid_label_request_does_not_write_inventory(client, db, payload):
    response = client.post("/v1/barcode/create-label", json=payload)

    assert response.status_code == 422
    assert db.query(InventoryItem).count() == 0
    assert db.query(BarcodeLookup).count() == 0
    assert db.query(InventoryEvent).count() == 0


def test_barcode_collision_does_not_overwrite_existing_mapping(client, db, monkeypatch):
    existing = BarcodeLookup(barcode="PH-" + "a" * 32, product_name="Existing item", source="manual")
    db.add(existing)
    db.commit()
    monkeypatch.setattr(barcode_routes, "_generate_internal_barcode", lambda: existing.barcode, raising=False)

    response = client.post(
        "/v1/barcode/create-label",
        json={"product_name": "New item", "quantity_estimate": 1},
    )

    assert response.status_code == 409
    assert db.query(BarcodeLookup).filter_by(barcode=existing.barcode).one().product_name == "Existing item"
    assert db.query(InventoryItem).count() == 0
    assert db.query(InventoryState).count() == 0
    assert db.query(InventoryEvent).count() == 0


def test_create_label_requires_bearer_auth(client, db, monkeypatch):
    monkeypatch.setattr(api_auth, "_EXPECTED", "test-label-token")
    payload = {"product_name": "White rice", "quantity_estimate": 1}

    denied = client.post("/v1/barcode/create-label", json=payload)
    allowed = client.post(
        "/v1/barcode/create-label",
        json=payload,
        headers={"Authorization": "Bearer test-label-token"},
    )

    assert denied.status_code == 401
    assert allowed.status_code == 200
    assert db.query(InventoryItem).count() == 1


def test_scanning_internal_barcode_uses_local_cache_without_changing_count(client, db, monkeypatch):
    monkeypatch.setattr(
        barcode_routes,
        "lookup_barcode",
        lambda barcode: (_ for _ in ()).throw(AssertionError("external lookup must not run")),
    )
    created = client.post(
        "/v1/barcode/create-label",
        json={"product_name": "White rice", "package_description": "1 lb bag", "quantity_estimate": 1},
    ).json()
    item = db.query(InventoryItem).filter_by(canonical_name="White rice").one()
    state = db.query(InventoryState).filter_by(item_id=item.id).one()

    scanned = client.get(f"/v1/barcode/{created['barcode']}")

    assert scanned.status_code == 200
    result = scanned.json()
    assert result["found"] is True
    assert result["product_name"] == "White rice"
    assert result["already_in_inventory"] is True
    assert result["existing_item_name"] == "White rice"
    assert result["source"] == "manual"
    assert result["quantity"] == "1 lb bag"
    assert result["label_created_at"]
    assert state.count_estimate == 1


@pytest.mark.parametrize("initial_count", [None, 4])
def test_concurrent_label_creation_serializes_inventory_state_writes(
    tmp_path, monkeypatch, initial_count
):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'concurrent-labels.db'}",
        connect_args={"check_same_thread": False, "timeout": 20},
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    with session_factory() as db:
        item = InventoryItem(canonical_name="White rice")
        db.add(item)
        db.flush()
        if initial_count is not None:
            db.add(
                InventoryState(
                    item_id=item.id,
                    count_estimate=initial_count,
                    confidence=1.0,
                    is_manual=True,
                )
            )
        db.commit()
        item_id = item.id

    first_state_write_entered = Event()
    release_first_state_write = Event()
    second_state_write_entered = Event()
    state_write_lock = Lock()
    state_write_count = 0

    def synchronize_state_writes(conn, cursor, statement, parameters, context, executemany):
        nonlocal state_write_count
        normalized_statement = statement.lstrip().lower()
        if not (
            normalized_statement.startswith("insert into inventory_state")
            or normalized_statement.startswith("update inventory_state")
        ):
            return
        with state_write_lock:
            state_write_count += 1
            write_number = state_write_count
        if write_number == 1:
            first_state_write_entered.set()
            if not release_first_state_write.wait(timeout=10):
                raise TimeoutError("Test did not release the first inventory-state write")
        else:
            second_state_write_entered.set()

    event.listen(engine, "before_cursor_execute", synchronize_state_writes)

    dependency_lock = Lock()
    database_dependency_calls = 0
    second_database_dependency_started = Event()

    def override_get_db():
        nonlocal database_dependency_calls
        with dependency_lock:
            database_dependency_calls += 1
            if database_dependency_calls == 2:
                second_database_dependency_started.set()
        with session_factory() as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, override_get_db)

    def create_one_label(_):
        with TestClient(app) as client:
            return client.post(
                "/v1/barcode/create-label",
                json={"product_name": "White rice", "quantity_estimate": 1},
            )

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first_response = pool.submit(create_one_label, 1)
            assert first_state_write_entered.wait(timeout=5)
            second_response = pool.submit(create_one_label, 2)
            assert second_database_dependency_started.wait(timeout=5)
            second_write_raced = second_state_write_entered.wait(timeout=2)
            release_first_state_write.set()
            responses = [first_response.result(timeout=10), second_response.result(timeout=10)]
    finally:
        release_first_state_write.set()
        event.remove(engine, "before_cursor_execute", synchronize_state_writes)

    assert second_write_raced is False
    assert [response.status_code for response in responses] == [200, 200]
    with session_factory() as db:
        states = db.query(InventoryState).filter(
            InventoryState.item_id == item_id,
            InventoryState.location_id.is_(None),
        ).all()
        assert len(states) == 1
        assert states[0].count_estimate == (initial_count or 0) + 2
    engine.dispose()
