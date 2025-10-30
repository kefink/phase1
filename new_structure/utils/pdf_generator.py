"""
PDF generation utilities for the Hillview School Management System.
Unified PDF generation for guaranteed format parity between single and batch downloads.
"""
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import os
import re
import tempfile
import pdfkit
from flask import current_app

# Fixed relative import: this module resides inside the top-level 'utils' package, so use a single-dot relative import.
from .performance import get_performance_category, get_grade_and_points


# ============================================================================
# UNIFIED PDF GENERATION - Single Source of Truth
# ============================================================================

def inject_print_css(html):
    """
    Minimal CSS injection for PDF generation - preserves template's original styling.
    Only adds print-specific tweaks: hide interactive elements, enforce print mode.
    """
    import re
    
    # DO NOT remove external stylesheets or existing styles - let template CSS work!
    # Only inject minimal print-mode CSS
    
    # Step 1: Add minimal print CSS that works alongside existing styles
    minimal_print_css = """
    <style type="text/css" media="print">
        /* Minimal print-mode CSS - preserves template styling */
        @page {
            size: A4 portrait;
            margin: 0.5in;
        }
        
        @media print {
            /* Hide interactive elements only */
            .action-buttons,
            .print-controls,
            .delete-btn,
            .modal,
            button:not(.keep-for-print),
            .btn:not(.keep-for-print),
            .navigation,
            nav,
            .back-button {
                display: none !important;
            }
            
            /* Ensure content fits on page */
            body {
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }
            
            /* Prevent page breaks in critical sections */
            .report-container,
            .marks-table,
            table,
            .summary-section {
                page-break-inside: avoid;
            }
        }
    </style>
    """
    
    # Step 2: Inject our minimal CSS at the end of <head>
    if '</head>' in html:
        html = html.replace('</head>', f'{minimal_print_css}</head>')
    elif '<body' in html:
        # If no </head>, inject right before body
        html = html.replace('<body', f'{minimal_print_css}<body', 1)
    else:
        # Last resort: prepend to entire document
        html = minimal_print_css + html
    
    return html


def convert_static_urls_to_file_paths(html: str, static_folder: str) -> str:
    """
    Convert /static/... URLs to file:/// absolute paths for wkhtmltopdf.
    Prevents HostNotFoundError and ensures local asset loading.
    """
    def _replace_static_attr(m):
        rel = m.group(1)
        abs_path = os.path.join(static_folder, rel).replace('\\', '/')
        return f'"file:///{abs_path}"'
    
    def _replace_static_url_in_css(m):
        rel = m.group(1)
        abs_path = os.path.join(static_folder, rel).replace('\\', '/')
        return f'url("file:///{abs_path}")'
    
    # Replace src/href attributes
    html = re.sub(r'["\']?/static/([^"\'>\s]+)["\']?', lambda m: _replace_static_attr(m), html)
    
    # Replace CSS url() references
    html = re.sub(
        r'url\(["\']?/static/([^"\')\s]+)["\']?\)',
        lambda m: _replace_static_url_in_css(m),
        html
    )
    
    return html


def get_standard_pdf_options() -> dict:
    """
    Centralized wkhtmltopdf configuration.
    MUST be identical for single and batch generation to ensure format parity.
    """
    return {
        'page-size': 'A4',
        'orientation': 'Portrait',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': 'UTF-8',
        'no-outline': None,
        'enable-local-file-access': None,
        
        # 🔥 CRITICAL: Force print media type for white background
        'print-media-type': None,
        
        'disable-javascript': None,
        'load-error-handling': 'ignore',
        'load-media-error-handling': 'ignore',
        
        # Ensure consistent rendering
        'dpi': 96,
        'image-quality': 100,
        
        # Background rendering (crucial for white background)
        'background': None,
    }


def get_wkhtmltopdf_config():
    """
    Get wkhtmltopdf configuration with explicit path for Windows.
    """
    WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    
    if os.path.exists(WKHTMLTOPDF_PATH):
        current_app.logger.info(f"Using wkhtmltopdf at: {WKHTMLTOPDF_PATH}")
        return pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
    else:
        current_app.logger.warning("wkhtmltopdf not found at standard path, using default configuration")
        return pdfkit.configuration()


def render_pdf_from_html(html: str, static_folder: str) -> bytes:
    """
    Convert HTML to PDF bytes using wkhtmltopdf with standardized configuration.
    
    Args:
        html: HTML content to convert
        static_folder: Path to static assets folder
        
    Returns:
        PDF content as bytes
    """
    # Step 1: Inject print CSS
    html = inject_print_css(html)
    
    # Step 2: Convert /static URLs to file:/// paths
    html = convert_static_urls_to_file_paths(html, static_folder)
    
    # Step 3: Get standardized wkhtmltopdf configuration
    config = get_wkhtmltopdf_config()
    options = get_standard_pdf_options()
    
    # Step 4: Render via temporary HTML file for stability on Windows
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
        temp_html.write(html)
        temp_html_path = temp_html.name
    
    try:
        # Generate PDF and return bytes
        pdf_bytes = pdfkit.from_file(temp_html_path, False, options=options, configuration=config)
        return pdf_bytes
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_html_path)
        except OSError:
            pass


