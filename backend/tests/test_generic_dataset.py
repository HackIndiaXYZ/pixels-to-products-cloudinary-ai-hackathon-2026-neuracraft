"""
Tests for generic CSV/Excel ingestion with aliased column names.

Verifies that the column normalisation layer correctly maps common
real-world header variations to canonical field names without touching
the actual data values (creative IDs must pass through unchanged).

These tests are NOT tied to the current 100-row test CSV — they use
independent data to prove the ingestion engine is truly generic.
"""
import io
import pandas as pd
import pytest

from app.services.validation_service import PerformanceValidator


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_df(**col_overrides) -> pd.DataFrame:
    """
    Return a minimal valid 5-row DataFrame using the provided column names.
    col_overrides maps canonical field → desired header name for this test.
    """
    canonical = {
        "creative_id": ["ad_001", "ad_002", "ad_003", "ad_004", "ad_005"],
        "platform":    ["facebook", "instagram", "tiktok", "facebook", "google"],
        "impressions": [10_000, 20_000, 15_000, 8_000, 12_000],
        "clicks":      [500, 800, 600, 400, 700],
        "conversions": [50, 80, 60, 40, 70],
        "spend":       [100.0, 200.0, 150.0, 80.0, 140.0],
        "revenue":     [300.0, 600.0, 450.0, 240.0, 420.0],
    }
    renamed = {}
    for canon, values in canonical.items():
        header = col_overrides.get(canon, canon)   # use override or keep canonical
        renamed[header] = values
    return pd.DataFrame(renamed)


def _validate(df: pd.DataFrame):
    v = PerformanceValidator()
    result, clean_df = v.validate_file(df)
    return result, clean_df


# ---------------------------------------------------------------------------
# Dataset B — "Creative ID, Channel, Link Clicks, Purchases, Amount Spent, Sales"
# (mimics a Facebook Ads-style export)
# ---------------------------------------------------------------------------

class TestGenericDatasetB:
    """Tests for the alternate-header dataset described in the task."""

    def test_all_alias_headers_accepted(self):
        df = _make_df(
            creative_id="Creative ID",
            platform="Channel",
            clicks="Link Clicks",
            conversions="Purchases",
            spend="Amount Spent",
            revenue="Sales",
        )
        result, clean = _validate(df)
        assert result.valid is True, f"Expected valid, got errors: {result.errors}"
        assert result.valid_rows == 5
        assert result.excluded_rows == 0

    def test_canonical_columns_present_after_normalisation(self):
        df = _make_df(
            creative_id="Creative ID",
            platform="Channel",
            clicks="Link Clicks",
            conversions="Purchases",
            spend="Amount Spent",
            revenue="Sales",
        )
        _, clean = _validate(df)
        for col in ["creative_id", "platform", "impressions", "clicks",
                    "conversions", "spend", "revenue"]:
            assert col in clean.columns, f"Missing canonical column: {col}"

    def test_creative_ids_pass_through_unchanged(self):
        """Creative ID values must never be remapped (ad_001 stays ad_001, not C001)."""
        df = _make_df(
            creative_id="Creative ID",
            platform="Channel",
            clicks="Link Clicks",
            conversions="Purchases",
            spend="Amount Spent",
            revenue="Sales",
        )
        _, clean = _validate(df)
        expected_ids = {"ad_001", "ad_002", "ad_003", "ad_004", "ad_005"}
        actual_ids   = set(clean["creative_id"].tolist())
        assert actual_ids == expected_ids, (
            f"Creative IDs were remapped. Expected {expected_ids}, got {actual_ids}"
        )

    def test_alias_mapping_warning_emitted(self):
        df = _make_df(
            creative_id="Creative ID",
            platform="Channel",
            clicks="Link Clicks",
            conversions="Purchases",
            spend="Amount Spent",
            revenue="Sales",
        )
        result, _ = _validate(df)
        warning_types = [w.type for w in result.warnings]
        assert "COLUMN_ALIAS_MAPPING" in warning_types

    def test_metrics_are_numerically_correct(self):
        """Verify that values are not mangled during normalisation."""
        df = _make_df(
            creative_id="Creative ID",
            platform="Channel",
            clicks="Link Clicks",
            conversions="Purchases",
            spend="Amount Spent",
            revenue="Sales",
        )
        _, clean = _validate(df)
        # Total spend should be 100+200+150+80+140 = 670
        assert abs(clean["spend"].sum() - 670.0) < 0.01
        # Total revenue should be 300+600+450+240+420 = 2010
        assert abs(clean["revenue"].sum() - 2010.0) < 0.01
        # Total clicks
        assert int(clean["clicks"].sum()) == 3000


