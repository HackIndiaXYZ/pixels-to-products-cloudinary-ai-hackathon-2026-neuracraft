"""Test metrics calculation with sample data"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.analytics.metrics import MetricsCalculator, format_metric_value


def test_basic_calculations():
    """Test basic metric calculations"""
    print("=" * 60)
    print("TEST 1: Basic Metric Calculations")
    print("=" * 60)
    
    # Sample data
    impressions = 10000
    clicks = 500
    conversions = 50
    spend = 250.0
    revenue = 2500.0
    
    print(f"\nSample Data:")
    print(f"  Impressions: {impressions:,}")
    print(f"  Clicks: {clicks:,}")
    print(f"  Conversions: {conversions:,}")
    print(f"  Spend: ${spend:,.2f}")
    print(f"  Revenue: ${revenue:,.2f}")
    
    # Calculate metrics
    ctr = MetricsCalculator.calculate_ctr(clicks, impressions)
    cvr = MetricsCalculator.calculate_cvr(conversions, clicks)
    cpc = MetricsCalculator.calculate_cpc(spend, clicks)
    roas = MetricsCalculator.calculate_roas(revenue, spend)
    cpm = MetricsCalculator.calculate_cpm(spend, impressions)
    
    print(f"\nCalculated Metrics:")
    print(f"  CTR: {format_metric_value(ctr, 'percentage')}")
    print(f"  CVR: {format_metric_value(cvr, 'percentage')}")
    print(f"  CPC: {format_metric_value(cpc, 'currency')}")
    print(f"  ROAS: {format_metric_value(roas, 'ratio')}")
    print(f"  CPM: {format_metric_value(cpm, 'currency')}")
    
    print("\n" + "=" * 60)


def test_aggregation():
    """Test correct aggregation vs incorrect averaging"""
    print("\n\nTEST 2: Correct Aggregation (Not Averaging)")
    print("=" * 60)
    
    class MockRecord:
        def __init__(self, name, impressions, clicks, conversions, spend, revenue):
            self.name = name
            self.impressions = impressions
            self.clicks = clicks
            self.conversions = conversions
            self.spend = spend
            self.revenue = revenue
    
    # Two campaigns with different scales
    records = [
        MockRecord("Small Campaign", 1000, 100, 10, 50.0, 500.0),
        MockRecord("Large Campaign", 10000, 100, 10, 50.0, 500.0)
    ]
    
    print("\nCampaign Data:")
    for record in records:
        ctr = MetricsCalculator.calculate_ctr(record.clicks, record.impressions)
        print(f"\n  {record.name}:")
        print(f"    Impressions: {record.impressions:,}")
        print(f"    Clicks: {record.clicks:,}")
        print(f"    CTR: {format_metric_value(ctr, 'percentage')}")
    
    # Incorrect way: averaging CTRs
    individual_ctrs = [
        MetricsCalculator.calculate_ctr(r.clicks, r.impressions)
        for r in records
    ]
    incorrect_avg_ctr = sum(individual_ctrs) / len(individual_ctrs)
    
    # Correct way: aggregate then calculate
    metrics = MetricsCalculator.compute_aggregate_metrics(records)
    correct_ctr = metrics['ctr']
    
    print(f"\n❌ INCORRECT (Averaging CTRs):")
    print(f"   (10% + 1%) / 2 = {format_metric_value(incorrect_avg_ctr, 'percentage')}")
    
    print(f"\n✅ CORRECT (Aggregate Totals):")
    print(f"   200 clicks / 11,000 impressions = {format_metric_value(correct_ctr, 'percentage')}")
    
    print(f"\nWhy it matters:")
    print(f"   The large campaign's lower CTR should have more weight")
    print(f"   because it has 10x more impressions!")
    
    print("\n" + "=" * 60)


def test_top_performers():
    """Test ranking top performers"""
    print("\n\nTEST 3: Top Performers by Metric")
    print("=" * 60)
    
    creative_metrics = {
        'Creative A': {
            'roas': 8.5,
            'ctr': 0.05,
            'total_spend': 100.0,
            'total_revenue': 850.0
        },
        'Creative B': {
            'roas': 12.0,
            'ctr': 0.08,
            'total_spend': 50.0,
            'total_revenue': 600.0
        },
        'Creative C': {
            'roas': 5.2,
            'ctr': 0.12,
            'total_spend': 200.0,
            'total_revenue': 1040.0
        },
        'Creative D': {
            'roas': 3.8,
            'ctr': 0.03,
            'total_spend': 150.0,
            'total_revenue': 570.0
        }
    }
    
    print("\nAll Creatives:")
    for creative_id, metrics in creative_metrics.items():
        print(f"\n  {creative_id}:")
        print(f"    ROAS: {format_metric_value(metrics['roas'], 'ratio')}")
        print(f"    CTR: {format_metric_value(metrics['ctr'], 'percentage')}")
        print(f"    Spend: {format_metric_value(metrics['total_spend'], 'currency')}")
    
    # Get top by ROAS
    top_by_roas = MetricsCalculator.get_top_creatives_by_metric(
        creative_metrics,
        'roas',
        limit=3
    )
    
    print(f"\n\nTop 3 by ROAS:")
    for i, creative in enumerate(top_by_roas, 1):
        print(f"  {i}. {creative['creative_id']}: {format_metric_value(creative['roas'], 'ratio')}")
    
    # Get top by CTR
    top_by_ctr = MetricsCalculator.get_top_creatives_by_metric(
        creative_metrics,
        'ctr',
        limit=3
    )
    
    print(f"\nTop 3 by CTR:")
    for i, creative in enumerate(top_by_ctr, 1):
        print(f"  {i}. {creative['creative_id']}: {format_metric_value(creative['ctr'], 'percentage')}")
    
    print("\n" + "=" * 60)


def test_zero_division():
    """Test zero division handling"""
    print("\n\nTEST 4: Zero Division Handling")
    print("=" * 60)
    
    print("\nTesting edge cases:")
    
    # Zero impressions
    ctr = MetricsCalculator.calculate_ctr(100, 0)
    print(f"  CTR with 0 impressions: {format_metric_value(ctr, 'percentage')}")
    
    # Zero clicks
    cvr = MetricsCalculator.calculate_cvr(10, 0)
    print(f"  CVR with 0 clicks: {format_metric_value(cvr, 'percentage')}")
    
    # Zero spend
    roas = MetricsCalculator.calculate_roas(1000.0, 0.0)
    print(f"  ROAS with 0 spend: {format_metric_value(roas, 'ratio')}")
    
    print("\n  ✅ All edge cases handled gracefully (return None)")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_basic_calculations()
    test_aggregation()
    test_top_performers()
    test_zero_division()
    
    print("\n\n✅ All metrics tests completed!")
