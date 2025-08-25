"""
Report generation services for the Hillview School Management System.
"""
from ..models import Student, Mark, Subject, Stream, Grade, Term, AssessmentType
from ..utils import get_performance_category, get_grade_and_points
from ..extensions import db
from collections import defaultdict
import os
import tempfile
import pdfkit
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from flask import render_template_string
from .enhanced_composite_service import EnhancedCompositeService

def get_class_report_data(grade, stream, term, assessment_type, selected_subject_ids=None):
    """
    Get data for a class report.

    Args:
        grade: The grade level
        stream: The class stream
        term: The term
        assessment_type: The assessment type
        selected_subject_ids: Optional list of subject IDs to include in the report

    Returns:
        Dictionary containing class report data
    """
    # Get the stream object - handle different stream name formats
    if stream.startswith("Stream "):
        stream_letter = stream.replace("Stream ", "").strip()
    else:
        stream_letter = stream.strip()

    stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream_letter).first()

    if not stream_obj:
        # Try alternative stream name formats
        # Try with just the last character
        alt_stream_letter = stream[-1] if len(stream) > 0 else stream
        stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == alt_stream_letter).first()

        if stream_obj:
            stream_letter = alt_stream_letter

    if not stream_obj:
        return {"error": f"No students found for grade {grade} stream {stream_letter}"}

    # Get the term and assessment type objects
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (term_obj and assessment_type_obj):
        return {"error": "Invalid selection for term or assessment type"}

    # Get the students in the stream
    students = Student.query.filter_by(stream_id=stream_obj.id).all()

    # Determine education level based on grade
    grade_num = int(grade.split()[1]) if len(grade.split()) > 1 else int(grade)
    if 1 <= grade_num <= 3:
        education_level = "lower_primary"
    elif 4 <= grade_num <= 6:
        education_level = "upper_primary"
    elif 7 <= grade_num <= 9:
        education_level = "junior_secondary"
    else:
        education_level = ""

    # Import the composite subject service for new architecture
    from .composite_subject_service import CompositeSubjectService

    # Get subjects for this education level using the new architecture
    if education_level:
        # Get subjects for upload (excludes old composite subjects, includes components)
        all_subjects = CompositeSubjectService.get_subjects_for_upload(education_level)

        # Filter by selected subject IDs if provided
        if selected_subject_ids and len(selected_subject_ids) > 0:
            subjects = [s for s in all_subjects if s.id in selected_subject_ids]
        else:
            subjects = all_subjects
    else:
        # Fallback to all subjects if education level can't be determined
        subjects_query = Subject.query
        if selected_subject_ids and len(selected_subject_ids) > 0:
            subjects_query = subjects_query.filter(Subject.id.in_(selected_subject_ids))
        subjects = subjects_query.all()

    # Prepare class data
    class_data = []
    default_total_marks = 100  # Default total marks if not specified

    for student in students:
        student_marks = {}
        student_raw_marks = {}
        subject_count = 0
        student_standardized_total = 0

        # Import the composite subject service for new architecture
        from .composite_subject_service import CompositeSubjectService

        # Get all composite subjects for this education level
        composite_subjects = CompositeSubjectService.get_all_composite_subjects(education_level)

        # Process subjects: handle both regular subjects and composite subjects
        processed_subjects = {}

        for subject in subjects:
            # Skip component subjects - they'll be handled as part of composite subjects
            if hasattr(subject, 'is_component') and subject.is_component:
                continue

            # Skip old composite subjects - they're replaced by the new architecture
            if hasattr(subject, 'is_composite') and subject.is_composite:
                continue

            # Handle regular subjects
            mark = Mark.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                term_id=term_obj.id,
                assessment_type_id=assessment_type_obj.id
            ).first()

            if mark:
                processed_subjects[subject.name] = mark.percentage

        # Handle composite subjects using the new architecture
        student_component_marks = {}
        for composite_name in composite_subjects:
            composite_data = CompositeSubjectService.get_composite_subject_mark(
                student.id, composite_name, term_obj.id, assessment_type_obj.id, education_level
            )

            if composite_data:
                processed_subjects[composite_name] = composite_data['combined_percentage']

                # Store component marks for template
                student_component_marks[composite_name] = {}
                for component_name, component_data in composite_data['components'].items():
                    student_component_marks[composite_name][component_name] = component_data['percentage']

        # Calculate totals and averages from processed subjects
        for subject_name, percentage in processed_subjects.items():
            # Ensure percentage doesn't exceed 100%
            standardized_mark = min(percentage, 100.0) if percentage > 0 else 0

            # Store the standardized mark
            student_marks[subject_name] = standardized_mark
            student_raw_marks[subject_name] = standardized_mark  # For compatibility

            # Add to standardized total for average calculation
            if standardized_mark > 0:
                student_standardized_total += standardized_mark
                subject_count += 1

        # Calculate total possible marks based on processed subjects (includes composite subjects)
        total_possible_marks = len(processed_subjects) * 100  # Always 100 per subject for standardized marks

        # Calculate average only for subjects that have marks
        if subject_count > 0:
            avg_percentage = student_standardized_total / subject_count
        else:
            avg_percentage = 0

        class_data.append({
            'student': student.name,
            'student_id': student.id,  # Add student ID for component marks lookup
            'marks': student_marks,
            'raw_marks': student_raw_marks,
            'component_marks': student_component_marks,  # Add component marks
            'total_marks': student_standardized_total,
            'total_possible_marks': total_possible_marks,
            'average_percentage': avg_percentage,
            'subject_count': subject_count
        })

    # Sort by total marks (descending)
    class_data.sort(key=lambda x: x['total_marks'], reverse=True)

    # Add ranking
    for i, student_data in enumerate(class_data, 1):
        student_data['rank'] = i

    # Calculate statistics
    stats = {'exceeding': 0, 'meeting': 0, 'approaching': 0, 'below': 0}
    for student_data in class_data:
        avg = student_data['average_percentage']
        if avg >= 75:
            stats['exceeding'] += 1
        elif 41 <= avg < 75:
            stats['meeting'] += 1
        elif 21 <= avg < 41:
            stats['approaching'] += 1
        else:
            stats['below'] += 1

    # Build the final subjects list including composite subjects
    final_subjects = []

    # Add regular subjects (non-component, non-composite)
    for subject in subjects:
        if not (hasattr(subject, 'is_component') and subject.is_component) and not (hasattr(subject, 'is_composite') and subject.is_composite):
            final_subjects.append(subject.name)

    # Add composite subjects
    composite_subjects = CompositeSubjectService.get_all_composite_subjects(education_level)
    final_subjects.extend(composite_subjects)

    # Sort the final subjects list
    final_subjects.sort()

    # Prepare component structure data for template
    subject_components = {}
    component_marks_data = {}

    for composite_name in composite_subjects:
        # Get component subjects for this composite
        component_subjects = Subject.query.filter_by(
            composite_parent=composite_name,
            education_level=education_level,
            is_component=True
        ).all()

        if component_subjects:
            subject_components[composite_name] = component_subjects

            # Prepare component marks data structure expected by template
            component_marks_data = {}
            for student_data in class_data:
                student_id = student_data['student_id']
                component_marks_data[student_id] = student_data.get('component_marks', {})

    return {
        "class_data": class_data,
        "stats": stats,
        "subjects": final_subjects,
        "subject_components": subject_components,  # Add component structure
        "component_marks_data": component_marks_data,  # Add component marks data
        "total_marks": default_total_marks,  # Using default total marks
        "error": None,
        "education_level": education_level
    }



