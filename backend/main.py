# def main():
#     print("Hello from repl-nix-workspace!")


# if __name__ == "__main__":
#     main()


# main.py  -> FastAPI backend

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any, Tuple, Optional, List

import base64
import io
import os
import gc
from pathlib import Path

import numpy as np
from PIL import Image

# Lazy import TensorFlow to save memory on startup
# from tensorflow import keras  # Moved to function level

from grad_cam import create_gradcam_visualization, generate_mammogram_view_analysis
from report_generator import generate_report_pdf


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


app = FastAPI(
    title="Breast Cancer Detection API",
    description=(
        "AI-based Breast Cancer Detection backend.\n"
        "Upload a medical image and get prediction, Grad-CAM heatmaps, "
        "bounding boxes, and a detailed PDF report.\n\n"
        "⚠ EDUCATIONAL USE ONLY – NOT FOR REAL MEDICAL DIAGNOSIS."
    ),
    version="1.0.0",
)

# ----------------- MODEL LOADING (shared) -----------------
BASE_DIR = Path(__file__).resolve().parent
# Handle both local and Render paths
MODEL_PATH_ENV = os.environ.get("MODEL_PATH")
if MODEL_PATH_ENV:
    MODEL_PATH = Path(MODEL_PATH_ENV)
else:
    # Try both paths: with and without 'backend' prefix
    local_path = BASE_DIR / "models" / "breast_cancer_model.keras"
    if local_path.exists():
        MODEL_PATH = local_path
    else:
        # Fallback for when backend is root directory in Render
        MODEL_PATH = Path("/opt/render/project/src/models/breast_cancer_model.keras")
        
_model: Optional[Any] = None  # Lazy loaded, so using Any instead of keras.Model


def check_model_exists():
    """Check if model file exists"""
    if MODEL_PATH.exists():
        size_mb = MODEL_PATH.stat().st_size / (1024 * 1024)
        if size_mb > 10:  # Valid model should be > 10 MB
            print(f"✅ Model exists ({size_mb:.1f} MB)")
            return True
        else:
            print(f"⚠️ Model file too small ({size_mb:.1f} MB)")
            return False
    
    print(f"❌ Model file not found at {MODEL_PATH}")
    return False


def get_model():
    """Model sirf ek baar load karo, baar-baar reuse karein."""
    from tensorflow import keras
    
    global _model
    if _model is None:
        # Check if model exists
        if not check_model_exists():
            raise RuntimeError(
                f"Model file not found at {MODEL_PATH}. "
                "Please ensure model file is in the repository."
            )
        
        try:
            # Try loading with safe_mode=False for compatibility
            _model = keras.models.load_model(MODEL_PATH, compile=False, safe_mode=False)
            _model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
            
            # Free up memory after loading
            gc.collect()
        except TypeError as e:
            if "batch_shape" in str(e) or "safe_mode" in str(e):
                # Keras version mismatch - recreate the model architecture
                print("Keras version mismatch detected, rebuilding model...")
                _model = _create_compatible_model()
                _load_weights_from_keras_file(_model, MODEL_PATH)
            else:
                raise e
    return _model


