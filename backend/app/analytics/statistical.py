"""Statistical analysis for Creative DNA"""
from scipy.stats import mannwhitneyu
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging


logger = logging.getLogger(__name__)


class StatisticalAnalyzer:
    """Statistical analysis for comparing creative features against performance metrics"""
    
    # Minimum sample size per group
    MIN_SAMPLE_SIZE = 5
    
    @staticmethod
    def mann_whitney_test(
        group_positive: List[float],
        group_negative: List[float]
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Perform Mann-Whitney U test
        
        Args:
            group_positive: Values for positive group
            group_negative: Values for negative group
            
        Returns:
            Tuple of (p_value, effect_size) or (None, None) if insufficient data
        """
        if len(group_positive) < StatisticalAnalyzer.MIN_SAMPLE_SIZE or \
           len(group_negative) < StatisticalAnalyzer.MIN_SAMPLE_SIZE:
            return None, None
        
        try:
            # Perform Mann-Whitney U test
            statistic, p_value = mannwhitneyu(
                group_positive,
                group_negative,
                alternative='two-sided'
            )
            
            # Calculate rank-biserial effect size
            effect_size = StatisticalAnalyzer._calculate_rank_biserial_effect_size(
                group_positive,
                group_negative,
                statistic
            )
            
            return float(p_value), float(effect_size)
        
        except Exception as e:
            logger.error(f"Error in Mann-Whitney test: {str(e)}")
            return None, None
    
    @staticmethod
    def _calculate_rank_biserial_effect_size(
        group_positive: List[float],
        group_negative: List[float],
        u_statistic: float
    ) -> float:
        """
        Calculate rank-biserial correlation effect size
        
        Formula: r = 1 - (2U) / (n1 * n2)
        where U is the Mann-Whitney U statistic
        
        Args:
            group_positive: Values for positive group
            group_negative: Values for negative group
            u_statistic: Mann-Whitney U statistic
            
        Returns:
            Effect size between -1 and 1
        """
        n1 = len(group_positive)
        n2 = len(group_negative)
        
        # Rank-biserial correlation
        r = 1 - (2 * u_statistic) / (n1 * n2)
        
        return float(r)
    
    @staticmethod
    def calculate_medians_and_difference(
        group_positive: List[float],
        group_negative: List[float]
    ) -> Tuple[float, float, float]:
        """
        Calculate medians and percent difference
        
        Args:
            group_positive: Values for positive group
            group_negative: Values for negative group
            
        Returns:
            Tuple of (positive_median, negative_median, percent_difference)
        """
        positive_median = float(np.median(group_positive))
        negative_median = float(np.median(group_negative))
        
        # Calculate percent difference
        if negative_median != 0:
            percent_difference = ((positive_median - negative_median) / abs(negative_median)) * 100
        else:
            percent_difference = 0 if positive_median == 0 else float('inf')
        
        return positive_median, negative_median, float(percent_difference)
    
    @staticmethod
    def determine_evidence_tier(
        sample_size_positive: int,
        sample_size_negative: int,
        p_value: Optional[float],
        effect_size: Optional[float],
        percent_difference: float
    ) -> str:
        """
        Determine evidence tier based on statistical results
        
        Tiers:
        - strong: Statistically significant + meaningful effect + sufficient sample
        - moderate: Meaningful effect with weaker statistical evidence
        - weak: Small effect or weak statistical evidence
        - no_clear_evidence: Little/no observed difference
        - insufficient_evidence: Sample size below minimum
        
        Args:
            sample_size_positive: Size of positive group
            sample_size_negative: Size of negative group
            p_value: P-value from statistical test
            effect_size: Effect size
            percent_difference: Percent difference between medians
            
        Returns:
            Evidence tier string
        """
        # Check minimum sample size
        if sample_size_positive < StatisticalAnalyzer.MIN_SAMPLE_SIZE or \
           sample_size_negative < StatisticalAnalyzer.MIN_SAMPLE_SIZE:
            return "insufficient_evidence"
        
        # If no statistical test results
        if p_value is None or effect_size is None:
            return "insufficient_evidence"
        
        # Check for meaningful difference
        meaningful_difference = abs(percent_difference) >= 10  # At least 10% difference
        
        # Check statistical significance
        statistically_significant = p_value < 0.05
        
        # Check effect size magnitude
        large_effect = abs(effect_size) >= 0.5
        medium_effect = abs(effect_size) >= 0.3
        
        # Determine tier
        if statistically_significant and large_effect and meaningful_difference:
            return "strong"
        elif (statistically_significant and medium_effect) or (large_effect and meaningful_difference):
            return "moderate"
        elif statistically_significant or medium_effect or meaningful_difference:
            return "weak"
        elif abs(percent_difference) < 5:
            return "no_clear_evidence"
        else:
            return "weak"
    
    @staticmethod
    def generate_explanation(
        feature_name: str,
        metric_name: str,
        positive_group: str,
        negative_group: str,
        positive_median: float,
        negative_median: float,
        percent_difference: float,
        evidence_tier: str
    ) -> str:
        """
        Generate human-readable explanation
        
        Args:
            feature_name: Name of the feature
            metric_name: Name of the performance metric
            positive_group: Label for positive group
            negative_group: Label for negative group
            positive_median: Median for positive group
            negative_median: Median for negative group
            percent_difference: Percent difference
            evidence_tier: Evidence tier
            
        Returns:
            Human-readable explanation
        """
        # Format feature and metric names
        feature_display = feature_name.replace('_', ' ').title()
        metric_display = metric_name.upper() if metric_name in ['ctr', 'cvr', 'cpc', 'cpm'] else metric_name.upper()
        
        # Determine comparison direction
        if positive_median > negative_median:
            comparison = "higher"
            direction = "higher"
        elif positive_median < negative_median:
            comparison = "lower"
            direction = "lower"
        else:
            comparison = "similar"
            direction = "similar"
        
        # Base explanation
        if evidence_tier == "insufficient_evidence":
            explanation = (
                f"Insufficient data to determine the relationship between {feature_display} "
                f"and {metric_display}. More creatives are needed in each group."
            )
        elif evidence_tier == "no_clear_evidence":
            explanation = (
                f"Creatives with {positive_group} {feature_display} showed similar {metric_display} "
                f"to creatives with {negative_group} {feature_display} in this dataset. "
                f"The observed difference was minimal ({abs(percent_difference):.1f}%)."
            )
        else:
            # Standard explanation
            explanation = (
                f"Creatives with {positive_group} {feature_display} had {comparison} median {metric_display} "
                f"({positive_median:.4f}) compared to creatives with {negative_group} {feature_display} "
                f"({negative_median:.4f}) in this dataset. "
                f"This represents a {abs(percent_difference):.1f}% {direction} observed {metric_display}."
            )
        
        # Add disclaimer
        explanation += " Association does not imply causation."
        
        return explanation


class CreativeDNAGenerator:
    """Generate Creative DNA insights from features and metrics"""
    
    # Features to analyze (boolean and categorical)
    BOOLEAN_FEATURES = [
        'bright_background',
        'portrait',
        'landscape',
        'human_present'
    ]
    
    # Metrics to compare against
    METRICS = ['roas', 'ctr', 'cvr', 'cpc', 'cpm']
    
    @staticmethod
    def generate_insights(
        features_data: List[Dict[str, Any]],
        metrics_data: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate Creative DNA insights
        
        Args:
            features_data: List of feature dictionaries with creative_id
            metrics_data: Dictionary mapping creative_id to metrics
            
        Returns:
            List of insight dictionaries
        """
        insights = []
        
        # Analyze each boolean feature
        for feature in CreativeDNAGenerator.BOOLEAN_FEATURES:
            # Skip if feature is unavailable
            if all(f.get(feature) is None for f in features_data):
                logger.info(f"Skipping feature {feature} - no data available")
                continue
            
            # Analyze against each metric
            for metric in CreativeDNAGenerator.METRICS:
                insight = CreativeDNAGenerator._analyze_feature_metric(
                    feature,
                    metric,
                    features_data,
                    metrics_data
                )
                
                if insight:
                    insights.append(insight)
        
        return insights
    
    @staticmethod
    def _analyze_feature_metric(
        feature: str,
        metric: str,
        features_data: List[Dict[str, Any]],
        metrics_data: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a single feature-metric combination
        
        Args:
            feature: Feature name
            metric: Metric name
            features_data: List of feature dictionaries
            metrics_data: Dictionary mapping creative_id to metrics
            
        Returns:
            Insight dictionary or None
        """
        # Group creatives by feature value
        positive_group = []  # Feature is True
        negative_group = []  # Feature is False
        
        for feature_record in features_data:
            creative_id = feature_record.get('creative_id')
            feature_value = feature_record.get(feature)
            
            # Skip if feature is None or creative has no metrics
            if feature_value is None or creative_id not in metrics_data:
                continue
            
            metric_value = metrics_data[creative_id].get(metric)
            
            # Skip if metric is None
            if metric_value is None:
                continue
            
            if feature_value is True:
                positive_group.append(metric_value)
            elif feature_value is False:
                negative_group.append(metric_value)
        
        # Check minimum sample sizes
        if len(positive_group) < StatisticalAnalyzer.MIN_SAMPLE_SIZE or \
           len(negative_group) < StatisticalAnalyzer.MIN_SAMPLE_SIZE:
            # Still create insight but mark as insufficient
            positive_median = float(np.median(positive_group)) if positive_group else 0
            negative_median = float(np.median(negative_group)) if negative_group else 0
            
            return {
                'feature_name': feature,
                'metric_name': metric,
                'positive_group': 'True',
                'negative_group': 'False',
                'positive_median': positive_median,
                'negative_median': negative_median,
                'percent_difference': 0,
                'sample_size_positive': len(positive_group),
                'sample_size_negative': len(negative_group),
                'p_value': None,
                'effect_size': None,
                'evidence_tier': 'insufficient_evidence',
                'explanation': StatisticalAnalyzer.generate_explanation(
                    feature, metric, 'True', 'False',
                    positive_median, negative_median, 0,
                    'insufficient_evidence'
                )
            }
        
        # Perform statistical analysis
        p_value, effect_size = StatisticalAnalyzer.mann_whitney_test(
            positive_group,
            negative_group
        )
        
        positive_median, negative_median, percent_difference = \
            StatisticalAnalyzer.calculate_medians_and_difference(
                positive_group,
                negative_group
            )
        
        evidence_tier = StatisticalAnalyzer.determine_evidence_tier(
            len(positive_group),
            len(negative_group),
            p_value,
            effect_size,
            percent_difference
        )
        
        explanation = StatisticalAnalyzer.generate_explanation(
            feature,
            metric,
            'True',
            'False',
            positive_median,
            negative_median,
            percent_difference,
            evidence_tier
        )
        
        return {
            'feature_name': feature,
            'metric_name': metric,
            'positive_group': 'True',
            'negative_group': 'False',
            'positive_median': positive_median,
            'negative_median': negative_median,
            'percent_difference': percent_difference,
            'sample_size_positive': len(positive_group),
            'sample_size_negative': len(negative_group),
            'p_value': p_value,
            'effect_size': effect_size,
            'evidence_tier': evidence_tier,
            'explanation': explanation
        }
