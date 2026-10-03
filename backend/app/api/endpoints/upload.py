"""Upload endpoints for performance data and assets"""
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.core.deps import get_user_analysis
from app.models.analysis import Analysis, AnalysisStatus
from app.models.performance import PerformanceRecord
from app.models.asset import Asset
from app.schemas.validation import PerformanceUploadResponse
from app.schemas.asset import AssetRegister, AssetResponse
from app.services.validation_service import PerformanceValidator, load_performance_file
from typing import List
import logging


router = APIRouter()
logger = logging.getLogger(__name__)


class PlaceholderRegistrationRequest(BaseModel):
    """Request body for registering placeholder assets.

    The creative_ids list must contain IDs that already exist in the
    analysis performance records.  IDs not found in the performance data
    are rejected rather than silently ignored.
    """
    creative_ids: List[str]


@router.post("/{analysis_id}/performance/upload", response_model=PerformanceUploadResponse)
async def upload_performance_data(
    file: UploadFile = File(...),
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Upload performance data (CSV or XLSX)
    
    Expected columns:
    - creative_id (required)
    - platform (required)
    - impressions (required)
    - clicks (required)
    - conversions (required)
    - spend (required)
    - revenue (required)
    - date (optional)
    
    Args:
        file: Uploaded file
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        Upload response with validation results
        
    Raises:
        HTTPException: If file format is invalid or validation fails critically
    """
    # Check file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    file_extension = file.filename.lower().split('.')[-1]
    if file_extension not in ['csv', 'xlsx', 'xls']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {file_extension}. Supported formats: CSV, XLSX, XLS"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Load into DataFrame
        df = load_performance_file(content, file.filename)
        
        # Validate
        validator = PerformanceValidator()
        validation_result, valid_df = validator.validate_file(df)
        
        # If there are blocking errors, return validation result without saving
        if not validation_result.valid:
            return PerformanceUploadResponse(
                validation=validation_result,
                records_created=0,
                message="Validation failed - no records were saved"
            )
        
        # Delete existing performance records for this analysis
        db.query(PerformanceRecord).filter(
            PerformanceRecord.analysis_id == analysis.id
        ).delete()
        
        # Save valid records
        records_created = 0
        
        for _, row in valid_df.iterrows():
            record = PerformanceRecord(
                analysis_id=analysis.id,
                creative_id=str(row['creative_id']),
                platform=str(row['platform']),
                impressions=int(row['impressions']),
                clicks=int(row['clicks']),
                conversions=int(row['conversions']),
                spend=float(row['spend']),
                revenue=float(row['revenue']),
                date=row.get('date') if 'date' in row and pd.notna(row.get('date')) else None
            )
            db.add(record)
            records_created += 1
        
        # Update analysis status
        if analysis.status == AnalysisStatus.DRAFT:
            analysis.status = AnalysisStatus.UPLOADING
        
        db.commit()
        
        logger.info(f"Uploaded {records_created} performance records for analysis {analysis.id}")
        
        return PerformanceUploadResponse(
            validation=validation_result,
            records_created=records_created,
            message=f"Successfully uploaded {records_created} performance records",
            creative_ids=sorted(valid_df['creative_id'].astype(str).unique().tolist()) if records_created > 0 else []
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Error uploading performance data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )



@router.post("/{analysis_id}/assets/register-placeholders")
def register_placeholder_assets(
    payload: PlaceholderRegistrationRequest,
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Register local_demo placeholder assets for a given list of creative IDs.

    The IDs must already exist in the analysis performance records.
    This endpoint NEVER modifies performance records.
    It NEVER generates creative IDs that were not provided by the caller.

    Request body:
        { "creative_ids": ["creative_001", "creative_002", ...] }
    """
    creative_ids = payload.creative_ids

    if not creative_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="creative_ids must be a non-empty list of strings"
        )

    # Validate that the provided IDs actually exist in the performance records
    existing_perf_ids = {
        r[0]
        for r in db.query(PerformanceRecord.creative_id)
                   .filter(PerformanceRecord.analysis_id == analysis.id)
                   .distinct()
                   .all()
    }

    registered = []
    skipped_existing = []
    rejected_unknown = []

    for raw_id in creative_ids:
        cid = str(raw_id).strip()
        if not cid:
            continue

        if cid not in existing_perf_ids:
            rejected_unknown.append(cid)
            continue

        existing_asset = db.query(Asset).filter(
            Asset.analysis_id == analysis.id,
            Asset.creative_id == cid
        ).first()

        if existing_asset:
            skipped_existing.append(cid)
            continue

        asset = Asset(
            analysis_id=analysis.id,
            creative_id=cid,
            filename=f"{cid}.placeholder",
            source="local_demo"
        )
        db.add(asset)
        registered.append(cid)

    if registered:
        # Update status if still draft
        if analysis.status == AnalysisStatus.DRAFT:
            analysis.status = AnalysisStatus.UPLOADING
        db.commit()

    response: dict = {
        "registered": registered,
        "skipped_already_existed": skipped_existing,
        "rejected_not_in_performance_data": rejected_unknown,
        "registered_count": len(registered),
    }

    if rejected_unknown:
        response["warning"] = (
            f"{len(rejected_unknown)} ID(s) were not registered because they do not "
            f"appear in the performance data for this analysis: {', '.join(rejected_unknown)}"
        )

    return response


