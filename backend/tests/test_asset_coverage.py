"""
Tests for asset registration (idempotency) and asset coverage endpoint.

Key behaviours verified:
 - Registering a new Cloudinary asset → 200 with the new record
 - Registering the same creative_id again → 200 with existing record (idempotent, no 409)
 - Upgrading a placeholder to a real Cloudinary asset via register → works
 - Coverage endpoint returns correct counts
 - Missing IDs are correctly identified
"""
from __future__ import annotations

import io
import csv
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.db.session import Base, get_db
import app.models  # noqa


# ── Test DB ───────────────────────────────────────────────────────────────────

def _engine():
    e = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=e)
    return e


@pytest.fixture()
def db_override():
    e = _engine()
    Sess = sessionmaker(autocommit=False, autoflush=False, bind=e)

    def _override():
        db = Sess()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _override
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)
    e.dispose()


@pytest.fixture()
def client(db_override):
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        yield c


# ── Helpers ───────────────────────────────────────────────────────────────────

def _signup(client, email="cov@example.com"):
    r = client.post("/api/auth/signup", json={"email": email, "password": "pass123456"})
    assert r.status_code in (200, 201), f"signup {r.status_code}: {r.text}"
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _new_analysis(client, headers):
    r = client.post("/api/analyses", json={"name": "CovTest"}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


def _upload_csv(client, headers, aid, n_creatives=10):
    rows = [["creative_id", "platform", "impressions", "clicks",
             "conversions", "spend", "revenue"]]
    for i in range(1, n_creatives + 1):
        rows.append([f"creative_{i:03d}", "facebook", "10000",
                     "500", "50", "1000.00", "5000.00"])
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    r = client.post(
        f"/api/analyses/{aid}/performance/upload",
        files={"file": ("t.csv", buf.getvalue().encode(), "text/csv")},
        headers=headers,
    )
    assert r.status_code == 200, f"upload {r.status_code}: {r.text}"
    return r.json().get("creative_ids", [])


def _asset_payload(creative_id: str, aid: int) -> dict:
    return {
        "creative_id": creative_id,
        "filename": f"{creative_id}.jpg",
        "cloudinary_public_id": f"creativepulse/{aid}/{creative_id}",
        "cloudinary_url": f"http://res.cloudinary.com/test/{creative_id}.jpg",
        "secure_url": f"https://res.cloudinary.com/test/{creative_id}.jpg",
        "width": 1080, "height": 1080,
        "format": "jpg", "bytes": 100000,
        "source": "cloudinary",
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_register_new_asset_returns_200(client):
    token = _signup(client, "reg_new@example.com")
    headers = _h(token)
    aid = _new_analysis(client, headers)
    _upload_csv(client, headers, aid, n_creatives=3)

    r = client.post(
        f"/api/analyses/{aid}/assets/register",
        json=_asset_payload("creative_001", aid),
        headers=headers,
    )
    assert r.status_code == 200, f"register {r.status_code}: {r.text}"
    body = r.json()
    assert body["creative_id"] == "creative_001"
    assert body["source"] == "cloudinary"


def test_register_duplicate_creative_id_is_idempotent(client):
    """Registering the same creative_id twice must NOT return 409.
    The existing record is returned on the second call."""
    token = _signup(client, "reg_dup@example.com")
    headers = _h(token)
    aid = _new_analysis(client, headers)
    _upload_csv(client, headers, aid, n_creatives=3)

    payload = _asset_payload("creative_001", aid)

    r1 = client.post(f"/api/analyses/{aid}/assets/register", json=payload, headers=headers)
    assert r1.status_code == 200, f"first register {r1.status_code}: {r1.text}"
    id1 = r1.json()["id"]

    r2 = client.post(f"/api/analyses/{aid}/assets/register", json=payload, headers=headers)
    assert r2.status_code == 200, (
        f"second register returned {r2.status_code} — expected idempotent 200, "
        f"not 409 Conflict. Response: {r2.text}"
    )
    id2 = r2.json()["id"]
    assert id1 == id2, "Idempotent re-registration should return the same record ID"


def test_placeholder_upgraded_to_cloudinary_on_register(client):
    """Registering a Cloudinary asset for a creative that already has a
    placeholder upgrades the record to 'cloudinary' source."""
    token = _signup(client, "upgrade@example.com")
    headers = _h(token)
    aid = _new_analysis(client, headers)
    _upload_csv(client, headers, aid, n_creatives=3)

    # First register a placeholder
    r = client.post(
        f"/api/analyses/{aid}/assets/register-placeholders",
        json={"creative_ids": ["creative_001"]},
        headers=headers,
    )
    assert r.status_code == 200

    # Check it's a placeholder
    assets_resp = client.get(f"/api/analyses/{aid}/assets/list", headers=headers)
    assert assets_resp.status_code == 200
    assets = assets_resp.json()
    assert isinstance(assets, list), f"Expected list, got: {type(assets)} — {assets_resp.text[:200]}"
    c001 = next((a for a in assets if a["creative_id"] == "creative_001"), None)
    assert c001 is not None
    assert c001["source"] == "local_demo"

    # Now register a real Cloudinary asset for the same creative
    r2 = client.post(
        f"/api/analyses/{aid}/assets/register",
        json=_asset_payload("creative_001", aid),
        headers=headers,
    )
    assert r2.status_code == 200, f"upgrade {r2.status_code}: {r2.text}"
    assert r2.json()["source"] == "cloudinary"

    # Verify coverage shows it as real
    cov = client.get(f"/api/analyses/{aid}/assets/coverage", headers=headers).json()
    assert "creative_001" in cov["registered_real_ids"]


def test_coverage_endpoint_all_missing(client):
    """With no assets registered, all csv_creative_ids should be missing."""
    token = _signup(client, "cov_missing@example.com")
    headers = _h(token)
    aid = _new_analysis(client, headers)
    _upload_csv(client, headers, aid, n_creatives=5)

    cov = client.get(f"/api/analyses/{aid}/assets/coverage", headers=headers).json()
    assert cov["total_csv"] == 5
    assert cov["total_real"] == 0
    assert cov["total_missing"] == 5
    assert sorted(cov["missing_ids"]) == ["creative_001", "creative_002",
                                           "creative_003", "creative_004",
                                           "creative_005"]
    assert cov["coverage_complete"] is False


def test_coverage_endpoint_partial_coverage(client):
    """Register 3 of 5 assets and verify missing_ids contains the other 2."""
    token = _signup(client, "cov_partial@example.com")
    headers = _h(token)
    aid = _new_analysis(client, headers)
    _upload_csv(client, headers, aid, n_creatives=5)

    for i in (1, 2, 3):
        client.post(
            f"/api/analyses/{aid}/assets/register",
            json=_asset_payload(f"creative_{i:03d}", aid),
            headers=headers,
        )

    cov = client.get(f"/api/analyses/{aid}/assets/coverage", headers=headers).json()
    assert cov["total_csv"] == 5
    assert cov["total_real"] == 3
    assert cov["total_missing"] == 2
    assert sorted(cov["missing_ids"]) == ["creative_004", "creative_005"]
    assert cov["coverage_complete"] is False


def test_coverage_endpoint_full_coverage(client):
    """Register all 5 assets → coverage_complete must be True, missing_ids empty."""
    token = _signup(client, "cov_full@example.com")
    headers = _h(token)
    aid = _new_analysis(client, headers)
    _upload_csv(client, headers, aid, n_creatives=5)

    for i in range(1, 6):
        r = client.post(
            f"/api/analyses/{aid}/assets/register",
            json=_asset_payload(f"creative_{i:03d}", aid),
            headers=headers,
        )
        assert r.status_code == 200, f"register creative_{i:03d}: {r.text}"

    cov = client.get(f"/api/analyses/{aid}/assets/coverage", headers=headers).json()
    assert cov["total_csv"] == 5
    assert cov["total_real"] == 5
    assert cov["total_missing"] == 0
    assert cov["missing_ids"] == []
    assert cov["coverage_complete"] is True


def test_coverage_placeholders_do_not_count_as_real(client):
    """Placeholder assets are NOT counted in total_real and appear in missing_ids."""
    token = _signup(client, "cov_ph@example.com")
    headers = _h(token)
    aid = _new_analysis(client, headers)
    _upload_csv(client, headers, aid, n_creatives=5)

    # Register all as placeholders
    client.post(
        f"/api/analyses/{aid}/assets/register-placeholders",
        json={"creative_ids": [f"creative_{i:03d}" for i in range(1, 6)]},
        headers=headers,
    )

    cov = client.get(f"/api/analyses/{aid}/assets/coverage", headers=headers).json()
    assert cov["total_real"] == 0, "Placeholders must NOT count as real assets"
    assert cov["total_missing"] == 5
    assert cov["coverage_complete"] is False
