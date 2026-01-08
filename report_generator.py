# report_generator.py

from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image as RLImage,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
import io
from PIL import Image
import numpy as np


# =============================
#  PDF REPORT GENERATOR
# =============================
def generate_report_pdf(
    result,
    probability,
    risk_level,
    benign_prob,
    malignant_prob,
    stats,
    image_size,
    file_format,
    original_image,
    overlay_image,
    heatmap_only,
    bbox_image,
    cancer_type_image,
    confidence,
    patient_name="Patient Name",
    patient_age="N/A",
    patient_sex="Female",
    patient_hn="N/A",
    department="Radiology",
    request_doctor="Dr. [Name]",
    report_by="Dr. [Radiologist Name]",
    findings=None,
    view_analysis=None,
):
    """
    Professional Mammogram Report Generator with Clinical Format
    """

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    story = []
    styles = getSampleStyleSheet()

    # -------------------------
    # CUSTOM STYLES - CLINICAL
    # -------------------------
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceBefore=10,
        spaceAfter=8,
    )

    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Heading3'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=6,
    )

    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4,
    )

    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#C62828'),
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )

    # ----------------------------------------
    # Helper: Convert PIL → ReportLab Image
    # ----------------------------------------
    def pil_to_rl_image(img, max_w=5.5 * inch, max_h=4.0 * inch):
        if img is None:
            return None
        if isinstance(img, np.ndarray):
            img = Image.fromarray(img.astype('uint8'))

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        rl_img = RLImage(buf)

        # maintain aspect ratio
        w, h = img.size
        aspect = w / h

        if aspect > (max_w / max_h):  # width-dominant
            rl_img.drawWidth = max_w
            rl_img.drawHeight = max_w / aspect
        else:
            rl_img.drawHeight = max_h
            rl_img.drawWidth = max_h * aspect

        return rl_img

    # ============================
    #  HEADER - CLINICAL REPORT
    # ============================
    story.append(Paragraph("MAMMOGRAPHY REPORT", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("Mammogram and AI-Assisted Breast Analysis", subtitle_style))
    story.append(Spacer(1, 6))
    
    # Patient Information Table
    current_date = datetime.now().strftime('%B %d, %Y')
    current_time = datetime.now().strftime('%I:%M %p')
    
    patient_info_data = [
        [Paragraph('<b>Date:</b>', normal_style), current_date, Paragraph('<b>Time:</b>', normal_style), current_time],
        [Paragraph('<b>Name:</b>', normal_style), patient_name, Paragraph('<b>Age:</b>', normal_style), patient_age],
        [Paragraph('<b>Sex:</b>', normal_style), patient_sex, Paragraph('<b>HN:</b>', normal_style), patient_hn],
        [Paragraph('<b>Department:</b>', normal_style), department, '', ''],
        [Paragraph('<b>Request Doctor:</b>', normal_style), request_doctor, '', ''],
        [Paragraph('<b>Report By:</b>', normal_style), report_by, '', ''],
    ]
    
    patient_table = Table(patient_info_data, colWidths=[1.2*inch, 2.1*inch, 0.8*inch, 2.6*inch])
    patient_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(patient_table)
    story.append(Spacer(1, 12))

    # ============================
    # MAMMOGRAPHY SECTION
    # ============================
    story.append(Paragraph('<b>MAMMOGRAPHY (AI-ASSISTED)</b>', heading_style))
    story.append(Spacer(1, 6))
    
    # Determine breast tissue description based on image stats
    breast_tissue_desc = "Heterogeneously dense breast tissue, may lower the sensitivity of mammography"
    if stats['mean_intensity'] > 200:
        breast_tissue_desc = "Fatty breast tissue, optimal for mammographic evaluation"
    elif stats['mean_intensity'] > 150:
        breast_tissue_desc = "Scattered areas of fibroglandular density"
    
    # Determine BI-RADS category
    birads_category = "BI-RADS 1 (Negative)"
    if malignant_prob >= 90:
        birads_category = "BI-RADS 5: Highly suggestive of malignancy"
    elif malignant_prob >= 75:
        birads_category = "BI-RADS 4C: High suspicion for malignancy"
    elif malignant_prob >= 60:
        birads_category = "BI-RADS 4B: Intermediate suspicion for malignancy"
    elif malignant_prob >= 40:
        birads_category = "BI-RADS 4A: Low suspicion for malignancy"
    elif malignant_prob >= 25:
        birads_category = "BI-RADS 3: Probably benign"
    elif malignant_prob >= 10:
        birads_category = "BI-RADS 2: Benign finding"
    
    # Determine detected findings from regions
    detected_types = set()
    if findings and findings.get('regions'):
        for region in findings['regions']:
            cancer_type = region.get('cancer_type', '')
            if cancer_type:
                detected_types.add(cancer_type)
    
    def get_finding_status(finding_type):
        """Check if a finding type was detected in the regions"""
        for detected in detected_types:
            if finding_type.lower() in detected.lower() or detected.lower() in finding_type.lower():
                return 'Detected - requires further evaluation'
        return 'Not detectable'
    
    mammography_findings = [
        ['Clinical:', 'Screening / AI-Assisted Analysis'],
        ['Technique:', 'Digital Mammography with AI Enhancement'],
        ['Breast tissue:', breast_tissue_desc],
        ['Mass:', get_finding_status('Mass')],
        ['Calcifications:', get_finding_status('Calcifications')],
        ['Architectural distortion:', get_finding_status('Architectural distortion')],
        ['Focal/breast asymmetry:', get_finding_status('Focal/breast asymmetry')],
        ['Skin thickening:', get_finding_status('Skin thickening')],
        ['Others:', f'AI analysis applied - {len(detected_types)} type(s) detected' if detected_types else 'AI analysis applied'],
    ]
    
    findings_table = Table(mammography_findings, colWidths=[1.8*inch, 4.9*inch])
    findings_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(findings_table)
    story.append(Spacer(1, 12))
    
    # ============================
    # AI ANALYSIS SECTION
    # ============================
    story.append(Paragraph('<b>AI-ASSISTED ANALYSIS:</b>', heading_style))
    story.append(Spacer(1, 6))
    
    ai_analysis = [
        ['Classification:', result],
        ['Confidence Score:', f"{probability:.2f}%"],
        ['Benign Probability:', f"{benign_prob:.2f}%"],
        ['Malignant Probability:', f"{malignant_prob:.2f}%"],
        ['Risk Assessment:', risk_level],
    ]
    
    ai_table = Table(ai_analysis, colWidths=[1.8*inch, 4.9*inch])
    ai_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
    ]))
    
    story.append(ai_table)
    story.append(Spacer(1, 12))
    
    # ============================
    # DETAILED IMAGE ANALYSIS SECTION
    # ============================
    if findings:
        story.append(Paragraph('<b>DETAILED IMAGE ANALYSIS:</b>', heading_style))
        story.append(Spacer(1, 6))
        
        # AI Summary
        summary_text = findings.get('summary', 'Analysis summary not available.')
        story.append(Paragraph(f"<b>AI Summary:</b> {summary_text}", normal_style))
        story.append(Spacer(1, 10))
        
        # Detection Statistics Table
        story.append(Paragraph('<b>Detection Statistics</b>', subheading_style))
        story.append(Spacer(1, 4))
        
        num_regions = findings.get('num_regions', 0)
        high_attention = findings.get('high_attention_percentage', 0)
        max_activation = findings.get('max_activation', 0) * 100  # Convert to percentage
        overall_activity = findings.get('overall_activation', 0) * 100  # Convert to percentage
        
        stats_header = [
            [Paragraph('<b>Metric</b>', normal_style), 
             Paragraph('<b>Value</b>', normal_style), 
             Paragraph('<b>Description</b>', normal_style)]
        ]
        stats_data = [
            ['Regions Detected', str(num_regions), 'Number of suspicious areas identified'],
            ['High Attention Areas', f"{high_attention:.2f}%", 'Percentage of image with high AI activation'],
            ['Max Activation', f"{max_activation:.2f}%", 'Peak intensity level detected'],
            ['Overall Activity', f"{overall_activity:.2f}%", 'Average activation across the image'],
            ['Malignant Probability', f"{malignant_prob:.2f}%", 'Probability of cancerous tissue'],
            ['Benign Probability', f"{benign_prob:.2f}%", 'Probability of healthy tissue'],
        ]
        
        stats_table_data = stats_header + stats_data
        detection_stats_table = Table(stats_table_data, colWidths=[1.8*inch, 1.2*inch, 3.7*inch])
        detection_stats_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        
        story.append(detection_stats_table)
        story.append(Spacer(1, 12))
        
        # Detected Regions Detail Table
        regions = findings.get('regions', [])
        if regions and len(regions) > 0:
            story.append(Paragraph('<b>Detected Regions Detail</b>', subheading_style))
            story.append(Spacer(1, 4))
            
            regions_header = [[
                Paragraph('<b>Region</b>', normal_style),
                Paragraph('<b>Type</b>', normal_style),
                Paragraph('<b>Location</b>', normal_style),
                Paragraph('<b>Confidence</b>', normal_style),
                Paragraph('<b>BI-RADS</b>', normal_style),
                Paragraph('<b>Severity</b>', normal_style),
                Paragraph('<b>Area %</b>', normal_style),
            ]]
            
            regions_data = []
            for region in regions:
                region_id = region.get('id', '?')
                cancer_type = region.get('cancer_type', 'Unknown')
                location = region.get('location', {}).get('quadrant', 'Unknown')
                conf = region.get('confidence', 0)
                birads = region.get('birads_region', '—')
                severity = region.get('severity', 'low')
                area_pct = region.get('size', {}).get('area_percentage', 0)
                
                regions_data.append([
                    f"#{region_id}",
                    cancer_type,
                    location,
                    f"{conf:.1f}%",
                    birads,
                    severity,
                    f"{area_pct:.2f}%"
                ])
            
            regions_table_data = regions_header + regions_data
            regions_table = Table(regions_table_data, colWidths=[0.5*inch, 1.4*inch, 1.2*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.6*inch])
            regions_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (3, 0), (3, -1), 'CENTER'),
                ('ALIGN', (4, 0), (4, -1), 'CENTER'),
                ('ALIGN', (6, 0), (6, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(regions_table)
            story.append(Spacer(1, 12))
            
            # ============================
            # DETAILED LESION ANALYSIS (NEW)
            # ============================
            story.append(Paragraph('<b>Detailed Lesion Analysis</b>', subheading_style))
            story.append(Spacer(1, 6))
            
            for region in regions:
                region_id = region.get('id', '?')
                cancer_type = region.get('cancer_type', 'Unknown')
                conf = region.get('confidence', 0)
                
                # Region header
                story.append(Paragraph(f'<b>Region #{region_id}: {cancer_type} ({conf:.1f}% confidence)</b>', normal_style))
                story.append(Spacer(1, 4))
                
                # Morphology details
                morphology = region.get('morphology', {})
                margin = region.get('margin', {})
                density = region.get('density', {})
                vascularity = region.get('vascularity', {})
                tissue = region.get('tissue_composition', {})
                calc_details = region.get('calcification_details')
                
                lesion_details = [
                    ['Morphology:', f"{morphology.get('shape', '—')} - {morphology.get('shape_detail', '')}"],
                    ['Margin:', f"{margin.get('type', '—')} - {margin.get('detail', '')}"],
                    ['Margin Risk:', margin.get('risk_level', '—')],
                    ['Density:', f"{density.get('level', '—')} ({density.get('intensity_score', 0)}%)"],
                    ['Vascularity:', f"{vascularity.get('assessment', '—')} - {vascularity.get('detail', '')}"],
                    ['Tissue Type:', f"{tissue.get('type', '—')} - {tissue.get('detail', '')}"],
                ]
                
                # Add calcification details if present
                if calc_details:
                    lesion_details.append(['Calc. Morphology:', calc_details.get('morphology', '—')])
                    lesion_details.append(['Calc. Distribution:', calc_details.get('distribution', '—')])
                
                # Clinical significance and recommendation
                lesion_details.append(['Clinical Significance:', region.get('clinical_significance', '—')])
                lesion_details.append(['Recommended Action:', region.get('recommended_action', '—')])
                
                lesion_table = Table(lesion_details, colWidths=[1.5*inch, 5.2*inch])
                lesion_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
                ]))
                
                story.append(lesion_table)
                story.append(Spacer(1, 8))
        
        # ============================
        # COMPREHENSIVE IMAGE ANALYSIS (NEW SECTION)
        # ============================
        comprehensive = findings.get('comprehensive_analysis', {})
        if comprehensive:
            story.append(PageBreak())
            story.append(Paragraph('<b>COMPREHENSIVE IMAGE ANALYSIS</b>', heading_style))
            story.append(Spacer(1, 10))
            
            # 1. BREAST DENSITY ANALYSIS
            density_analysis = comprehensive.get('breast_density', {})
            if density_analysis:
                story.append(Paragraph('<b>1. Breast Density Assessment (ACR BI-RADS)</b>', subheading_style))
                story.append(Spacer(1, 4))
                
                density_data = [
                    ['Category:', f"BI-RADS Density {density_analysis.get('category', '—')} - {density_analysis.get('description', '')}"],
                    ['Density Percentage:', f"{density_analysis.get('density_percentage', 0)}%"],
                    ['Mammography Sensitivity:', density_analysis.get('sensitivity', '—')],
                    ['Masking Risk:', density_analysis.get('masking_risk', '—')],
                    ['Clinical Detail:', density_analysis.get('detail', '—')],
                    ['Recommendation:', density_analysis.get('recommendation', '—')],
                ]
                
                density_table = Table(density_data, colWidths=[1.8*inch, 4.9*inch])
                density_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#E3F2FD")),
                ]))
                story.append(density_table)
                story.append(Spacer(1, 12))
            
            # 2. TISSUE TEXTURE ANALYSIS
            texture_analysis = comprehensive.get('tissue_texture', {})
            if texture_analysis:
                story.append(Paragraph('<b>2. Tissue Texture Analysis</b>', subheading_style))
                story.append(Spacer(1, 4))
                
                texture_data = [
                    ['Pattern:', f"{texture_analysis.get('pattern', '—')} - {texture_analysis.get('pattern_detail', '')}"],
                    ['Uniformity Score:', f"{texture_analysis.get('uniformity_score', 0)}%"],
                    ['Coefficient of Variation:', f"{texture_analysis.get('coefficient_of_variation', 0)}%"],
                    ['Distribution:', texture_analysis.get('distribution', '—')],
                    ['Clinical Note:', texture_analysis.get('clinical_note', '—')],
                ]
                
                texture_table = Table(texture_data, colWidths=[1.8*inch, 4.9*inch])
                texture_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                ]))
                story.append(texture_table)
                story.append(Spacer(1, 12))
            
            # 3. SYMMETRY ANALYSIS
            symmetry_analysis = comprehensive.get('symmetry', {})
            if symmetry_analysis:
                story.append(Paragraph('<b>3. Breast Symmetry Analysis</b>', subheading_style))
                story.append(Spacer(1, 4))
                
                symmetry_data = [
                    ['Assessment:', f"{symmetry_analysis.get('assessment', '—')} - {symmetry_analysis.get('detail', '')}"],
                    ['Symmetry Score:', f"{symmetry_analysis.get('symmetry_score', 0)}%"],
                    ['Asymmetric Area:', f"{symmetry_analysis.get('asymmetric_area_percentage', 0)}%"],
                    ['Clinical Significance:', symmetry_analysis.get('clinical_significance', '—')],
                    ['Recommendation:', symmetry_analysis.get('recommendation', '—')],
                ]
                
                symmetry_table = Table(symmetry_data, colWidths=[1.8*inch, 4.9*inch])
                symmetry_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                ]))
                story.append(symmetry_table)
                story.append(Spacer(1, 12))
            
            # 4. SKIN & NIPPLE ANALYSIS
            skin_analysis = comprehensive.get('skin_nipple', {})
            if skin_analysis:
                story.append(Paragraph('<b>4. Skin and Nipple Assessment</b>', subheading_style))
                story.append(Spacer(1, 4))
                
                skin_data = [
                    ['Skin Status:', f"{skin_analysis.get('skin_status', '—')} - {skin_analysis.get('skin_detail', '')}"],
                    ['Skin Thickness Score:', f"{skin_analysis.get('skin_thickness_score', 0)}%"],
                    ['Concern Level:', skin_analysis.get('skin_concern_level', '—')],
                    ['Nipple Retraction:', skin_analysis.get('nipple_retraction', '—')],
                    ['Recommendation:', skin_analysis.get('recommendation', '—')],
                ]
                
                skin_table = Table(skin_data, colWidths=[1.8*inch, 4.9*inch])
                skin_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                ]))
                story.append(skin_table)
                story.append(Spacer(1, 12))
            
            # 5. VASCULAR PATTERN ANALYSIS
            vascular_analysis = comprehensive.get('vascular_patterns', {})
            if vascular_analysis:
                story.append(Paragraph('<b>5. Vascular Pattern Analysis</b>', subheading_style))
                story.append(Spacer(1, 4))
                
                vascular_data = [
                    ['Pattern:', f"{vascular_analysis.get('pattern', '—')} - {vascular_analysis.get('detail', '')}"],
                    ['Vascular Score:', f"{vascular_analysis.get('vascular_score', 0)}%"],
                    ['Prominent Vessels:', f"{vascular_analysis.get('prominent_vessel_percentage', 0)}%"],
                    ['Clinical Note:', vascular_analysis.get('clinical_note', '—')],
                ]
                
                vascular_table = Table(vascular_data, colWidths=[1.8*inch, 4.9*inch])
                vascular_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                ]))
                story.append(vascular_table)
                story.append(Spacer(1, 12))
            
            # 6. PECTORAL MUSCLE ANALYSIS
            pectoral_analysis = comprehensive.get('pectoral_muscle', {})
            if pectoral_analysis:
                story.append(Paragraph('<b>6. Pectoral Muscle & Image Quality</b>', subheading_style))
                story.append(Spacer(1, 4))
                
                pectoral_data = [
                    ['Visibility:', f"{pectoral_analysis.get('visibility', '—')} - {pectoral_analysis.get('detail', '')}"],
                    ['Visibility Score:', f"{pectoral_analysis.get('visibility_score', 0)}%"],
                    ['Image Quality:', pectoral_analysis.get('quality', '—')],
                    ['Positioning:', 'Adequate' if pectoral_analysis.get('positioning_adequate', False) else 'Suboptimal'],
                    ['Recommendation:', pectoral_analysis.get('recommendation', '—')],
                ]
                
                pectoral_table = Table(pectoral_data, colWidths=[1.8*inch, 4.9*inch])
                pectoral_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                ]))
                story.append(pectoral_table)
                story.append(Spacer(1, 12))
            
            # 7. CALCIFICATION ANALYSIS
            calc_analysis = comprehensive.get('calcification_analysis', {})
            if calc_analysis and calc_analysis.get('detected', False):
                story.append(Paragraph('<b>7. Calcification Pattern Analysis</b>', subheading_style))
                story.append(Spacer(1, 4))
                
                calc_data = [
                    ['Calcifications Detected:', 'Yes'],
                    ['Count:', str(calc_analysis.get('count', 0))],
                    ['Distribution:', f"{calc_analysis.get('distribution', '—')} - {calc_analysis.get('distribution_detail', '')}"],
                    ['Morphology:', f"{calc_analysis.get('morphology', '—')} - {calc_analysis.get('morphology_detail', '')}"],
                    ['BI-RADS Category:', calc_analysis.get('birads_category', '—')],
                    ['Clinical Significance:', calc_analysis.get('clinical_significance', '—')],
                    ['Recommendation:', calc_analysis.get('recommendation', '—')],
                ]
                
                calc_table = Table(calc_data, colWidths=[1.8*inch, 4.9*inch])
                calc_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFF3E0")),
                ]))
                story.append(calc_table)
                story.append(Spacer(1, 12))
            
            # 8. OVERALL IMAGE QUALITY SUMMARY
            quality_analysis = comprehensive.get('image_quality', {})
            if quality_analysis:
                story.append(Paragraph('<b>8. Overall Image Quality Assessment</b>', subheading_style))
                story.append(Spacer(1, 4))
                
                quality_data = [
                    ['Overall Quality Score:', f"{quality_analysis.get('overall_score', 0)}%"],
                    ['Positioning Quality:', quality_analysis.get('positioning', '—')],
                    ['Technical Adequacy:', quality_analysis.get('technical_adequacy', '—')],
                ]
                
                quality_table = Table(quality_data, colWidths=[1.8*inch, 4.9*inch])
                quality_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#E8F5E9")),
                ]))
                story.append(quality_table)
                story.append(Spacer(1, 12))
    
    # ============================
    # VIEW-SPECIFIC ANALYSIS (CC/MLO)
    # ============================
    if view_analysis:
        # Check if we have both CC and MLO views
        cc_analysis = view_analysis.get('cc')
        mlo_analysis = view_analysis.get('mlo')
        
        if cc_analysis or mlo_analysis:
            story.append(Paragraph('<b>VIEW-SPECIFIC MAMMOGRAM ANALYSIS</b>', heading_style))
            story.append(Spacer(1, 8))
        
        # CC View Analysis
        if cc_analysis:
            story.append(Paragraph('<b>CRANIOCAUDAL (CC) VIEW:</b>', subheading_style))
            story.append(Spacer(1, 4))
            
            cc_data = [
                ['Image Quality:', cc_analysis.get('image_quality', 'Adequate')],
                ['Breast Positioning:', cc_analysis.get('positioning', 'Properly positioned')],
                ['Breast Density:', cc_analysis.get('breast_density', 'Heterogeneously dense')],
                ['Masses:', cc_analysis.get('masses', 'See detected regions above')],
                ['Calcifications:', cc_analysis.get('calcifications', 'See detected regions above')],
                ['Asymmetry:', cc_analysis.get('asymmetry', 'No significant asymmetry')],
                ['Skin/Nipple Changes:', cc_analysis.get('skin_nipple_changes', 'No abnormality detected')],
                ['Medial Coverage:', cc_analysis.get('medial_coverage', 'Adequate')],
                ['Lateral Coverage:', cc_analysis.get('lateral_coverage', 'Adequate')],
                ['CC View Impression:', cc_analysis.get('impression', 'Findings as described above')],
            ]
            
            cc_table = Table(cc_data, colWidths=[1.8*inch, 4.9*inch])
            cc_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0F8FF")),
            ]))
            story.append(cc_table)
            story.append(Spacer(1, 10))
        
        # MLO View Analysis
        if mlo_analysis:
            story.append(Paragraph('<b>MEDIOLATERAL OBLIQUE (MLO) VIEW:</b>', subheading_style))
            story.append(Spacer(1, 4))
            
            mlo_data = [
                ['Image Quality:', mlo_analysis.get('image_quality', 'Adequate')],
                ['Breast Positioning:', mlo_analysis.get('positioning', 'Properly positioned')],
                ['Breast Density:', mlo_analysis.get('breast_density', 'Heterogeneously dense')],
                ['Masses:', mlo_analysis.get('masses', 'See detected regions above')],
                ['Calcifications:', mlo_analysis.get('calcifications', 'See detected regions above')],
                ['Architectural Distortion:', mlo_analysis.get('architectural_distortion', 'No distortion detected')],
                ['Pectoral Muscle:', mlo_analysis.get('pectoral_muscle', 'Adequately visualized to nipple level')],
                ['Axillary Region:', mlo_analysis.get('axillary_findings', 'No suspicious lymph nodes')],
                ['Inframammary Fold:', mlo_analysis.get('inframammary_fold', 'Included')],
                ['MLO View Impression:', mlo_analysis.get('impression', 'Findings as described above')],
            ]
            
            mlo_table = Table(mlo_data, colWidths=[1.8*inch, 4.9*inch])
            mlo_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFF8F0")),
            ]))
            story.append(mlo_table)
            story.append(Spacer(1, 10))
        
        # Comparative Analysis / Summary
        comparison_text = view_analysis.get('comparison', '')
        if comparison_text:
            if cc_analysis and mlo_analysis:
                # Both views present - show comparative analysis
                story.append(Paragraph('<b>COMPARATIVE ANALYSIS (CC vs MLO):</b>', subheading_style))
            else:
                # Single view - show summary
                story.append(Paragraph('<b>VIEW SUMMARY:</b>', subheading_style))
            
            story.append(Spacer(1, 4))
            story.append(Paragraph(comparison_text, normal_style))
            story.append(Spacer(1, 12))
    
    # ============================
    # IMPRESSION SECTION
    # ============================
    story.append(Paragraph('<b>IMPRESSION:</b>', heading_style))
    story.append(Spacer(1, 4))
    
    if malignant_prob >= 50:
        impression_text = f"AI analysis suggests features concerning for malignancy<br/><b>{birads_category}</b>"
    else:
        impression_text = f"No mammographic evidence of malignancy detected by AI analysis<br/><b>{birads_category}</b>"
    
    story.append(Paragraph(impression_text, normal_style))
    story.append(Spacer(1, 12))
    
    # ============================
    # SUGGESTION SECTION
    # ============================
    story.append(Paragraph('<b>SUGGESTION:</b>', heading_style))
    story.append(Spacer(1, 4))
    
    if malignant_prob >= 75:
        suggestion = "Immediate clinical correlation and tissue biopsy recommended"
    elif malignant_prob >= 40:
        suggestion = "Follow-up imaging and clinical correlation recommended"
    else:
        suggestion = "Self breast exam monthly and follow up study yearly"
    
    story.append(Paragraph(suggestion, normal_style))
    story.append(Spacer(1, 12))
    
    # ============================
    # NOTE SECTION
    # ============================
    story.append(Paragraph('<b>Note:</b>', heading_style))
    story.append(Spacer(1, 4))
    
    note_bullets = [
        "- The false negative rate of mammography is approximately 10%",
        "- Dense breast may obscure underlying neoplasm",
        "- Management of a palpable abnormality must be based on clinical assessment",
        "- This report includes AI-assisted analysis for educational purposes",
        "- Final diagnosis should be made by qualified radiologist with clinical correlation"
    ]
    
    for bullet in note_bullets:
        story.append(Paragraph(bullet, normal_style))
    
    story.append(Spacer(1, 14))
    
    # ============================
    # BI-RADS REFERENCE
    # ============================
    story.append(Paragraph('<b>BI-RADS Classification Reference:</b>', heading_style))
    story.append(Spacer(1, 4))
    
    birads_ref = [
        ['BI-RADS 0: Need additional image', 'BI-RADS 1: Negative'],
        ['BI-RADS 2: Benign Finding', 'BI-RADS 3: Probably Benign'],
        ['BI-RADS 4: Suspicious Abnormality (4A: low, 4B: intermediate, 4C: high)', ''],
        ['BI-RADS 5: Highly suggestive of malignancy', ''],
        ['BI-RADS 6: Known malignancy', ''],
    ]
    
    birads_table = Table(birads_ref, colWidths=[3.35*inch, 3.35*inch])
    birads_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(birads_table)
    story.append(PageBreak())

    # ============================
    # IMAGING ANALYSIS PAGE
    # ============================
    story.append(Paragraph('<b>IMAGING ANALYSIS</b>', heading_style))
    story.append(Spacer(1, 10))

    # Original Image
    story.append(Paragraph('<b>1. Original Mammogram Image</b>', subheading_style))
    if original_image:
        story.append(pil_to_rl_image(original_image, max_w=5.5*inch, max_h=3.5*inch))
    story.append(Spacer(1, 12))

    # AI Heatmap Overlay
    story.append(Paragraph('<b>2. AI Attention Map (Grad-CAM Overlay)</b>', subheading_style))
    if overlay_image:
        story.append(pil_to_rl_image(overlay_image, max_w=5.5*inch, max_h=3.5*inch))
    else:
        story.append(Paragraph('Heatmap visualization not available', normal_style))
    story.append(Spacer(1, 12))

    # Suspicious Regions and Cancer Type Detection - Side by Side or Sequential
    story.append(Paragraph('<b>3. Suspicious Regions Highlighted</b>', subheading_style))
    if bbox_image:
        story.append(pil_to_rl_image(bbox_image, max_w=5.0*inch, max_h=3.0*inch))
    else:
        story.append(Paragraph('No high-activation regions detected above threshold', normal_style))
    story.append(Spacer(1, 8))

    # Cancer Type Detection Image - Right after Suspicious Regions
    story.append(Paragraph('<b>4. Cancer Type Detection</b>', subheading_style))
    if cancer_type_image:
        story.append(pil_to_rl_image(cancer_type_image, max_w=5.0*inch, max_h=3.0*inch))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            '<i>Detected regions with cancer type classifications and confidence scores</i>',
            ParagraphStyle('ImageCaption', parent=normal_style, fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
        ))
    else:
        story.append(Paragraph('Cancer type visualization not available', normal_style))
    
    story.append(PageBreak())

    # ============================
    # TECHNICAL DETAILS
    # ============================
    story.append(Paragraph('<b>TECHNICAL DETAILS</b>', heading_style))
    story.append(Spacer(1, 6))
    
    tech_details = [
        ['Image Dimensions:', f"{image_size[0]} x {image_size[1]} pixels"],
        ['Image Format:', file_format],
        ['Mean Intensity:', f"{stats['mean_intensity']:.2f}"],
        ['Brightness Index:', f"{stats['brightness']:.2f}%"],
        ['Contrast Index:', f"{stats['contrast']:.2f}%"],
        ['AI Model Confidence:', f"{confidence:.6f}"],
    ]
    
    tech_table = Table(tech_details, colWidths=[2.0*inch, 4.7*inch])
    tech_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    
    story.append(tech_table)
    story.append(Spacer(1, 16))

    # ============================
    # CLINICAL RECOMMENDATIONS
    # ============================
    story.append(Paragraph('<b>CLINICAL RECOMMENDATIONS:</b>', heading_style))
    story.append(Spacer(1, 6))

    if confidence > 0.5:
        recs = [
            "- Immediate consultation with oncologist or breast specialist recommended",
            "- Additional diagnostic imaging (ultrasound, MRI) may be warranted",
            "- Tissue biopsy strongly recommended for definitive diagnosis",
            "- Close clinical follow-up and correlation with physical examination",
            "- Share this report with your healthcare provider for review"
        ]
    else:
        recs = [
            "- Continue routine breast cancer screening as per guidelines",
            "- Perform monthly self-breast examination",
            "- Annual mammography screening recommended",
            "- Report any new symptoms or changes to your healthcare provider",
            "- Maintain healthy lifestyle and follow preventive measures"
        ]

    for r in recs:
        story.append(Paragraph(r, normal_style))
    
    story.append(Spacer(1, 20))

    # ============================
    # DISCLAIMER BOX
    # ============================
    disclaimer_text = """
    <b>IMPORTANT MEDICAL DISCLAIMER</b><br/><br/>
    This report contains AI-assisted analysis for <b>educational and research purposes only</b>. 
    The AI system is NOT clinically validated and should NOT be used as the sole basis for medical 
    diagnosis, treatment decisions, or patient management. This analysis must be reviewed and 
    interpreted by qualified radiologists and healthcare professionals. Always consult licensed 
    medical professionals for definitive diagnosis, imaging interpretation, and treatment planning.
    Clinical correlation is essential.
    """

    disclaimer_box = Table(
        [[Paragraph(disclaimer_text, disclaimer_style)]],
        colWidths=[6.7 * inch],
    )
    disclaimer_box.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFF3E0")),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#E65100")),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]
        )
    )

    story.append(disclaimer_box)
    story.append(Spacer(1, 0.3 * inch))

    # ============================
    # FOOTER & SIGNATURE
    # ============================
    story.append(Spacer(1, 0.2 * inch))
    
    footer_note = f"<b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/><b>Generated by:</b> AI-Powered Breast Cancer Detection System<br/><b>Educational Use Only</b> - Not for Clinical Diagnosis"
    
    story.append(Paragraph(footer_note, footer_style))
    
    story.append(Spacer(1, 0.3 * inch))
    
    # Signature line
    sig_line = [
        ['', '', ''],
        ['_____________________', '_____________________', '_____________________'],
        ['Radiologic Technologist', 'Radiologist (MD)', 'Reviewing Physician (MD)'],
    ]
    
    sig_table = Table(sig_line, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 2),
    ]))
    
    story.append(sig_table)

    # ============================
    # FINAL BUILD
    # ============================
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
