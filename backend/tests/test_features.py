"""Tests for visual feature extraction"""
import pytest
import numpy as np
from PIL import Image
import io
from app.analytics.features import FeatureExtractor


def create_test_image(width: int, height: int, color: tuple) -> Image.Image:
    """Create a test image with specified dimensions and color"""
    img = Image.new('RGB', (width, height), color)
    return img


def test_aspect_ratio():
    """Test aspect ratio calculation"""
    # Square image
    img = create_test_image(100, 100, (128, 128, 128))
    features = FeatureExtractor._extract_from_image(img)
    assert features['aspect_ratio'] == 1.0
    
    # Portrait (taller than wide)
    img = create_test_image(100, 200, (128, 128, 128))
    features = FeatureExtractor._extract_from_image(img)
    assert features['aspect_ratio'] == 0.5
    assert features['portrait'] is True
    assert features['landscape'] is False
    
    # Landscape (wider than tall)
    img = create_test_image(200, 100, (128, 128, 128))
    features = FeatureExtractor._extract_from_image(img)
    assert features['aspect_ratio'] == 2.0
    assert features['portrait'] is False
    assert features['landscape'] is True


def test_brightness_calculation():
    """Test brightness calculation"""
    # White image (maximum brightness)
    img = create_test_image(100, 100, (255, 255, 255))
    features = FeatureExtractor._extract_from_image(img)
    assert features['brightness'] == pytest.approx(1.0, rel=1e-4)
    
    # Black image (minimum brightness)
    img = create_test_image(100, 100, (0, 0, 0))
    features = FeatureExtractor._extract_from_image(img)
    assert features['brightness'] == pytest.approx(0.0, rel=1e-4)
    
    # Gray image (medium brightness)
    img = create_test_image(100, 100, (128, 128, 128))
    features = FeatureExtractor._extract_from_image(img)
    assert features['brightness'] == pytest.approx(0.502, rel=0.01)


def test_bright_background_detection():
    """Test bright background detection"""
    # Bright image
    img = create_test_image(100, 100, (220, 220, 220))
    features = FeatureExtractor._extract_from_image(img)
    assert features['bright_background'] is True
    
    # Dark image
    img = create_test_image(100, 100, (50, 50, 50))
    features = FeatureExtractor._extract_from_image(img)
    assert features['bright_background'] is False


def test_contrast_calculation():
    """Test contrast calculation"""
    # Uniform image (no contrast)
    img = create_test_image(100, 100, (128, 128, 128))
    features = FeatureExtractor._extract_from_image(img)
    assert features['contrast'] == pytest.approx(0.0, abs=0.001)
    
    # High contrast image would need more complex setup
    # Just verify it's calculated
    img = create_test_image(100, 100, (255, 255, 255))
    features = FeatureExtractor._extract_from_image(img)
    assert features['contrast'] is not None
    assert features['contrast'] >= 0.0


def test_edge_density_calculation():
    """Test edge density calculation"""
    # Uniform image (no edges)
    img = create_test_image(100, 100, (128, 128, 128))
    features = FeatureExtractor._extract_from_image(img)
    assert features['edge_density'] == pytest.approx(0.0, abs=0.1)
    
    # Any non-uniform image should have some edges
    img = create_test_image(100, 100, (255, 255, 255))
    features = FeatureExtractor._extract_from_image(img)
    assert features['edge_density'] is not None
    assert features['edge_density'] >= 0.0


def test_dominant_color_detection():
    """Test dominant color detection"""
    # Red
    img = create_test_image(100, 100, (255, 0, 0))
    features = FeatureExtractor._extract_from_image(img)
    assert features['dominant_color'] == 'red'
    
    # White
    img = create_test_image(100, 100, (255, 255, 255))
    features = FeatureExtractor._extract_from_image(img)
    assert features['dominant_color'] == 'white'
    
    # Black
    img = create_test_image(100, 100, (0, 0, 0))
    features = FeatureExtractor._extract_from_image(img)
    assert features['dominant_color'] == 'black'
    
    # Gray
    img = create_test_image(100, 100, (128, 128, 128))
    features = FeatureExtractor._extract_from_image(img)
    assert features['dominant_color'] == 'gray'


def test_feature_sources():
    """Test that feature sources are tracked"""
    img = create_test_image(100, 100, (128, 128, 128))
    features = FeatureExtractor._extract_from_image(img)
    
    assert 'feature_sources' in features
    assert features['feature_sources']['brightness'] == 'Computed'
    assert features['feature_sources']['contrast'] == 'Computed'
    assert features['feature_sources']['edge_density'] == 'Computed'
    assert features['feature_sources']['dominant_color'] == 'Computed'
    assert features['feature_sources']['human_present'] == 'Unavailable'


def test_human_presence_placeholder():
    """Test that human presence is None (placeholder)"""
    img = create_test_image(100, 100, (128, 128, 128))
    features = FeatureExtractor._extract_from_image(img)
    
    # Should be None since we don't have actual detection
    assert features['human_present'] is None
    assert features['feature_sources']['human_present'] == 'Unavailable'


def test_extract_from_bytes():
    """Test extraction from bytes"""
    img = create_test_image(100, 100, (128, 128, 128))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    features = FeatureExtractor.extract_from_bytes(img_bytes)
    
    assert features['aspect_ratio'] == 1.0
    assert features['brightness'] is not None
    assert features['contrast'] is not None


def test_empty_features():
    """Test empty features structure"""
    features = FeatureExtractor._empty_features()
    
    assert features['aspect_ratio'] is None
    assert features['brightness'] is None
    assert features['contrast'] is None
    assert features['edge_density'] is None
    assert features['dominant_color'] is None
    assert features['bright_background'] is None
    assert features['portrait'] is None
    assert features['landscape'] is None
    assert features['human_present'] is None
    
    # All sources should be Unavailable
    for source in features['feature_sources'].values():
        assert source == 'Unavailable'
