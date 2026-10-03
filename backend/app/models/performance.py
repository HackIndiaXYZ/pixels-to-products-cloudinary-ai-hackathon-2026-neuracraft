"""Performance record model"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class PerformanceRecord(Base):
    """Performance data for creative assets"""
    
    __tablename__ = "performance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    creative_id = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=False)
    impressions = Column(Integer, nullable=False)
    clicks = Column(Integer, nullable=False)
    conversions = Column(Integer, nullable=False)
    spend = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)
    date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis = relationship("Analysis", back_populates="performance_records")
