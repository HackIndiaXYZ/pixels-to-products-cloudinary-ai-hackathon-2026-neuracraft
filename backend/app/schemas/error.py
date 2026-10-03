"""Error response schemas"""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorDetail(BaseModel):
    """Error detail schema"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: ErrorDetail
