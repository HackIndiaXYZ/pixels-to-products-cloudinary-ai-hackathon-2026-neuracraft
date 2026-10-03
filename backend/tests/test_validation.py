"""Tests for performance data validation"""
import pytest
import pandas as pd
from app.services.validation_service import PerformanceValidator


def test_valid_performance_data():
    """Test validation of valid performance data"""
    df = pd.DataFrame({
        'creative_id': ['C001', 'C002', 'C003'],
        'platform': ['facebook', 'instagram', 'facebook'],
        'impressions': [1000, 2000, 1500],
        'clicks': [100, 200, 150],
        'conversions': [10, 20, 15],
        'spend': [50.0, 100.0, 75.0],
        'revenue': [500.0, 1000.0, 750.0]
    })
    
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    
    assert result.valid is True
    assert len(result.errors) == 0
    assert result.valid_rows == 3
    assert result.total_rows == 3
    assert result.excluded_rows == 0


def test_missing_required_columns():
    """Test validation fails with missing columns"""
    df = pd.DataFrame({
        'creative_id': ['C001'],
        'platform': ['facebook'],
        'impressions': [1000]
        # Missing: clicks, conversions, spend, revenue
    })
    
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    
    assert result.valid is False
    assert len(result.errors) > 0
    assert any(error.type == "MISSING_COLUMNS" for error in result.errors)


def test_negative_values_excluded():
    """Test that rows with negative values are excluded"""
    df = pd.DataFrame({
        'creative_id': ['C001', 'C002', 'C003'],
        'platform': ['facebook', 'instagram', 'facebook'],
        'impressions': [1000, 2000, 1500],
        'clicks': [100, 200, -50],  # Negative clicks
        'conversions': [10, 20, 15],
        'spend': [50.0, -100.0, 75.0],  # Negative spend
        'revenue': [500.0, 1000.0, 750.0]
    })
    
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    
    assert result.valid is True  # Valid structure, just excludes bad rows
    assert result.valid_rows < result.total_rows
    assert any(warning.type == "NEGATIVE_VALUES" for warning in result.warnings)


def test_clicks_greater_than_impressions():
    """Test that rows with clicks > impressions are excluded"""
    df = pd.DataFrame({
        'creative_id': ['C001', 'C002'],
        'platform': ['facebook', 'instagram'],
        'impressions': [1000, 2000],
        'clicks': [100, 2500],  # Clicks > impressions for C002
        'conversions': [10, 20],
        'spend': [50.0, 100.0],
        'revenue': [500.0, 1000.0]
    })
    
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    
    assert result.valid is True
    assert result.valid_rows == 1  # Only C001 should be valid
    assert any(warning.type == "INVALID_CTR" for warning in result.warnings)


def test_conversions_greater_than_clicks():
    """Test that rows with conversions > clicks are excluded"""
    df = pd.DataFrame({
        'creative_id': ['C001', 'C002'],
        'platform': ['facebook', 'instagram'],
        'impressions': [1000, 2000],
        'clicks': [100, 200],
        'conversions': [10, 250],  # Conversions > clicks for C002
        'spend': [50.0, 100.0],
        'revenue': [500.0, 1000.0]
    })
    
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    
    assert result.valid is True
    assert result.valid_rows == 1  # Only C001 should be valid
    assert any(warning.type == "INVALID_CVR" for warning in result.warnings)


def test_duplicate_rows_warning():
    """Test that duplicate rows generate a warning"""
    df = pd.DataFrame({
        'creative_id': ['C001', 'C001', 'C002'],  # C001 duplicated
        'platform': ['facebook', 'facebook', 'instagram'],
        'impressions': [1000, 1000, 2000],
        'clicks': [100, 100, 200],
        'conversions': [10, 10, 20],
        'spend': [50.0, 50.0, 100.0],
        'revenue': [500.0, 500.0, 1000.0]
    })
    
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    
    assert result.valid is True
    assert any(warning.type == "DUPLICATE_ROWS" for warning in result.warnings)


def test_column_name_cleaning():
    """Test that column names are cleaned (whitespace, case)"""
    df = pd.DataFrame({
        ' Creative_ID ': ['C001'],  # Extra spaces, mixed case
        'Platform': ['facebook'],
        'IMPRESSIONS': [1000],
        'clicks  ': [100],
        'Conversions': [10],
        'Spend': [50.0],
        'Revenue': [500.0]
    })
    
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    
    assert result.valid is True
    assert 'creative_id' in valid_df.columns
    assert 'platform' in valid_df.columns
    assert 'impressions' in valid_df.columns


def test_null_values_excluded():
    """Test that rows with null required values are excluded"""
    df = pd.DataFrame({
        'creative_id': ['C001', None, 'C003'],  # Null creative_id
        'platform': ['facebook', 'instagram', 'facebook'],
        'impressions': [1000, 2000, None],  # Null impressions
        'clicks': [100, 200, 150],
        'conversions': [10, 20, 15],
        'spend': [50.0, 100.0, 75.0],
        'revenue': [500.0, 1000.0, 750.0]
    })
    
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    
    assert result.valid is True
    assert result.valid_rows == 1  # Only C001 should be valid
    assert any(warning.type == "NULL_VALUES" for warning in result.warnings)


def test_optional_date_column():
    """Test that date column is optional"""
    df = pd.DataFrame({
        'creative_id': ['C001', 'C002'],
        'platform': ['facebook', 'instagram'],
        'impressions': [1000, 2000],
        'clicks': [100, 200],
        'conversions': [10, 20],
        'spend': [50.0, 100.0],
        'revenue': [500.0, 1000.0],
        'date': ['2024-01-01', '2024-01-02']
    })
    
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    
    assert result.valid is True
    assert result.valid_rows == 2


