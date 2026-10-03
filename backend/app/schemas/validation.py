"""Validation schemas"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ValidationWarning(BaseModel):
    """Schema for validation warning"""
    type: str
    message: str
    count: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class ValidationError(BaseModel):
    """Schema for validation error"""
    type: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    """Schema for validation result"""
    valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationWarning] = []
    excluded_rows: int = 0
    total_rows: int = 0
    valid_rows: int = 0


class PerformanceUploadResponse(BaseModel):
    """Schema for performance data upload response"""
    validation: ValidationResult
    records_created: int
    message: str
    # Unique creative_id values present in the validated dataset.
    # The wizard uses this to show the user exactly which IDs they uploaded
    # so they can register matching assets.
    creative_ids: List[str] = []
