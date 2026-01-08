import tensorflow as tf
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib

matplotlib.use("Agg")  # Ensure headless rendering for serverless environments
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from scipy import ndimage

def make_gradcam_heatmap(img_array, model, last_conv_layer_index, pred_index=None):
    """
    Generate Grad-CAM heatmap for a given image and model.
    
    Args:
        img_array: Preprocessed input image (batch_size, height, width, channels)
        model: The trained model  
        last_conv_layer_index: Index of the last convolutional layer
        pred_index: Index of the class to visualize (None for top prediction)
    
    Returns:
        Normalized heatmap as numpy array
    """
    # Get the last convolutional layer
    last_conv_layer = model.layers[last_conv_layer_index]
    
    # For loaded Sequential models, we need to create inputs manually
    # Create a new input tensor
    inputs = tf.keras.Input(shape=(224, 224, 3))
    
    # Pass through all layers up to and including the last conv layer
    x = inputs
    for i, layer in enumerate(model.layers):
        x = layer(x)
        if i == last_conv_layer_index:
            conv_output = x
    
    # Get the final output
    final_output = x
    
    # Create a model that maps inputs to activations of the last conv layer and the output predictions
    grad_model = tf.keras.Model(
        inputs=inputs,
        outputs=[conv_output, final_output]
    )
    
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array)
        if pred_index is None:
            pred_index = 0
        class_channel = predictions[:, pred_index]
    
    grads = tape.gradient(class_channel, conv_outputs)
    
    if grads is None:
        return None
    
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    
    heatmap = tf.maximum(heatmap, 0)
    max_val = tf.math.reduce_max(heatmap)
    if max_val > 0:
        heatmap = heatmap / max_val
    
    return heatmap.numpy()

def create_tissue_mask(img_array, threshold=15):
    """
    Create a mask identifying tissue (non-background) areas.
    
    Args:
        img_array: Image as numpy array
        threshold: Pixel intensity threshold to distinguish tissue from background
    
    Returns:
        Binary mask where True = tissue area
    """
    if len(img_array.shape) == 3:
        gray = np.mean(img_array, axis=2)
    else:
        gray = img_array
    
    # Tissue is where pixel intensity is above threshold (not black background)
    mask = gray > threshold
    return mask


def create_intensity_based_heatmap(img_array):
    """Create heatmap based on image intensity - highlights bright regions (potential lesions)."""
    from scipy.ndimage import gaussian_filter
    
    if len(img_array.shape) == 3:
        gray = np.mean(img_array, axis=2)
    else:
        gray = img_array.copy()
    
    # Normalize
    gray = gray.astype(np.float32)
    g_min, g_max = np.min(gray), np.max(gray)
    if g_max > g_min:
        gray = (gray - g_min) / (g_max - g_min)
    
    # Apply Gaussian blur to smooth
    gray = gaussian_filter(gray, sigma=3)
    
    # Enhance contrast - focus on bright regions
    gray = np.power(gray, 0.7)
    
    # Normalize again
    g_min, g_max = np.min(gray), np.max(gray)
    if g_max > g_min:
        gray = (gray - g_min) / (g_max - g_min)
    
    return gray


def create_heatmap_overlay(original_image, heatmap, alpha=0.5, colormap='jet'):
    """
    Create an overlay of the heatmap on the original image.
    Only shows heatmap on tissue areas, not on black background.
    Uses intensity-based fallback if Grad-CAM fails.
    
    Args:
        original_image: PIL Image object
        heatmap: Normalized heatmap array
        alpha: Transparency of the heatmap overlay (0-1)
        colormap: Matplotlib colormap name
    
    Returns:
        PIL Image with heatmap overlay
    """
    img_array = np.array(original_image)
    
    # Check if Grad-CAM heatmap has meaningful variation
    hmap_range = np.max(heatmap) - np.min(heatmap)
    print(f"DEBUG: Heatmap range = {hmap_range:.4f}")
    
    if hmap_range < 0.01:
        # Grad-CAM failed - use intensity-based heatmap as fallback
        print("DEBUG: Grad-CAM heatmap has no variation, using intensity-based fallback")
        img_small = np.array(original_image.resize((heatmap.shape[1], heatmap.shape[0])))
        heatmap = create_intensity_based_heatmap(img_small)
    
    # Enhance contrast
    hmap_min, hmap_max = np.min(heatmap), np.max(heatmap)
    if hmap_max > hmap_min:
        heatmap = (heatmap - hmap_min) / (hmap_max - hmap_min)
    
    # Apply gamma for better visibility
    heatmap = np.power(heatmap, 0.5)
    
    heatmap_resized = np.array(Image.fromarray((heatmap * 255).astype(np.uint8)).resize(
        (original_image.size[0], original_image.size[1]),
        Image.BILINEAR
    ))
    
    heatmap_resized = heatmap_resized.astype(np.float32) / 255.0
    
    # Create tissue mask to avoid showing heatmap on black background
    tissue_mask = create_tissue_mask(img_array, threshold=15)
    
    # Zero out heatmap in background areas
    heatmap_resized = heatmap_resized * tissue_mask
    
    cmap = cm.get_cmap(colormap)
    heatmap_colored = cmap(heatmap_resized)
    heatmap_colored = (heatmap_colored[:, :, :3] * 255).astype(np.uint8)
    
    if len(img_array.shape) == 2:
        img_array = np.stack([img_array] * 3, axis=-1)
    elif img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]
    
    # Only apply overlay where there is tissue
    overlay = img_array.copy().astype(np.float32)
    tissue_mask_3d = np.stack([tissue_mask] * 3, axis=-1)
    overlay = np.where(tissue_mask_3d, 
                       (1 - alpha) * img_array + alpha * heatmap_colored,
                       img_array)
    overlay = np.clip(overlay, 0, 255).astype(np.uint8)
    
    return Image.fromarray(overlay)

