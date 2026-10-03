"""Cloudinary upload service for backend operations"""
import cloudinary.uploader
from typing import Dict, Any, Optional
from app.core.cloudinary_config import is_cloudinary_available
import logging


logger = logging.getLogger(__name__)


class CloudinaryService:
    """Service for Cloudinary operations"""
    
    @staticmethod
    def upload_image(
        file_path: str,
        folder: str = "creativepulse",
        public_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Upload an image to Cloudinary
        
        Args:
            file_path: Path to the image file
            folder: Cloudinary folder
            public_id: Optional public ID for the asset
            
        Returns:
            Upload result dictionary or None if Cloudinary not configured
        """
        if not is_cloudinary_available():
            logger.warning("Cloudinary not configured - skipping upload")
            return None
        
        try:
            upload_options = {
                "folder": folder,
                "resource_type": "image",
                "quality": "auto",
                "fetch_format": "auto"
            }
            
            if public_id:
                upload_options["public_id"] = public_id
            
            result = cloudinary.uploader.upload(file_path, **upload_options)
            
            logger.info(f"Uploaded image to Cloudinary: {result.get('public_id')}")
            
            return {
                "public_id": result.get("public_id"),
                "url": result.get("url"),
                "secure_url": result.get("secure_url"),
                "width": result.get("width"),
                "height": result.get("height"),
                "format": result.get("format"),
                "bytes": result.get("bytes")
            }
        
        except Exception as e:
            logger.error(f"Error uploading to Cloudinary: {str(e)}")
            return None
    
    @staticmethod
    def delete_image(public_id: str) -> bool:
        """
        Delete an image from Cloudinary
        
        Args:
            public_id: Public ID of the image
            
        Returns:
            True if successful, False otherwise
        """
        if not is_cloudinary_available():
            logger.warning("Cloudinary not configured - skipping delete")
            return False
        
        try:
            result = cloudinary.uploader.destroy(public_id)
            success = result.get("result") == "ok"
            
            if success:
                logger.info(f"Deleted image from Cloudinary: {public_id}")
            else:
                logger.warning(f"Failed to delete image from Cloudinary: {public_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error deleting from Cloudinary: {str(e)}")
            return False
    
    @staticmethod
    def get_image_info(public_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a Cloudinary image
        
        Args:
            public_id: Public ID of the image
            
        Returns:
            Image information dictionary or None
        """
        if not is_cloudinary_available():
            return None
        
        try:
            result = cloudinary.api.resource(public_id)
            
            return {
                "public_id": result.get("public_id"),
                "url": result.get("url"),
                "secure_url": result.get("secure_url"),
                "width": result.get("width"),
                "height": result.get("height"),
                "format": result.get("format"),
                "bytes": result.get("bytes"),
                "created_at": result.get("created_at")
            }
        
        except Exception as e:
            logger.error(f"Error getting Cloudinary image info: {str(e)}")
            return None
