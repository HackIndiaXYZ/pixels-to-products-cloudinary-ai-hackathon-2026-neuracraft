"""
Integration tests for the analytics assistant endpoint.

Database isolation strategy
----------------------------
Each test function gets its own fresh SQLite in-memory database.  The
``db_override`` fixture (function scope) wires it up through FastAPI's
dependency-override mechanism and tears it down cleanly afterwards so
that no state leaks between tests.

This deliberately does NOT use the application's on-disk
``creativepulse_test.db`` file.

CORS coverage
-------------
The test client is constructed with ``raise_server_exceptions=False`` so
that we can inspect HTTP status codes and headers even when the app
raises an internal error.
"""
from __future__ import annotations

import io
import csv
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import app and the exact get_db function that FastAPI resolves at
# request time.  Overriding this function object is the canonical way
# to swap databases in FastAPI tests.
#
# IMPORTANT: We alias `fastapi_app` to avoid a name collision between
# the FastAPI application instance and the `app/` Python package.
# Without the alias, `app.dependency_overrides` resolves to the package
# directory object, not the FastAPI instance, causing AttributeError.
from app.main import app as fastapi_app
from app.db.session import Base, get_db

# Import all models so their metadata is registered on Base before we
# call create_all.  This mirrors what app/main.py does at startup.
import app.models  # noqa: F401 — side-effect import


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_db():
    """Create a fresh named temporary SQLite engine with all tables.

    Uses StaticPool so that every connection the engine hands out
    goes to the same underlying SQLite in-memory database.  This is
    the correct way to share a single in-memory DB across multiple
    connections in SQLAlchemy without the URI shared-cache trick
    (which requires SQLite to be compiled with URI support and is
    fragile across SQLAlchemy versions).
    """
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


def _csv_bytes(rows: list[list]) -> bytes:
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    return buf.getvalue().encode()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_override():
    """
    Function-scoped fixture that:
    1. Builds a fresh in-memory SQLite database.
    2. Registers a ``get_db`` override on the FastAPI app.
    3. Yields (nothing — callers use the ``client`` fixture instead).
    4. Removes the override and disposes the engine after each test.
    """
    engine = _build_db()
    _Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def _override():
        db = _Session()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _override
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)
    engine.dispose()


@pytest.fixture()
def client(db_override):
    """TestClient wired to a fresh isolated database."""
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers that create standard test resources through the API
# ---------------------------------------------------------------------------

def _signup(client: TestClient, email: str = "t@example.com") -> str:
    r = client.post("/api/auth/signup", json={"email": email, "password": "pass123456"})
    assert r.status_code in (200, 201), (
        f"signup returned {r.status_code}: {r.text}"
    )
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_analysis(client: TestClient, headers: dict, name: str = "Test") -> int:
    r = client.post("/api/analyses", json={"name": name}, headers=headers)
    assert r.status_code == 201, f"create analysis {r.status_code}: {r.text}"
    return r.json()["id"]


def _upload_csv(client: TestClient, headers: dict, aid: int) -> None:
    rows = [
        ["creative_id", "platform", "impressions", "clicks",
         "conversions", "spend", "revenue"],
        ["creative_001", "facebook",  "10000", "500", "50", "1000.00", "5000.00"],
        ["creative_001", "instagram",  "8000", "400", "40",  "800.00", "4000.00"],
        ["creative_002", "facebook",  "12000", "300", "20",  "900.00", "2000.00"],
        ["creative_002", "instagram",  "9000", "180", "15",  "700.00", "1500.00"],
    ]
    r = client.post(
        f"/api/analyses/{aid}/performance/upload",
        files={"file": ("perf.csv", _csv_bytes(rows), "text/csv")},
        headers=headers,
    )
    assert r.status_code == 200, f"upload CSV {r.status_code}: {r.text}"


# ---------------------------------------------------------------------------
# STEP A: Verify test DB isolation (signup must return 201, not 500)
# ---------------------------------------------------------------------------

