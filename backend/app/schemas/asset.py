"""Asset schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AssetRegister(BaseModel):
    """Schema for registering an asset"""
    creative_id: str
    filename: str
    cloudinary_public_id: Optional[str] = None
    cloudinary_url: Optional[str] = None
    secure_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    bytes: Optional[int] = None
    source: str = "cloudinary"  # 'cloudinary' or 'local_demo'


class AssetResponse(BaseModel):
    """Schema for asset response"""
    id: int
    analysis_id: int
    creative_id: str
    filename: str
    cloudinary_public_id: Optional[str] = None
    cloudinary_url: Optional[str] = None
    secure_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    bytes: Optional[int] = None
    source: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class RepurposeRequest(BaseModel):
    """Schema for repurposing an asset"""
    source_asset_id: int
    format: str  # '4:5', '9:16', '16:9', '1:1'


class GeneratedAssetResponse(BaseModel):
    """Schema for generated asset response"""
    id: int
    analysis_id: int
    source_asset_id: int
    format: str
    transformation: Optional[dict] = None
    generated_url: str
    created_at: datetime
    
    class Config:
        from_attributes = True
