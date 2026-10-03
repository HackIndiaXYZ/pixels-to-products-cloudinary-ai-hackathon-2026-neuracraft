"""Tests for metrics calculation"""
import pytest
from app.analytics.metrics import MetricsCalculator
from app.models.performance import PerformanceRecord


def test_ctr_calculation():
    """Test CTR calculation"""
    ctr = MetricsCalculator.calculate_ctr(clicks=100, impressions=1000)
    assert ctr == 0.1  # 10%
    
    ctr = MetricsCalculator.calculate_ctr(clicks=50, impressions=2000)
    assert ctr == 0.025  # 2.5%


def test_cvr_calculation():
    """Test conversion rate calculation"""
    cvr = MetricsCalculator.calculate_cvr(conversions=10, clicks=100)
    assert cvr == 0.1  # 10%
    
    cvr = MetricsCalculator.calculate_cvr(conversions=5, clicks=200)
    assert cvr == 0.025  # 2.5%


def test_cpc_calculation():
    """Test cost per click calculation"""
    cpc = MetricsCalculator.calculate_cpc(spend=100.0, clicks=50)
    assert cpc == 2.0
    
    cpc = MetricsCalculator.calculate_cpc(spend=250.0, clicks=100)
    assert cpc == 2.5


def test_roas_calculation():
    """Test ROAS calculation"""
    roas = MetricsCalculator.calculate_roas(revenue=500.0, spend=100.0)
    assert roas == 5.0
    
    roas = MetricsCalculator.calculate_roas(revenue=150.0, spend=100.0)
    assert roas == 1.5


def test_cpm_calculation():
    """Test CPM calculation"""
    cpm = MetricsCalculator.calculate_cpm(spend=100.0, impressions=10000)
    assert cpm == 10.0  # $10 per 1000 impressions
    
    cpm = MetricsCalculator.calculate_cpm(spend=50.0, impressions=5000)
    assert cpm == 10.0


def test_zero_division_handling():
    """Test that zero division returns None"""
    ctr = MetricsCalculator.calculate_ctr(clicks=100, impressions=0)
    assert ctr is None
    
    cvr = MetricsCalculator.calculate_cvr(conversions=10, clicks=0)
    assert cvr is None
    
    cpc = MetricsCalculator.calculate_cpc(spend=100.0, clicks=0)
    assert cpc is None
    
    roas = MetricsCalculator.calculate_roas(revenue=500.0, spend=0.0)
    assert roas is None
    
    cpm = MetricsCalculator.calculate_cpm(spend=100.0, impressions=0)
    assert cpm is None


def test_aggregate_metrics_computation():
    """Test aggregate metrics from multiple records"""
    # Create mock records
    class MockRecord:
        def __init__(self, impressions, clicks, conversions, spend, revenue):
            self.impressions = impressions
            self.clicks = clicks
            self.conversions = conversions
            self.spend = spend
            self.revenue = revenue
    
    records = [
        MockRecord(1000, 100, 10, 50.0, 500.0),
        MockRecord(2000, 200, 20, 100.0, 1000.0),
        MockRecord(1500, 150, 15, 75.0, 750.0)
    ]
    
    metrics = MetricsCalculator.compute_aggregate_metrics(records)
    
    # Check totals
    assert metrics['total_impressions'] == 4500
    assert metrics['total_clicks'] == 450
    assert metrics['total_conversions'] == 45
    assert metrics['total_spend'] == 225.0
    assert metrics['total_revenue'] == 2250.0
    
    # Check computed metrics
    assert metrics['ctr'] == pytest.approx(0.1, rel=1e-4)  # 450/4500
    assert metrics['cvr'] == pytest.approx(0.1, rel=1e-4)  # 45/450
    assert metrics['cpc'] == pytest.approx(0.5, rel=1e-2)  # 225/450
    assert metrics['roas'] == pytest.approx(10.0, rel=1e-2)  # 2250/225
    assert metrics['cpm'] == pytest.approx(50.0, rel=1e-2)  # (225/4500)*1000


def test_aggregate_metrics_empty_list():
    """Test aggregate metrics with empty list"""
    metrics = MetricsCalculator.compute_aggregate_metrics([])
    
    assert metrics['total_impressions'] == 0
    assert metrics['total_clicks'] == 0
    assert metrics['total_conversions'] == 0
    assert metrics['total_spend'] == 0.0
    assert metrics['total_revenue'] == 0.0
    assert metrics['ctr'] is None
    assert metrics['cvr'] is None
    assert metrics['cpc'] is None
    assert metrics['roas'] is None
    assert metrics['cpm'] is None


def test_correct_aggregation_not_averaging():
    """
    Test that we aggregate correctly, not by averaging ratios
    
    This is a critical test to ensure we don't make the common mistake
    of averaging CTR/CVR instead of computing from totals.
    """
    class MockRecord:
        def __init__(self, impressions, clicks, conversions, spend, revenue):
            self.impressions = impressions
            self.clicks = clicks
            self.conversions = conversions
            self.spend = spend
            self.revenue = revenue
    
    # Two campaigns with very different scales
    records = [
        MockRecord(1000, 100, 10, 50.0, 500.0),  # CTR=10%, CVR=10%
        MockRecord(10000, 100, 10, 50.0, 500.0)  # CTR=1%, CVR=10%
    ]
    
    metrics = MetricsCalculator.compute_aggregate_metrics(records)
    
    # Correct: total_clicks / total_impressions = 200 / 11000 ≈ 1.82%
    # Incorrect would be: average(10%, 1%) = 5.5%
    correct_ctr = 200 / 11000
    assert metrics['ctr'] == pytest.approx(correct_ctr, rel=1e-4)
    
    # Both have same CVR, so aggregation should match
    assert metrics['cvr'] == pytest.approx(0.1, rel=1e-4)


def test_top_creatives_sorting():
    """Test getting top creatives by metric"""
    creative_metrics = {
        'C001': {'roas': 5.0, 'ctr': 0.1},
        'C002': {'roas': 3.0, 'ctr': 0.15},
        'C003': {'roas': 8.0, 'ctr': 0.05},
        'C004': {'roas': None, 'ctr': 0.2},  # Missing ROAS
    }
    
    top_by_roas = MetricsCalculator.get_top_creatives_by_metric(
        creative_metrics,
        'roas',
        limit=3
    )
    
    # Should be sorted by ROAS descending, excluding C004 (None)
    assert len(top_by_roas) == 3
    assert top_by_roas[0]['creative_id'] == 'C003'  # 8.0
    assert top_by_roas[1]['creative_id'] == 'C001'  # 5.0
    assert top_by_roas[2]['creative_id'] == 'C002'  # 3.0
    
    # Test ascending order (lowest first)
    bottom_by_roas = MetricsCalculator.get_top_creatives_by_metric(
        creative_metrics,
        'roas',
        limit=2,
        ascending=True
    )
    
    assert bottom_by_roas[0]['creative_id'] == 'C002'  # 3.0
    assert bottom_by_roas[1]['creative_id'] == 'C001'  # 5.0
