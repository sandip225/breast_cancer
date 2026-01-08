"""Test script to debug view detection"""
import sys
sys.path.insert(0, '.')

from PIL import Image
import numpy as np

# Import the detection functions
from grad_cam import (
    detect_colored_text_label,
    detect_text_label_in_image,
    detect_mammogram_view_type,
    detect_breast_laterality,
    generate_mammogram_view_analysis
)

def test_with_image(image_path):
    """Test view detection with an image"""
    print(f"\n{'='*60}")
    print(f"Testing image: {image_path}")
    print('='*60)
    
    # Load image
    image = Image.open(image_path)
    print(f"Image size: {image.size} (width x height)")
    print(f"Image mode: {image.mode}")
    
    # Get arrays
    rgb_array = np.array(image.convert('RGB'))
    gray_array = np.array(image.convert('L'))
    
    height, width = gray_array.shape
    aspect_ratio = height / width
    print(f"Aspect ratio (h/w): {aspect_ratio:.3f}")
    
    # Test colored text detection
    print("\n--- Testing Colored Text Detection ---")
    lat, view = detect_colored_text_label(rgb_array)
    print(f"Result: laterality={lat}, view={view}")
    
    # Test grayscale text detection
    print("\n--- Testing Grayscale Text Detection ---")
    lat2, view2 = detect_text_label_in_image(gray_array)
    print(f"Result: laterality={lat2}, view={view2}")
    
    # Test view type detection
    print("\n--- Testing View Type Detection ---")
    view_type = detect_mammogram_view_type(gray_array)
    print(f"Result: {view_type}")
    
    # Test laterality detection
    print("\n--- Testing Laterality Detection ---")
    laterality = detect_breast_laterality(gray_array)
    print(f"Result: {laterality}")
    
    # Test full analysis
    print("\n--- Testing Full View Analysis ---")
    # Create a dummy heatmap
    heatmap = np.zeros((224, 224))
    analysis = generate_mammogram_view_analysis(image, heatmap, 0.8, [])
    print(f"View Code: {analysis.get('view_code')}")
    print(f"View Type: {analysis.get('view_type')}")
    print(f"Laterality: {analysis.get('laterality')}")

if __name__ == "__main__":
    # Test with sample images if provided
    if len(sys.argv) > 1:
        test_with_image(sys.argv[1])
    else:
        print("Usage: python test_view_detection.py <image_path>")
        print("\nLooking for sample images in datasets folder...")
        
        import os
        dataset_path = "datasets/breast_cancer/images/train"
        if os.path.exists(dataset_path):
            images = [f for f in os.listdir(dataset_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
            if images:
                test_with_image(os.path.join(dataset_path, images[0]))