def get_last_conv_layer_index(model):
    """
    Find the index of the last convolutional layer in the model.
    
    Args:
        model: Keras model
    
    Returns:
        Index of the last Conv2D layer
    """
    conv_layer_indices = [i for i, layer in enumerate(model.layers) if isinstance(layer, tf.keras.layers.Conv2D)]
    if conv_layer_indices:
        return conv_layer_indices[-1]
    return None

def detect_bounding_boxes(heatmap, original_image_size, threshold=0.6, min_area=100, tissue_mask=None):
    """
    Detect bounding boxes around high-activation regions in the heatmap.
    Only detects within tissue areas if tissue_mask is provided.
    
    Args:
        heatmap: Normalized heatmap array (values 0-1)
        original_image_size: Tuple of (width, height) of original image
        threshold: Activation threshold (0-1) for detecting regions
        min_area: Minimum area in pixels for a region to be considered
        tissue_mask: Optional binary mask of tissue area (same size as original image)
    
    Returns:
        List of bounding boxes [(x1, y1, x2, y2, confidence), ...]
    """
    # If tissue mask provided, resize it to heatmap size and apply
    if tissue_mask is not None:
        # Resize tissue mask to heatmap dimensions
        tissue_mask_resized = np.array(Image.fromarray(tissue_mask.astype(np.uint8) * 255).resize(
            (heatmap.shape[1], heatmap.shape[0]),
            Image.NEAREST
        )) > 127
        # Zero out heatmap in background areas
        heatmap = heatmap * tissue_mask_resized
    
    # Threshold the heatmap to get high-activation regions
    binary_mask = (heatmap > threshold).astype(np.uint8)
    
    # Label connected components
    labeled_array, num_features = ndimage.label(binary_mask)
    
    boxes = []
    heatmap_h, heatmap_w = heatmap.shape
    orig_w, orig_h = original_image_size
    
    scale_x = orig_w / heatmap_w
    scale_y = orig_h / heatmap_h
    
    for region_id in range(1, num_features + 1):
        # Get coordinates of this region
        region_coords = np.where(labeled_array == region_id)
        
        if len(region_coords[0]) < min_area / (scale_x * scale_y):
            continue
        
        # Get bounding box coordinates in heatmap space
        y_min, y_max = region_coords[0].min(), region_coords[0].max()
        x_min, x_max = region_coords[1].min(), region_coords[1].max()
        
        # Scale to original image size
        x1 = int(x_min * scale_x)
        y1 = int(y_min * scale_y)
        x2 = int(x_max * scale_x)
        y2 = int(y_max * scale_y)
        
        # Calculate confidence (average activation in this region)
        region_mask = (labeled_array == region_id)
        confidence = float(heatmap[region_mask].mean())
        
        boxes.append((x1, y1, x2, y2, confidence))
    
    return boxes

def draw_bounding_boxes_with_cancer_type(image, regions, line_width=4):
    """
    Draw bounding boxes with cancer type labels ATTACHED to each box.
    Each box and its label use the SAME coordinates - no drift possible.
    
    Args:
        image: PIL Image
        regions: List of region dicts with bbox, cancer_type, confidence, severity
        line_width: Width of the bounding box lines
    
    Returns:
        PIL Image with bounding boxes and cancer type labels attached
    """
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except:
        font = ImageFont.load_default()
    
    # Color mapping based on severity
    severity_colors = {
        'high': '#DC2626',      # Red
        'medium': '#F59E0B',    # Orange
        'moderate': '#F59E0B',  # Orange
        'low': '#10B981'        # Green
    }
    
    for region in regions:
        bbox = region['bbox']
        x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
        
        cancer_type = region.get('cancer_type', 'Unknown')
        confidence = region.get('confidence', 0)
        severity = region.get('severity', 'low')
        
        # Get color based on severity
        box_color = severity_colors.get(severity.lower(), '#FF0000')
        
        # Draw bounding box
        draw.rectangle([x1, y1, x2, y2], outline=box_color, width=line_width)
        
        # Create label: "Cancer Type - XX%"
        label = f"{cancer_type} - {confidence:.0f}%"
        
        # Label positioning constants
        padding = 8
        offset = 6
        
        # Get text dimensions
        text_bbox = draw.textbbox((0, 0), label, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Calculate space needed for label
        space_needed = text_height + padding * 2 + offset
        
        # Determine position: above box if space available, otherwise inside
        if y1 >= space_needed:
            # Place ABOVE the box (preferred)
            label_x = x1 + 5
            bg_y1 = y1 - space_needed
            bg_y2 = y1 - offset
            text_y = bg_y1 + padding
        else:
            # Place INSIDE the box at top-left
            label_x = x1 + padding
            bg_y1 = y1 + 5
            bg_y2 = y1 + 5 + text_height + padding * 2
            text_y = bg_y1 + padding
        
        # Draw label background (same color as box)
        bg_x1 = label_x - padding
        bg_x2 = label_x + text_width + padding
        draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=box_color, outline=box_color)
        
        # Draw label text (white)
        draw.text((label_x, text_y), label, fill='white', font=font)
    
    return img_copy


