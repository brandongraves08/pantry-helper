"""Write-route auth coverage for APIAuthMiddleware.

The middleware is the only thing standing between the LAN and every mutating
endpoint, so pin its behaviour: writes need the shared bearer token, reads never
do, /v1/ingest* is exempt (it authenticates with its own device token), and no
mutating route escapes it when the token is configured.
"""

import pytest

from app.middleware import api_auth
from app.middleware.api_auth import APIAuthMiddleware

TOKEN = "test-shared-token"


@pytest.fixture
def token_enforced(monkeypatch):
    """Force the middleware into 'token configured' mode (module-level global)."""
    monkeypatch.setattr(api_auth, "_EXPECTED", TOKEN)
    return TOKEN


def test_write_without_token_is_rejected(client, token_enforced):
    resp = client.post(
        "/v1/inventory/override", json={"item_name": "Milk", "count_estimate": 2}
    )

    assert resp.status_code == 401
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_write_with_wrong_token_is_rejected(client, token_enforced):
    resp = client.post(
        "/v1/inventory/override",
        json={"item_name": "Milk", "count_estimate": 2},
        headers={"Authorization": "Bearer nope"},
    )

    assert resp.status_code == 401


def test_write_with_token_is_allowed(client, token_enforced):
    resp = client.post(
        "/v1/inventory/override",
        json={"item_name": "Milk", "count_estimate": 2},
        headers={"Authorization": f"Bearer {token_enforced}"},
    )

    assert resp.status_code == 200


def test_get_without_token_is_allowed(client, token_enforced):
    resp = client.get("/v1/inventory")

    assert resp.status_code == 200


def test_gear_write_requires_shared_token_but_read_is_allowed(client, token_enforced):
    payload = {"name": "Camp stove", "category": "Cooking", "quantity": 1}

    rejected = client.post("/v1/gear", json=payload)
    assert rejected.status_code == 401
    assert rejected.headers.get("www-authenticate") == "Bearer"

    assert client.get("/v1/gear").status_code == 200

    accepted = client.post(
        "/v1/gear",
        json=payload,
        headers={"Authorization": f"Bearer {token_enforced}"},
    )
    assert accepted.status_code == 201


def test_patch_and_delete_require_token(client, token_enforced):
    """Non-POST mutating verbs must be covered too (router-level routes included)."""
    patch_resp = client.patch(
        "/v1/household/members/does-not-exist", json={"name": "x"}
    )
    delete_resp = client.delete("/v1/zones/does-not-exist")

    assert patch_resp.status_code == 401
    assert delete_resp.status_code == 401


def test_ingest_is_exempt_from_shared_token(client, token_enforced):
    """Ingest does its own device-token auth, so the shared-token 401 must not apply."""
    resp = client.post(
        "/v1/ingest",
        data={"device_id": "unknown-device", "trigger_type": "manual"},
        files={"image": ("x.jpg", b"data", "image/jpeg")},
    )

    middleware_detail = "Unauthorized: valid Bearer token required"
    assert resp.status_code == 401  # device auth still rejects the request...
    assert (
        resp.json()["detail"] != middleware_detail
    )  # ...but not via APIAuthMiddleware
    assert resp.json()["detail"] == "Device not found"


def test_no_token_configured_allows_writes(client, monkeypatch):
    """Documented dev-mode behaviour: unset PANTRY_API_TOKEN means writes are open."""
    monkeypatch.setattr(api_auth, "_EXPECTED", None)

    resp = client.post(
        "/v1/inventory/override", json={"item_name": "Bread", "count_estimate": 1}
    )

    assert resp.status_code == 200