# ---------------------------------------------------------------------------
# Dataset C — uppercase underscore-separated (e.g. Google Ads bulk export)
# ---------------------------------------------------------------------------

class TestUppercaseHeaders:
    """AD_ID, NETWORK, IMPR, LINK_CLICKS, LEADS, COST, CONVERSION_VALUE, DAY"""

    def test_uppercase_aliased_headers(self):
        data = {
            "AD_ID":             ["gads_001", "gads_002", "gads_003"],
            "NETWORK":           ["google", "google", "youtube"],
            "IMPR":              [50_000, 60_000, 40_000],
            "LINK_CLICKS":       [2_500, 3_000, 2_000],
            "LEADS":             [125, 150, 100],
            "COST":              [500.0, 600.0, 400.0],
            "CONVERSION_VALUE":  [1500.0, 1800.0, 1200.0],
            "DAY":               ["2024-01-01", "2024-01-02", "2024-01-03"],
        }
        df = pd.DataFrame(data)
        result, clean = _validate(df)
        assert result.valid is True, f"Errors: {result.errors}"
        assert result.valid_rows == 3
        # IDs pass through unchanged
        assert set(clean["creative_id"].tolist()) == {"gads_001", "gads_002", "gads_003"}
        # Date column accepted
        assert "date" in clean.columns

    def test_impr_maps_to_impressions(self):
        data = {
            "AD_ID":      ["x_001"],
            "NETWORK":    ["google"],
            "IMPR":       [10_000],
            "LINK_CLICKS":[ 500],
            "LEADS":      [ 25],
            "COST":       [100.0],
            "CONVERSION_VALUE": [300.0],
        }
        df = pd.DataFrame(data)
        _, clean = _validate(df)
        assert "impressions" in clean.columns
        assert int(clean["impressions"].iloc[0]) == 10_000


# ---------------------------------------------------------------------------
# Dataset D — spaces in headers + report_date alias
# ---------------------------------------------------------------------------

class TestSpacesAndReportDate:
    def test_spaced_headers(self):
        data = {
            "creative name": ["sp_001", "sp_002"],
            "platform":      ["facebook", "instagram"],
            "impressions":   [5_000, 8_000],
            "clicks":        [250, 400],
            "conversions":   [25, 40],
            "ad spend":      [50.0, 80.0],
            "purchase value":[150.0, 240.0],
            "report date":   ["2024-02-01", "2024-02-02"],
        }
        df = pd.DataFrame(data)
        result, clean = _validate(df)
        assert result.valid is True, f"Errors: {result.errors}"
        assert "creative_id" in clean.columns
        assert "spend"       in clean.columns
        assert "revenue"     in clean.columns
        assert "date"        in clean.columns

    def test_creative_name_values_preserved(self):
        data = {
            "creative name": ["my_creative_A", "my_creative_B"],
            "platform":      ["facebook", "instagram"],
            "impressions":   [5_000, 8_000],
            "clicks":        [250, 400],
            "conversions":   [25, 40],
            "ad spend":      [50.0, 80.0],
            "purchase value":[150.0, 240.0],
        }
        df = pd.DataFrame(data)
        _, clean = _validate(df)
        assert set(clean["creative_id"].tolist()) == {"my_creative_A", "my_creative_B"}


# ---------------------------------------------------------------------------
# Dataset E — exact canonical names (regression: no alias warning)
# ---------------------------------------------------------------------------

class TestExactCanonicalNames:
    def test_no_alias_warning_with_canonical_names(self):
        df = _make_df()   # uses exact canonical names
        result, _ = _validate(df)
        assert result.valid is True
        warning_types = [w.type for w in result.warnings]
        assert "COLUMN_ALIAS_MAPPING" not in warning_types


# ---------------------------------------------------------------------------
# Dataset F — Excel (.xlsx) round-trip
# ---------------------------------------------------------------------------