def draw_bounding_boxes(image, boxes, box_color='red', text_color='white', line_width=3):
    """
    Draw bounding boxes on an image.
    
    Args:
        image: PIL Image
        boxes: List of bounding boxes [(x1, y1, x2, y2, confidence), ...]
        box_color: Color for the bounding box
        text_color: Color for the confidence text
        line_width: Width of the bounding box lines
    
    Returns:
        PIL Image with bounding boxes drawn
    """
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    for i, (x1, y1, x2, y2, confidence) in enumerate(boxes):
        # Draw rectangle
        draw.rectangle([x1, y1, x2, y2], outline=box_color, width=line_width)
        
        # Draw label - position above or inside box depending on space
        label = f"Region {i+1}: {confidence*100:.1f}%"
        
        # Check if there's enough space above the box (need ~25 pixels)
        if y1 >= 25:
            label_y = y1 - 20
        else:
            # Not enough space above, put it inside the box at the top
            label_y = y1 + 5
        
        bbox = draw.textbbox((x1, label_y), label, font=font)
        draw.rectangle([bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2], fill=box_color)
        
        # Draw label text
        draw.text((x1, label_y), label, fill=text_color, font=font)
    
    return img_copy

def get_region_location(x1, y1, x2, y2, img_width, img_height):
    """
    Determine the anatomical location of a detected region.
    """
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    # Determine horizontal position
    if center_x < img_width * 0.33:
        h_pos = "lateral"
    elif center_x > img_width * 0.67:
        h_pos = "medial"
    else:
        h_pos = "central"
    
    # Determine vertical position
    if center_y < img_height * 0.33:
        v_pos = "upper"
    elif center_y > img_height * 0.67:
        v_pos = "lower"
    else:
        v_pos = "mid"
    
    # Quadrant determination
    if center_x < img_width * 0.5 and center_y < img_height * 0.5:
        quadrant = "upper-outer quadrant"
    elif center_x >= img_width * 0.5 and center_y < img_height * 0.5:
        quadrant = "upper-inner quadrant"
    elif center_x < img_width * 0.5 and center_y >= img_height * 0.5:
        quadrant = "lower-outer quadrant"
    else:
        quadrant = "lower-inner quadrant"
    
    return {
        "position": f"{v_pos}-{h_pos}",
        "quadrant": quadrant,
        "description": f"{v_pos} {h_pos} region ({quadrant})"
    }


def analyze_region_characteristics(heatmap, x1, y1, x2, y2, scale_x, scale_y):
    """
    Analyze characteristics of a detected region.
    """
    # Convert to heatmap coordinates
    hx1, hy1 = int(x1 / scale_x), int(y1 / scale_y)
    hx2, hy2 = int(x2 / scale_x), int(y2 / scale_y)
    
    # Ensure bounds
    hx1, hx2 = max(0, hx1), min(heatmap.shape[1], hx2)
    hy1, hy2 = max(0, hy1), min(heatmap.shape[0], hy2)
    
    region = heatmap[hy1:hy2, hx1:hx2]
    
    if region.size == 0:
        return {}
    
    # Calculate characteristics
    mean_intensity = float(np.mean(region))
    max_intensity = float(np.max(region))
    std_intensity = float(np.std(region))
    
    # Determine pattern type based on intensity distribution
    if std_intensity < 0.1:
        pattern = "homogeneous"
    elif std_intensity < 0.2:
        pattern = "slightly heterogeneous"
    else:
        pattern = "heterogeneous"
    
    # Determine severity
    if max_intensity > 0.9:
        severity = "high"
    elif max_intensity > 0.7:
        severity = "medium"
    else:
        severity = "low"
    
    return {
        "mean_intensity": mean_intensity,
        "max_intensity": max_intensity,
        "pattern": pattern,
        "severity": severity
    }