@router.post("/{analysis_id}/assets/register", response_model=AssetResponse)
def register_asset(
    asset_data: AssetRegister,
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Register a creative asset after a successful Cloudinary upload.

    Idempotent: if an asset with the same creative_id already exists for
    this analysis, the existing record is returned (HTTP 200) rather than
    raising a 409.  This prevents spurious upload-error banners when the
    same image is uploaded twice (e.g. after a page refresh) and ensures
    every successful Cloudinary upload always results in a registered asset.

    Args:
        asset_data: Asset registration data
        analysis: Analysis object (verified by dependency)
        db: Database session

    Returns:
        Registered asset (new or existing)
    """
    existing_asset = db.query(Asset).filter(
        Asset.analysis_id == analysis.id,
        Asset.creative_id == asset_data.creative_id
    ).first()

    if existing_asset:
        # Update Cloudinary fields if we now have real ones (upgrading a placeholder)
        upgraded = False
        if asset_data.source == 'cloudinary' and existing_asset.source != 'cloudinary':
            existing_asset.source = asset_data.source
            existing_asset.filename = asset_data.filename
            existing_asset.cloudinary_public_id = asset_data.cloudinary_public_id
            existing_asset.cloudinary_url = asset_data.cloudinary_url
            existing_asset.secure_url = asset_data.secure_url
            existing_asset.width = asset_data.width
            existing_asset.height = asset_data.height
            existing_asset.format = asset_data.format
            existing_asset.bytes = asset_data.bytes
            db.commit()
            db.refresh(existing_asset)
            upgraded = True
            logger.info(
                f"Upgraded placeholder asset {asset_data.creative_id} "
                f"to Cloudinary for analysis {analysis.id}"
            )
        else:
            logger.info(
                f"Asset {asset_data.creative_id} already registered for "
                f"analysis {analysis.id} — returning existing record"
            )
        return existing_asset

    # Create new asset
    asset = Asset(
        analysis_id=analysis.id,
        creative_id=asset_data.creative_id,
        filename=asset_data.filename,
        cloudinary_public_id=asset_data.cloudinary_public_id,
        cloudinary_url=asset_data.cloudinary_url,
        secure_url=asset_data.secure_url,
        width=asset_data.width,
        height=asset_data.height,
        format=asset_data.format,
        bytes=asset_data.bytes,
        source=asset_data.source
    )

    db.add(asset)

    # Update analysis status if needed
    if analysis.status == AnalysisStatus.DRAFT:
        analysis.status = AnalysisStatus.UPLOADING

    db.commit()
    db.refresh(asset)

    logger.info(f"Registered asset {asset.creative_id} for analysis {analysis.id}")

    return asset


@router.get("/{analysis_id}/assets/coverage")
def get_asset_coverage(
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Return asset coverage summary for an analysis.

    Compares unique creative_ids in performance_records against registered
    real Cloudinary assets.  The frontend uses this to show the user exactly
    which creatives are missing before starting the pipeline.

    Returns:
        {
          "csv_creative_ids": [...],       # from performance_records
          "registered_real_ids": [...],    # source == 'cloudinary' with secure_url
          "registered_placeholder_ids": [...],
          "missing_ids": [...],            # csv_ids not in real assets
          "total_csv":  int,
          "total_real": int,
          "total_placeholders": int,
          "total_missing": int,
          "coverage_complete": bool,       # true when total_missing == 0
        }
    """
    csv_ids = sorted(set(
        r[0] for r in
        db.query(PerformanceRecord.creative_id)
          .filter(PerformanceRecord.analysis_id == analysis.id)
          .distinct()
          .all()
    ))

    real_assets = db.query(Asset).filter(
        Asset.analysis_id == analysis.id,
        Asset.source == 'cloudinary',
    ).all()
    real_ids = {a.creative_id for a in real_assets if a.secure_url}

    placeholder_assets = db.query(Asset).filter(
        Asset.analysis_id == analysis.id,
        Asset.source == 'local_demo',
    ).all()
    placeholder_ids = {a.creative_id for a in placeholder_assets}

    missing_ids = sorted(set(csv_ids) - real_ids)

    return {
        "csv_creative_ids": csv_ids,
        "registered_real_ids": sorted(real_ids),
        "registered_placeholder_ids": sorted(placeholder_ids),
        "missing_ids": missing_ids,
        "total_csv": len(csv_ids),
        "total_real": len(real_ids),
        "total_placeholders": len(placeholder_ids),
        "total_missing": len(missing_ids),
        "coverage_complete": len(missing_ids) == 0,
    }


@router.get("/{analysis_id}/assets/list", response_model=List[AssetResponse])
def list_assets(
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    List all assets for an analysis
    
    Args:
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        List of assets
    """
    assets = db.query(Asset).filter(
        Asset.analysis_id == analysis.id
    ).all()
    
    return assets


@router.delete("/{analysis_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: int,
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Delete an asset
    
    Args:
        asset_id: Asset ID to delete
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        No content
        
    Raises:
        HTTPException: If asset not found
    """
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.analysis_id == analysis.id
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    db.delete(asset)
    db.commit()
    
    return None
