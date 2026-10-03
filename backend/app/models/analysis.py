"""Analysis model"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class AnalysisStatus(str, enum.Enum):
    """Analysis status enumeration"""
    DRAFT = "draft"
    UPLOADING = "uploading"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Analysis(Base):
    """Analysis model representing a complete creative analysis project"""
    
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.DRAFT, nullable=False)
    current_stage = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="analyses")
    assets = relationship("Asset", back_populates="analysis", cascade="all, delete-orphan")
    performance_records = relationship("PerformanceRecord", back_populates="analysis", cascade="all, delete-orphan")
    creative_features = relationship("CreativeFeature", back_populates="analysis", cascade="all, delete-orphan")
    creative_dna_insights = relationship("CreativeDNAInsight", back_populates="analysis", cascade="all, delete-orphan")
    generated_assets = relationship("GeneratedAsset", back_populates="analysis", cascade="all, delete-orphan")
