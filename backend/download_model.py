#!/usr/bin/env python3
"""
Download model file from Hugging Face Hub on startup
This avoids Git LFS bandwidth issues
"""
import os
from pathlib import Path

def download_model():
    """Download model file if not present"""
    model_path = Path(__file__).parent / "models" / "breast_cancer_model.keras"
    
    # Skip if model already exists
    if model_path.exists() and model_path.stat().st_size > 100_000_000:  # > 100 MB
        print(f"✓ Model already exists at {model_path}")
        print(f"  Size: {model_path.stat().st_size / (1024*1024):.2f} MB")
        return True
    
    # Create models directory
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try different download methods
    
    # Method 1: From Hugging Face Hub (if uploaded there)
    hf_repo = os.environ.get("HF_MODEL_REPO")
    if hf_repo:
        print(f"📥 Downloading from Hugging Face: {hf_repo}")
        try:
            from huggingface_hub import hf_hub_download
            downloaded_path = hf_hub_download(
                repo_id=hf_repo,
                filename="breast_cancer_model.keras",
                cache_dir=str(model_path.parent)
            )
            # Move to correct location
            import shutil
            shutil.copy(downloaded_path, model_path)
            print(f"✓ Downloaded from Hugging Face successfully!")
            return True
        except Exception as e:
            print(f"⚠️  Hugging Face download failed: {e}")
    
    # Method 2: From direct URL (Google Drive, S3, etc.)
    model_url = os.environ.get("MODEL_URL")
    if model_url:
        print(f"📥 Downloading from URL: {model_url}")
        try:
            import urllib.request
            urllib.request.urlretrieve(model_url, str(model_path))
            print(f"✓ Downloaded from URL successfully!")
            print(f"  Size: {model_path.stat().st_size / (1024*1024):.2f} MB")
            return True
        except Exception as e:
            print(f"⚠️  URL download failed: {e}")
    
    # Method 3: From Google Drive
    gdrive_id = os.environ.get("GDRIVE_FILE_ID")
    if gdrive_id:
        print(f"📥 Downloading from Google Drive: {gdrive_id}")
        try:
            import gdown
            url = f"https://drive.google.com/uc?id={gdrive_id}"
            gdown.download(url, str(model_path), quiet=False)
            print(f"✓ Downloaded from Google Drive successfully!")
            return True
        except Exception as e:
            print(f"⚠️  Google Drive download failed: {e}")
    
    print("❌ No download method configured!")
    print("   Set one of these environment variables:")
    print("   - HF_MODEL_REPO: Hugging Face repo (e.g., 'username/model-name')")
    print("   - MODEL_URL: Direct download URL")
    print("   - GDRIVE_FILE_ID: Google Drive file ID")
    return False

if __name__ == "__main__":
    success = download_model()
    if not success:
        print("\n⚠️  Model download failed. App may not work correctly.")
        exit(1)

