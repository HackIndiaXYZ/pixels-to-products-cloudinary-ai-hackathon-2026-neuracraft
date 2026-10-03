"""
Tests for Creative DNA evidence gating in the pipeline.

Strategy: Call AnalysisPipeline.run_complete_pipeline() directly with a
test SQLAlchemy session.  This avoids the BackgroundTasks issue where the
production session is used rather than the test override.

Key rules verified:
 - 0 real assets           → DNA skipped, 0 insights
 - 1 real asset            → DNA skipped (< 2 minimum), 0 insights
 - Placeholder assets only → DNA skipped, 0 insights
 - DNA_MIN_REAL_ASSETS constant == 2

These tests mock FeatureExtractor.extract_from_url so no real HTTP occurs.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.user import User
from app.models.analysis import Analysis, AnalysisStatus
from app.models.asset import Asset
from app.models.performance import PerformanceRecord
from app.models.dna_insight import CreativeDNAInsight
from app.services.pipeline import AnalysisPipeline
from app.core.security import hash_password

import app.models  # noqa — register all models on Base


# ── Test DB fixture ───────────────────────────────────────────────────────────

@pytest.fixture()
def db():
    """Fresh isolated in-memory SQLite session for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


# ── Fixture data helpers ──────────────────────────────────────────────────────

