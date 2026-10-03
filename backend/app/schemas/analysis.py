"""Analysis schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AnalysisBase(BaseModel):
    """Base analysis schema"""
    name: str
    description: Optional[str] = None


class AnalysisCreate(AnalysisBase):
    """Schema for analysis creation"""
    pass


class AnalysisResponse(AnalysisBase):
    """Schema for analysis response"""
    id: int
    user_id: int
    status: str
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisStatusResponse(BaseModel):
    """Schema for analysis status response"""
    id: int
    status: str
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True
