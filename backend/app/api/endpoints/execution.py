"""Analysis execution endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_user_analysis
from app.models.analysis import Analysis, AnalysisStatus
from app.schemas.analysis import AnalysisStatusResponse
from app.services.analysis_service import AnalysisService
import logging


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{analysis_id}/run", response_model=AnalysisStatusResponse)
def run_analysis(
    background_tasks: BackgroundTasks,
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db)
):
    """
    Start running an analysis
    
    This endpoint initiates the analysis pipeline which includes:
    1. Loading data
    2. Validating data
    3. Computing metrics
    4. Extracting creative features
    5. Running statistical analysis
    6. Building Creative DNA
    7. Finalizing results
    
    The pipeline supports both performance-only and real-asset workflows:
    - Performance-only: Skips visual analysis and Creative DNA
    - Real assets: Extracts features and generates DNA insights
    
    Args:
        background_tasks: FastAPI background tasks
        analysis: Analysis object (verified by dependency)
        db: Database session
        
    Returns:
        Analysis status
        
    Raises:
        HTTPException: If analysis is not in a valid state to run
    """
    # Verify analysis has performance data to process
    if len(analysis.performance_records) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot run analysis without performance data. Please upload a CSV first."
        )
    
    # Check if analysis is already processing or completed
    if analysis.status in [AnalysisStatus.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis is already processing"
        )
    
    # Log asset coverage for diagnostics (not blocking)
    performance_creative_ids = set(r.creative_id for r in analysis.performance_records)
    asset_creative_ids = set(a.creative_id for a in analysis.assets)
    missing_assets = performance_creative_ids - asset_creative_ids
    
    if missing_assets and len(missing_assets) < len(performance_creative_ids):
        logger.warning(
            f"Analysis {analysis.id}: Partial asset coverage. "
            f"{len(missing_assets)}/{len(performance_creative_ids)} creative IDs "
            f"have no registered assets: {sorted(list(missing_assets))[:5]}"
        )
    elif missing_assets:
        logger.info(
            f"Analysis {analysis.id}: Performance-only workflow. "
            f"No assets registered for {len(performance_creative_ids)} creative IDs."
        )
    
    # Update status to processing
    analysis = AnalysisService.start_processing(db, analysis)
    
    # Schedule the analysis pipeline in the background
    # Note: In production, this should use a task queue like Celery
    background_tasks.add_task(run_analysis_pipeline, analysis.id)
    
    return AnalysisStatusResponse(
        id=analysis.id,
        status=analysis.status.value,
        current_stage=analysis.current_stage,
        error_message=analysis.error_message
    )


def run_analysis_pipeline(analysis_id: int):
    """
    Run the complete analysis pipeline
    
    Args:
        analysis_id: ID of the analysis to process
    """
    from app.db.session import SessionLocal
    from app.services.pipeline import AnalysisPipeline
    
    db = SessionLocal()
    
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        
        if not analysis:
            logger.error(f"Analysis {analysis_id} not found")
            return
        
        logger.info(f"Running analysis pipeline for analysis {analysis_id}")
        
        # Run the complete pipeline
        success = AnalysisPipeline.run_complete_pipeline(db, analysis)
        
        if success:
            logger.info(f"Analysis {analysis_id} completed successfully")
        else:
            logger.error(f"Analysis {analysis_id} failed")
        
    except Exception as e:
        logger.error(f"Error running analysis {analysis_id}: {str(e)}", exc_info=True)
        
        if analysis:
            AnalysisService.mark_failed(
                db,
                analysis,
                f"Pipeline error: {str(e)}"
            )
    
    finally:
        db.close()