def generate_class_report_pdf_from_html(grade, stream, term, assessment_type, class_data, stats, total_marks, subjects, education_level="", subject_averages=None, class_average=0, selected_subject_ids=None, staff_info=None):
    """
    Generate a PDF report for a class using HTML template.

    Args:
        grade: The grade level
        stream: The class stream
        term: The term
        assessment_type: The assessment type
        class_data: List of dictionaries containing student data
        stats: Dictionary containing performance statistics
        total_marks: The total marks per subject
        subjects: List of subject names
        education_level: The education level
        subject_averages: Dictionary of subject averages
        class_average: The class average
        selected_subject_ids: Optional list of subject IDs to include in the report

    Returns:
        Path to the generated PDF file
    """
    try:
        # Import Flask's render_template_string function
        from flask import render_template_string

        # First, get the template content
        with open('new_structure/templates/preview_class_report.html', 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Add print-specific CSS to the template
        print_css = """
        <style>
        @page {
            size: landscape;
            margin: 1cm;
        }
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        .action-buttons, .print-controls, .delete-btn, .modal {
            display: none !important;
        }
        </style>
        """
        template_content = template_content.replace('</head>', f'{print_css}</head>')

        # Process class_data to ensure it has filtered_marks
        processed_class_data = []
        for student_data in class_data:
            # Create a copy of the student data
            processed_student = dict(student_data)

            # Debug: Print the marks for this student
            print(f"\nProcessing student: {processed_student.get('student', 'Unknown')}")
            print(f"Original marks: {processed_student.get('marks', {})}")

            # Ensure all composite subjects have correct marks
            for subject_name, mark_value in processed_student.get('marks', {}).items():
                subject = Subject.query.filter_by(name=subject_name).first()
                if subject and hasattr(subject, 'is_composite') and subject.is_composite:
                    print(f"Found composite subject: {subject_name}, current mark: {mark_value}")

                    # Get the student
                    student = Student.query.filter_by(name=processed_student.get('student', '')).first()
                    if student:
                        # Get the term and assessment type
                        term_obj = Term.query.filter_by(name=term).first()
                        assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

                        if term_obj and assessment_type_obj:
                            # Get the mark
                            mark = Mark.query.filter_by(
                                student_id=student.id,
                                subject_id=subject.id,
                                term_id=term_obj.id,
                                assessment_type_id=assessment_type_obj.id
                            ).first()

                            if mark:
                                # Recalculate from components
                                from ..models.academic import ComponentMark
                                component_marks = ComponentMark.query.filter_by(mark_id=mark.id).all()

                                if component_marks:
                                    # Get the components for this subject
                                    components = subject.get_components() if hasattr(subject, 'get_components') else []

                                    # Calculate weighted percentage
                                    total_weighted_percentage = 0
                                    total_weight = 0

                                    for component in components:
                                        # Find the component mark
                                        cm = next((cm for cm in component_marks if cm.component_id == component.id), None)
                                        if cm:
                                            # Calculate percentage from raw mark and max raw mark
                                            component_percentage = (cm.raw_mark / cm.max_raw_mark) * 100 if cm.max_raw_mark > 0 else 0
                                            # Cap at 100%
                                            component_percentage = min(component_percentage, 100)
                                            print(f"  Component {component.name}: {cm.raw_mark}/{cm.max_raw_mark} = {component_percentage:.1f}% (weight: {component.weight})")
                                            total_weighted_percentage += component_percentage * component.weight
                                            total_weight += component.weight

                                    if total_weight > 0:
                                        # Calculate the weighted percentage
                                        weighted_percentage = total_weighted_percentage / total_weight
                                        print(f"  Calculated weighted percentage: {weighted_percentage}%")

                                        # Update the mark in the student data
                                        processed_student['marks'][subject_name] = weighted_percentage

                                        # Update the mark in the database
                                        mark.percentage = weighted_percentage
                                        mark.raw_mark = (weighted_percentage / 100) * (mark.max_raw_mark or 100)
                                        mark.mark = mark.raw_mark  # Update old field name too
                                        try:
                                            db.session.commit()
                                            print(f"  Updated mark in database: {weighted_percentage}%")
                                        except Exception as e:
                                            db.session.rollback()
                                            print(f"  Error updating mark: {e}")

            # Filter marks based on selected subjects
            if selected_subject_ids and len(selected_subject_ids) > 0:
                # Get the subject names for the selected subject IDs
                selected_subject_names = [subject for subject in subjects if Subject.query.filter_by(name=subject).first() and Subject.query.filter_by(name=subject).first().id in selected_subject_ids]

                # Create filtered marks dictionary
                filtered_marks = {}
                filtered_total = 0
                filtered_subject_count = 0

                for subject_name in selected_subject_names:
                    if subject_name in processed_student.get('marks', {}):
                        filtered_marks[subject_name] = processed_student['marks'][subject_name]
                        filtered_total += processed_student['marks'][subject_name]
                        filtered_subject_count += 1

                # Calculate filtered average
                filtered_average = filtered_total / filtered_subject_count if filtered_subject_count > 0 else 0

                # Add filtered data to processed student
                processed_student['filtered_marks'] = filtered_marks
                processed_student['filtered_total'] = filtered_total
                processed_student['filtered_average'] = filtered_average
                processed_student['performance_category'] = get_performance_category(filtered_average)
            else:
                # If no subjects are selected, use all marks
                processed_student['filtered_marks'] = processed_student.get('marks', {})
                processed_student['filtered_total'] = processed_student.get('total_marks', 0)
                processed_student['filtered_average'] = processed_student.get('average_percentage', 0)
                processed_student['performance_category'] = get_performance_category(processed_student.get('average_percentage', 0))

            # Debug: Print the filtered marks
            print(f"Filtered marks: {processed_student.get('filtered_marks', {})}")

            processed_class_data.append(processed_student)

        # Get school information for dynamic display
        from ..services.school_config_service import SchoolConfigService
        school_info = SchoolConfigService.get_school_info_dict()

        # Render the template with the data
        html_content = render_template_string(
            template_content,
            grade=grade,
            stream=stream,
            term=term,
            assessment_type=assessment_type,
            class_data=processed_class_data,
            stats=stats,
            total_marks=total_marks,
            subject_names=subjects,
            education_level=education_level,
            subject_averages=subject_averages,
            class_average=class_average,
            staff_info=staff_info,  # Include staff information
            school_info=school_info,  # Include school information
            print_mode=True  # Flag to indicate PDF generation
        )

        # Generate PDF from HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"class_report_{grade}_{stream}_{term}_{assessment_type}_{timestamp}.pdf"

        # Create a temporary file
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, filename)

        # Configure pdfkit options for better formatting
        options = {
            'page-size': 'A4',
            'orientation': 'Landscape',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': True,  # Enable local file access for images
            'print-media-type': None
        }

        # Convert HTML to PDF
        import pdfkit
        pdfkit.from_string(html_content, pdf_path, options=options)

        return pdf_path
    except Exception as e:
        print(f"Error generating PDF from HTML: {str(e)}")
        # Fallback to the old PDF generation method
        return generate_class_report_pdf(
            grade=grade,
            stream=stream,
            term=term,
            assessment_type=assessment_type,
            class_data=class_data,
            stats=stats,
            total_marks=total_marks,
            subjects=subjects,
            education_level=education_level,
            subject_averages=subject_averages,
            class_average=class_average
        )