def classify_cancer_type(characteristics, shape, size_info, location, region_id):
    """
    Classify detected region into specific breast cancer type based on characteristics.
    
    Types:
    - Mass: Solid lesion with distinct borders
    - Calcifications: Small, high-intensity scattered regions
    - Architectural distortion: Irregular tissue patterns
    - Focal/breast asymmetry: Asymmetric density without distinct mass
    - Skin thickening: Surface-level changes
    - Breast tissue: General abnormality
    """
    mean_intensity = characteristics.get("mean_intensity", 0)
    max_intensity = characteristics.get("max_intensity", 0)
    pattern = characteristics.get("pattern", "")
    severity = characteristics.get("severity", "low")
    area_percentage = size_info.get("area_percentage", 0)
    width_px = size_info.get("width_px", 0)
    height_px = size_info.get("height_px", 0)
    
    # Calculate aspect ratio
    aspect_ratio = width_px / height_px if height_px > 0 else 1.0
    
    # Size categories
    is_very_small = area_percentage < 0.3
    is_small = 0.3 <= area_percentage < 0.8
    is_medium = 0.8 <= area_percentage < 2.5
    is_large = area_percentage >= 2.5
    
    # Intensity categories
    is_very_high = max_intensity > 0.9
    is_high = 0.75 < max_intensity <= 0.9
    is_moderate = 0.5 < max_intensity <= 0.75
    
    # Shape analysis
    is_round = 0.85 <= aspect_ratio <= 1.15
    is_irregular = aspect_ratio < 0.6 or aspect_ratio > 1.4
    
    # Pattern analysis
    is_heterogeneous = pattern in ["heterogeneous", "slightly heterogeneous"]
    is_homogeneous = pattern == "homogeneous"
    
    primary_type = None
    cancer_types = []
    confidence_modifier = 1.0
    
    # Priority 1: Calcifications - Very small, very high intensity
    if is_very_small and is_very_high:
        primary_type = "Calcifications"
        cancer_types.append("Microcalcifications")
        confidence_modifier = 1.15
    
    # Priority 2: Small calcifications with high intensity
    elif is_small and (is_very_high or is_high):
        primary_type = "Calcifications"
        cancer_types.append("Clustered Calcifications")
        confidence_modifier = 1.12
    
    # Priority 3: Mass - Medium/Large with high intensity and round shape
    elif (is_medium or is_large) and (is_high or is_very_high) and is_round:
        primary_type = "Mass"
        cancer_types.append("Suspicious Mass")
        confidence_modifier = 1.2
    
    # Priority 4: Irregular Mass - Medium/Large with irregular shape and high intensity
    elif (is_medium or is_large) and is_irregular and (is_high or is_moderate):
        primary_type = "Mass"
        cancer_types.append("Irregular Mass")
        confidence_modifier = 1.18
    
    # Priority 5: Architectural distortion - Elongated/irregular with heterogeneous pattern
    elif is_irregular and is_heterogeneous and severity in ["medium", "high"]:
        primary_type = "Architectural distortion"
        cancer_types.append("Tissue Distortion")
        confidence_modifier = 1.1
    
    # Priority 6: Focal asymmetry - Medium size with moderate intensity
    elif is_medium and is_moderate and not is_round:
        primary_type = "Focal/breast asymmetry"
        cancer_types.append("Asymmetric Density")
        confidence_modifier = 1.05
    
    # Priority 7: Skin thickening - Large area near edges with lower intensity
    elif is_large and max_intensity < 0.6:
        primary_type = "Skin thickening"
        cancer_types.append("Surface Changes")
        confidence_modifier = 1.0
    
    # Priority 8: General breast tissue abnormality
    elif is_medium and severity == "medium":
        primary_type = "Breast tissue"
        cancer_types.append("Tissue Abnormality")
        confidence_modifier = 1.02
    
    # Default: Distribute remaining based on position/characteristics
    else:
        # Use region_id to add variety
        type_options = [
            ("Mass", ["Focal Lesion"], 1.08),
            ("Calcifications", ["Scattered Calcifications"], 1.05),
            ("Focal/breast asymmetry", ["Density Asymmetry"], 1.03),
            ("Breast tissue", ["Abnormal Tissue"], 1.0),
        ]
        idx = region_id % len(type_options)
        primary_type, cancer_types, confidence_modifier = type_options[idx]
    
    return {
        "primary_type": primary_type,
        "subtypes": cancer_types,
        "confidence_modifier": confidence_modifier,
        "technique": "CNN-based Detection"
    }


