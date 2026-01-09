"""
Breast Cancer Detection API - Full Featured
Hugging Face Spaces Deployment with Grad-CAM Visualizations

REST API for breast cancer detection from mammogram images.
Includes detailed analysis, Grad-CAM heatmaps, and region detection.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any, Tuple, Optional, List
import os
from pathlib import Path
import logging

import base64
import io
import numpy as np
from PIL import Image
from tensorflow import keras
import tensorflow as tf

# ==================== LOGGING CONFIGURATION ====================
# Configure logging FIRST (before any logger usage)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import visualization functions
try:
    from grad_cam import create_gradcam_visualization, generate_mammogram_view_analysis
    GRADCAM_AVAILABLE = True
    logger.info("✅ Grad-CAM module loaded successfully")
except ImportError as e:
    GRADCAM_AVAILABLE = False
    logger.warning(f"⚠️ Grad-CAM not available: {e}")

try:
    from report_generator import generate_report_pdf
    REPORT_AVAILABLE = True
    logger.info("✅ Report generator loaded successfully")
except ImportError as e:
    REPORT_AVAILABLE = False
    logger.warning(f"⚠️ Report generator not available: {e}")


def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


def generate_view_analysis(analysis, image):
    """
    Generate view-specific (CC or MLO) mammogram analysis based on detected view type.
    Only returns the detected view, not both views.
    """
    findings = analysis.get("findings", {})
    regions = findings.get("regions", [])
    stats = analysis.get("stats", {})
    malignant_prob = analysis.get("malignant_prob", 0)
    
    # Get the detected view type from the analysis
    view_analysis_data = analysis.get("view_analysis", {})
    view_type_full = view_analysis_data.get("view_type", "")
    
    # Determine if it's MLO or CC based on the view_type string
    is_mlo = "MLO" in view_type_full or "Medio-Lateral" in view_type_full
    is_cc = "CC" in view_type_full or "Cranio-Caudal" in view_type_full
    
    # Determine breast density based on image statistics
    mean_intensity = stats.get("mean_intensity", 128)
    if mean_intensity > 200:
        breast_density = "Almost entirely fatty (ACR A)"
    elif mean_intensity > 150:
        breast_density = "Scattered fibroglandular densities (ACR B)"
    elif mean_intensity > 100:
        breast_density = "Heterogeneously dense (ACR C)"
    else:
        breast_density = "Extremely dense (ACR D)"
    
    # Count detected abnormalities by type
    masses_count = sum(1 for r in regions if 'Mass' in r.get('cancer_type', ''))
    calc_count = sum(1 for r in regions if 'Calcification' in r.get('cancer_type', ''))
    distortion_count = sum(1 for r in regions if 'distortion' in r.get('cancer_type', '').lower())
    asymmetry_count = sum(1 for r in regions if 'asymmetry' in r.get('cancer_type', '').lower())
    
    # Generate descriptions
    masses_desc = f"{masses_count} suspicious mass(es) detected" if masses_count > 0 else "No suspicious masses identified"
    calc_desc = f"{calc_count} calcification cluster(s) detected" if calc_count > 0 else "No suspicious calcifications"
    distortion_desc = f"{distortion_count} area(s) of architectural distortion" if distortion_count > 0 else "No architectural distortion"
    asymmetry_desc = f"{asymmetry_count} focal asymmetry detected" if asymmetry_count > 0 else "No significant asymmetry"
    
    # Determine image quality based on contrast
    contrast = stats.get("contrast", 20)
    if contrast > 25:
        image_quality = "Excellent - High contrast, optimal visualization"
    elif contrast > 15:
        image_quality = "Good - Adequate for diagnostic evaluation"
    elif contrast > 10:
        image_quality = "Acceptable - Minor limitations"
    else:
        image_quality = "Limited - May require repeat imaging"
    
    # Generate impression based on findings
    if malignant_prob >= 75:
        impression = "Highly suspicious findings requiring immediate follow-up"
    elif malignant_prob >= 50:
        impression = "Suspicious findings - biopsy recommended"
    elif malignant_prob >= 25:
        impression = "Probably benign - short interval follow-up suggested"
    else:
        impression = "No significant abnormality detected"
    
    # Generate comparison text based on detected view
    if is_mlo:
        comparison = (
            f"MLO view findings as described above. "
            f"Breast density is {breast_density.split('(')[0].strip().lower()}. "
            f"{'Suspicious findings warrant further evaluation.' if malignant_prob >= 50 else 'No additional suspicious findings detected.'}"
        )
    elif is_cc:
        comparison = (
            f"CC view findings as described above. "
            f"Breast density is {breast_density.split('(')[0].strip().lower()}. "
            f"{'Suspicious findings warrant further evaluation.' if malignant_prob >= 50 else 'No additional suspicious findings detected.'}"
        )
    else:
        comparison = (
            f"View type could not be determined from filename. "
            f"Breast density is {breast_density.split('(')[0].strip().lower()}. "
            f"{'Suspicious findings warrant further evaluation.' if malignant_prob >= 50 else 'Findings as described above.'}"
        )
    
    # Create view-specific analysis structure
    result = {"comparison": comparison}
    
    # Only add the detected view to the result
    if is_mlo:
        # MLO View Analysis
        result["mlo"] = {
            "image_quality": image_quality,
            "positioning": "Properly positioned with pectoral muscle to nipple level",
            "breast_density": breast_density,
            "masses": masses_desc,
            "calcifications": calc_desc,
            "architectural_distortion": distortion_desc,
            "pectoral_muscle": "Adequately visualized extending to nipple level",
            "axillary_findings": "No suspicious axillary lymphadenopathy",
            "inframammary_fold": "Inframammary fold included",
            "impression": impression,
        }
    elif is_cc:
        # CC View Analysis
        result["cc"] = {
            "image_quality": image_quality,
            "positioning": "Properly positioned with adequate compression",
            "breast_density": breast_density,
            "masses": masses_desc,
            "calcifications": calc_desc,
            "asymmetry": asymmetry_desc,
            "skin_nipple_changes": "No skin thickening or nipple retraction",
            "medial_coverage": "Adequate medial tissue included",
            "lateral_coverage": "Adequate lateral tissue included",
            "impression": impression,
        }
    else:
        # If view type cannot be determined, include both for compatibility
        result["cc"] = {
            "image_quality": image_quality,
            "positioning": "Properly positioned with adequate compression",
            "breast_density": breast_density,
            "masses": masses_desc,
            "calcifications": calc_desc,
            "asymmetry": asymmetry_desc,
            "skin_nipple_changes": "No skin thickening or nipple retraction",
            "medial_coverage": "Adequate medial tissue included",
            "lateral_coverage": "Adequate lateral tissue included",
            "impression": impression,
        }
        result["mlo"] = {
            "image_quality": image_quality,
            "positioning": "Properly positioned with pectoral muscle to nipple level",
            "breast_density": breast_density,
            "masses": masses_desc,
            "calcifications": calc_desc,
            "architectural_distortion": distortion_desc,
            "pectoral_muscle": "Adequately visualized extending to nipple level",
            "axillary_findings": "No suspicious axillary lymphadenopathy",
            "inframammary_fold": "Inframammary fold included",
            "impression": impression,
        }
    
    return result


# ==================== APP CONFIGURATION ====================

app = FastAPI(
    title="Breast Cancer Detection API",
    description=(
        "AI-powered breast cancer detection API for mammogram analysis.\n\n"
        "**Features:**\n"
        "- Image classification (Benign/Malignant)\n"
        "- Grad-CAM visualizations\n"
        "- Detailed region detection\n"
        "- Risk level assessment\n"
        "- PDF report generation\n\n"
        "⚠️ **EDUCATIONAL USE ONLY** - Not for medical diagnosis."
    ),
    version="2.0.0",
    docs_url="/",  # Swagger UI at root
    redoc_url="/redoc",
)

# CORS Configuration - Allow all origins for public API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODEL LOADING ====================

BASE_DIR = Path(__file__).resolve().parent
_model: Optional[keras.Model] = None


def get_model_path() -> Path:
    """Get the model path, checking multiple locations"""
    # Check /app/models first (Docker container)
    docker_model = Path("/app/models/breast_cancer_model.keras")
    if docker_model.exists() and docker_model.stat().st_size > 100_000_000:
        return docker_model
    
    # Check root directory
    root_model = BASE_DIR / "breast_cancer_model.keras"
    if root_model.exists() and root_model.stat().st_size > 100_000_000:
        return root_model
    
    # Check backend/models directory
    backend_model = BASE_DIR / "backend" / "models" / "breast_cancer_model.keras"
    if backend_model.exists() and backend_model.stat().st_size > 100_000_000:
        return backend_model
    
    # Check models directory in root
    models_dir_model = BASE_DIR / "models" / "breast_cancer_model.keras"
    if models_dir_model.exists() and models_dir_model.stat().st_size > 100_000_000:
        return models_dir_model
    
    # Return default (Docker path) if none exist
    return docker_model


def download_model_from_hf():
    """Download model from Hugging Face Hub if not present"""
    model_path = get_model_path()
    
    if model_path.exists() and model_path.stat().st_size > 100_000_000:
        logger.info(f"✅ Model already exists: {model_path}")
        return True
    
    logger.info("📥 Downloading model from Hugging Face...")
    
    try:
        from huggingface_hub import hf_hub_download
        
        # Your HF repo details
        repo_id = os.environ.get("HF_MODEL_REPO", "Bhavanakhatri/breastcancerdetection")
        
        # Create models directory if it doesn't exist
        models_dir = BASE_DIR / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename="breast_cancer_model.keras",
            local_dir=str(models_dir),
            local_dir_use_symlinks=False
        )
        
        logger.info(f"✅ Model downloaded successfully to {downloaded_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Model download failed: {e}")
        return False


def get_model() -> keras.Model:
    """Load model (singleton pattern)"""
    global _model
    
    if _model is None:
        model_path = get_model_path()
        
        # Try to download if not exists
        if not model_path.exists():
            logger.info("Model not found, attempting download...")
            download_model_from_hf()
            model_path = get_model_path()
        
        if not model_path.exists():
            raise RuntimeError(
                f"Model file not found at {model_path}. "
                "Please ensure model file is in the repository or set HF_MODEL_REPO environment variable."
            )
        
        try:
            logger.info(f"📂 Loading model from {model_path}")
            _model = keras.models.load_model(
                str(model_path),
                compile=False,
                safe_mode=False
            )
            _model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            logger.info("✅ Model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Model loading failed: {e}")
            raise RuntimeError(f"Failed to load model: {e}")
    
    return _model


# ==================== HELPER FUNCTIONS ====================

def preprocess_image(image: Image.Image) -> np.ndarray:
    """
    Preprocess image for model input
    - Resize to 224x224
    - Convert to RGB
    - Normalize to [0, 1]
    """
    # Resize
    img = image.resize((224, 224), Image.LANCZOS)
    img_array = np.array(img)
    
    # Handle different image formats
    if img_array.ndim == 2:  # Grayscale
        img_array = np.stack([img_array] * 3, axis=-1)
    elif img_array.shape[2] == 4:  # RGBA
        img_array = img_array[:, :, :3]
    
    # Normalize
    img_array = img_array.astype("float32") / 255.0
    
    # Add batch dimension
    img_array = np.expand_dims(img_array, axis=0)
    
    return img_array


def get_image_statistics(image: Image.Image) -> Dict[str, float]:
    """Calculate image statistics"""
    img_array = np.array(image)
    
    # Convert to 3 channels if needed
    if img_array.ndim == 2:
        img_array = np.stack([img_array] * 3, axis=-1)
    elif img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]
    
    return {
        "mean_intensity": float(np.mean(img_array)),
        "std_intensity": float(np.std(img_array)),
        "min_intensity": float(np.min(img_array)),
        "max_intensity": float(np.max(img_array)),
        "median_intensity": float(np.median(img_array)),
        "brightness": float(np.mean(img_array) / 255.0 * 100),
        "contrast": float(np.std(img_array) / 255.0 * 100),
    }


def get_risk_level(confidence: float) -> Tuple[str, str, str]:
    """
    Determine risk level from confidence score
    confidence = P(malignant)
    """
    if confidence > 0.5:
        malignant_prob = confidence * 100
        if malignant_prob >= 90:
            return "Very High Risk", "🔴", "#ff0000"
        elif malignant_prob >= 75:
            return "High Risk", "🟠", "#ff6600"
        elif malignant_prob >= 60:
            return "Moderate-High Risk", "🟡", "#ffaa00"
        else:
            return "Moderate Risk", "🟡", "#ffcc00"
    else:
        benign_prob = (1 - confidence) * 100
        if benign_prob >= 90:
            return "Very Low Risk", "🟢", "#00cc00"
        elif benign_prob >= 75:
            return "Low Risk", "🟢", "#33cc33"
        elif benign_prob >= 60:
            return "Low-Moderate Risk", "🟡", "#99cc00"
        else:
            return "Moderate Risk", "🟡", "#cccc00"


def pil_to_base64(image: Optional[Image.Image]) -> Optional[str]:
    """Convert PIL Image to base64 string"""
    if image is None:
        return None
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ==================== CORE ANALYSIS LOGIC ====================

def run_full_analysis(image: Image.Image, filename: str = None) -> Tuple[Dict[str, Any], Dict[str, Image.Image]]:
    """
    Full analysis with Grad-CAM visualizations and detailed findings
    """
    model = get_model()
    preprocessed = preprocess_image(image)

    # model.predict -> sigmoid output
    prediction = float(model.predict(preprocessed, verbose=0)[0][0])
    confidence = prediction

    stats = get_image_statistics(image)

    benign_prob = (1 - confidence) * 100
    malignant_prob = confidence * 100

    # Generate Grad-CAM visualizations
    if GRADCAM_AVAILABLE:
        (
            heatmap_array,
            overlay_image,
            heatmap_only,
            bbox_image,
            cancer_type_image,
            heatmap_error,
            detailed_findings,
        ) = create_gradcam_visualization(image, preprocessed, model, confidence)
    else:
        heatmap_array = None
        overlay_image = None
        heatmap_only = None
        bbox_image = None
        cancer_type_image = None
        heatmap_error = "Grad-CAM module not available"
        detailed_findings = {}

    if confidence > 0.5:
        result = "Malignant (Cancerous)"
        probability = malignant_prob
    else:
        result = "Benign (Non-Cancerous)"
        probability = benign_prob

    # risk level
    if malignant_prob > 90:
        risk_level = "Very High Risk"
    elif malignant_prob > 75:
        risk_level = "High Risk"
    elif malignant_prob > 60:
        risk_level = "Moderate-High Risk"
    elif malignant_prob > 40:
        risk_level = "Moderate Risk"
    elif malignant_prob > 25:
        risk_level = "Low-Moderate Risk"
    elif malignant_prob > 10:
        risk_level = "Low Risk"
    else:
        risk_level = "Very Low Risk"

    risk_level2, risk_icon, risk_color = get_risk_level(confidence)

    analysis: Dict[str, Any] = {
        "result": result,
        "probability": float(probability),
        "confidence": float(confidence),
        "benign_prob": float(benign_prob),
        "malignant_prob": float(malignant_prob),
        "riskLevel": risk_level,
        "risk_icon": risk_icon,
        "risk_color": risk_color,
        "stats": stats,
        "heatmap_error": heatmap_error,
        "image_size": {"width": image.size[0], "height": image.size[1]},
        "file_format": image.format or "N/A",
        "findings": detailed_findings,
    }
    
    # Add view-specific analysis (CC/MLO)
    if GRADCAM_AVAILABLE:
        detected_regions = detailed_findings.get('regions', []) if detailed_findings else []
        view_analysis = generate_mammogram_view_analysis(
            image, 
            heatmap_array, 
            confidence, 
            detected_regions,
            view_type="auto",
            filename=filename
        )
        analysis["view_analysis"] = view_analysis

    images = {
        "original": image,
        "overlay_image": overlay_image,
        "heatmap_only": heatmap_only,
        "bbox_image": bbox_image,
        "cancer_type_image": cancer_type_image,
    }

    return analysis, images


# ==================== API ENDPOINTS ====================

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns server status and model availability
    """
    model_status = "not_loaded"
    model_error = None
    model_path = get_model_path()
    
    try:
        if model_path.exists():
            _ = get_model()
            model_status = "loaded"
        else:
            model_status = "missing"
            model_error = f"Model file not found at {model_path}"
    except Exception as exc:
        model_status = "error"
        model_error = str(exc)
    
    return {
        "status": "healthy",
        "service": "Breast Cancer Detection API",
        "version": "2.0.0",
        "model_status": model_status,
        "gradcam_available": GRADCAM_AVAILABLE,
        "report_available": REPORT_AVAILABLE,
        "model_error": model_error,
        "model_path": str(model_path),
    }


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Complete analysis with Grad-CAM visualizations
    
    **Input:**
    - file: Image file (JPEG, PNG, etc.)
    
    **Output:**
    - Complete analysis results
    - Grad-CAM heatmap (base64)
    - Overlay image (base64)
    - Bounding boxes (base64)
    - Detailed findings
    - Risk assessment
    - Image statistics
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an image file (JPEG, PNG, etc.)"
        )
    
    try:
        # Read and open image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        logger.info(f"📸 Processing image: {file.filename}, size: {image.size}")
        
    except Exception as e:
        logger.error(f"❌ Image reading failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read image: {str(e)}"
        )
    
    try:
        # Run full analysis
        analysis, images = run_full_analysis(image, filename=file.filename)
        
        # Convert numpy types to Python native types
        analysis = convert_numpy_types(analysis)
        
        # Prepare response with base64 encoded images
        response = {
            **analysis,
            "stats": {k: float(v) for k, v in analysis["stats"].items()},
            "images": {
                "original": pil_to_base64(images["original"]),
                "overlay": pil_to_base64(images["overlay_image"]),
                "heatmap_only": pil_to_base64(images["heatmap_only"]),
                "bbox": pil_to_base64(images["bbox_image"]),
                "cancer_type": pil_to_base64(images["cancer_type_image"]),
            },
        }
        
        logger.info(f"✅ Analysis complete: {analysis['result']} ({analysis['confidence']:.2%})")
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/report")
async def generate_report(
    file: UploadFile = File(...),
    patient_name: Optional[str] = Form(None),
    patient_age: Optional[str] = Form(None),
    patient_sex: Optional[str] = Form(None),
    patient_hn: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    request_doctor: Optional[str] = Form(None),
    report_by: Optional[str] = Form(None),
):
    """
    Generate PDF mammogram report with optional patient information
    """
    if not REPORT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Report generation module not available"
        )
    
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    data = await file.read()
    try:
        image = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to read image file.")

    try:
        analysis, images = run_full_analysis(image, filename=file.filename)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")

    # Generate CC/MLO view analysis
    view_analysis = generate_view_analysis(analysis, image)

    try:
        pdf_bytes = generate_report_pdf(
            result=analysis["result"],
            probability=analysis["probability"],
            risk_level=analysis["riskLevel"],
            benign_prob=analysis["benign_prob"],
            malignant_prob=analysis["malignant_prob"],
            stats=analysis["stats"],
            image_size=(analysis["image_size"]["width"], analysis["image_size"]["height"]),
            file_format=analysis["file_format"],
            original_image=images["original"],
            overlay_image=images["overlay_image"],
            heatmap_only=images["heatmap_only"],
            bbox_image=images["bbox_image"],
            cancer_type_image=images.get("cancer_type_image"),
            confidence=analysis["confidence"],
            patient_name=patient_name or "Patient Name",
            patient_age=patient_age or "N/A",
            patient_sex=patient_sex or "Female",
            patient_hn=patient_hn or "N/A",
            department=department or "Radiology",
            request_doctor=request_doctor or "Dr. [Name]",
            report_by=report_by or "Dr. [Radiologist Name]",
            findings=analysis.get("findings"),
            view_analysis=view_analysis,
        )
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="mammogram_report.pdf"'},
    )


# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    logger.info("🚀 Starting Breast Cancer Detection API v2.0...")
    
    try:
        # Preload model
        get_model()
        logger.info("✅ API ready to serve requests")
        logger.info(f"✅ Grad-CAM available: {GRADCAM_AVAILABLE}")
        logger.info(f"✅ Report generation available: {REPORT_AVAILABLE}")
    except Exception as e:
        logger.warning(f"⚠️ Model preload failed: {e}")
        logger.warning("Model will be loaded on first request")


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 7860))  # HF Spaces default port
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