def generate_class_report_pdf(grade, stream, term, assessment_type, class_data, stats, total_marks, subjects, education_level="", subject_averages=None, class_average=0):
    """
    Generate a PDF report for a class.

    Args:
        grade: The grade level
        stream: The class stream
        term: The term
        assessment_type: The assessment type
        class_data: List of dictionaries containing student data
        stats: Dictionary containing performance statistics
        total_marks: The total marks per subject
        subjects: List of subject names
        education_level: The education level
        subject_averages: Dictionary of subject averages
        class_average: The class average

    Returns:
        Path to the generated PDF file
    """
    # Initialize subject_averages if not provided
    if subject_averages is None:
        subject_averages = {}

    # Create a temporary file
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(temp_dir, f"class_report_{grade}_{stream}_{term}_{assessment_type}_{timestamp}.pdf")

    # Create the PDF document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    # Define styles
    styles = getSampleStyleSheet()

    # Create custom styles to match the HTML preview
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=16,
        alignment=1,  # Center alignment
        spaceAfter=6
    )

    school_name_style = ParagraphStyle(
        'SchoolName',
        parent=styles['Title'],
        fontSize=20,
        alignment=1,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=6
    )

    report_title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6
    )

    normal_style = styles["Normal"]

    # Create content
    content = []

    # Add school logo
    from reportlab.platypus import Image
    try:
        # Get dynamic logo path from school setup
        from ..services.school_config_service import SchoolConfigService
        logo_filename = SchoolConfigService.get_school_logo_path()
        logo_path = f'new_structure/static/{logo_filename}'
        logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
        content.append(logo)
    except Exception as e:
        print(f"Error adding logo: {str(e)}")
        # Fallback to default logo if dynamic logo fails
        try:
            fallback_logo_path = 'new_structure/static/hv.jpg'
            logo = Image(fallback_logo_path, width=1.5*inch, height=1.5*inch)
            content.append(logo)
        except Exception as fallback_error:
            print(f"Error adding fallback logo: {str(fallback_error)}")

    # Add school header using dynamic school information
    from ..services.school_config_service import SchoolConfigService
    school_info = SchoolConfigService.get_school_info_dict()

    school_name = Paragraph(school_info.get('school_name', 'KIRIMA PRIMARY SCHOOL'), school_name_style)
    content.append(school_name)

    school_address = Paragraph(f"{school_info.get('school_address', 'P.O. BOX 123, KIRIMA')} | TEL: {school_info.get('school_phone', '+254 123 456789')}", subtitle_style)
    content.append(school_address)

    school_contact = Paragraph(f"Email: {school_info.get('school_email', 'info@kirimaprimary.ac.ke')} | Website: {school_info.get('school_website', 'www.kirimaprimary.ac.ke')}", subtitle_style)
    content.append(school_contact)

    # Add report title
    clean_grade = grade.replace('Grade ', '')
    clean_stream = stream.replace('Stream ', '')

    report_title = Paragraph(f"{education_level.upper()} MARKSHEET", report_title_style)
    content.append(report_title)

    report_details = Paragraph(
        f"GRADE: {clean_grade} | STREAM: {clean_stream} | " +
        f"TERM: {term.replace('_', ' ').upper()} | ASSESSMENT: {assessment_type.upper()}",
        subtitle_style
    )
    content.append(report_details)
    content.append(Spacer(1, 0.2*inch))

    # Prepare table data for student marks
    # Create header row with abbreviated subject names
    abbreviated_subjects = []
    for subject in subjects:
        # Create abbreviation (first letter of each word)
        words = subject.split()
        if len(words) > 1:
            abbr = ''.join(word[0].upper() for word in words)
        else:
            # If single word, use first 3 letters
            abbr = subject[:3].upper()
        abbreviated_subjects.append(abbr)

    table_data = [["S/N", "STUDENT NAME"] + abbreviated_subjects + ["TOTAL", "AVG %", "GRD", "RANK"]]

    # Add student data rows
    for student in class_data:
        row = [
            student.get("index", ""),
            student.get("student", "").upper()
        ]

        # Add marks for each subject
        for subject in subjects:
            row.append(student.get("filtered_marks", {}).get(subject, 0))

        # Add total, average, grade and rank
        row.append(student.get("filtered_total", 0))
        row.append(f"{student.get('filtered_average', 0):.0f}%")
        row.append(student.get("performance_category", ""))
        row.append(student.get("rank", ""))

        table_data.append(row)

    # Add subject averages row
    subject_avg_row = ["", "SUBJECT AVERAGES"]
    for subject in subjects:
        subject_avg_row.append(subject_averages.get(subject, 0))
    subject_avg_row.extend(["", "", "", ""])  # Empty cells for total, avg, grade, rank
    table_data.append(subject_avg_row)

    # Add class average row
    class_avg_row = ["", "CLASS AVERAGE"]
    class_avg_row.extend([""] * len(subjects))  # Empty cells for subjects
    class_avg_row.append(class_average)  # Total average

    # Calculate class average percentage
    avg_percentage_total = 0
    avg_student_count = 0
    for student_data in class_data:
        if student_data.get('filtered_average', 0) > 0:
            avg_percentage_total += student_data.get('filtered_average', 0)
            avg_student_count += 1

    class_avg_percentage = round(avg_percentage_total / avg_student_count, 2) if avg_student_count > 0 else 0
    class_avg_row.append(f"{class_avg_percentage}%")  # Average percentage
    class_avg_row.extend(["", ""])  # Empty cells for grade, rank
    table_data.append(class_avg_row)

    # Calculate column widths based on content
    col_widths = [0.4*inch, 1.8*inch] + [0.5*inch] * len(subjects) + [0.6*inch, 0.6*inch, 0.5*inch, 0.5*inch]

    # Create the table
    class_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Style the table to match the HTML preview
    table_style = [
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),

        # Grid styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

        # Alignment for data cells
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # S/N column centered
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Student name left-aligned
        ('ALIGN', (2, 1), (-4, -1), 'CENTER'), # Subject marks centered
        ('ALIGN', (-3, 1), (-1, -1), 'CENTER'), # Total, Avg, Grade, Rank centered

        # Valign all cells to middle
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Zebra striping for student rows (using alternating rows)
        ('BACKGROUND', (0, 1), (-1, -3), colors.HexColor('#f2f7ff')),

        # Subject averages row styling
        ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#eaf2f8')),
        ('FONTNAME', (0, -2), (-1, -2), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -2), (1, -2), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, -2), (1, -2), colors.white),

        # Class average row styling
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d4efdf')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (1, -1), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, -1), (1, -1), colors.white),

        # Total column styling
        ('BACKGROUND', (-4, 1), (-4, -3), colors.HexColor('#eaf2f8')),
        ('FONTNAME', (-4, 1), (-4, -3), 'Helvetica-Bold'),

        # Average column styling
        ('TEXTCOLOR', (-3, 1), (-3, -3), colors.HexColor('#2980b9')),
        ('FONTNAME', (-3, 1), (-3, -3), 'Helvetica-Bold'),
    ]

    class_table.setStyle(TableStyle(table_style))
    content.append(class_table)
    content.append(Spacer(1, 0.25*inch))

    # Add performance summary section
    summary_title = Paragraph("Performance Summary", heading_style)
    content.append(summary_title)

    # Create a 2x2 grid for performance statistics
    stats_data = [
        [
            Paragraph(f"<font color='#155724'><b>EE1/EE2 (Exceeding Expectation, ≥75%):</b> {stats['exceeding']} learners</font>", normal_style),
            Paragraph(f"<font color='#004085'><b>ME1/ME2 (Meeting Expectation, 41-74%):</b> {stats['meeting']} learners</font>", normal_style)
        ],
        [
            Paragraph(f"<font color='#856404'><b>AE1/AE2 (Approaching Expectation, 21-40%):</b> {stats['approaching']} learners</font>", normal_style),
            Paragraph(f"<font color='#721c24'><b>BE1/BE2 (Below Expectation, &lt;21%):</b> {stats['below']} learners</font>", normal_style)
        ]
    ]

    stats_table = Table(stats_data, colWidths=[4*inch, 4*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#d4edda')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#cce5ff')),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#fff3cd')),
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#f8d7da')),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#c3e6cb')),
        ('BOX', (1, 0), (1, 0), 1, colors.HexColor('#b8daff')),
        ('BOX', (0, 1), (0, 1), 1, colors.HexColor('#ffeeba')),
        ('BOX', (1, 1), (1, 1), 1, colors.HexColor('#f5c6cb')),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    content.append(stats_table)
    content.append(Spacer(1, 0.25*inch))

    # Add signature section
    signature_data = [
        ["Class Teacher", "Deputy Head Teacher", "Head Teacher"],
        ["", "", ""],
        ["", "", ""]
    ]

    signature_table = Table(signature_data, colWidths=[2.8*inch, 2.8*inch, 2.8*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('LINEBELOW', (0, 1), (0, 1), 1, colors.black),
        ('LINEBELOW', (1, 1), (1, 1), 1, colors.black),
        ('LINEBELOW', (2, 1), (2, 1), 1, colors.black),
        ('TOPPADDING', (0, 1), (-1, 1), 30),
    ]))
    content.append(signature_table)

    # Add footer with dynamic school information
    current_date = datetime.now().strftime("%Y-%m-%d")
    # Debug: Check what school_info contains
    print(f"DEBUG FOOTER: school_info = {school_info}")
    school_name = school_info.get('school_name', 'School Name Not Set')
    footer_text = Paragraph(f"Generated on: {current_date}<br/>{school_name} | Powered by CbcTeachkit", subtitle_style)
    content.append(Spacer(1, 0.25*inch))
    content.append(footer_text)

    # Build the PDF
    doc.build(content)

    return pdf_path

def generate_individual_report_pdf_from_html(student, grade, stream, term, assessment_type, report_data, education_level=""):
    """
    Generate a PDF report for an individual student using HTML template.

    Args:
        student: The student object
        grade: The grade level
        stream: The class stream
        term: The term
        assessment_type: The assessment type
        report_data: Dictionary containing student report data
        education_level: The education level

    Returns:
        Path to the generated PDF file
    """
    try:
        # Import Flask's render_template_string function
        from flask import render_template_string

        # First, get the template content
        with open('new_structure/templates/preview_individual_report.html', 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Add print-specific CSS to the template
        print_css = """
        <style>
        @page {
            size: portrait;
            margin: 1cm;
        }
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        .action-buttons, .print-controls {
            display: none !important;
        }
        </style>
        """
        template_content = template_content.replace('</head>', f'{print_css}</head>')

        # Get current date for the report
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Get student marks
        student_marks = {}
        total = 0
        subject_count = 0

        # Find student data in the report data
        student_data = next((data for data in report_data.get("class_data", []) if data.get("student") == student.name), None)

        if not student_data:
            return None

        # Calculate mean grade and points
        avg_percentage = student_data.get("average_percentage", 0)
        from ..utils import get_grade_and_points
        mean_grade, mean_points = get_grade_and_points(avg_percentage)

        # Prepare table data for the report
        table_data = []
        for subject in report_data.get("subjects", []):
            mark = student_data.get("marks", {}).get(subject, 0)
            # For now, we'll use the same mark for all assessment types
            # In a real implementation, you'd get different marks for different assessment types
            table_data.append({
                "subject": subject,
                "entrance": mark,
                "mid_term": mark,
                "end_term": mark,
                "avg": mark,
                "remarks": get_performance_remarks(mark, report_data.get("total_marks", 100))
            })

        # Calculate total marks and points
        total_marks = student_data.get("total_marks", 0)
        total_possible_marks = len(report_data.get("subjects", [])) * report_data.get("total_marks", 100)
        total_points = mean_points * len(report_data.get("subjects", []))

        # Generate admission number if not available
        admission_no = student.admission_number if hasattr(student, 'admission_number') and student.admission_number else f"KPS{grade}{stream[-1]}{student.id}"

        # Get academic year
        from ..models import Term
        term_obj = Term.query.filter_by(name=term).first()
        academic_year = term_obj.academic_year if term_obj and hasattr(term_obj, 'academic_year') and term_obj.academic_year else "2023"

        # Get school information for dynamic display
        from ..services.school_config_service import SchoolConfigService
        school_info = SchoolConfigService.get_school_info_dict()

        # Render the template with the data
        html_content = render_template_string(
            template_content,
            student=student,
            student_data=student_data,
            grade=grade,
            stream=stream,
            term=term,
            assessment_type=assessment_type,
            education_level=education_level,
            current_date=current_date,
            table_data=table_data,
            total=total_marks,
            avg_percentage=avg_percentage,
            mean_grade=mean_grade,
            mean_points=mean_points,
            total_possible_marks=total_possible_marks,
            total_points=total_points,
            admission_no=admission_no,
            academic_year=academic_year,
            school_info=school_info  # Include school information
        )

        # Generate PDF from HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"individual_report_{student.name}_{grade}_{stream}_{term}_{assessment_type}_{timestamp}.pdf"

        # Create a temporary file
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, filename)

        # Configure pdfkit options for better formatting
        options = {
            'page-size': 'A4',
            'orientation': 'Portrait',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': True,  # Enable local file access for images
            'print-media-type': None
        }

        # Convert HTML to PDF
        import pdfkit
        pdfkit.from_string(html_content, pdf_path, options=options)

        return pdf_path
    except Exception as e:
        print(f"Error generating individual PDF from HTML: {str(e)}")
        return None

def get_performance_remarks(mark, total_marks=100):
    """Generate performance remarks based on marks."""
    percentage = (mark / total_marks) * 100 if total_marks > 0 else 0

    if percentage >= 90:
        return "EE1"  # Exceeding Expectation 1
    elif percentage >= 75:
        return "EE2"  # Exceeding Expectation 2
    elif percentage >= 58:
        return "ME1"  # Meeting Expectation 1
    elif percentage >= 41:
        return "ME2"  # Meeting Expectation 2
    elif percentage >= 31:
        return "AE1"  # Approaching Expectation 1
    elif percentage >= 21:
        return "AE2"  # Approaching Expectation 2
    elif percentage >= 11:
        return "BE1"  # Below Expectation 1
    else:
        return "BE2"  # Below Expectation 2

def generate_individual_report(student, grade, stream, term, assessment_type, education_level=""):
    """
    Generate an individual student report.

    Args:
        student: The student object
        grade: The grade level
        stream: The class stream
        term: The term
        assessment_type: The assessment type
        education_level: The education level

    Returns:
        Path to the generated PDF file or error message
    """
    # Get class data
    class_data_result = get_class_report_data(grade, stream, term, assessment_type)

    if class_data_result.get("error"):
        return {"error": class_data_result["error"]}

    class_data = class_data_result["class_data"]
    subjects = class_data_result["subjects"]
    total_marks = class_data_result["total_marks"]

    # Create a temporary file
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(temp_dir, f"individual_report_{student.name}_{grade}_{stream}_{term}_{assessment_type}_{timestamp}.pdf")

    # Create the PDF document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading1"]
    subheading_style = styles["Heading2"]
    normal_style = styles["Normal"]

    # Create content
    content = []

    # Add title
    title = Paragraph(f"Student Report Card", title_style)
    content.append(title)
    content.append(Spacer(1, 0.25*inch))

    # Add student information
    student_info = [
        ["Student Name:", student.name],
        ["Admission Number:", student.admission_number],
        ["Grade:", grade],
        ["Stream:", stream],
        ["Term:", term],
        ["Assessment:", assessment_type],
        ["Date:", datetime.now().strftime('%Y-%m-%d')]
    ]

    info_table = Table(student_info, colWidths=[1.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    content.append(info_table)
    content.append(Spacer(1, 0.25*inch))

    # Find student's marks
    student_data = None
    for data in class_data:
        if data["student"] == student.name:
            student_data = data
            break

    if not student_data:
        # Create a simple PDF with error message
        error_text = Paragraph(f"No marks found for student {student.name}", normal_style)
        content.append(error_text)
        doc.build(content)
        return pdf_path

    # Add marks table
    marks_heading = Paragraph("Academic Performance", heading_style)
    content.append(marks_heading)
    content.append(Spacer(1, 0.1*inch))

    marks_data = [["Subject", "Marks", "Out of", "Percentage", "Grade", "Remarks"]]

    for subject in subjects:
        mark = student_data["marks"].get(subject, 0)
        percentage = (mark / total_marks) * 100 if total_marks > 0 else 0
        grade_letter, points = get_grade_and_points(percentage)
        performance = get_performance_category(percentage)

        marks_data.append([
            subject,
            mark,
            total_marks,
            f"{percentage:.1f}%",
            grade_letter,
            performance
        ])

    # Add total row
    total_percentage = student_data["average_percentage"]
    total_grade, total_points = get_grade_and_points(total_percentage)
    total_performance = get_performance_category(total_percentage)

    marks_data.append([
        "TOTAL",
        student_data["total_marks"],
        total_marks * len(subjects),
        f"{total_percentage:.1f}%",
        total_grade,
        total_performance
    ])

    marks_table = Table(marks_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 1*inch, 0.8*inch, 1.5*inch])
    marks_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Total row background
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Total row bold
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (4, -1), 'CENTER'),  # Center numeric columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    content.append(marks_table)
    content.append(Spacer(1, 0.25*inch))

    # Add class position
    position_heading = Paragraph("Class Position", subheading_style)
    content.append(position_heading)
    content.append(Spacer(1, 0.1*inch))

    position = student_data.get("rank", "N/A")
    out_of = len(class_data)

    position_text = Paragraph(f"Position: {position} out of {out_of}", normal_style)
    content.append(position_text)
    content.append(Spacer(1, 0.25*inch))

    # Add signature section
    signature_data = [
        ["Class Teacher's Signature", "Date", "Principal's Signature", "Date"],
        ["_________________", "________", "_________________", "________"]
    ]

    signature_table = Table(signature_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('LINEBELOW', (0, 1), (0, 1), 1, colors.black),
        ('LINEBELOW', (2, 1), (2, 1), 1, colors.black),
        ('LINEBELOW', (1, 1), (1, 1), 1, colors.black),
        ('LINEBELOW', (3, 1), (3, 1), 1, colors.black),
    ]))
    content.append(signature_table)

    # Build the PDF
    doc.build(content)

    return pdf_path