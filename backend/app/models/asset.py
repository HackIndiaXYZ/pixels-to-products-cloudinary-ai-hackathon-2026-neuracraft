"""Asset model for creative images"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Asset(Base):
    """Creative asset model"""
    
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    creative_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    cloudinary_public_id = Column(String, nullable=True)
    cloudinary_url = Column(String, nullable=True)
    secure_url = Column(String, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    format = Column(String, nullable=True)
    bytes = Column(Integer, nullable=True)
    source = Column(String, nullable=False)  # 'cloudinary', 'local_demo'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis = relationship("Analysis", back_populates="assets")
    generated_assets = relationship("GeneratedAsset", back_populates="source_asset", cascade="all, delete-orphan")
