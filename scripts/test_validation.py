"""Test validation service with sample data"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.validation_service import PerformanceValidator
from app.services.sample_data import generate_sample_performance_dataframe, generate_invalid_performance_csv
import pandas as pd


def test_valid_data():
    """Test with valid data"""
    print("=" * 60)
    print("TEST 1: Valid Performance Data")
    print("=" * 60)
    
    df = generate_sample_performance_dataframe()
    print(f"\nGenerated {len(df)} rows of sample data")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst 3 rows:")
    print(df.head(3))
    
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    
    print(f"\n--- Validation Results ---")
    print(f"Valid: {result.valid}")
    print(f"Total rows: {result.total_rows}")
    print(f"Valid rows: {result.valid_rows}")
    print(f"Excluded rows: {result.excluded_rows}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    
    for warning in result.warnings:
        print(f"\n  Warning ({warning.type}): {warning.message}")
    
    print("\n" + "=" * 60)


def test_invalid_data():
    """Test with invalid data"""
    print("\n\nTEST 2: Invalid Performance Data")
    print("=" * 60)
    
    csv_string = generate_invalid_performance_csv()
    df = pd.read_csv(pd.io.common.StringIO(csv_string))
    
    print(f"\nGenerated {len(df)} rows with intentional issues")
    print(f"\nData preview:")
    print(df)
    
    validator = PerformanceValidator()
    result, valid_df = validator.validate_file(df)
    
    print(f"\n--- Validation Results ---")
    print(f"Valid: {result.valid}")
    print(f"Total rows: {result.total_rows}")
    print(f"Valid rows: {result.valid_rows}")
    print(f"Excluded rows: {result.excluded_rows}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    
    for error in result.errors:
        print(f"\n  Error ({error.type}): {error.message}")
    
    for warning in result.warnings:
        print(f"\n  Warning ({warning.type}): {warning.message}")
    
    print(f"\n\nValid data after filtering:")
    print(valid_df)
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_valid_data()
    test_invalid_data()
    
    print("\n\n✅ Validation tests completed!")
