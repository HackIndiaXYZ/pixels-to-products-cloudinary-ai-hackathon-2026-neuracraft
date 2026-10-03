"""Generated asset model for repurposed creatives"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class GeneratedAsset(Base):
    """Assets generated through Cloudinary transformations"""
    
    __tablename__ = "generated_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    source_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    format = Column(String, nullable=False)  # '4:5', '9:16', '16:9', '1:1'
    transformation = Column(JSON, nullable=True)  # Cloudinary transformation parameters
    generated_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis = relationship("Analysis", back_populates="generated_assets")
    source_asset = relationship("Asset", back_populates="generated_assets")