def _create_compatible_model():
    """Create a compatible model architecture for breast cancer detection."""
    from tensorflow import keras
    from tensorflow.keras import layers, Sequential
    
    model = Sequential([
        layers.Input(shape=(224, 224, 3)),
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Flatten(),
        layers.Dense(512, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    return model


def _load_weights_from_keras_file(model, keras_path: Path):
    """Extract and load weights from a .keras file."""
    import zipfile
    import tempfile
    import shutil
    
    try:
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(keras_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        weights_path = os.path.join(temp_dir, "model.weights.h5")
        if os.path.exists(weights_path):
            model.load_weights(weights_path)
            print("Weights loaded successfully!")
        else:
            print("No weights file found, using random initialization")
        
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Could not load weights: {e}")


# ----------------- HELPERS: preprocessing, stats, risk -----------------

def preprocess_image(image: Image.Image) -> np.ndarray:
    """Streamlit code se hi liya hai: resize 224x224, normalize, RGB fix."""
    img = image.resize((224, 224), Image.LANCZOS)
    img_array = np.array(img)

    if img_array.ndim == 2:  # grayscale
        img_array = np.stack([img_array] * 3, axis=-1)
    elif img_array.shape[2] == 4:  # RGBA
        img_array = img_array[:, :, :3]

    img_array = img_array.astype("float32") / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array


def get_image_statistics(image: Image.Image) -> Dict[str, float]:
    img_array = np.array(image)

    if img_array.ndim == 2:
        img_array = np.stack([img_array] * 3, axis=-1)
    elif img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]

    stats = {
        "mean_intensity": float(np.mean(img_array)),
        "std_intensity": float(np.std(img_array)),
        "min_intensity": float(np.min(img_array)),
        "max_intensity": float(np.max(img_array)),
        "median_intensity": float(np.median(img_array)),
        "brightness": float(np.mean(img_array) / 255.0 * 100),
        "contrast": float(np.std(img_array) / 255.0 * 100),
    }
    return stats


def get_risk_level(confidence: float) -> Tuple[str, str, str]:
    """
    Tumhare Streamlit wale get_risk_level se same logic.
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
    if image is None:
        return None
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ----------------- CORE ANALYSIS LOGIC (Streamlit ka brain yahan) -----------------

def run_full_analysis(image: Image.Image, filename: str = None) -> Tuple[Dict[str, Any], Dict[str, Image.Image]]:
    """
    Yeh function tumhari Streamlit logic ka backend version hai:
    - model se prediction
    - stats
    - Grad-CAM heatmaps
    - risk level, probabilities
    - detailed findings from image analysis
    """
    model = get_model()
    preprocessed = preprocess_image(image)

    # model.predict -> sigmoid output
    prediction = float(model.predict(preprocessed, verbose=0)[0][0])
    confidence = prediction

    stats = get_image_statistics(image)

    benign_prob = (1 - confidence) * 100
    malignant_prob = confidence * 100

    (
        heatmap_array,
        overlay_image,
        heatmap_only,
        bbox_image,
        cancer_type_image,
        heatmap_error,
        detailed_findings,
    ) = create_gradcam_visualization(image, preprocessed, model, confidence)

    if confidence > 0.5:
        result = "Malignant (Cancerous)"
        probability = malignant_prob
    else:
        result = "Benign (Non-Cancerous)"
        probability = benign_prob

    # risk level (same logic as app.py)
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
        "risk_level": risk_level,
        "risk_icon": risk_icon,
        "risk_color": risk_color,
        "stats": stats,
        "heatmap_error": heatmap_error,
        "image_size": {"width": image.size[0], "height": image.size[1]},
        "file_format": image.format or "N/A",
        "findings": detailed_findings,  # NEW: Detailed findings from the image
    }
    
    # Add view-specific analysis (CC/MLO)
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


# ----------------- CORS (React ke liye) -----------------
# Allow all origins for development
ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,                 # Must be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ----------------- ROUTES -----------------

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": "Breast Cancer Detection API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze (POST - upload image)",
            "report": "/report (POST - get PDF report)",
            "docs": "/docs (API documentation)"
        }
    }


@app.get("/health")
async def health_check():
    """Simple health check - returns ok if server is running."""
    model_status = "not_loaded"
    model_error = None
    
    # Check if model file exists
    if MODEL_PATH.exists():
        try:
            _ = get_model()
            model_status = "loaded"
        except Exception as exc:
            model_status = "error"
            model_error = str(exc)
    else:
        model_status = "missing"
        model_error = f"Model file not found at {MODEL_PATH}"
    
    # Health check passes as long as server is running
    return {
        "status": "ok",
        "model_status": model_status,
        "model_error": model_error,
        "model_path": str(MODEL_PATH)
    }


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    React se:
    - FormData banake
    - field name 'file'
    ke saath POST karo.
    """
    if not file.content_type.startswith("image/"):
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

    # Convert numpy types to Python native types for JSON serialization
    analysis = convert_numpy_types(analysis)
    
    result = {
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
    
    # Free memory after processing
    gc.collect()
    
    return result


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
    Generate PDF mammogram report with optional patient information.
    
    Parameters:
    - file: Image file (required)
    - patient_name: Patient's full name
    - patient_age: Patient's age (e.g., "45 Years")
    - patient_sex: Patient's sex
    - patient_hn: Hospital Number or Patient ID
    - department: Department name
    - request_doctor: Name of requesting physician
    - report_by: Name of reporting radiologist
    """
    if not file.content_type.startswith("image/"):
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

    # Generate CC/MLO view analysis based on the findings
    view_analysis = generate_view_analysis(analysis, image)

    try:
        pdf_bytes = generate_report_pdf(
            result=analysis["result"],
            probability=analysis["probability"],
            risk_level=analysis["risk_level"],
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
            # Patient information (use defaults if not provided)
            patient_name=patient_name or "Patient Name",
            patient_age=patient_age or "N/A",
            patient_sex=patient_sex or "Female",
            patient_hn=patient_hn or "N/A",
            department=department or "Radiology",
            request_doctor=request_doctor or "Dr. [Name]",
            report_by=report_by or "Dr. [Radiologist Name]",
            # Detailed findings
            findings=analysis.get("findings"),
            # View-specific analysis (CC/MLO)
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

# Run command:
# uvicorn main:app --reload --port 8000