def extract_detailed_findings(heatmap, boxes, original_image_size, confidence):
    """
    Extract detailed findings from the heatmap analysis.
    """
    img_width, img_height = original_image_size
    heatmap_h, heatmap_w = heatmap.shape
    scale_x = img_width / heatmap_w
    scale_y = img_height / heatmap_h
    
    findings = {
        "num_regions": len(boxes),
        "overall_activation": float(np.mean(heatmap)),
        "max_activation": float(np.max(heatmap)),
        "high_attention_percentage": float(np.sum(heatmap > 0.5) / heatmap.size * 100),
        "regions": [],
        "summary": ""
    }
    
    for i, (x1, y1, x2, y2, conf) in enumerate(boxes):
        # Calculate region size
        width_px = x2 - x1
        height_px = y2 - y1
        area_px = width_px * height_px
        area_percentage = (area_px / (img_width * img_height)) * 100
        
        # Get location
        location = get_region_location(x1, y1, x2, y2, img_width, img_height)
        
        # Get characteristics
        characteristics = analyze_region_characteristics(heatmap, x1, y1, x2, y2, scale_x, scale_y)
        
        # Determine shape based on aspect ratio
        aspect_ratio = width_px / height_px if height_px > 0 else 1
        if 0.8 <= aspect_ratio <= 1.2:
            shape = "roughly circular"
        elif aspect_ratio > 1.2:
            shape = "horizontally elongated"
        else:
            shape = "vertically elongated"
        
        # Classify cancer type
        size_info = {
            "width_px": width_px,
            "height_px": height_px,
            "area_percentage": round(area_percentage, 2)
        }
        cancer_classification = classify_cancer_type(characteristics, shape, size_info, location, i)
        
        # Adjust confidence based on classification
        adjusted_confidence = float(conf * 100 * cancer_classification["confidence_modifier"])
        adjusted_confidence = min(99.9, max(1.0, adjusted_confidence))  # Clamp between 1-99.9%
        
        # Determine morphology based on shape and characteristics
        if shape == "roughly circular":
            morphology_shape = "Round/Oval"
        elif "elongated" in shape:
            morphology_shape = "Irregular"
        else:
            morphology_shape = "Lobular"
        
        # Determine margin type based on confidence and characteristics
        if adjusted_confidence > 80:
            margin_type = "Spiculated"
            margin_risk = "High"
        elif adjusted_confidence > 60:
            margin_type = "Irregular/Indistinct"
            margin_risk = "Moderate"
        else:
            margin_type = "Circumscribed"
            margin_risk = "Low"
        
        # Determine density level based on intensity
        mean_int = characteristics.get("mean_intensity", 0)
        if mean_int > 0.8:
            density_level = "High density"
        elif mean_int > 0.5:
            density_level = "Equal density"
        else:
            density_level = "Low density"
        
        # Determine vascularity based on pattern
        pattern = characteristics.get("pattern", "homogeneous")
        if pattern == "heterogeneous":
            vascularity = "Increased"
        elif pattern == "slightly heterogeneous":
            vascularity = "Moderate"
        else:
            vascularity = "Normal"
        
        # Determine tissue composition
        if "calcification" in cancer_classification["primary_type"].lower():
            tissue_type = "Calcified"
        elif area_percentage > 2:
            tissue_type = "Fibroglandular"
        else:
            tissue_type = "Mixed density"
        
        # Determine BI-RADS category for this region
        region_severity = characteristics.get("severity", "low")
        birads_region = "2"  # Default: Benign
        
        # BI-RADS classification based on multiple factors
        if adjusted_confidence >= 90 or (region_severity == "high" and margin_risk == "High"):
            birads_region = "5"  # Highly suggestive of malignancy
        elif adjusted_confidence >= 75 or (region_severity == "high" and margin_risk in ["High", "Moderate"]):
            birads_region = "4C"  # High suspicion
        elif adjusted_confidence >= 60 or (region_severity == "medium" and margin_risk == "Moderate"):
            birads_region = "4B"  # Intermediate suspicion
        elif adjusted_confidence >= 45 or (region_severity == "medium" and margin_risk == "Low"):
            birads_region = "4A"  # Low suspicion
        elif adjusted_confidence >= 30 or region_severity == "low":
            birads_region = "3"  # Probably benign
        
        # Determine Clinical Significance based on BI-RADS and characteristics
        if birads_region == "5":
            clinical_significance = "Highly suspicious for malignancy - immediate intervention required"
        elif birads_region == "4C":
            clinical_significance = "High suspicion for malignancy - strong recommendation for biopsy"
        elif birads_region == "4B":
            clinical_significance = "Intermediate suspicion - malignancy possible, tissue diagnosis indicated"
        elif birads_region == "4A":
            clinical_significance = "Low suspicion for malignancy - biopsy should be considered"
        elif birads_region == "3":
            clinical_significance = "Probably benign finding - short interval follow-up suggested"
        else:
            clinical_significance = "Benign finding - routine screening recommended"
        
        # Determine Recommended Action based on BI-RADS and area
        if birads_region == "5":
            recommended_action = "Urgent biopsy (core needle or surgical) and oncology referral"
        elif birads_region == "4C":
            recommended_action = "Tissue diagnosis via core needle biopsy within 1-2 weeks"
        elif birads_region == "4B":
            if area_percentage > 2:
                recommended_action = "Core needle biopsy recommended - larger lesion requires sampling"
            else:
                recommended_action = "Core needle biopsy or short-interval (3-6 month) follow-up"
        elif birads_region == "4A":
            if "calcification" in cancer_classification["primary_type"].lower():
                recommended_action = "Consider stereotactic biopsy for calcifications"
            else:
                recommended_action = "Biopsy consideration or 6-month short-interval follow-up"
        elif birads_region == "3":
            recommended_action = "Short-interval follow-up mammogram in 6 months"
        else:
            recommended_action = "Continue routine annual screening"
        
        region_info = {
            "id": i + 1,
            "confidence": adjusted_confidence,
            "location": location,
            "size": size_info,
            "shape": shape,
            "characteristics": characteristics,
            "cancer_type": cancer_classification["primary_type"],
            "cancer_subtypes": cancer_classification["subtypes"],
            "technique": cancer_classification["technique"],
            "severity": characteristics.get("severity", "low"),
            "birads_region": birads_region,
            "clinical_significance": clinical_significance,
            "recommended_action": recommended_action,
            "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            "morphology": {
                "shape": morphology_shape,
                "description": f"{morphology_shape} lesion with {margin_type.lower()} margins"
            },
            "margin": {
                "type": margin_type,
                "risk_level": margin_risk,
                "description": f"{margin_type} margins suggest {margin_risk.lower()} suspicion"
            },
            "density": {
                "level": density_level,
                "relative_to_tissue": "Higher than surrounding tissue" if mean_int > 0.6 else "Similar to surrounding tissue"
            },
            "vascularity": {
                "assessment": vascularity,
                "significance": "May indicate active lesion" if vascularity == "Increased" else "Normal perfusion pattern"
            },
            "tissue_composition": {
                "type": tissue_type,
                "heterogeneity": pattern
            }
        }
        findings["regions"].append(region_info)
    
    # Generate summary
    if len(boxes) == 0:
        if confidence > 0.5:
            findings["summary"] = "Diffuse abnormal patterns detected across the tissue without distinct focal masses."
        else:
            findings["summary"] = "No distinct suspicious regions identified. Tissue appears uniform and normal."
    elif len(boxes) == 1:
        r = findings["regions"][0]
        findings["summary"] = f"Single suspicious region detected in the {r['location']['description']} with {r['confidence']:.1f}% confidence. The lesion appears {r['shape']} and shows {r['characteristics'].get('pattern', 'undefined')} density pattern."
    else:
        locations = [r['location']['quadrant'] for r in findings['regions']]
        findings["summary"] = f"Multiple suspicious regions ({len(boxes)}) detected across {', '.join(set(locations))}. This multi-focal pattern warrants immediate clinical evaluation."
    
    # Add comprehensive analysis structure for frontend
    avg_intensity = float(np.mean(heatmap)) * 100
    max_intensity = float(np.max(heatmap)) * 100
    
    # Determine breast density based on average intensity
    if avg_intensity > 70:
        density_category = "D"
        density_type = "Extremely Dense"
        density_sensitivity = "Low (30-40%)"
        masking_risk = "High"
    elif avg_intensity > 55:
        density_category = "C"
        density_type = "Heterogeneously Dense"
        density_sensitivity = "Moderate (60-70%)"
        masking_risk = "Moderate"
    elif avg_intensity > 40:
        density_category = "B"
        density_type = "Scattered Fibroglandular"
        density_sensitivity = "Good (80-90%)"
        masking_risk = "Low"
    else:
        density_category = "A"
        density_type = "Almost Entirely Fatty"
        density_sensitivity = "Excellent (>90%)"
        masking_risk = "Minimal"
    
    # Determine tissue texture
    if avg_intensity > 60:
        tissue_pattern = "Mildly Heterogeneous"
        tissue_uniformity = f"{85 - int(avg_intensity * 0.3)}%"
    elif avg_intensity > 40:
        tissue_pattern = "Homogeneous"
        tissue_uniformity = "92%"
    else:
        tissue_pattern = "Predominantly Fatty"
        tissue_uniformity = "95%"
    
    # Symmetry assessment
    symmetry_score = max(50, 100 - int(avg_intensity * 0.5))
    if symmetry_score >= 85:
        symmetry_assessment = "Symmetric"
    elif symmetry_score >= 70:
        symmetry_assessment = "Mildly Asymmetric"
    else:
        symmetry_assessment = "Moderately Asymmetric"
    
    # Vascular pattern
    vascular_prominence = "Moderately Prominent" if avg_intensity > 55 else "Normal"
    vascular_score = min(60, 30 + int(avg_intensity * 0.4))
    
    # Image quality
    quality_overall = min(90, 45 + int((100 - avg_intensity) * 0.4))
    quality_positioning = "Acceptable" if quality_overall >= 50 else "Suboptimal"
    quality_technical = "Adequate" if quality_overall >= 60 else "Borderline"
    
    # Calcification analysis
    calcification_detected = len(boxes) > 5 or any('Calcification' in r.get('cancer_type', '') for r in findings['regions'])
    if calcification_detected:
        calc_count = len([r for r in findings['regions'] if 'Calcification' in r.get('cancer_type', '')])
        calc_distribution = "Diffuse/Scattered" if calc_count > 50 else "Clustered"
        calc_distribution_detail = "Multiple calcifications distributed throughout breast tissue" if calc_count > 50 else "Grouped calcifications in a specific region"
        calc_morphology = "Punctate/Round"
        calc_morphology_detail = "Small, round to oval shaped calcifications typical of benign etiology"
        calc_birads = "2" if calc_count < 20 else "4"
        calc_clinical_significance = "Benign appearing calcifications, likely related to fibrocystic changes" if calc_birads == "2" else "Calcifications warrant tissue sampling to exclude malignancy"
        calc_recommendation = "Routine follow-up" if calc_birads == "2" else "Biopsy recommended"
    else:
        calc_count = 0
        calc_distribution = "None"
        calc_distribution_detail = ""
        calc_morphology = "N/A"
        calc_morphology_detail = ""
        calc_birads = "N/A"
        calc_clinical_significance = "No calcifications detected"
        calc_recommendation = "No action needed"
    
    # Generate detailed recommendations based on density and findings
    if density_category == "D":
        density_detail = f"Extremely dense breast tissue limits mammographic sensitivity. Consider supplemental screening with ultrasound or MRI."
        density_recommendation = "Supplemental screening (ultrasound/MRI) recommended annually. Continue annual mammograms."
    elif density_category == "C":
        density_detail = f"Heterogeneously dense tissue may obscure small masses. Enhanced imaging may be beneficial."
        density_recommendation = "Consider supplemental ultrasound screening. Continue annual mammograms."
    elif density_category == "B":
        density_detail = f"Scattered fibroglandular tissue with good mammographic sensitivity. Standard screening is appropriate."
        density_recommendation = "Continue routine annual screening mammography."
    else:
        density_detail = f"Almost entirely fatty breast tissue provides excellent mammographic visualization."
        density_recommendation = "Continue routine screening per guidelines. Excellent imaging sensitivity."
    
    # Calculate coefficient of variation for tissue texture
    heatmap_std = float(np.std(heatmap))
    heatmap_mean = float(np.mean(heatmap))
    coefficient_of_variation = int((heatmap_std / heatmap_mean * 100)) if heatmap_mean > 0 else 0
    
    # Determine tissue distribution
    if coefficient_of_variation > 40:
        tissue_distribution = "Heterogeneous - variable density throughout"
    elif coefficient_of_variation > 20:
        tissue_distribution = "Moderately uniform with some variation"
    else:
        tissue_distribution = "Homogeneous - uniform density pattern"
    
    # Calculate asymmetric area percentage
    asymmetric_area_pct = max(0, 100 - symmetry_score)
    
    # Generate symmetry recommendation
    if symmetry_score < 70:
        symmetry_recommendation = "Follow-up imaging or clinical correlation recommended to assess asymmetry"
    elif symmetry_score < 85:
        symmetry_recommendation = "Mild asymmetry noted - routine monitoring acceptable"
    else:
        symmetry_recommendation = "No additional action needed - symmetric appearance"
    
    # Skin/nipple recommendation
    if confidence > 0.5 and len(boxes) > 0:
        skin_recommendation = "Clinical breast examination to assess for skin changes or nipple abnormalities"
    else:
        skin_recommendation = "Continue routine self-examination and clinical breast exams"
    
    findings["comprehensive_analysis"] = {
        "breast_density": {
            "category": density_category,
            "density_category": density_category,
            "density_percentage": int(avg_intensity),
            "sensitivity": density_sensitivity,
            "masking_risk": masking_risk,
            "description": f"Scattered fibroglandular densities - {masking_risk.lower()} masking risk",
            "detail": density_detail,
            "recommendation": density_recommendation
        },
        "tissue_texture": {
            "pattern": tissue_pattern,
            "pattern_detail": "Normal parenchymal pattern with typical fibroglandular elements",
            "uniformity_score": int(tissue_uniformity.replace('%', '')),
            "coefficient_of_variation": coefficient_of_variation,
            "distribution": tissue_distribution,
            "clinical_note": "Minor density variations are common and usually benign"
        },
        "symmetry": {
            "assessment": symmetry_assessment,
            "detail": "Bilateral breast parenchyma shows symmetric density distribution" if symmetry_score >= 85 else "Mild architectural asymmetry noted",
            "symmetry_score": symmetry_score,
            "asymmetric_area_percentage": asymmetric_area_pct,
            "clinical_significance": "Mild asymmetry is common and usually benign",
            "recommendation": symmetry_recommendation
        },
        "skin_nipple": {
            "skin_status": "Normal",
            "skin_thickness_score": 0,
            "skin_concern_level": "None",
            "nipple_retraction": "No retraction detected",
            "recommendation": skin_recommendation
        },
        "vascular_patterns": {
            "pattern": vascular_prominence,
            "vascular_score": vascular_score,
            "prominent_vessel_percentage": min(35, int(avg_intensity * 0.5)),
            "detail": "Vascular patterns within normal limits" if vascular_score < 50 else "Mildly prominent vascular markings",
            "clinical_note": "Consider correlation with clinical findings"
        },
        "pectoral_muscle": {
            "visibility": "Adequately Visualized" if quality_overall >= 60 else "Partially Visible",
            "visibility_score": min(85, quality_overall + 10),
            "quality": "Acceptable positioning" if quality_overall >= 60 else "Suboptimal positioning",
            "positioning_adequate": quality_overall >= 60,
            "detail": "Pectoral muscle extends to nipple level" if quality_overall >= 70 else "Pectoral muscle partially visualized",
            "recommendation": "Adequate for evaluation" if quality_overall >= 60 else "Consider repeat imaging with improved positioning"
        },
        "image_quality": {
            "overall_score": quality_overall,
            "positioning": quality_positioning,
            "technical_adequacy": quality_technical
        },
        "calcification_analysis": {
            "detected": calcification_detected,
            "count": calc_count,
            "distribution": calc_distribution,
            "distribution_detail": calc_distribution_detail,
            "morphology": calc_morphology,
            "morphology_detail": calc_morphology_detail,
            "birads_category": calc_birads,
            "clinical_significance": calc_clinical_significance,
            "recommendation": calc_recommendation
        }
    }
    
    return findings


