"""
YOLO Breast Cancer Detector Integration
Replaces Grad-CAM with trained YOLO model for accurate cancer type detection
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
from ultralytics import YOLO
import os

# Cancer type mapping
CANCER_TYPES = {
    0: "Mass",
    1: "Calcifications",
    2: "Architectural distortion",
    3: "Focal/breast asymmetry",
    4: "Skin thickening"
}

# Severity colors
SEVERITY_COLORS = {
    "high": "#DC2626",
    "medium": "#F59E0B",
    "low": "#10B981"
}

class YOLOCancerDetector:
    """
    YOLO-based breast cancer detector
    """
    
    def __init__(self, model_path="models/breast_cancer_yolo.pt", confidence_threshold=0.25):
        """
        Initialize YOLO detector
        
        Args:
            model_path: Path to trained YOLO model
            confidence_threshold: Minimum confidence for detection
        """
        self.confidence_threshold = confidence_threshold
        
        # Check if model exists
        if not os.path.exists(model_path):
            print(f"⚠️  YOLO model not found at {model_path}")
            print("   Using pretrained model. Train custom model with: python train_yolo.py")
            model_path = "yolov8n.pt"  # Fallback to pretrained
        
        # Load model
        self.model = YOLO(model_path)
        print(f"✓ YOLO model loaded: {model_path}")
    
    
    def detect(self, image, conf_threshold=None):
        """
        Detect cancer regions in mammogram image
        
        Args:
            image: PIL Image or numpy array
            conf_threshold: Override confidence threshold
            
        Returns:
            List of detections with bbox, class, confidence
        """
        if conf_threshold is None:
            conf_threshold = self.confidence_threshold
        
        # Convert PIL to numpy if needed
        if isinstance(image, Image.Image):
            img_array = np.array(image)
        else:
            img_array = image
        
        # Run YOLO inference
        results = self.model.predict(
            img_array,
            conf=conf_threshold,
            iou=0.45,
            verbose=False
        )[0]
        
        detections = []
        
        # Process detections
        if results.boxes is not None and len(results.boxes) > 0:
            for i, box in enumerate(results.boxes):
                # Get box coordinates (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # Get class and confidence
                class_id = int(box.cls[0].cpu().numpy())
                confidence = float(box.conf[0].cpu().numpy())
                
                # Get cancer type
                cancer_type = CANCER_TYPES.get(class_id, "Unknown")
                
                # Calculate size
                width = x2 - x1
                height = y2 - y1
                area = width * height
                img_area = img_array.shape[0] * img_array.shape[1]
                area_percentage = (area / img_area) * 100
                
                # Determine severity based on confidence and size
                if confidence > 0.8 or area_percentage > 2.0:
                    severity = "high"
                elif confidence > 0.5 or area_percentage > 0.8:
                    severity = "medium"
                else:
                    severity = "low"
                
                # Get location
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                location = self._get_location(center_x, center_y, img_array.shape[1], img_array.shape[0])
                
                # Determine BI-RADS category for this detection
                conf_pct = confidence * 100
                birads_region = "2"  # Default: Benign
                
                if conf_pct >= 90 or (severity == "high" and area_percentage > 3.0):
                    birads_region = "5"  # Highly suggestive of malignancy
                elif conf_pct >= 75 or (severity == "high" and area_percentage > 1.5):
                    birads_region = "4C"  # High suspicion
                elif conf_pct >= 60 or severity == "medium":
                    birads_region = "4B"  # Intermediate suspicion
                elif conf_pct >= 45:
                    birads_region = "4A"  # Low suspicion
                elif conf_pct >= 30 or severity == "low":
                    birads_region = "3"  # Probably benign
                
                # Determine Clinical Significance based on BI-RADS
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
                
                # Determine Recommended Action based on BI-RADS and characteristics
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
                    if "calcification" in cancer_type.lower():
                        recommended_action = "Consider stereotactic biopsy for calcifications"
                    else:
                        recommended_action = "Biopsy consideration or 6-month short-interval follow-up"
                elif birads_region == "3":
                    recommended_action = "Short-interval follow-up mammogram in 6 months"
                else:
                    recommended_action = "Continue routine annual screening"
                
                detection = {
                    "id": i + 1,
                    "cancer_type": cancer_type,
                    "class_id": class_id,
                    "confidence": confidence * 100,
                    "bbox": {
                        "x1": int(x1),
                        "y1": int(y1),
                        "x2": int(x2),
                        "y2": int(y2)
                    },
                    "size": {
                        "width_px": int(width),
                        "height_px": int(height),
                        "area_percentage": round(area_percentage, 2)
                    },
                    "severity": severity,
                    "birads_region": birads_region,
                    "clinical_significance": clinical_significance,
                    "recommended_action": recommended_action,
                    "location": location,
                    "technique": "YOLOv8"
                }
                
                detections.append(detection)
        
        # Sort by confidence
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        
        return detections
    
    
    def _get_location(self, center_x, center_y, img_width, img_height):
        """
        Determine anatomical location of detection
        """
        # Horizontal position
        if center_x < img_width * 0.33:
            h_pos = "lateral"
        elif center_x > img_width * 0.67:
            h_pos = "medial"
        else:
            h_pos = "central"
        
        # Vertical position
        if center_y < img_height * 0.33:
            v_pos = "upper"
        elif center_y > img_height * 0.67:
            v_pos = "lower"
        else:
            v_pos = "mid"
        
        # Quadrant
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
    
    
    def visualize_detections(self, image, detections, draw_labels=True):
        """
        Draw bounding boxes and labels on image
        
        Args:
            image: PIL Image
            detections: List of detection dicts
            draw_labels: Whether to draw labels
            
        Returns:
            PIL Image with visualizations
        """
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        for detection in detections:
            bbox = detection['bbox']
            x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
            
            # Get color based on severity
            severity = detection['severity']
            color = SEVERITY_COLORS.get(severity, "#6B7280")
            
            # Draw bounding box
            draw.rectangle([x1, y1, x2, y2], outline=color, width=4)
            
            if draw_labels:
                # Create label
                cancer_type = detection['cancer_type']
                confidence = detection['confidence']
                label = f"#{detection['id']}: {cancer_type} ({confidence:.0f}%)"
                
                # Draw label background
                bbox_text = draw.textbbox((x1, y1 - 25), label, font=font)
                draw.rectangle([bbox_text[0]-2, bbox_text[1]-2, bbox_text[2]+2, bbox_text[3]+2], fill=color)
                
                # Draw label text
                draw.text((x1, y1 - 25), label, fill="white", font=font)
        
        return img_copy
    
    
    def create_heatmap_overlay(self, image, detections):
        """
        Create heatmap-style overlay for compatibility with existing frontend
        """
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Create empty heatmap
        heatmap = np.zeros((height, width), dtype=np.float32)
        
        # Fill regions with intensity based on confidence
        for detection in detections:
            bbox = detection['bbox']
            x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
            confidence = detection['confidence'] / 100.0
            
            # Fill bbox region
            heatmap[y1:y2, x1:x2] = np.maximum(
                heatmap[y1:y2, x1:x2],
                confidence
            )
        
        # Apply Gaussian blur for smooth heatmap
        heatmap = cv2.GaussianBlur(heatmap, (51, 51), 0)
        
        # Create colored heatmap
        heatmap_colored = cv2.applyColorMap(
            (heatmap * 255).astype(np.uint8),
            cv2.COLORMAP_JET
        )
        
        # Overlay on original
        overlay = cv2.addWeighted(
            img_array,
            0.6,
            heatmap_colored,
            0.4,
            0
        )
        
        return Image.fromarray(overlay), heatmap
    
    
    def generate_findings(self, detections, overall_confidence):
        """
        Generate structured findings similar to Grad-CAM output
        """
        findings = {
            "num_regions": len(detections),
            "regions": [],
            "summary": ""
        }
        
        # Process each detection
        for det in detections:
            region_info = {
                "id": det['id'],
                "cancer_type": det['cancer_type'],
                "confidence": det['confidence'],
                "location": det['location'],
                "size": det['size'],
                "severity": det['severity'],
                "bbox": det['bbox'],
                "technique": "YOLOv8",
                "shape": self._estimate_shape(det['size']),
                "characteristics": {
                    "pattern": "detected",
                    "severity": det['severity']
                },
                "cancer_subtypes": [det['cancer_type']]
            }
            findings["regions"].append(region_info)
        
        # Generate summary
        if len(detections) == 0:
            findings["summary"] = "No distinct suspicious regions detected by YOLO model."
        elif len(detections) == 1:
            det = detections[0]
            findings["summary"] = f"Single {det['cancer_type']} detected in {det['location']['quadrant']} with {det['confidence']:.1f}% confidence."
        else:
            types = [d['cancer_type'] for d in detections]
            findings["summary"] = f"Multiple regions detected: {', '.join(set(types))}. Total {len(detections)} suspicious areas identified."
        
        return findings
    
    
    def _estimate_shape(self, size_info):
        """Estimate shape from bbox dimensions"""
        width = size_info['width_px']
        height = size_info['height_px']
        aspect_ratio = width / height if height > 0 else 1
        
        if 0.8 <= aspect_ratio <= 1.2:
            return "roughly circular"
        elif aspect_ratio > 1.2:
            return "horizontally elongated"
        else:
            return "vertically elongated"


# Test function
if __name__ == "__main__":
    print("Testing YOLO Cancer Detector...")
    
    detector = YOLOCancerDetector()
    
    # Test with sample image
    test_image_path = "test_images/sample_mammogram.png"
    if os.path.exists(test_image_path):
        image = Image.open(test_image_path)
        detections = detector.detect(image)
        
        print(f"\n✓ Detected {len(detections)} regions:")
        for det in detections:
            print(f"   #{det['id']}: {det['cancer_type']} ({det['confidence']:.1f}%)")
        
        # Visualize
        vis_image = detector.visualize_detections(image, detections)
        vis_image.save("test_output.png")
        print("\n✓ Visualization saved: test_output.png")
    else:
        print(f"Test image not found: {test_image_path}")