# ============================================================================
# Legacy ReportLab PDF Generation (Original)
# ============================================================================

def generate_individual_report_pdf(grade, stream, term, assessment_type, student_name, class_data, education_level, total_marks, subjects):
    """
    Generate a PDF report for an individual student.
    
    Args:
        grade: The grade level
        stream: The class stream
        term: The term
        assessment_type: The assessment type
        student_name: The student's name
        class_data: Data for the entire class
        education_level: The education level
        total_marks: The total possible marks
        subjects: List of subjects
        
    Returns:
        Path to the generated PDF file
    """
    stream_letter = stream[-1] if stream else ''
    student_data = next((data for data in class_data if data['student'].lower() == student_name.lower()), None)
    
    if not student_data:
        return None

    pdf_file = f"individual_report_{grade}_{stream}_{student_name.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    heading3_style = styles['Heading3']

    elements.append(Paragraph("KIRIMA PRIMARY SCHOOL", title_style))
    elements.append(Paragraph("P.O. Box 12345 - 00100, Nairobi, Kenya", subtitle_style))
    elements.append(Paragraph("Tel: 0712345678", subtitle_style))
    elements.append(Paragraph(f"ACADEMIC REPORT TERM {term.replace('_', ' ').upper()} 2025", subtitle_style))
    elements.append(Spacer(1, 12))

    student_name_upper = student_name.upper()
    admission_no = f"HS{grade}{stream_letter}{str(class_data.index(student_data) + 1).zfill(3)}"
    elements.append(Paragraph(f"{student_name_upper}  ADM NO.: {admission_no}", normal_style))
    elements.append(Paragraph(f"Grade {grade} {education_level} {stream}", normal_style))

    total = student_data['total_marks']
    avg_percentage = student_data['average_percentage']
    mean_grade, mean_points = get_grade_and_points(avg_percentage)
    total_possible_marks = len(subjects) * total_marks
    total_points = sum(get_grade_and_points(student_data['marks'].get(subject, 0))[1] for subject in subjects)

    elements.append(Paragraph(f"MEAN GRADE: {mean_grade}", normal_style))
    elements.append(Paragraph(f"Mean Points: {mean_points}  Total Marks: {int(total)} out of: {total_possible_marks}", normal_style))
    elements.append(Paragraph(f"Mean Mark: {avg_percentage:.2f}%", normal_style))
    elements.append(Paragraph(f"Total Points: {total_points}", normal_style))
    elements.append(Spacer(1, 12))

    # Create table for subject marks
    headers = ["Subjects", "Entrance", "Mid Term", "End Term", "Avg.", "Subject Remarks"]
    data = [headers]
    for subject in subjects:
        mark = student_data['marks'].get(subject, 0)
        avg = mark
        percentage = (mark / total_marks) * 100 if total_marks > 0 else 0
        performance = get_performance_category(percentage)
        data.append([
            subject.upper(),
            "",
            "",
            str(int(mark)),
            str(int(avg)),
            f"{performance}"
        ])

    data.append([
        "Totals",
        "",
        "",
        str(int(total)),
        str(int(total)),
        ""
    ])

    table = Table(data)
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    table.setStyle(TableStyle(table_style))
    elements.append(table)

    # Add remarks
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Class Teacher's Remarks:", heading3_style))
    elements.append(Paragraph("Well done! With continued focus and consistency, you have the potential to achieve even more.", normal_style))
    elements.append(Paragraph("Class Teacher: Moses Barasa", normal_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Head Teacher's Remarks:", heading3_style))
    elements.append(Paragraph("Great progress! Your growing confidence is evident - keep practicing, and you'll excel even further.", normal_style))
    elements.append(Paragraph("Head Teacher Name: Mr. Paul Mwangi", normal_style))
    elements.append(Paragraph("Head Teacher Signature: ____________________", normal_style))
    elements.append(Paragraph("Next Term Begins on: TBD", normal_style))

    # Add footer
    elements.append(Spacer(1, 12))
    footer_style = styles['Normal']
    footer_style.alignment = 1
    current_date = datetime.now().strftime("%Y-%m-%d")
    elements.append(Paragraph(f"Generated on: {current_date}", footer_style))
    elements.append(Paragraph("Kirima Primary School powered by CbcTeachkit", footer_style))

    doc.build(elements)
    return pdf_file