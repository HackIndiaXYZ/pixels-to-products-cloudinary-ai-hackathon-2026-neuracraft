"""Test visual feature extraction"""
import sys
import os
from PIL import Image
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.analytics.features import FeatureExtractor


def create_sample_images():
    """Create sample images for testing"""
    samples_dir = "test_samples"
    os.makedirs(samples_dir, exist_ok=True)
    
    images = []
    
    # 1. Bright portrait image
    img1 = Image.new('RGB', (600, 800), (240, 240, 240))
    img1_path = os.path.join(samples_dir, "bright_portrait.png")
    img1.save(img1_path)
    images.append(("Bright Portrait", img1_path))
    
    # 2. Dark landscape image
    img2 = Image.new('RGB', (800, 600), (40, 40, 40))
    img2_path = os.path.join(samples_dir, "dark_landscape.png")
    img2.save(img2_path)
    images.append(("Dark Landscape", img2_path))
    
    # 3. Red square image
    img3 = Image.new('RGB', (500, 500), (220, 30, 30))
    img3_path = os.path.join(samples_dir, "red_square.png")
    img3.save(img3_path)
    images.append(("Red Square", img3_path))
    
    # 4. Blue portrait with gradient
    img4_array = np.zeros((800, 600, 3), dtype=np.uint8)
    for i in range(800):
        img4_array[i, :, 2] = int(50 + (i / 800) * 150)  # Blue gradient
    img4 = Image.fromarray(img4_array)
    img4_path = os.path.join(samples_dir, "blue_gradient.png")
    img4.save(img4_path)
    images.append(("Blue Gradient", img4_path))
    
    # 5. High contrast checkerboard
    img5_array = np.zeros((600, 600, 3), dtype=np.uint8)
    for i in range(0, 600, 100):
        for j in range(0, 600, 100):
            if (i // 100 + j // 100) % 2 == 0:
                img5_array[i:i+100, j:j+100] = 255
    img5 = Image.fromarray(img5_array)
    img5_path = os.path.join(samples_dir, "checkerboard.png")
    img5.save(img5_path)
    images.append(("Checkerboard (High Edge Density)", img5_path))
    
    return images


def format_feature_value(value, feature_name):
    """Format feature value for display"""
    if value is None:
        return "N/A"
    elif isinstance(value, bool):
        return "Yes" if value else "No"
    elif isinstance(value, float):
        if feature_name in ['brightness', 'contrast', 'edge_density']:
            return f"{value:.4f}"
        else:
            return f"{value:.2f}"
    else:
        return str(value)


def test_feature_extraction():
    """Test feature extraction on sample images"""
    print("=" * 70)
    print("Visual Feature Extraction Test")
    print("=" * 70)
    
    # Create sample images
    print("\nCreating sample images...")
    images = create_sample_images()
    print(f"Created {len(images)} test images")
    
    # Extract features from each image
    for name, path in images:
        print("\n" + "=" * 70)
        print(f"Image: {name}")
        print("=" * 70)
        
        # Extract features
        features = FeatureExtractor.extract_from_file(path)
        
        # Display features
        print(f"\nDimensions & Orientation:")
        print(f"  Aspect Ratio: {format_feature_value(features['aspect_ratio'], 'aspect_ratio')}")
        print(f"  Portrait: {format_feature_value(features['portrait'], 'portrait')}")
        print(f"  Landscape: {format_feature_value(features['landscape'], 'landscape')}")
        
        print(f"\nColor & Brightness:")
        print(f"  Brightness: {format_feature_value(features['brightness'], 'brightness')}")
        print(f"  Dominant Color: {format_feature_value(features['dominant_color'], 'dominant_color')}")
        print(f"  Bright Background: {format_feature_value(features['bright_background'], 'bright_background')}")
        
        print(f"\nTexture & Detail:")
        print(f"  Contrast: {format_feature_value(features['contrast'], 'contrast')}")
        print(f"  Edge Density: {format_feature_value(features['edge_density'], 'edge_density')}")
        
        print(f"\nAdvanced Features:")
        print(f"  Human Present: {format_feature_value(features['human_present'], 'human_present')}")
        
        print(f"\nFeature Sources:")
        for feature, source in features['feature_sources'].items():
            if feature != 'human_present':  # Skip unavailable feature
                print(f"  {feature}: {source}")
    
    print("\n" + "=" * 70)
    print("\n✅ Feature extraction test completed!")
    print(f"\nTest images saved in: test_samples/")


def test_feature_consistency():
    """Test that feature extraction is deterministic"""
    print("\n\n" + "=" * 70)
    print("Feature Extraction Consistency Test")
    print("=" * 70)
    
    # Create a test image
    img = Image.new('RGB', (500, 500), (128, 128, 128))
    
    # Extract features multiple times
    features1 = FeatureExtractor._extract_from_image(img)
    features2 = FeatureExtractor._extract_from_image(img)
    
    # Check consistency
    print("\nTesting deterministic extraction...")
    
    consistent = True
    for key in ['aspect_ratio', 'brightness', 'contrast', 'edge_density', 'dominant_color']:
        if features1[key] != features2[key]:
            print(f"  ❌ {key}: {features1[key]} != {features2[key]}")
            consistent = False
    
    if consistent:
        print("  ✅ All features are consistent across extractions")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_feature_extraction()
    test_feature_consistency()
