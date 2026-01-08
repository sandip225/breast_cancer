#!/usr/bin/env python3
"""
Test script for Breast Cancer Detection API
Tests both local and deployed versions
"""

import requests
import sys
from pathlib import Path

# Configuration
LOCAL_URL = "http://localhost:7860"
DEPLOYED_URL = "https://bhavanakhatri-breastcancerdetection.hf.space"


def test_health(base_url):
    """Test health endpoint"""
    print(f"\n🏥 Testing health endpoint: {base_url}/health")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Status: {data['status']}")
        print(f"✅ Model Status: {data['model_status']}")
        
        if data['model_status'] != 'loaded':
            print(f"⚠️  Warning: {data.get('model_error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_prediction(base_url, image_path):
    """Test prediction endpoint"""
    print(f"\n🔮 Testing prediction: {base_url}/predict")
    
    if not Path(image_path).exists():
        print(f"⚠️  Image file not found: {image_path}")
        print("   Skipping prediction test...")
        return False
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{base_url}/predict",
                files=files,
                timeout=30
            )
        
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Prediction: {data['prediction']}")
        print(f"✅ Confidence: {data['confidence']:.2%}")
        print(f"✅ Risk Level: {data['risk_assessment']['level']}")
        print(f"   Benign: {data['probabilities']['benign']:.2f}%")
        print(f"   Malignant: {data['probabilities']['malignant']:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False


def test_batch_prediction(base_url, image_paths):
    """Test batch prediction endpoint"""
    print(f"\n📦 Testing batch prediction: {base_url}/batch-predict")
    
    # Filter existing files
    existing_files = [p for p in image_paths if Path(p).exists()]
    
    if not existing_files:
        print("⚠️  No image files found. Skipping batch test...")
        return False
    
    try:
        files = [('files', open(p, 'rb')) for p in existing_files]
        
        response = requests.post(
            f"{base_url}/batch-predict",
            files=files,
            timeout=60
        )
        
        # Close file handles
        for _, f in files:
            f.close()
        
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Total images: {data['total_images']}")
        print(f"✅ Successful: {data['successful']}")
        print(f"✅ Summary:")
        print(f"   Benign: {data['summary']['benign']}")
        print(f"   Malignant: {data['summary']['malignant']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch prediction failed: {e}")
        return False


def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 Breast Cancer Detection API - Test Suite")
    print("=" * 60)
    
    # Determine which API to test
    if len(sys.argv) > 1:
        if sys.argv[1] == "local":
            base_url = LOCAL_URL
            print("\n🏠 Testing LOCAL API")
        elif sys.argv[1] == "deployed":
            base_url = DEPLOYED_URL
            print("\n🌐 Testing DEPLOYED API")
        else:
            base_url = sys.argv[1]
            print(f"\n🔗 Testing CUSTOM URL: {base_url}")
    else:
        # Default to local
        base_url = LOCAL_URL
        print("\n🏠 Testing LOCAL API (use 'deployed' for production)")
    
    print(f"URL: {base_url}")
    print("=" * 60)
    
    # Test health
    health_ok = test_health(base_url)
    
    if not health_ok:
        print("\n❌ Health check failed. Stopping tests.")
        sys.exit(1)
    
    # Test single prediction
    test_image = "test_image.jpg"
    if Path(test_image).exists():
        test_prediction(base_url, test_image)
    else:
        print(f"\n⚠️  Test image not found: {test_image}")
        print("   Create a test image to test prediction endpoint")
    
    # Test batch prediction
    test_images = ["test1.jpg", "test2.jpg", "test3.jpg"]
    existing_images = [img for img in test_images if Path(img).exists()]
    
    if existing_images:
        test_batch_prediction(base_url, existing_images)
    else:
        print("\n⚠️  No test images found for batch prediction test")
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")
    print("=" * 60)
    
    print("\n📚 View API documentation:")
    print(f"   {base_url}/")
    print("\n🔍 ReDoc documentation:")
    print(f"   {base_url}/redoc")


if __name__ == "__main__":
    main()

