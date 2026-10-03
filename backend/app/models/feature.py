"""Creative feature model for visual characteristics"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class CreativeFeature(Base):
    """Visual features extracted from creative assets"""
    
    __tablename__ = "creative_features"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    creative_id = Column(String, nullable=False, index=True)
    
    # Visual features
    aspect_ratio = Column(Float, nullable=True)
    brightness = Column(Float, nullable=True)
    contrast = Column(Float, nullable=True)
    edge_density = Column(Float, nullable=True)
    dominant_color = Column(String, nullable=True)
    bright_background = Column(Boolean, nullable=True)
    portrait = Column(Boolean, nullable=True)
    landscape = Column(Boolean, nullable=True)
    human_present = Column(Boolean, nullable=True)
    
    # Feature metadata
    feature_sources = Column(JSON, nullable=True)  # Dictionary of feature -> source
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis = relationship("Analysis", back_populates="creative_features")
