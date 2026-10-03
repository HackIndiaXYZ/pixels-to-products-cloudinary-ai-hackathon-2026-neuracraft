"""Metrics computation for performance data"""
from typing import Dict, List, Optional, Any
import pandas as pd
from sqlalchemy.orm import Session
from app.models.performance import PerformanceRecord
import logging


logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Calculator for marketing performance metrics
    
    Important: Metrics are computed using aggregated totals, not averaged ratios,
    to ensure mathematical correctness.
    """
    
    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: Optional[float] = None) -> Optional[float]:
        """
        Safely divide two numbers, handling zero division
        
        Args:
            numerator: Top number
            denominator: Bottom number
            default: Default value if division fails
            
        Returns:
            Result of division or default value
        """
        if denominator == 0 or pd.isna(denominator):
            return default
        
        result = numerator / denominator
        
        # Check for NaN or infinity
        if pd.isna(result) or result == float('inf') or result == float('-inf'):
            return default
        
        return result
    
    @staticmethod
    def calculate_ctr(clicks: int, impressions: int) -> Optional[float]:
        """
        Calculate Click-Through Rate
        
        Formula: clicks / impressions
        
        Args:
            clicks: Total clicks
            impressions: Total impressions
            
        Returns:
            CTR as decimal (e.g., 0.05 for 5%) or None
        """
        return MetricsCalculator.safe_divide(clicks, impressions)
    
    @staticmethod
    def calculate_cvr(conversions: int, clicks: int) -> Optional[float]:
        """
        Calculate Conversion Rate
        
        Formula: conversions / clicks
        
        Args:
            conversions: Total conversions
            clicks: Total clicks
            
        Returns:
            CVR as decimal or None
        """
        return MetricsCalculator.safe_divide(conversions, clicks)
    
    @staticmethod
    def calculate_cpc(spend: float, clicks: int) -> Optional[float]:
        """
        Calculate Cost Per Click
        
        Formula: spend / clicks
        
        Args:
            spend: Total spend
            clicks: Total clicks
            
        Returns:
            CPC or None
        """
        return MetricsCalculator.safe_divide(spend, clicks)
    
    @staticmethod
    def calculate_roas(revenue: float, spend: float) -> Optional[float]:
        """
        Calculate Return on Ad Spend
        
        Formula: revenue / spend
        
        Args:
            revenue: Total revenue
            spend: Total spend
            
        Returns:
            ROAS or None
        """
        return MetricsCalculator.safe_divide(revenue, spend)
    
    @staticmethod
    def calculate_cpm(spend: float, impressions: int) -> Optional[float]:
        """
        Calculate Cost Per Mille (thousand impressions)
        
        Formula: (spend / impressions) * 1000
        
        Args:
            spend: Total spend
            impressions: Total impressions
            
        Returns:
            CPM or None
        """
        cpm = MetricsCalculator.safe_divide(spend, impressions)
        return cpm * 1000 if cpm is not None else None
    
    @staticmethod
    def compute_aggregate_metrics(records: List[PerformanceRecord]) -> Dict[str, Any]:
        """
        Compute aggregate metrics from performance records
        
        Args:
            records: List of performance records
            
        Returns:
            Dictionary with computed metrics
        """
        if not records:
            return {
                "total_impressions": 0,
                "total_clicks": 0,
                "total_conversions": 0,
                "total_spend": 0.0,
                "total_revenue": 0.0,
                "ctr": None,
                "cvr": None,
                "cpc": None,
                "roas": None,
                "cpm": None
            }
        
        # Aggregate totals
        total_impressions = sum(r.impressions for r in records)
        total_clicks = sum(r.clicks for r in records)
        total_conversions = sum(r.conversions for r in records)
        total_spend = sum(r.spend for r in records)
        total_revenue = sum(r.revenue for r in records)
        
        # Compute derived metrics from aggregates
        ctr = MetricsCalculator.calculate_ctr(total_clicks, total_impressions)
        cvr = MetricsCalculator.calculate_cvr(total_conversions, total_clicks)
        cpc = MetricsCalculator.calculate_cpc(total_spend, total_clicks)
        roas = MetricsCalculator.calculate_roas(total_revenue, total_spend)
        cpm = MetricsCalculator.calculate_cpm(total_spend, total_impressions)
        
        return {
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_spend": round(total_spend, 2),
            "total_revenue": round(total_revenue, 2),
            "ctr": round(ctr, 6) if ctr is not None else None,
            "cvr": round(cvr, 6) if cvr is not None else None,
            "cpc": round(cpc, 4) if cpc is not None else None,
            "roas": round(roas, 4) if roas is not None else None,
            "cpm": round(cpm, 4) if cpm is not None else None
        }
    
    @staticmethod
    def compute_creative_metrics(db: Session, analysis_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Compute metrics for each creative in an analysis
        
        Args:
            db: Database session
            analysis_id: Analysis ID
            
        Returns:
            Dictionary mapping creative_id to metrics
        """
        records = db.query(PerformanceRecord).filter(
            PerformanceRecord.analysis_id == analysis_id
        ).all()
        
        # Group by creative_id
        creative_records: Dict[str, List[PerformanceRecord]] = {}
        for record in records:
            if record.creative_id not in creative_records:
                creative_records[record.creative_id] = []
            creative_records[record.creative_id].append(record)
        
        # Compute metrics for each creative
        creative_metrics = {}
        for creative_id, records_list in creative_records.items():
            creative_metrics[creative_id] = MetricsCalculator.compute_aggregate_metrics(records_list)
        
        return creative_metrics
    
    @staticmethod
    def compute_platform_metrics(db: Session, analysis_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Compute metrics for each platform in an analysis
        
        Args:
            db: Database session
            analysis_id: Analysis ID
            
        Returns:
            Dictionary mapping platform to metrics
        """
        records = db.query(PerformanceRecord).filter(
            PerformanceRecord.analysis_id == analysis_id
        ).all()
        
        # Group by platform
        platform_records: Dict[str, List[PerformanceRecord]] = {}
        for record in records:
            if record.platform not in platform_records:
                platform_records[record.platform] = []
            platform_records[record.platform].append(record)
        
        # Compute metrics for each platform
        platform_metrics = {}
        for platform, records_list in platform_records.items():
            platform_metrics[platform] = MetricsCalculator.compute_aggregate_metrics(records_list)
        
        return platform_metrics
    
    @staticmethod
    def get_top_creatives_by_metric(
        creative_metrics: Dict[str, Dict[str, Any]],
        metric: str,
        limit: int = 10,
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get top creatives by a specific metric
        
        Args:
            creative_metrics: Dictionary of creative metrics
            metric: Metric name (e.g., 'roas', 'ctr')
            limit: Number of top creatives to return
            ascending: If True, return lowest values; if False, return highest
            
        Returns:
            List of creatives with their metrics, sorted by the specified metric
        """
        # Filter out creatives where metric is None
        valid_creatives = [
            {
                "creative_id": creative_id,
                **metrics
            }
            for creative_id, metrics in creative_metrics.items()
            if metrics.get(metric) is not None
        ]
        
        # Sort by metric
        sorted_creatives = sorted(
            valid_creatives,
            key=lambda x: x[metric],
            reverse=not ascending
        )
        
        return sorted_creatives[:limit]


def format_metric_value(value: Optional[float], metric_type: str) -> str:
    """
    Format a metric value for display
    
    Args:
        value: Metric value
        metric_type: Type of metric ('percentage', 'currency', 'number', 'ratio')
        
    Returns:
        Formatted string
    """
    if value is None:
        return "N/A"
    
    if metric_type == 'percentage':
        return f"{value * 100:.2f}%"
    elif metric_type == 'currency':
        return f"${value:,.2f}"
    elif metric_type == 'number':
        return f"{int(value):,}"
    elif metric_type == 'ratio':
        return f"{value:.2f}x"
    else:
        return f"{value:.2f}"
