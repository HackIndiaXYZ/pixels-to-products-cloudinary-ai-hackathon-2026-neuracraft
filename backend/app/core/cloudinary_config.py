"""Cloudinary configuration and utilities"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def init_cloudinary() -> bool:
    """
    Initialize Cloudinary configuration
    
    Returns:
        True if successfully configured, False otherwise
    """
    if not settings.cloudinary_configured:
        return False
    
    try:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
        return True
    except Exception:
        return False


def is_cloudinary_available() -> bool:
    """
    Check if Cloudinary is configured and available
    
    Returns:
        True if Cloudinary is available, False otherwise
    """
    return settings.cloudinary_configured


def generate_upload_signature(params: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate a signed upload signature for client-side uploads
    
    Args:
        params: Upload parameters (timestamp, folder, etc.)
        
    Returns:
        Dictionary with signature, timestamp, and api_key
        
    Note:
        This allows the frontend to upload directly to Cloudinary
        without exposing the API secret
    """
    if not is_cloudinary_available():
        raise ValueError("Cloudinary is not configured")
    
    # Cloudinary SDK expects integer timestamp for signing
    # but we return it as string for the frontend
    signature = cloudinary.utils.api_sign_request(
        params,
        settings.CLOUDINARY_API_SECRET
    )
    
    return {
        "signature": signature,
        "timestamp": str(params.get("timestamp", "")),
        "api_key": settings.CLOUDINARY_API_KEY,
        "cloud_name": settings.CLOUDINARY_CLOUD_NAME
    }


def generate_transformation_url(
    public_id: str,
    format: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    crop: str = "fill",
    gravity: str = "auto"
) -> str:
    """
    Generate a Cloudinary transformation URL
    
    Args:
        public_id: Cloudinary public ID of the asset
        format: Target format (e.g., "4:5", "9:16", "16:9", "1:1")
        width: Target width
        height: Target height
        crop: Crop mode (default: "fill")
        gravity: Gravity mode (default: "auto")
        
    Returns:
        Transformed image URL
    """
    if not is_cloudinary_available():
        raise ValueError("Cloudinary is not configured")
    
    # Map format to aspect ratio
    aspect_ratios = {
        "4:5": (4, 5),
        "9:16": (9, 16),
        "16:9": (16, 9),
        "1:1": (1, 1)
    }
    
    transformation = {
        "crop": crop,
        "gravity": gravity,
        "quality": "auto",
        "fetch_format": "auto"
    }
    
    if format in aspect_ratios:
        ar_w, ar_h = aspect_ratios[format]
        transformation["aspect_ratio"] = f"{ar_w}:{ar_h}"
        
        if width:
            transformation["width"] = width
        elif height:
            transformation["height"] = height
        else:
            # Default size based on format
            if format == "9:16":
                transformation["width"] = 1080
            elif format == "16:9":
                transformation["width"] = 1920
            else:
                transformation["width"] = 1080
    
    return cloudinary.utils.cloudinary_url(
        public_id,
        **transformation
    )[0]


# Initialize Cloudinary on module import
_cloudinary_initialized = init_cloudinary()

if _cloudinary_initialized:
    logger.info("Cloudinary configured successfully")
else:
    logger.info("Cloudinary not configured - repurposing features will be limited")