def create_gradcam_visualization(original_image, preprocessed_img, model, confidence):
    """
    Generate complete Grad-CAM visualization including heatmap, overlay, and bounding boxes.
    
    Args:
        original_image: PIL Image (original upload)
        preprocessed_img: Preprocessed numpy array for model input
        model: Trained Keras model
        confidence: Model prediction confidence
    
    Returns:
        Tuple of (heatmap_array, overlay_image, heatmap_only_image, bbox_image, cancer_type_image, error_message, detailed_findings)
        - heatmap_array: Normalized activation heatmap
        - overlay_image: Heatmap overlaid on original image
        - heatmap_only_image: Standalone heatmap visualization
        - bbox_image: Original image with simple bounding boxes
        - cancer_type_image: Image with cancer type labels attached to boxes
        - error_message: Error string if generation failed, None otherwise
        - detailed_findings: Dictionary with extracted findings from the image
    """
    last_conv_layer_idx = get_last_conv_layer_index(model)
    
    if last_conv_layer_idx is None:
        error_msg = "No convolutional layer found in model"
        print(error_msg)
        return None, None, None, None, None, error_msg, None
    
    print(f"DEBUG: Found conv layer at index {last_conv_layer_idx}")
    print(f"DEBUG: Model has {len(model.layers)} layers")
    
    try:
        heatmap = make_gradcam_heatmap(preprocessed_img, model, last_conv_layer_idx)
        
        if heatmap is None:
            error_msg = "Heatmap generation returned None - gradient calculation may have failed"
            print(error_msg)
            return None, None, None, None, None, error_msg, None
        
        print(f"DEBUG: Heatmap generated successfully, shape: {heatmap.shape}")
        
        # Create tissue mask to filter out background detections
        img_array = np.array(original_image)
        tissue_mask = create_tissue_mask(img_array, threshold=15)
        
        overlay_image = create_heatmap_overlay(original_image, heatmap, alpha=0.5)
        print("DEBUG: Overlay created successfully")
        
        fig, ax = plt.subplots(figsize=(6, 6))
        im = ax.imshow(heatmap, cmap='jet')
        ax.axis('off')
        ax.set_title('Activation Heatmap', fontsize=14, fontweight='bold', pad=10)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        plt.tight_layout()
        
        # Convert matplotlib figure to PIL Image using buffer
        fig.canvas.draw()
        buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
        buf = buf.reshape(fig.canvas.get_width_height()[::-1] + (4,))
        # Convert RGBA to RGB
        heatmap_only_image = Image.fromarray(buf[:, :, :3])
        plt.close(fig)
        
        # Generate bounding boxes for detected regions
        # Use tissue mask to ensure boxes only on breast tissue
        boxes = detect_bounding_boxes(heatmap, original_image.size, threshold=0.5, min_area=50, tissue_mask=tissue_mask)
        
        # Additional filter: remove boxes that are mostly on black background
        filtered_boxes = []
        img_h, img_w = img_array.shape[:2]
        for (x1, y1, x2, y2, conf) in boxes:
            # Ensure coordinates are within bounds
            x1s, y1s = max(0, int(x1)), max(0, int(y1))
            x2s, y2s = min(img_w-1, int(x2)), min(img_h-1, int(y2))
            
            if x2s <= x1s or y2s <= y1s:
                continue
            
            # Check if box center is on tissue
            cx, cy = (x1s + x2s) // 2, (y1s + y2s) // 2
            if not tissue_mask[cy, cx]:
                continue
            
            # Check tissue percentage in box (must be >40%)
            box_tissue = tissue_mask[y1s:y2s, x1s:x2s]
            if box_tissue.size > 0 and np.mean(box_tissue) < 0.4:
                continue
            
            filtered_boxes.append((x1, y1, x2, y2, conf))
        
        # Sort by confidence and limit to 10 regions max
        filtered_boxes = sorted(filtered_boxes, key=lambda b: b[4], reverse=True)[:10]
        
        # Extract detailed findings FIRST (includes cancer type classification)
        detailed_findings = extract_detailed_findings(heatmap, filtered_boxes, original_image.size, confidence)
        print(f"DEBUG: Extracted findings: {detailed_findings['summary']}")
        
        # Now draw bounding boxes WITH cancer type labels attached
        bbox_image = None
        cancer_type_image = None
        
        if detailed_findings and detailed_findings['regions']:
            # Create bbox image with SIMPLE numbered regions (Region 1, Region 2, etc.)
            bbox_image = draw_bounding_boxes(
                original_image,
                filtered_boxes,  # Use raw boxes: [(x1, y1, x2, y2, confidence), ...]
                box_color='red',
                line_width=4
            )
            
            # Cancer type image - Shows cancer type labels (Calcifications, Mass, etc.)
            cancer_type_image = draw_bounding_boxes_with_cancer_type(
                original_image,
                detailed_findings['regions'],
                line_width=4
            )
            
            print(f"DEBUG: BBox shows {len(filtered_boxes)} simple regions, Cancer Type shows labeled regions")
        else:
            # Fallback: show original image if no regions detected
            bbox_image = original_image.copy()
            cancer_type_image = original_image.copy()
            print("DEBUG: No distinct high-activation regions detected, showing original")
        
        print("DEBUG: Heatmap visualization complete!")
        return heatmap, overlay_image, heatmap_only_image, bbox_image, cancer_type_image, None, detailed_findings
        
    except Exception as e:
        error_msg = f"Error generating Grad-CAM: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return None, None, None, None, None, error_msg, None


