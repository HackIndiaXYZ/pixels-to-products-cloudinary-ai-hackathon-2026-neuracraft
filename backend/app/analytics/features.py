"""Visual feature extraction for creative assets"""
from PIL import Image
import numpy as np
from typing import Dict, Any, Optional
import io
import requests
from pathlib import Path
import logging


logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract visual features from creative assets"""
    
    @staticmethod
    def extract_from_url(url: str) -> Dict[str, Any]:
        """
        Extract features from an image URL
        
        Args:
            url: Image URL
            
        Returns:
            Dictionary of extracted features
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            image_data = io.BytesIO(response.content)
            return FeatureExtractor.extract_from_bytes(image_data)
        except Exception as e:
            logger.error(f"Error loading image from URL {url}: {str(e)}")
            return FeatureExtractor._empty_features()
    
    @staticmethod
    def extract_from_file(file_path: str) -> Dict[str, Any]:
        """
        Extract features from a local file
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dictionary of extracted features
        """
        try:
            with Image.open(file_path) as img:
                return FeatureExtractor._extract_from_image(img)
        except Exception as e:
            logger.error(f"Error loading image from file {file_path}: {str(e)}")
            return FeatureExtractor._empty_features()
    
    @staticmethod
    def extract_from_bytes(image_bytes: io.BytesIO) -> Dict[str, Any]:
        """
        Extract features from image bytes
        
        Args:
            image_bytes: Image data as BytesIO
            
        Returns:
            Dictionary of extracted features
        """
        try:
            with Image.open(image_bytes) as img:
                return FeatureExtractor._extract_from_image(img)
        except Exception as e:
            logger.error(f"Error processing image bytes: {str(e)}")
            return FeatureExtractor._empty_features()
    
    @staticmethod
    def _extract_from_image(img: Image.Image) -> Dict[str, Any]:
        """
        Extract all visual features from a PIL Image
        
        Args:
            img: PIL Image object
            
        Returns:
            Dictionary with all extracted features
        """
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Extract features
        features = {}
        feature_sources = {}
        
        # Aspect ratio
        width, height = img.size
        features['aspect_ratio'] = round(width / height, 4)
        feature_sources['aspect_ratio'] = 'Computed'
        
        # Orientation
        features['portrait'] = height > width
        features['landscape'] = width > height
        feature_sources['portrait'] = 'Computed'
        feature_sources['landscape'] = 'Computed'
        
        # Convert to numpy array for pixel analysis
        img_array = np.array(img)
        
        # Brightness (mean normalized pixel brightness)
        brightness = FeatureExtractor._calculate_brightness(img_array)
        features['brightness'] = round(brightness, 4)
        feature_sources['brightness'] = 'Computed'
        
        # Contrast (standard deviation of luminance)
        contrast = FeatureExtractor._calculate_contrast(img_array)
        features['contrast'] = round(contrast, 4)
        feature_sources['contrast'] = 'Computed'
        
        # Edge density
        edge_density = FeatureExtractor._calculate_edge_density(img_array)
        features['edge_density'] = round(edge_density, 4)
        feature_sources['edge_density'] = 'Computed'
        
        # Dominant color
        dominant_color = FeatureExtractor._get_dominant_color(img_array)
        features['dominant_color'] = dominant_color
        feature_sources['dominant_color'] = 'Computed'
        
        # Bright background (based on brightness)
        features['bright_background'] = brightness > 0.6
        feature_sources['bright_background'] = 'Computed'
        
        # Human presence - placeholder (would need actual detection)
        features['human_present'] = None
        feature_sources['human_present'] = 'Unavailable'
        
        # Add feature sources
        features['feature_sources'] = feature_sources
        
        return features
    
    @staticmethod
    def _calculate_brightness(img_array: np.ndarray) -> float:
        """
        Calculate mean normalized pixel brightness
        
        Formula: Mean of all RGB values / 255
        
        Args:
            img_array: Image as numpy array
            
        Returns:
            Brightness value between 0 and 1
        """
        mean_brightness = np.mean(img_array) / 255.0
        return float(mean_brightness)
    
    @staticmethod
    def _calculate_contrast(img_array: np.ndarray) -> float:
        """
        Calculate contrast as standard deviation of luminance
        
        Args:
            img_array: Image as numpy array
            
        Returns:
            Contrast value (normalized)
        """
        # Convert to grayscale
        if len(img_array.shape) == 3:
            # Use luminance formula: 0.299*R + 0.587*G + 0.114*B
            gray = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]
        else:
            gray = img_array
        
        # Calculate standard deviation
        contrast = np.std(gray) / 255.0
        return float(contrast)
    
    @staticmethod
    def _calculate_edge_density(img_array: np.ndarray) -> float:
        """
        Calculate edge density using simple edge detection
        
        Formula: Proportion of pixels that are likely edge pixels
        
        Args:
            img_array: Image as numpy array
            
        Returns:
            Edge density between 0 and 1
        """
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]
        else:
            gray = img_array
        
        # Simple Sobel-like edge detection
        # Horizontal gradient
        gx = np.abs(gray[:-1, :] - gray[1:, :])
        # Vertical gradient
        gy = np.abs(gray[:, :-1] - gray[:, 1:])
        
        # Combine gradients (take minimum size)
        min_height = min(gx.shape[0], gy.shape[0])
        min_width = min(gx.shape[1], gy.shape[1])
        
        gradient_magnitude = np.sqrt(
            gx[:min_height, :min_width]**2 + gy[:min_height, :min_width]**2
        )
        
        # Threshold for edge pixels (somewhat arbitrary but consistent)
        edge_threshold = 30
        edge_pixels = np.sum(gradient_magnitude > edge_threshold)
        total_pixels = gradient_magnitude.size
        
        edge_density = edge_pixels / total_pixels
        return float(edge_density)
    
    @staticmethod
    def _get_dominant_color(img_array: np.ndarray) -> str:
        """
        Get dominant color category
        
        Categories: red, orange, yellow, green, blue, purple, pink, brown, white, gray, black
        
        Args:
            img_array: Image as numpy array
            
        Returns:
            Dominant color category
        """
        # Calculate mean color
        mean_r = np.mean(img_array[:, :, 0])
        mean_g = np.mean(img_array[:, :, 1])
        mean_b = np.mean(img_array[:, :, 2])
        
        # Determine dominant color based on mean RGB
        if mean_r > 200 and mean_g > 200 and mean_b > 200:
            return "white"
        elif mean_r < 50 and mean_g < 50 and mean_b < 50:
            return "black"
        elif abs(mean_r - mean_g) < 30 and abs(mean_g - mean_b) < 30 and abs(mean_r - mean_b) < 30:
            # Colors are similar - grayscale
            if mean_r > 150:
                return "white"
            elif mean_r < 100:
                return "gray"
            else:
                return "gray"
        elif mean_r > mean_g and mean_r > mean_b:
            # Red dominant
            if mean_g > 150:
                return "orange" if mean_b < 100 else "pink"
            elif mean_g > 100:
                return "orange"
            else:
                return "red"
        elif mean_g > mean_r and mean_g > mean_b:
            # Green dominant
            if mean_r > 150:
                return "yellow"
            else:
                return "green"
        elif mean_b > mean_r and mean_b > mean_g:
            # Blue dominant
            if mean_r > 100:
                return "purple"
            else:
                return "blue"
        else:
            # Fallback
            return "gray"
    
    @staticmethod
    def _empty_features() -> Dict[str, Any]:
        """
        Return empty features dictionary
        
        Returns:
            Dictionary with None values and Unavailable sources
        """
        return {
            'aspect_ratio': None,
            'brightness': None,
            'contrast': None,
            'edge_density': None,
            'dominant_color': None,
            'bright_background': None,
            'portrait': None,
            'landscape': None,
            'human_present': None,
            'feature_sources': {
                'aspect_ratio': 'Unavailable',
                'brightness': 'Unavailable',
                'contrast': 'Unavailable',
                'edge_density': 'Unavailable',
                'dominant_color': 'Unavailable',
                'bright_background': 'Unavailable',
                'portrait': 'Unavailable',
                'landscape': 'Unavailable',
                'human_present': 'Unavailable'
            }
        }
