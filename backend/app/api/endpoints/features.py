"""Creative features endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.session import get_db
from app.core.deps import get_user_analysis
from app.models.analysis import Analysis
from app.services.feature_service import FeatureService
from pydantic import BaseModel


router = APIRouter()


class FeatureResponse(BaseModel):
    """Response schema for creative features"""
    creative_id: str
    aspect_ratio: float | None
    brightness: float | None
    contrast: float | None
    edge_density: float | None
    dominant_color: str | None
    bright_background: bool | None
    portrait: bool | None
    landscape: bool | None
    human_present: bool | None
    feature_sources: Dict[str, str] | None
    
    class Config:
        from_attributes = True


@router.get("/{analysis_id}/features", response_model=List[FeatureResponse])
def get_creative_features(
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Get all creative features for an analysis
    
    Args:
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        List of creative features
    """
    features = FeatureService.get_all_features(db, analysis.id)
    return features


@router.get("/{analysis_id}/features/{creative_id}", response_model=FeatureResponse)
def get_creative_feature(
    creative_id: str,
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Get features for a specific creative
    
    Args:
        creative_id: Creative ID
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        Creative features
    """
    from fastapi import HTTPException, status
    
    feature = FeatureService.get_features_by_creative_id(db, analysis.id, creative_id)
    
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Features not found for creative {creative_id}"
        )
    
    return feature
