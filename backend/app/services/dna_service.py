"""Creative DNA service for generating and storing insights"""
from sqlalchemy.orm import Session
from app.models.dna_insight import CreativeDNAInsight
from app.models.feature import CreativeFeature
from app.analytics.statistical import CreativeDNAGenerator
from app.analytics.metrics import MetricsCalculator
from typing import List
import logging


logger = logging.getLogger(__name__)


class DNAService:
    """Service for Creative DNA generation"""
    
    @staticmethod
    def generate_dna_for_analysis(db: Session, analysis_id: int) -> int:
        """
        Generate Creative DNA insights for an analysis
        
        Args:
            db: Database session
            analysis_id: Analysis ID
            
        Returns:
            Number of insights generated
        """
        # Get all features for this analysis
        features = db.query(CreativeFeature).filter(
            CreativeFeature.analysis_id == analysis_id
        ).all()
        
        if not features:
            logger.warning(f"No features found for analysis {analysis_id}")
            return 0
        
        # Get creative metrics
        creative_metrics = MetricsCalculator.compute_creative_metrics(db, analysis_id)
        
        if not creative_metrics:
            logger.warning(f"No metrics found for analysis {analysis_id}")
            return 0
        
        # Convert features to dictionaries
        features_data = []
        for feature in features:
            features_data.append({
                'creative_id': feature.creative_id,
                'bright_background': feature.bright_background,
                'portrait': feature.portrait,
                'landscape': feature.landscape,
                'human_present': feature.human_present
            })
        
        # Generate insights
        insights = CreativeDNAGenerator.generate_insights(features_data, creative_metrics)
        
        # Delete existing insights for this analysis
        db.query(CreativeDNAInsight).filter(
            CreativeDNAInsight.analysis_id == analysis_id
        ).delete()
        
        # Save new insights
        saved_count = 0
        for insight in insights:
            dna_insight = CreativeDNAInsight(
                analysis_id=analysis_id,
                feature_name=insight['feature_name'],
                metric_name=insight['metric_name'],
                positive_group=insight['positive_group'],
                negative_group=insight['negative_group'],
                positive_median=insight['positive_median'],
                negative_median=insight['negative_median'],
                percent_difference=insight['percent_difference'],
                sample_size_positive=insight['sample_size_positive'],
                sample_size_negative=insight['sample_size_negative'],
                p_value=insight['p_value'],
                effect_size=insight['effect_size'],
                evidence_tier=insight['evidence_tier'],
                explanation=insight['explanation']
            )
            
            db.add(dna_insight)
            saved_count += 1
        
        db.commit()
        
        logger.info(f"Generated {saved_count} Creative DNA insights for analysis {analysis_id}")
        
        return saved_count
    
    @staticmethod
    def get_insights(
        db: Session,
        analysis_id: int,
        evidence_tier: str = None
    ) -> List[CreativeDNAInsight]:
        """
        Get Creative DNA insights for an analysis
        
        Args:
            db: Database session
            analysis_id: Analysis ID
            evidence_tier: Optional filter by evidence tier
            
        Returns:
            List of insights
        """
        query = db.query(CreativeDNAInsight).filter(
            CreativeDNAInsight.analysis_id == analysis_id
        )
        
        if evidence_tier:
            query = query.filter(CreativeDNAInsight.evidence_tier == evidence_tier)
        
        return query.all()
    
    @staticmethod
    def get_top_insights(
        db: Session,
        analysis_id: int,
        limit: int = 10
    ) -> List[CreativeDNAInsight]:
        """
        Get top insights by evidence strength
        
        Args:
            db: Database session
            analysis_id: Analysis ID
            limit: Maximum number of insights to return
            
        Returns:
            List of top insights
        """
        # Define evidence tier order
        tier_order = {
            'strong': 1,
            'moderate': 2,
            'weak': 3,
            'no_clear_evidence': 4,
            'insufficient_evidence': 5
        }
        
        insights = DNAService.get_insights(db, analysis_id)
        
        # Sort by evidence tier and percent difference
        sorted_insights = sorted(
            insights,
            key=lambda x: (
                tier_order.get(x.evidence_tier, 99),
                -abs(x.percent_difference)
            )
        )
        
        return sorted_insights[:limit]
