"""Creative repurposing endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.core.deps import get_user_analysis
from app.core.cloudinary_config import is_cloudinary_available, generate_transformation_url
from app.models.analysis import Analysis
from app.models.asset import Asset
from app.models.generated_asset import GeneratedAsset
from app.schemas.asset import RepurposeRequest, GeneratedAssetResponse
import logging


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{analysis_id}/repurpose", response_model=GeneratedAssetResponse)
def repurpose_asset(
    repurpose_data: RepurposeRequest,
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Repurpose a creative asset into a different format using Cloudinary transformations
    
    Supported formats:
    - 4:5 (Instagram portrait)
    - 9:16 (Story format)
    - 16:9 (Landscape/YouTube)
    - 1:1 (Square/Feed)
    
    Args:
        repurpose_data: Repurposing request
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        Generated asset with transformed URL
        
    Raises:
        HTTPException: If Cloudinary is not configured or asset not found
    """
    # Check Cloudinary availability
    if not is_cloudinary_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary is not configured. Repurposing features require Cloudinary."
        )
    
    # Get source asset
    source_asset = db.query(Asset).filter(
        Asset.id == repurpose_data.source_asset_id,
        Asset.analysis_id == analysis.id
    ).first()
    
    if not source_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source asset not found"
        )
    
    # Check if source is from Cloudinary
    if source_asset.source != "cloudinary" or not source_asset.cloudinary_public_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Asset must be uploaded to Cloudinary before repurposing. Please upload this creative to Cloudinary first."
        )
    
    # Validate format
    valid_formats = ["4:5", "9:16", "16:9", "1:1"]
    if repurpose_data.format not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Supported formats: {', '.join(valid_formats)}"
        )
    
    try:
        # Generate transformation URL
        transformed_url = generate_transformation_url(
            public_id=source_asset.cloudinary_public_id,
            format=repurpose_data.format
        )
        
        # Check if this transformation already exists
        existing = db.query(GeneratedAsset).filter(
            GeneratedAsset.analysis_id == analysis.id,
            GeneratedAsset.source_asset_id == source_asset.id,
            GeneratedAsset.format == repurpose_data.format
        ).first()
        
        if existing:
            # Update existing
            existing.generated_url = transformed_url
            existing.transformation = {
                "format": repurpose_data.format,
                "crop": "fill",
                "gravity": "auto"
            }
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new generated asset
        generated_asset = GeneratedAsset(
            analysis_id=analysis.id,
            source_asset_id=source_asset.id,
            format=repurpose_data.format,
            transformation={
                "format": repurpose_data.format,
                "crop": "fill",
                "gravity": "auto"
            },
            generated_url=transformed_url
        )
        
        db.add(generated_asset)
        db.commit()
        db.refresh(generated_asset)
        
        logger.info(f"Generated {repurpose_data.format} variant for asset {source_asset.id}")
        
        return generated_asset
    
    except Exception as e:
        logger.error(f"Error generating transformation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate transformation: {str(e)}"
        )


@router.get("/{analysis_id}/generated-assets", response_model=List[GeneratedAssetResponse])
def list_generated_assets(
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    List all generated assets for an analysis
    
    Args:
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        List of generated assets
    """
    generated_assets = db.query(GeneratedAsset).filter(
        GeneratedAsset.analysis_id == analysis.id
    ).all()
    
    return generated_assets


@router.delete("/{analysis_id}/generated-assets/{generated_asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_generated_asset(
    generated_asset_id: int,
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Delete a generated asset
    
    Args:
        generated_asset_id: Generated asset ID to delete
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        No content
        
    Raises:
        HTTPException: If generated asset not found
    """
    generated_asset = db.query(GeneratedAsset).filter(
        GeneratedAsset.id == generated_asset_id,
        GeneratedAsset.analysis_id == analysis.id
    ).first()
    
    if not generated_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated asset not found"
        )
    
    db.delete(generated_asset)
    db.commit()
    
    return None
