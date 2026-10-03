"""Analysis endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.core.deps import get_current_user, get_user_analysis
from app.models.user import User
from app.models.analysis import Analysis, AnalysisStatus
from app.schemas.analysis import AnalysisCreate, AnalysisResponse, AnalysisStatusResponse


router = APIRouter()


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
def create_analysis(
    analysis_data: AnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new analysis."""
    analysis = Analysis(
        user_id=current_user.id,
        name=analysis_data.name,
        description=analysis_data.description,
        status=AnalysisStatus.DRAFT,
        current_stage=None
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@router.get("", response_model=List[AnalysisResponse])
def list_analyses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all analyses for the current user."""
    analyses = db.query(Analysis).filter(
        Analysis.user_id == current_user.id
    ).order_by(Analysis.created_at.desc()).all()
    return analyses


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis: Analysis = Depends(get_user_analysis)
):
    """Get a specific analysis."""
    return analysis


@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
def get_analysis_status(
    analysis: Analysis = Depends(get_user_analysis)
):
    """Get analysis status."""
    return AnalysisStatusResponse(
        id=analysis.id,
        status=analysis.status.value,
        current_stage=analysis.current_stage,
        error_message=analysis.error_message
    )


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """Delete an analysis."""
    db.delete(analysis)
    db.commit()
    return None


@router.post("/{analysis_id}/seed-demo")
def seed_demo_data(
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Seed an analysis with deterministic demo performance data and placeholder assets.

    SAFETY GUARD: This endpoint REFUSES to run if the analysis already contains
    real performance data (i.e. data uploaded by the user).  It is intended only
    for a brand-new, empty analysis so that demo data never contaminates an
    analysis that holds user-uploaded records.

    The endpoint:
      1. Checks that zero performance records currently exist in the analysis.
      2. Generates ~400 deterministic demo performance records across 40 creatives.
      3. Registers local_demo placeholder assets for those 40 creative IDs.

    It does NOT delete or overwrite any existing user data.
    """
    from app.models.performance import PerformanceRecord
    from app.models.asset import Asset
    from app.services.sample_data import generate_demo_dataset
    import pandas as pd

    # ── Safety guard ──────────────────────────────────────────────────────────
    existing_records = db.query(PerformanceRecord).filter(
        PerformanceRecord.analysis_id == analysis.id
    ).count()

    if existing_records > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"This analysis already contains {existing_records} performance record(s) "
                "that were uploaded by the user. Demo data cannot be seeded into an analysis "
                "that already has data — this would contaminate your real dataset. "
                "Create a new empty analysis first if you want to explore the demo."
            )
        )

    # ── Generate deterministic demo dataset ───────────────────────────────────
    df, num_creatives = generate_demo_dataset()

    records_created = 0
    for _, row in df.iterrows():
        record = PerformanceRecord(
            analysis_id=analysis.id,
            creative_id=str(row['creative_id']),
            platform=str(row['platform']),
            impressions=int(row['impressions']),
            clicks=int(row['clicks']),
            conversions=int(row['conversions']),
            spend=float(row['spend']),
            revenue=float(row['revenue']),
            date=pd.to_datetime(row['date']).date() if row.get('date') else None
        )
        db.add(record)
        records_created += 1

    # ── Register placeholder assets for each demo creative ID ─────────────────
    unique_ids = df['creative_id'].unique()
    assets_created = 0
    for creative_id in unique_ids:
        existing_asset = db.query(Asset).filter(
            Asset.analysis_id == analysis.id,
            Asset.creative_id == str(creative_id)
        ).first()
        if not existing_asset:
            asset = Asset(
                analysis_id=analysis.id,
                creative_id=str(creative_id),
                filename=f"{creative_id}.demo",
                source="local_demo"
            )
            db.add(asset)
            assets_created += 1

    # Update status to reflect data is present
    if analysis.status == AnalysisStatus.DRAFT:
        analysis.status = AnalysisStatus.UPLOADING

    db.commit()

    return {
        "message": "Demo data seeded successfully",
        "records_created": records_created,
        "assets_created": assets_created
    }
