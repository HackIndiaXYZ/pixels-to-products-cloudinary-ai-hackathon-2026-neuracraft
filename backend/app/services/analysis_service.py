"""Analysis service for managing analysis lifecycle"""
from sqlalchemy.orm import Session
from app.models.analysis import Analysis, AnalysisStatus
from typing import Optional
import logging


logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for managing analysis lifecycle"""
    
    @staticmethod
    def update_status(
        db: Session,
        analysis: Analysis,
        status: AnalysisStatus,
        current_stage: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Analysis:
        """
        Update analysis status and stage
        
        Args:
            db: Database session
            analysis: Analysis to update
            status: New status
            current_stage: Current processing stage
            error_message: Error message if failed
            
        Returns:
            Updated analysis
        """
        analysis.status = status
        analysis.current_stage = current_stage
        
        if error_message:
            analysis.error_message = error_message
        
        db.commit()
        db.refresh(analysis)
        
        logger.info(f"Analysis {analysis.id} status updated to {status.value}, stage: {current_stage}")
        
        return analysis
    
    @staticmethod
    def mark_failed(
        db: Session,
        analysis: Analysis,
        error_message: str
    ) -> Analysis:
        """
        Mark analysis as failed
        
        Args:
            db: Database session
            analysis: Analysis to mark as failed
            error_message: Error message
            
        Returns:
            Updated analysis
        """
        return AnalysisService.update_status(
            db,
            analysis,
            AnalysisStatus.FAILED,
            current_stage=None,
            error_message=error_message
        )
    
    @staticmethod
    def start_processing(db: Session, analysis: Analysis) -> Analysis:
        """
        Start processing an analysis
        
        Args:
            db: Database session
            analysis: Analysis to start processing
            
        Returns:
            Updated analysis
        """
        return AnalysisService.update_status(
            db,
            analysis,
            AnalysisStatus.PROCESSING,
            current_stage="Stage 1: Loading data"
        )
    
    @staticmethod
    def complete_processing(db: Session, analysis: Analysis) -> Analysis:
        """
        Mark analysis as completed
        
        Args:
            db: Database session
            analysis: Analysis to complete
            
        Returns:
            Updated analysis
        """
        return AnalysisService.update_status(
            db,
            analysis,
            AnalysisStatus.COMPLETED,
            current_stage="Completed"
        )
    
    @staticmethod
    def get_analysis_summary(db: Session, analysis: Analysis) -> dict:
        """
        Get summary statistics for an analysis
        
        Args:
            db: Database session
            analysis: Analysis to summarize
            
        Returns:
            Dictionary with summary statistics
        """
        return {
            "id": analysis.id,
            "name": analysis.name,
            "status": analysis.status.value,
            "current_stage": analysis.current_stage,
            "total_assets": len(analysis.assets),
            "total_performance_records": len(analysis.performance_records),
            "total_features": len(analysis.creative_features),
            "total_insights": len(analysis.creative_dna_insights),
            "total_generated_assets": len(analysis.generated_assets),
            "created_at": analysis.created_at.isoformat(),
            "updated_at": analysis.updated_at.isoformat()
        }


# Processing stages for the pipeline
PROCESSING_STAGES = [
    "Stage 1: Loading data",
    "Stage 2: Validating data",
    "Stage 3: Computing metrics",
    "Stage 4: Extracting creative features",
    "Stage 5: Running statistical analysis",
    "Stage 6: Building Creative DNA",
    "Stage 7: Finalizing results",
    "Completed"
]