class TestExcelIngestion:
    def test_xlsx_with_alias_headers(self):
        """Simulate reading from an Excel buffer with aliased headers."""
        data = {
            "Creative ID":  ["xlsx_001", "xlsx_002", "xlsx_003"],
            "Channel":      ["facebook", "instagram", "tiktok"],
            "Impressions":  [10_000, 20_000, 15_000],
            "Link Clicks":  [500, 800, 600],
            "Purchases":    [50, 80, 60],
            "Amount Spent": [100.0, 200.0, 150.0],
            "Sales":        [300.0, 600.0, 450.0],
        }
        df_orig = pd.DataFrame(data)

        # Write to in-memory Excel buffer
        buf = io.BytesIO()
        df_orig.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)

        # Read back via load_performance_file
        from app.services.validation_service import load_performance_file
        df_loaded = load_performance_file(buf.read(), "test.xlsx")

        result, clean = _validate(df_loaded)
        assert result.valid is True, f"XLSX validation failed: {result.errors}"
        assert result.valid_rows == 3
        assert set(clean["creative_id"].tolist()) == {"xlsx_001", "xlsx_002", "xlsx_003"}


# ---------------------------------------------------------------------------
# Feature isolation — placeholder assets must not produce real features
# ---------------------------------------------------------------------------

class TestFeatureIsolation:
    """Verify that local_demo assets produce Unavailable features, not synthetic ones."""

    def test_unavailable_features_returned_for_placeholder(self):
        from app.services.feature_service import FeatureService
        features = FeatureService._unavailable_features()

        # Every numeric/boolean feature must be None
        for key in ["aspect_ratio", "brightness", "contrast", "edge_density",
                    "dominant_color", "bright_background", "portrait", "landscape",
                    "human_present"]:
            assert features[key] is None, f"Expected None for {key}, got {features[key]}"

        # Every source must say "Unavailable"
        for key, source in features["feature_sources"].items():
            assert source == "Unavailable", (
                f"Expected 'Unavailable' for {key}, got '{source}'"
            )

    def test_no_deterministic_hash_for_placeholders(self):
        """The old _get_demo_features() with SHA-256 hash must no longer exist."""
        from app.services import feature_service
        assert not hasattr(feature_service.FeatureService, "_get_demo_features"), (
            "_get_demo_features() still exists — placeholder assets could still "
            "generate synthetic features"
        )


# ---------------------------------------------------------------------------
# Assistant intent classification smoke tests
# ---------------------------------------------------------------------------

class TestAssistantClassification:
    """Verify the intent classifier covers all advertised question types."""

    def _classify(self, q: str):
        from app.api.endpoints.assistant import _classify
        return _classify(q)

    @pytest.mark.parametrize("q,expected", [
        ("What is the ROAS?",                          "roas"),
        ("How much did we spend?",                     "total_spend"),
        ("Total revenue",                              "total_revenue"),
        ("What is the CTR?",                           "ctr"),
        ("What is the CVR?",                           "cvr"),
        ("What is the CPC?",                           "cpc"),
        ("What is the CPM?",                           "cpm"),
        ("How many records were uploaded?",            "record_count"),
        ("How many unique creatives?",                 "creative_count"),
        ("Which creative has the highest CTR?",        "best_ctr"),
        ("Best ROAS creative",                         "best_roas"),
        ("Which platform generated the most revenue?", "platform_revenue"),
        ("Which platform has the highest spend?",      "platform_spend"),
        ("Are there Creative DNA insights?",           "dna_summary"),
        ("What is the date range?",                    "date_range"),
        ("Which platforms are in this analysis?",      "platforms_list"),
        ("What visual features were extracted?",       "visual_features"),
        ("Total impressions",                          "total_impressions"),
        ("Total clicks",                               "total_clicks"),
        ("Total conversions",                          "total_conversions"),
    ])
    def test_intent(self, q, expected):
        result = self._classify(q)
        assert result == expected, (
            f"Question '{q}': expected intent '{expected}', got '{result}'"
        )

    def test_unknown_question_returns_none(self):
        assert self._classify("What is the meaning of life?") is None
        assert self._classify("How are you?") is None
        assert self._classify("") is None
