"""Tests for statistical analysis and Creative DNA"""
import pytest
import numpy as np
from app.analytics.statistical import StatisticalAnalyzer, CreativeDNAGenerator


def test_mann_whitney_test():
    """Test Mann-Whitney U test"""
    # Two clearly different groups
    group1 = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    group2 = [7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
    
    p_value, effect_size = StatisticalAnalyzer.mann_whitney_test(group1, group2)
    
    assert p_value is not None
    assert effect_size is not None
    assert p_value < 0.05  # Should be statistically significant
    assert abs(effect_size) > 0.5  # Should have large effect


def test_mann_whitney_insufficient_sample():
    """Test Mann-Whitney with insufficient sample size"""
    group1 = [1.0, 2.0, 3.0]  # Too small
    group2 = [7.0, 8.0, 9.0, 10.0, 11.0]
    
    p_value, effect_size = StatisticalAnalyzer.mann_whitney_test(group1, group2)
    
    assert p_value is None
    assert effect_size is None


def test_median_calculation():
    """Test median and percent difference calculation"""
    group1 = [5.0, 6.0, 7.0, 8.0, 9.0]
    group2 = [3.0, 4.0, 5.0, 6.0, 7.0]
    
    pos_median, neg_median, pct_diff = StatisticalAnalyzer.calculate_medians_and_difference(
        group1, group2
    )
    
    assert pos_median == 7.0
    assert neg_median == 5.0
    assert pct_diff == pytest.approx(40.0, rel=0.1)  # (7-5)/5 * 100 = 40%


def test_evidence_tier_strong():
    """Test strong evidence tier classification"""
    tier = StatisticalAnalyzer.determine_evidence_tier(
        sample_size_positive=20,
        sample_size_negative=20,
        p_value=0.01,  # Significant
        effect_size=0.6,  # Large
        percent_difference=25.0  # Meaningful
    )
    
    assert tier == "strong"


def test_evidence_tier_moderate():
    """Test moderate evidence tier classification"""
    tier = StatisticalAnalyzer.determine_evidence_tier(
        sample_size_positive=15,
        sample_size_negative=15,
        p_value=0.03,  # Significant
        effect_size=0.4,  # Medium
        percent_difference=15.0  # Meaningful
    )
    
    assert tier == "moderate"


def test_evidence_tier_weak():
    """Test weak evidence tier classification"""
    tier = StatisticalAnalyzer.determine_evidence_tier(
        sample_size_positive=10,
        sample_size_negative=10,
        p_value=0.08,  # Not significant
        effect_size=0.25,  # Small
        percent_difference=12.0
    )
    
    assert tier == "weak"


def test_evidence_tier_no_clear_evidence():
    """Test no clear evidence tier"""
    tier = StatisticalAnalyzer.determine_evidence_tier(
        sample_size_positive=10,
        sample_size_negative=10,
        p_value=0.5,  # Not significant
        effect_size=0.1,  # Very small
        percent_difference=3.0  # Small difference
    )
    
    assert tier == "no_clear_evidence"


def test_evidence_tier_insufficient():
    """Test insufficient evidence tier"""
    tier = StatisticalAnalyzer.determine_evidence_tier(
        sample_size_positive=3,  # Too small
        sample_size_negative=10,
        p_value=0.01,
        effect_size=0.6,
        percent_difference=25.0
    )
    
    assert tier == "insufficient_evidence"


def test_explanation_generation():
    """Test human-readable explanation generation"""
    explanation = StatisticalAnalyzer.generate_explanation(
        feature_name="human_present",
        metric_name="roas",
        positive_group="True",
        negative_group="False",
        positive_median=5.2,
        negative_median=3.8,
        percent_difference=36.8,
        evidence_tier="strong"
    )
    
    assert "Human Present" in explanation
    assert "ROAS" in explanation
    assert "5.2" in explanation or "5.20" in explanation
    assert "3.8" in explanation or "3.80" in explanation
    assert "Association does not imply causation" in explanation


def test_explanation_insufficient():
    """Test explanation for insufficient evidence"""
    explanation = StatisticalAnalyzer.generate_explanation(
        feature_name="bright_background",
        metric_name="ctr",
        positive_group="True",
        negative_group="False",
        positive_median=0.05,
        negative_median=0.04,
        percent_difference=25.0,
        evidence_tier="insufficient_evidence"
    )
    
    assert "Insufficient data" in explanation
    assert "Bright Background" in explanation


def test_creative_dna_generation():
    """Test Creative DNA generation"""
    # Sample features data
    features_data = [
        {'creative_id': 'C001', 'human_present': True, 'bright_background': True, 'portrait': True, 'landscape': False},
        {'creative_id': 'C002', 'human_present': True, 'bright_background': False, 'portrait': True, 'landscape': False},
        {'creative_id': 'C003', 'human_present': False, 'bright_background': True, 'portrait': False, 'landscape': True},
        {'creative_id': 'C004', 'human_present': False, 'bright_background': False, 'portrait': False, 'landscape': True},
        {'creative_id': 'C005', 'human_present': True, 'bright_background': True, 'portrait': True, 'landscape': False},
        {'creative_id': 'C006', 'human_present': False, 'bright_background': False, 'portrait': False, 'landscape': True},
        {'creative_id': 'C007', 'human_present': True, 'bright_background': True, 'portrait': True, 'landscape': False},
        {'creative_id': 'C008', 'human_present': False, 'bright_background': False, 'portrait': False, 'landscape': True},
        {'creative_id': 'C009', 'human_present': True, 'bright_background': False, 'portrait': True, 'landscape': False},
        {'creative_id': 'C010', 'human_present': False, 'bright_background': True, 'portrait': False, 'landscape': True},
    ]
    
    # Sample metrics data
    metrics_data = {
        'C001': {'roas': 5.2, 'ctr': 0.05},
        'C002': {'roas': 4.8, 'ctr': 0.048},
        'C003': {'roas': 3.5, 'ctr': 0.035},
        'C004': {'roas': 3.2, 'ctr': 0.032},
        'C005': {'roas': 5.0, 'ctr': 0.052},
        'C006': {'roas': 3.8, 'ctr': 0.038},
        'C007': {'roas': 4.9, 'ctr': 0.049},
        'C008': {'roas': 3.3, 'ctr': 0.033},
        'C009': {'roas': 4.7, 'ctr': 0.047},
        'C010': {'roas': 3.6, 'ctr': 0.036},
    }
    
    # Generate insights
    insights = CreativeDNAGenerator.generate_insights(features_data, metrics_data)
    
    # Should generate insights for multiple feature-metric combinations
    assert len(insights) > 0
    
    # Check insight structure
    insight = insights[0]
    assert 'feature_name' in insight
    assert 'metric_name' in insight
    assert 'positive_median' in insight
    assert 'negative_median' in insight
    assert 'evidence_tier' in insight
    assert 'explanation' in insight


def test_creative_dna_with_none_values():
    """Test Creative DNA generation handles None values correctly"""
    features_data = [
        {'creative_id': 'C001', 'human_present': None, 'bright_background': True, 'portrait': True, 'landscape': False},
        {'creative_id': 'C002', 'human_present': None, 'bright_background': False, 'portrait': False, 'landscape': True},
    ]
    
    metrics_data = {
        'C001': {'roas': 5.2},
        'C002': {'roas': 3.5},
    }
    
    insights = CreativeDNAGenerator.generate_insights(features_data, metrics_data)
    
    # Should not crash, should skip human_present feature
    # Should still generate insights for other features
    feature_names = [i['feature_name'] for i in insights]
    assert 'bright_background' in feature_names
