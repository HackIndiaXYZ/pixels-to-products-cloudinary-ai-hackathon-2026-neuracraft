"""Analytics endpoints for retrieving computed metrics"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.db.session import get_db
from app.core.deps import get_user_analysis
from app.models.analysis import Analysis
from app.models.performance import PerformanceRecord
from app.models.asset import Asset
from app.analytics.metrics import MetricsCalculator
from app.services.dna_service import DNAService
from pydantic import BaseModel
import logging


router = APIRouter()
logger = logging.getLogger(__name__)


class DNAInsightResponse(BaseModel):
    """Response schema for Creative DNA insight"""
    id: int
    feature_name: str
    metric_name: str
    positive_group: str
    negative_group: str
    positive_median: float
    negative_median: float
    percent_difference: float
    sample_size_positive: int
    sample_size_negative: int
    p_value: float | None
    effect_size: float | None
    evidence_tier: str
    explanation: str
    
    class Config:
        from_attributes = True


@router.get("/{analysis_id}/overview")
def get_analysis_overview(
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get overview metrics for an analysis
    
    Args:
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        Overview metrics including totals and top performers
    """
    # Get all performance records
    records = db.query(PerformanceRecord).filter(
        PerformanceRecord.analysis_id == analysis.id
    ).all()
    
    # Compute aggregate metrics
    aggregate_metrics = MetricsCalculator.compute_aggregate_metrics(records)
    
    # Get creative metrics
    creative_metrics = MetricsCalculator.compute_creative_metrics(db, analysis.id)
    
    # Get top performers
    top_by_roas = MetricsCalculator.get_top_creatives_by_metric(
        creative_metrics,
        'roas',
        limit=5
    )
    
    top_by_ctr = MetricsCalculator.get_top_creatives_by_metric(
        creative_metrics,
        'ctr',
        limit=5
    )
    
    return {
        "analysis_id": analysis.id,
        "analysis_name": analysis.name,
        "status": analysis.status.value,
        "total_creatives": len(creative_metrics),
        "total_records": len(records),
        "aggregate_metrics": aggregate_metrics,
        "top_by_roas": top_by_roas,
        "top_by_ctr": top_by_ctr
    }


@router.get("/{analysis_id}/performance")
def get_performance_data(
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed performance data for an analysis
    
    Args:
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        Performance data with metrics for each creative and raw records
    """
    # Get all performance records
    records = db.query(PerformanceRecord).filter(
        PerformanceRecord.analysis_id == analysis.id
    ).all()
    
    # Get creative metrics
    creative_metrics = MetricsCalculator.compute_creative_metrics(db, analysis.id)
    
    # Convert to list format
    performance_data = []
    for creative_id, metrics in creative_metrics.items():
        performance_data.append({
            "creative_id": creative_id,
            **metrics
        })
    
    # Sort by ROAS descending
    performance_data.sort(
        key=lambda x: x.get('roas') or 0,
        reverse=True
    )
    
    # Convert records to dict format
    records_data = []
    for record in records:
        records_data.append({
            "creative_id": record.creative_id,
            "platform": record.platform,
            "impressions": record.impressions,
            "clicks": record.clicks,
            "conversions": record.conversions,
            "spend": record.spend,
            "revenue": record.revenue,
            "date": record.date.isoformat() if record.date else None
        })
    
    return {
        "analysis_id": analysis.id,
        "creatives": performance_data,
        "records": records_data
    }


@router.get("/{analysis_id}/assets")
def get_analysis_assets(
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get assets with their performance metrics
    
    Args:
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        Assets with performance metrics
    """
    # Get all assets
    assets = db.query(Asset).filter(
        Asset.analysis_id == analysis.id
    ).all()
    
    # Get creative metrics
    creative_metrics = MetricsCalculator.compute_creative_metrics(db, analysis.id)
    
    # Combine assets with metrics
    assets_with_metrics = []
    for asset in assets:
        metrics = creative_metrics.get(asset.creative_id, {})
        
        assets_with_metrics.append({
            "id": asset.id,
            "creative_id": asset.creative_id,
            "filename": asset.filename,
            "cloudinary_url": asset.cloudinary_url,
            "secure_url": asset.secure_url,
            "width": asset.width,
            "height": asset.height,
            "format": asset.format,
            "source": asset.source,
            "metrics": metrics
        })
    
    return {
        "analysis_id": analysis.id,
        "assets": assets_with_metrics
    }


@router.get("/{analysis_id}/platforms")
def get_platform_metrics(
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get metrics by platform
    
    Args:
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        Metrics grouped by platform
    """
    platform_metrics = MetricsCalculator.compute_platform_metrics(db, analysis.id)
    
    # Convert to list format
    platforms = []
    for platform, metrics in platform_metrics.items():
        platforms.append({
            "platform": platform,
            **metrics
        })
    
    # Sort by spend descending
    platforms.sort(
        key=lambda x: x.get('total_spend') or 0,
        reverse=True
    )
    
    return {
        "analysis_id": analysis.id,
        "platforms": platforms
    }



@router.get("/{analysis_id}/creative-dna", response_model=List[DNAInsightResponse])
def get_creative_dna(
    evidence_tier: str = None,
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Get Creative DNA insights for an analysis
    
    Args:
        evidence_tier: Optional filter by evidence tier
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        List of Creative DNA insights
    """
    insights = DNAService.get_insights(db, analysis.id, evidence_tier)
    return insights


@router.get("/{analysis_id}/insights", response_model=List[DNAInsightResponse])
def get_top_insights(
    limit: int = 10,
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Get top Creative DNA insights ordered by evidence strength
    
    Args:
        limit: Maximum number of insights to return
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        Top Creative DNA insights
    """
    insights = DNAService.get_top_insights(db, analysis.id, limit)
    return insights
