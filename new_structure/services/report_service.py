"""
Report generation services for the Hillview School Management System.
"""
from ..models import Student, Mark, Subject, Stream, Grade, Term, AssessmentType
from ..utils import get_performance_category, get_grade_and_points, generate_individual_report_pdf
from collections import defaultdict
import os
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def get_class_report_data(grade, stream, term, assessment_type):
    """
    Get data for a class report.

    Args:
        grade: The grade level
        stream: The class stream
        term: The term
        assessment_type: The assessment type

    Returns:
        Dictionary containing class report data
    """
    # Get the stream object
    stream_letter = stream[-1] if stream.startswith("Stream ") else stream[-1]
    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream_letter).first()

    if not stream_obj:
        return {"error": f"No students found for grade {grade} stream {stream_letter}"}

    # Get the term and assessment type objects
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (term_obj and assessment_type_obj):
        return {"error": "Invalid selection for term or assessment type"}

    # Get the students in the stream
    students = Student.query.filter_by(stream_id=stream_obj.id).all()

    # Get all subjects
    subjects = Subject.query.all()

    # Prepare class data
    class_data = []
    total_marks = 0

    for student in students:
        student_marks = {}
        for subject in subjects:
            mark = Mark.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                term_id=term_obj.id,
                assessment_type_id=assessment_type_obj.id
            ).first()
            student_marks[subject.name] = mark.mark if mark else 0
            if mark:
                total_marks = mark.total_marks

        total = sum(student_marks.values())
        avg_percentage = (total / (len(subjects) * total_marks)) * 100 if total_marks > 0 else 0

        class_data.append({
            'student': student.name,
            'marks': student_marks,
            'total_marks': total,
            'average_percentage': avg_percentage
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
        elif 50 <= avg < 75:
            stats['meeting'] += 1
        elif 30 <= avg < 50:
            stats['approaching'] += 1
        else:
            stats['below'] += 1

    return {
        "class_data": class_data,
        "stats": stats,
        "subjects": [subject.name for subject in subjects],
        "total_marks": total_marks,
        "error": None
    }

def generate_class_report_pdf(grade, stream, term, assessment_type, class_data, stats, total_marks, subjects):
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

    Returns:
        Path to the generated PDF file
    """
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
    title_style = styles["Title"]
    heading_style = styles["Heading1"]
    normal_style = styles["Normal"]

    # Create content
    content = []

    # Add title
    title = Paragraph(f"Class Report: {grade} {stream} - {term} {assessment_type}", title_style)
    content.append(title)
    content.append(Spacer(1, 0.25*inch))

    # Add date
    date_text = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style)
    content.append(date_text)
    content.append(Spacer(1, 0.25*inch))

    # Add statistics
    stats_heading = Paragraph("Performance Statistics", heading_style)
    content.append(stats_heading)
    content.append(Spacer(1, 0.1*inch))

    stats_data = [
        ["Performance Level", "Number of Students", "Percentage"],
        ["Exceeding Expectations (75-100%)", stats["exceeding"], f"{stats['exceeding']/len(class_data)*100:.1f}%" if class_data else "0%"],
        ["Meeting Expectations (50-74%)", stats["meeting"], f"{stats['meeting']/len(class_data)*100:.1f}%" if class_data else "0%"],
        ["Approaching Expectations (30-49%)", stats["approaching"], f"{stats['approaching']/len(class_data)*100:.1f}%" if class_data else "0%"],
        ["Below Expectations (0-29%)", stats["below"], f"{stats['below']/len(class_data)*100:.1f}%" if class_data else "0%"],
        ["Total", len(class_data), "100%"]
    ]

    stats_table = Table(stats_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    content.append(stats_table)
    content.append(Spacer(1, 0.25*inch))

    # Add class data
    class_heading = Paragraph("Student Performance", heading_style)
    content.append(class_heading)
    content.append(Spacer(1, 0.1*inch))

    # Prepare table data
    table_data = [["Rank", "Student Name"] + subjects + ["Total", "Average", "Performance"]]

    for student in class_data:
        row = [
            student.get("rank", ""),
            student.get("student", "")
        ]

        for subject in subjects:
            row.append(student.get("marks", {}).get(subject, ""))

        row.append(student.get("total_marks", ""))
        row.append(f"{student.get('average_percentage', 0):.1f}%")

        avg = student.get('average_percentage', 0)
        performance = "Exceeding" if avg >= 75 else "Meeting" if avg >= 50 else "Approaching" if avg >= 30 else "Below"
        row.append(performance)

        table_data.append(row)

    # Create the table
    col_widths = [0.5*inch, 2*inch] + [0.8*inch] * len(subjects) + [0.8*inch, 0.8*inch, 1*inch]
    class_table = Table(table_data, colWidths=col_widths)

    # Style the table
    class_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Rank column centered
        ('ALIGN', (2, 1), (-3, -1), 'CENTER'),  # Subject marks centered
        ('ALIGN', (-2, 1), (-2, -1), 'CENTER'),  # Average column centered
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    content.append(class_table)

    # Build the PDF
    doc.build(content)

    return pdf_path

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