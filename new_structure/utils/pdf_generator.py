"""
PDF generation utilities for the Hillview School Management System.
"""
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime

from ..utils.performance import get_performance_category, get_grade_and_points

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