def test_signup_returns_201_with_isolated_db(client):
    """Sanity-check that the DB override is working: signup must not return 500."""
    r = client.post(
        "/api/auth/signup",
        json={"email": "iso_test@example.com", "password": "password12345"},
    )
    assert r.status_code in (200, 201), (
        f"Expected 200 or 201, got {r.status_code}.  "
        f"Response: {r.text}.  "
        "This likely means the DB override is not being applied."
    )
    body = r.json()
    assert "access_token" in body, f"Missing access_token in {body}"


# ---------------------------------------------------------------------------
# CORS preflight
# ---------------------------------------------------------------------------

def test_cors_preflight_assistant(client):
    token = _signup(client)
    aid = _create_analysis(client, _auth(token))

    r = client.options(
        f"/api/analyses/{aid}/assistant",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )
    assert r.status_code in (200, 204), f"Preflight returned {r.status_code}"
    assert "access-control-allow-origin" in r.headers, (
        f"No ACAO header on preflight. Headers: {dict(r.headers)}"
    )
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_header_present_on_success(client):
    """ACAO header must appear on a normal 200 response."""
    token = _signup(client)
    headers = _auth(token)
    aid = _create_analysis(client, headers)

    r = client.post(
        f"/api/analyses/{aid}/assistant",
        json={"question": "What is the ROAS?"},
        headers={**headers, "Origin": "http://localhost:3000"},
    )
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    assert "access-control-allow-origin" in r.headers, (
        f"No ACAO on 200 response. Headers: {dict(r.headers)}"
    )
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_header_present_on_404(client):
    """Even a 404 must carry the ACAO header (CORS must not strip on errors)."""
    token = _signup(client)

    r = client.post(
        "/api/analyses/99999/assistant",
        json={"question": "test"},
        headers={**_auth(token), "Origin": "http://localhost:3000"},
    )
    assert r.status_code == 404
    assert "access-control-allow-origin" in r.headers, (
        f"No ACAO on 404. Headers: {dict(r.headers)}"
    )


def test_cors_header_present_on_401(client):
    """Unauthenticated requests must also get the ACAO header."""
    token = _signup(client)
    aid = _create_analysis(client, _auth(token))

    r = client.post(
        f"/api/analyses/{aid}/assistant",
        json={"question": "test"},
        headers={"Origin": "http://localhost:3000"},
        # No Authorization header intentionally
    )
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"
    assert "access-control-allow-origin" in r.headers, (
        f"No ACAO on {r.status_code}. Headers: {dict(r.headers)}"
    )


# ---------------------------------------------------------------------------
# Response structure
# ---------------------------------------------------------------------------