def _make_user(db) -> User:
    user = User(email="dnagate@test.com", password_hash=hash_password("pw"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_analysis(db, user: User) -> Analysis:
    a = Analysis(user_id=user.id, name="DNA Gate", status=AnalysisStatus.PROCESSING)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def _add_perf_records(db, analysis: Analysis, n_creatives: int = 10):
    """Add 10 performance rows per creative."""
    for i in range(1, n_creatives + 1):
        for _ in range(10):
            db.add(PerformanceRecord(
                analysis_id=analysis.id,
                creative_id=f"creative_{i:03d}",
                platform="facebook",
                impressions=10000, clicks=500, conversions=50,
                spend=1000.0, revenue=5000.0,
            ))
    db.commit()


def _add_real_asset(db, analysis: Analysis, creative_id: str) -> Asset:
    a = Asset(
        analysis_id=analysis.id,
        creative_id=creative_id,
        filename=f"{creative_id}.jpg",
        cloudinary_public_id=f"creativepulse/{analysis.id}/{creative_id}",
        cloudinary_url=f"http://res.cloudinary.com/test/{creative_id}.jpg",
        secure_url=f"https://res.cloudinary.com/test/{creative_id}.jpg",
        source="cloudinary",
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def _add_placeholder_asset(db, analysis: Analysis, creative_id: str) -> Asset:
    a = Asset(
        analysis_id=analysis.id,
        creative_id=creative_id,
        filename=f"{creative_id}.placeholder",
        source="local_demo",
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def _fake_features(i: int) -> dict:
    """Deterministic fake features; alternates bright_background by index."""
    bright = i % 2 == 0
    return {
        "aspect_ratio": 1.0,
        "brightness": 0.7 if bright else 0.3,
        "contrast": 0.2,
        "edge_density": 0.1,
        "dominant_color": "blue",
        "bright_background": bright,
        "portrait": False,
        "landscape": True,
        "human_present": None,
        "feature_sources": {k: "Computed" for k in [
            "aspect_ratio", "brightness", "contrast", "edge_density",
            "dominant_color", "bright_background", "portrait", "landscape",
            "human_present",
        ]},
    }


def _dna_count(db, analysis: Analysis) -> int:
    return (
        db.query(CreativeDNAInsight)
        .filter(CreativeDNAInsight.analysis_id == analysis.id)
        .count()
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_zero_assets_zero_dna_insights(db):
    """No assets → pipeline completes successfully with 0 DNA insights."""
    user = _make_user(db)
    analysis = _make_analysis(db, user)
    _add_perf_records(db, analysis)

    ok = AnalysisPipeline.run_complete_pipeline(db, analysis)

    db.refresh(analysis)
    assert ok is True
    assert analysis.status == AnalysisStatus.COMPLETED
    assert _dna_count(db, analysis) == 0, "Must produce 0 DNA insights with no assets"


def test_one_real_asset_zero_dna_insights(db):
    """Exactly 1 real Cloudinary asset → pipeline completes with 0 DNA insights.

    With only 1 asset there is nothing to compare — DNA requires >=2 real creatives.
    """
    user = _make_user(db)
    analysis = _make_analysis(db, user)
    _add_perf_records(db, analysis)
    _add_real_asset(db, analysis, "creative_001")

    counter = [0]
    def _fake_extract(url):
        counter[0] += 1
        return _fake_features(1)

    with patch(
        "app.analytics.features.FeatureExtractor.extract_from_url",
        side_effect=_fake_extract,
    ):
        ok = AnalysisPipeline.run_complete_pipeline(db, analysis)

    db.refresh(analysis)
    assert ok is True
    assert analysis.status == AnalysisStatus.COMPLETED
    assert counter[0] == 1, "Expected exactly 1 feature extraction call"
    assert _dna_count(db, analysis) == 0, (
        f"Must produce 0 DNA insights with only 1 real asset "
        f"(got {_dna_count(db, analysis)})"
    )


def test_placeholder_only_zero_dna_insights(db):
    """Placeholder assets only → 0 DNA insights (no real pixel data)."""
    user = _make_user(db)
    analysis = _make_analysis(db, user)
    _add_perf_records(db, analysis)
    for i in range(1, 6):
        _add_placeholder_asset(db, analysis, f"creative_{i:03d}")

    ok = AnalysisPipeline.run_complete_pipeline(db, analysis)

    db.refresh(analysis)
    assert ok is True
    assert analysis.status == AnalysisStatus.COMPLETED
    assert _dna_count(db, analysis) == 0, "Placeholders must not generate DNA insights"


def test_two_real_assets_dna_attempted(db):
    """>=2 real assets → DNA generation is attempted.

    With 2 assets both groups will be size 1 (< 5 minimum for Mann-Whitney),
    so all insights are insufficient_evidence — but the records exist.
    """
    user = _make_user(db)
    analysis = _make_analysis(db, user)
    _add_perf_records(db, analysis, n_creatives=2)
    _add_real_asset(db, analysis, "creative_001")
    _add_real_asset(db, analysis, "creative_002")

    call_n = [0]
    def _fake_extract(url):
        call_n[0] += 1
        return _fake_features(call_n[0])

    with patch(
        "app.analytics.features.FeatureExtractor.extract_from_url",
        side_effect=_fake_extract,
    ):
        ok = AnalysisPipeline.run_complete_pipeline(db, analysis)

    db.refresh(analysis)
    assert ok is True
    assert analysis.status == AnalysisStatus.COMPLETED
    assert call_n[0] == 2

    insights = (
        db.query(CreativeDNAInsight)
        .filter(CreativeDNAInsight.analysis_id == analysis.id)
        .all()
    )
    # With 2 assets, all insights are insufficient_evidence (n=1 < 5 per group)
    # but the pipeline DID attempt DNA (records were created)
    assert len(insights) > 0, "Pipeline should attempt DNA with 2 real assets"
    tiers = {i.evidence_tier for i in insights}
    assert tiers.issubset({"insufficient_evidence"}), (
        f"With only 2 assets all evidence tiers should be insufficient_evidence; got {tiers}"
    )


def test_ten_real_assets_dna_attempted_with_evidence(db):
    """10 real assets (with varied features) → DNA generation is attempted.

    With 10 assets and alternating bright_background, groups will be 5 each —
    right at the MIN_SAMPLE_SIZE threshold — so Mann-Whitney can run.
    """
    user = _make_user(db)
    analysis = _make_analysis(db, user)
    _add_perf_records(db, analysis, n_creatives=10)
    for i in range(1, 11):
        _add_real_asset(db, analysis, f"creative_{i:03d}")

    call_n = [0]
    def _fake_extract(url):
        call_n[0] += 1
        return _fake_features(call_n[0])

    with patch(
        "app.analytics.features.FeatureExtractor.extract_from_url",
        side_effect=_fake_extract,
    ):
        ok = AnalysisPipeline.run_complete_pipeline(db, analysis)

    db.refresh(analysis)
    assert ok is True
    assert analysis.status == AnalysisStatus.COMPLETED
    assert call_n[0] == 10

    insights = (
        db.query(CreativeDNAInsight)
        .filter(CreativeDNAInsight.analysis_id == analysis.id)
        .all()
    )
    assert len(insights) > 0, "Should generate DNA insights with 10 real assets"
    # With exactly 5 per group, Mann-Whitney runs; tiers may vary
    tiers = {i.evidence_tier for i in insights}
    valid_tiers = {"strong", "moderate", "weak", "no_clear_evidence",
                   "insufficient_evidence"}
    assert tiers.issubset(valid_tiers), f"Unknown evidence tiers: {tiers}"


def test_pipeline_constant_dna_min_is_2():
    """Verify DNA_MIN_REAL_ASSETS == 2 is present in pipeline.py."""
    import pathlib
    src = pathlib.Path(
        "C:/Users/amash/Desktop/HACKATHON/Hackathon Project/backend"
        "/app/services/pipeline.py"
    ).read_text(encoding="utf-8")
    assert "DNA_MIN_REAL_ASSETS = 2" in src, (
        "DNA_MIN_REAL_ASSETS constant not found or not equal to 2 in pipeline.py"
    )
