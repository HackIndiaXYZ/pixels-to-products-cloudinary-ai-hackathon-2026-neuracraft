"""Creative DNA insight model"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class CreativeDNAInsight(Base):
    """Creative DNA insights from statistical analysis"""
    
    __tablename__ = "creative_dna_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    
    # Feature and metric being compared
    feature_name = Column(String, nullable=False, index=True)
    metric_name = Column(String, nullable=False, index=True)
    
    # Groups
    positive_group = Column(String, nullable=False)  # e.g., "True", "portrait"
    negative_group = Column(String, nullable=False)  # e.g., "False", "landscape"
    
    # Statistical results
    positive_median = Column(Float, nullable=False)
    negative_median = Column(Float, nullable=False)
    percent_difference = Column(Float, nullable=False)
    sample_size_positive = Column(Integer, nullable=False)
    sample_size_negative = Column(Integer, nullable=False)
    p_value = Column(Float, nullable=True)
    effect_size = Column(Float, nullable=True)
    
    # Evidence tier
    evidence_tier = Column(String, nullable=False)  # strong, moderate, weak, no_clear_evidence, insufficient_evidence
    
    # Human-readable explanation
    explanation = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis = relationship("Analysis", back_populates="creative_dna_insights")
