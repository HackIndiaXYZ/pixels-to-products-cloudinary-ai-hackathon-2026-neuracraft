"""Cloudinary integration endpoints"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from app.core.cloudinary_config import is_cloudinary_available, generate_upload_signature
import time
import logging


router = APIRouter()
logger = logging.getLogger(__name__)


class SignatureRequest(BaseModel):
    """Request for upload signature"""
    folder: str = "creativepulse"
    public_id: str | None = None
    timestamp: int = None
    
    def __init__(self, **data):
        if data.get('timestamp') is None:
            data['timestamp'] = int(time.time())
        super().__init__(**data)


class SignatureResponse(BaseModel):
    """Response with upload signature"""
    signature: str
    timestamp: str
    api_key: str
    cloud_name: str
    folder: str
    public_id: str | None = None


@router.post("/signature", response_model=SignatureResponse)
def get_upload_signature(request: SignatureRequest):
    """
    Generate a signed upload signature for client-side Cloudinary uploads
    
    This endpoint allows the frontend to upload directly to Cloudinary
    without exposing the API secret. The signature proves the upload
    is authorized by the backend.
    
    Args:
        request: Signature request parameters
        
    Returns:
        Signature and upload parameters
        
    Raises:
        HTTPException: If Cloudinary is not configured
    """
    if not is_cloudinary_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary is not configured. Please set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET in environment variables."
        )
    
    try:
        # Prepare upload parameters - these MUST match what the frontend sends
        params = {
            "timestamp": request.timestamp,
            "folder": request.folder
        }
        
        # Add public_id if provided
        if request.public_id:
            params["public_id"] = request.public_id
        
        # Log the exact params being signed for debugging
        import hashlib
        sorted_params = sorted(params.items())
        to_sign = '&'.join([f'{k}={v}' for k, v in sorted_params])
        logger.info(f"String to sign: '{to_sign}'")
        logger.info(f"Params: {params}")
        
        # Generate signature
        signature_data = generate_upload_signature(params)
        
        logger.info(f"Generated signature: {signature_data['signature']}")
        
        response = SignatureResponse(
            signature=signature_data["signature"],
            timestamp=signature_data["timestamp"],
            api_key=signature_data["api_key"],
            cloud_name=signature_data["cloud_name"],
            folder=request.folder,
            public_id=request.public_id
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error generating Cloudinary signature: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate upload signature: {str(e)}"
        )


@router.get("/status")
def get_cloudinary_status() -> Dict[str, Any]:
    """
    Get Cloudinary configuration status
    
    Returns:
        Status information
    """
    configured = is_cloudinary_available()
    
    return {
        "configured": configured,
        "message": "Cloudinary is ready" if configured else "Cloudinary is not configured",
        "features_available": {
            "upload": configured,
            "transformations": configured,
            "repurposing": configured
        }
    }