def test_response_has_required_fields(client):
    token = _signup(client)
    headers = _auth(token)
    aid = _create_analysis(client, headers)

    r = client.post(
        f"/api/analyses/{aid}/assistant",
        json={"question": "What is the ROAS?"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert "answer" in body
    assert "source" in body
    assert "confidence" in body
    assert isinstance(body["answer"], str), f"answer type: {type(body['answer'])}"
    assert body["confidence"] in ("high", "medium", "low", "unavailable")


def test_empty_question_returns_unavailable(client):
    token = _signup(client)
    headers = _auth(token)
    aid = _create_analysis(client, headers)

    r = client.post(
        f"/api/analyses/{aid}/assistant",
        json={"question": ""},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["confidence"] == "unavailable"


# ---------------------------------------------------------------------------
# No performance data — must not crash
# ---------------------------------------------------------------------------

def test_assistant_with_no_perf_data_does_not_crash(client):
    """Empty analysis must return a graceful answer, never a 500."""
    token = _signup(client)
    headers = _auth(token)
    aid = _create_analysis(client, headers)

    for question in [
        "What is the total spend?",
        "Which creative has the highest CTR?",
        "What is the ROAS?",
        "How many performance records?",
    ]:
        r = client.post(
            f"/api/analyses/{aid}/assistant",
            json={"question": question},
            headers=headers,
        )
        assert r.status_code == 200, (
            f"Got {r.status_code} for '{question}': {r.text}"
        )
        body = r.json()
        assert isinstance(body["answer"], str), (
            f"answer is not a string for '{question}': {body}"
        )


# ---------------------------------------------------------------------------
# Auth errors
# ---------------------------------------------------------------------------

def test_invalid_analysis_id_returns_404(client):
    token = _signup(client)
    r = client.post(
        "/api/analyses/99999/assistant",
        json={"question": "What is the ROAS?"},
        headers=_auth(token),
    )
    assert r.status_code == 404
    assert "detail" in r.json()


def test_no_auth_returns_401_or_403(client):
    token = _signup(client)
    aid = _create_analysis(client, _auth(token))

    r = client.post(
        f"/api/analyses/{aid}/assistant",
        json={"question": "What is the ROAS?"},
        # No auth header
    )
    assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Data-grounded answers with real performance data
# ---------------------------------------------------------------------------

def test_roas_answer_is_numeric_and_high_confidence(client):
    token = _signup(client)
    headers = _auth(token)
    aid = _create_analysis(client, headers)
    _upload_csv(client, headers, aid)

    r = client.post(
        f"/api/analyses/{aid}/assistant",
        json={"question": "What is the ROAS?"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["confidence"] == "high"
    # Answer must reference a numeric ratio
    answer = body["answer"]
    assert "x" in answer.lower() or "roas" in answer.lower(), (
        f"Expected ROAS value in answer, got: {answer}"
    )


def test_best_ctr_names_a_real_creative(client):
    token = _signup(client)
    headers = _auth(token)
    aid = _create_analysis(client, headers)
    _upload_csv(client, headers, aid)

    r = client.post(
        f"/api/analyses/{aid}/assistant",
        json={"question": "Which creative has the highest CTR?"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["confidence"] == "high"
    assert "creative_00" in body["answer"], (
        f"Expected a creative ID in answer, got: {body['answer']}"
    )


def test_total_spend_shows_dollar_amount(client):
    token = _signup(client)
    headers = _auth(token)
    aid = _create_analysis(client, headers)
    _upload_csv(client, headers, aid)

    r = client.post(
        f"/api/analyses/{aid}/assistant",
        json={"question": "How much was the total spend?"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["confidence"] == "high"
    assert "$" in body["answer"], f"No dollar sign in answer: {body['answer']}"


def test_record_count_matches_uploaded_rows(client):
    """'Record count' question returns the correct uploaded row count."""
    token = _signup(client)
    headers = _auth(token)
    aid = _create_analysis(client, headers)
    _upload_csv(client, headers, aid)  # 4 rows

    r = client.post(
        f"/api/analyses/{aid}/assistant",
        json={"question": "What is the record count?"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["confidence"] == "high", f"confidence={body['confidence']}, answer={body['answer']}"
    assert "4" in body["answer"], (
        f"Expected '4' records in answer, got: {body['answer']}"
    )


def test_unknown_question_returns_unavailable_not_500(client):
    token = _signup(client)
    headers = _auth(token)
    aid = _create_analysis(client, headers)
    _upload_csv(client, headers, aid)

    r = client.post(
        f"/api/analyses/{aid}/assistant",
        json={"question": "What is the meaning of life?"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["confidence"] == "unavailable"
    assert isinstance(body["answer"], str)


def test_all_answers_are_strings_never_objects(client):
    """
    Critical: every question must return a string answer.
    A dict or list in the answer field would crash React rendering.
    """
    token = _signup(client)
    headers = _auth(token)
    aid = _create_analysis(client, headers)
    _upload_csv(client, headers, aid)

    questions = [
        "What is the ROAS?",
        "What is the CTR?",
        "What is the CVR?",
        "What is the CPC?",
        "What is the CPM?",
        "How many creatives?",
        "How many performance records?",
        "Which platform has the most revenue?",
        "Which platform has the most spend?",
        "What platforms are in this analysis?",
        "What is the date range?",
        "Tell me about Creative DNA",
        "What visual features are available?",
        "Which creative has the highest CTR?",
        "Which creative has the highest ROAS?",
        "What is the total spend?",
        "What is the total revenue?",
        "Total impressions",
        "Total clicks",
        "Total conversions",
        "Something completely random",
    ]
    for q in questions:
        r = client.post(
            f"/api/analyses/{aid}/assistant",
            json={"question": q},
            headers=headers,
        )
        assert r.status_code == 200, f"Got {r.status_code} for '{q}': {r.text}"
        body = r.json()
        assert isinstance(body["answer"], str), (
            f"answer is {type(body['answer'])} for '{q}': {body['answer']}"
        )