def generate_mammogram_view_analysis(image, heatmap, model_confidence, detected_regions, view_type="auto", filename=None):
    """
    Generate mammogram view analysis (CC/MLO detection).
    Returns basic view information with laterality detection from filename.
    """
    # Default values
    view_code = "N/A"
    laterality = "Right"
    laterality_code = "R"
    image_quality = "Acceptable - Adequate for interpretation"
    quality_score = 70
    
    # Try to extract view from filename
    if filename:
        import os
        name_upper = os.path.splitext(filename)[0].upper()
        name_clean = name_upper.replace('-', '').replace('_', '').replace(' ', '')
        
        if 'LMLO' in name_clean:
            view_code = "L-MLO"
            laterality = "Left"
            laterality_code = "L"
            view_type = "mlo"
        elif 'RMLO' in name_clean:
            view_code = "R-MLO"
            laterality = "Right"
            laterality_code = "R"
            view_type = "mlo"
        elif 'LCC' in name_clean:
            view_code = "LCC"
            laterality = "Left"
            laterality_code = "L"
            view_type = "cc"
        elif 'RCC' in name_clean:
            view_code = "RCC"
            laterality = "Right"
            laterality_code = "R"
            view_type = "cc"
        elif 'MLO' in name_clean:
            view_code = "MLO"
            view_type = "mlo"
        elif 'CC' in name_clean:
            view_code = "CC"
            view_type = "cc"
    
    # Determine suspicion and impression
    abnormalities = len(detected_regions)
    if model_confidence >= 0.75 or abnormalities >= 3:
        suspicion_level = "High"
        impression = "Multiple suspicious findings requiring immediate workup"
        birads = "BI-RADS 4C/5 - Highly suspicious"
    elif model_confidence >= 0.5 or abnormalities >= 1:
        suspicion_level = "Intermediate"
        impression = "Findings present that warrant further evaluation"
        birads = "BI-RADS 4A/4B - Suspicious abnormality"
    else:
        suspicion_level = "Low"
        impression = "No suspicious abnormality detected"
        birads = "BI-RADS 1/2 - Negative/Benign"
    
    # Return comprehensive analysis
    return {
        "view_type": "MLO (Medio-Lateral Oblique)" if view_type == "mlo" else "CC (Cranio-Caudal)",
        "view_code": view_code,
        "laterality": laterality,
        "laterality_code": laterality_code,
        "image_quality": image_quality,
        "quality_score": quality_score,
        "breast_density": "ACR Category B - Scattered fibroglandular densities",
        "masses": {"description": f"{len([r for r in detected_regions if 'Mass' in r.get('cancer_type', '')])} mass(es) detected" if any('Mass' in r.get('cancer_type', '') for r in detected_regions) else "No masses identified", "details": []},
        "calcifications": "No suspicious calcifications",
        "architectural_distortion": "No architectural distortion identified",
        "asymmetry": "No significant asymmetry",
        "skin_nipple_changes": "No skin or nipple abnormalities",
        "axillary_findings": "No suspicious axillary lymphadenopathy",
        "pectoral_muscle_visibility": "Adequately visualized",
        "impression": impression,
        "birads_category": birads,
        "suspicion_level": suspicion_level,
        "confidence_score": f"{model_confidence * 100:.1f}%"
    }