# ─── Column alias / normalization tests ──────────────────────────────────────

def test_column_aliases_ad_id():
    """creative_id alias: ad_id"""
    df = pd.DataFrame({
        'ad_id': ['C001', 'C002'],
        'platform': ['facebook', 'instagram'],
        'impressions': [1000, 2000],
        'clicks': [100, 200],
        'conversions': [10, 20],
        'spend': [50.0, 100.0],
        'revenue': [500.0, 1000.0],
    })
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    assert result.valid is True, f"Expected valid but got errors: {result.errors}"
    assert 'creative_id' in valid_df.columns
    assert result.valid_rows == 2


def test_column_aliases_cost_for_spend():
    """spend alias: cost"""
    df = pd.DataFrame({
        'creative_id': ['C001'],
        'platform': ['facebook'],
        'impressions': [1000],
        'clicks': [100],
        'conversions': [10],
        'cost': [50.0],          # alias for spend
        'revenue': [500.0],
    })
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    assert result.valid is True, f"Expected valid but got errors: {result.errors}"
    assert 'spend' in valid_df.columns
    assert float(valid_df['spend'].iloc[0]) == 50.0


def test_column_aliases_sales_for_revenue():
    """revenue alias: sales"""
    df = pd.DataFrame({
        'creative_id': ['C001'],
        'platform': ['facebook'],
        'impressions': [1000],
        'clicks': [100],
        'conversions': [10],
        'spend': [50.0],
        'sales': [500.0],        # alias for revenue
    })
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    assert result.valid is True, f"Expected valid but got errors: {result.errors}"
    assert 'revenue' in valid_df.columns
    assert float(valid_df['revenue'].iloc[0]) == 500.0


def test_column_aliases_uppercase_headers():
    """Uppercase headers with alias names should normalise correctly."""
    df = pd.DataFrame({
        'Creative ID': ['C001', 'C002'],
        'Platform': ['facebook', 'instagram'],
        'Impressions': [1000, 2000],
        'Clicks': [100, 200],
        'Conversions': [10, 20],
        'Spend': [50.0, 100.0],
        'Revenue': [500.0, 1000.0],
    })
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    assert result.valid is True, f"Expected valid but got errors: {result.errors}"
    assert result.valid_rows == 2
    expected_cols = {'creative_id', 'platform', 'impressions', 'clicks', 'conversions', 'spend', 'revenue'}
    assert expected_cols.issubset(set(valid_df.columns))


def test_column_alias_mapping_warning_emitted():
    """A COLUMN_ALIAS_MAPPING warning is emitted when aliases are resolved."""
    df = pd.DataFrame({
        'ad_id': ['C001'],
        'channel': ['facebook'],  # alias for platform
        'impressions': [1000],
        'clicks': [100],
        'conversions': [10],
        'cost': [50.0],           # alias for spend
        'sales': [500.0],         # alias for revenue
    })
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    assert result.valid is True
    warning_types = [w.type for w in result.warnings]
    assert 'COLUMN_ALIAS_MAPPING' in warning_types


def test_no_alias_warning_when_exact_names_used():
    """No COLUMN_ALIAS_MAPPING warning when canonical names are used exactly."""
    df = pd.DataFrame({
        'creative_id': ['C001'],
        'platform': ['facebook'],
        'impressions': [1000],
        'clicks': [100],
        'conversions': [10],
        'spend': [50.0],
        'revenue': [500.0],
    })
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    assert result.valid is True
    warning_types = [w.type for w in result.warnings]
    assert 'COLUMN_ALIAS_MAPPING' not in warning_types


def test_unknown_required_column_gives_clear_error():
    """An unrecognised column name for a required field gives a MISSING_COLUMNS error."""
    df = pd.DataFrame({
        'creative_identifier': ['C001'],  # not a known alias
        'platform': ['facebook'],
        'impressions': [1000],
        'clicks': [100],
        'conversions': [10],
        'spend': [50.0],
        'revenue': [500.0],
    })
    validator = PerformanceValidator()
    result, _ = validator.validate_file(df)
    assert result.valid is False
    error_types = [e.type for e in result.errors]
    assert 'MISSING_COLUMNS' in error_types
    # creative_id should be listed as missing
    missing_detail = next(e for e in result.errors if e.type == 'MISSING_COLUMNS')
    assert 'creative_id' in missing_detail.details['missing_columns']


def test_alias_purchases_for_conversions():
    """conversions alias: purchases"""
    df = pd.DataFrame({
        'creative_id': ['C001'],
        'platform': ['facebook'],
        'impressions': [1000],
        'clicks': [100],
        'purchases': [10],      # alias for conversions
        'spend': [50.0],
        'revenue': [500.0],
    })
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    assert result.valid is True
    assert 'conversions' in valid_df.columns
    assert int(valid_df['conversions'].iloc[0]) == 10


def test_data_integrity_preserved_with_aliases():
    """Creative IDs from an alias-mapped upload are stored verbatim — not remapped."""
    df = pd.DataFrame({
        'ad_id': ['creative_001', 'creative_002', 'creative_003'],
        'platform': ['facebook', 'instagram', 'tiktok'],
        'impressions': [1000, 2000, 3000],
        'clicks': [100, 200, 300],
        'conversions': [10, 20, 30],
        'spend': [50.0, 100.0, 150.0],
        'revenue': [500.0, 1000.0, 1500.0],
    })
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    assert result.valid is True
    assert result.valid_rows == 3
    # Creative IDs must be exactly what the user provided — not remapped to C001/C002/C003
    actual_ids = set(valid_df['creative_id'].tolist())
    assert actual_ids == {'creative_001', 'creative_002', 'creative_003'}
