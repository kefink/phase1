from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from reportlab.lib.pagesizes import letter, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

app = Flask(__name__)

# Hardcoded users for demo (teacher1, headteacher)
users = {"teacher1": "pass123", "headteacher": "admin123"}

# Embedded student data for MVP (Grades 1-9)
students_data = {
    "1": {
        "B": [f"Student {i} Grade 1B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 1G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 1Y" for i in range(1, 16)],
    },
    # ... (other grades follow the same structure up to grade 9)
    "9": {
        "B": [
            "ABIGAEL GAKENIA RWAMBA", "ADAU GAI ALONY", "ALLAN CHEGE NJOROGE", "ALPHA ALBERT MUIA",
            "ANGEL MAKENA KARIUKI", "ANGEL WANGECHI WAMBUI", "ANGELA MUTHONI WANGUI", "ANTONIETT NYAKIO MACHARIA",
            "ANTONY KARIA WANJOHI", "ASHLEY AMING'A GECHANGA", "BARNABAS MASAU MUTHOKA", "CELINE KENDI MURIITHI",
            "CHRIS KINYANJUI NJOROGE", "DAVID MUUWO MUSEMBI", "ETHAN ANDERSON NJOROGE"
        ],
        "G": [
            "ADIEL MUREITHI MURIUKI", "ADRIEL WANJIRU THEURI", "ALEX MWARIA KINYINGI", "ALVIN MACHARIA GITAU",
            "ANSELM CHEGE MUTURI", "BLESSING MIRELL GITHU", "BRIANAH NJERI WANGARI", "CHRISPIN GIVEN WACHIRA",
            "CORRINE JERONO MARIGAT", "DAK DUT PAL", "ELAINE EASTER NJOKI GICHUKI", "EUGENE MUGUCHU KIPKOECH L",
            "FARHAT ASANTE KITUMBIKA", "HOPEWELL SHILLOH MAPAYA", "JABARI MWACHONGO"
        ],
        "Y": [
            "AARON KIWELU GIFORO", "ADRIAN KIVUVA KIOKO", "ALEXANDER RANJA MBUTHIA", "AMUOR MANGAR MARIAL",
            "ANGEL HAWI ODHIAMBO", "ANGELA KINYA .", "ANNITA NYAWIRA MUNENE", "BRIGHT BUYANZI BARASA",
            "DELVINE WARWARE BARIMBUI", "DENNIS KARIUKI NDUNGU", "EILEEN JEBET MUKABI", "ETHAN MURIITHI GIKUNGU",
            "GEORGE GITAU MACHOYA", "IAN HUNJA NJERI", "IBRAHIM MWADIME MSHILA"
        ]
    }
}

# Store submitted marks and report data globally
report_data = {}

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username] == password:
            if username == "headteacher":
                return redirect(url_for("headteacher"))
            return "Invalid credentials for Admin"
        return "Invalid credentials"
    return render_template("admin_login.html")

@app.route("/teacher_login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username] == password:
            if username == "teacher1":
                return redirect(url_for("teacher"))
            return "Invalid credentials for Teacher"
        return "Invalid credentials"
    return render_template("teacher_login.html")

@app.route("/teacher", methods=["GET", "POST"])
def teacher():
    grades = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    if request.method == "POST":
        if "upload_marks" in request.form:
            education_level = request.form.get("education_level")
            subject = request.form.get("subject")
            grade = request.form.get("grade")
            stream = request.form.get("stream")
            term = request.form.get("term")
            assessment_type = request.form.get("assessment_type")
            total_marks = int(request.form.get("total_marks", 0))
            stream_letter = stream[-1] if stream else ''
            students = students_data.get(grade, {}).get(stream_letter, [])
            return render_template(
                "teacher.html",
                grades=grades,
                students=students,
                education_level=education_level,
                subject=subject,
                grade=grade,
                stream=stream,
                term=term,
                assessment_type=assessment_type,
                total_marks=total_marks,
                show_students=True
            )
        elif "submit_marks" in request.form:
            education_level = request.form.get("education_level")
            subject = request.form.get("subject")
            grade = request.form.get("grade")
            stream = request.form.get("stream")
            term = request.form.get("term")
            assessment_type = request.form.get("assessment_type")
            total_marks = int(request.form.get("total_marks", 0))
            marks_data = []
            stream_letter = stream[-1] if stream else ''
            students = students_data.get(grade, {}).get(stream_letter, [])
            for student in students:
                mark_key = f"mark_{student.replace(' ', '_')}"
                mark = request.form.get(mark_key, 0)
                if mark and str(mark).isdigit():
                    marks_data.append([student, int(mark)])
            mean_score = sum(mark[1] for mark in marks_data) / len(marks_data) if marks_data else 0
            global report_data
            report_data = {
                "marks_data": marks_data,
                "mean_score": mean_score,
                "education_level": education_level,
                "subject": subject,
                "grade": grade,
                "stream": stream,
                "term": term,
                "assessment_type": assessment_type,
                "total_marks": total_marks
            }
            return render_template(
                "report.html",
                data=marks_data,
                mean_score=mean_score,
                education_level=education_level,
                subject=subject,
                grade=grade,
                stream=stream,
                term=term,
                assessment_type=assessment_type,
                total_marks=total_marks
            )
    return render_template("teacher.html", grades=grades, show_students=False)

@app.route("/get_students/<grade>/<stream_letter>")
def get_students(grade, stream_letter):
    """Return a JSON list of students for the specified grade and stream."""
    students = students_data.get(grade, {}).get(stream_letter, [])
    return {"students": students}

@app.route("/test_students/<grade>/<stream_letter>")
def test_students(grade, stream_letter):
    students = students_data.get(grade, {}).get(stream_letter, [])
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"students": students}
        
    return render_template(
        "teacher.html",
        grades=["1", "2", "3", "4", "5", "6", "7", "8", "9"],
        students=students,
        education_level="test",
        subject="test",
        grade=grade,
        stream=f"{grade}{stream_letter}",
        term="test",
        assessment_type="test",
        total_marks=100,
        show_students=True
    )

@app.route("/headteacher")
def headteacher():
    dashboard_data = [
        {"grade": "8B", "mean": 65},
        {"grade": "8G", "mean": 70},
    ]
    return render_template("headteacher.html", data=dashboard_data)

@app.route("/generate_pdf/<grade>/<stream>")
def generate_pdf(grade, stream):
    # Check if we have data for this report
    if not report_data or report_data.get("grade") != grade or report_data.get("stream") != stream:
        return "No data available for this report. Please submit marks first.", 404
    
    pdf_file = f"report_{grade}_{stream}.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    elements = []
    
    # Get styles for text formatting
    styles = getSampleStyleSheet()
    
    # Create consistent styles
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center alignment
    
    subtitle_style = styles['Heading2']
    subtitle_style.alignment = 1  # Center alignment
    
    normal_style = styles['Normal']
    
    # Create a custom footer style
    footer_style = ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        alignment=1,  # Center alignment
        fontName='Helvetica-Bold',
        fontSize=10,
        spaceAfter=0,
        textColor=colors.darkblue
    )
    
    # Extract data from report_data
    marks_data = report_data.get("marks_data", [])
    mean_score = report_data.get("mean_score", 0)
    education_level = report_data.get("education_level", "")
    subject = report_data.get("subject", "")
    term = report_data.get("term", "")
    assessment_type = report_data.get("assessment_type", "")
    total_marks = report_data.get("total_marks", 0)
    
    # Add title and school information
    elements.append(Paragraph("HILL VIEW SCHOOL", title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Grade {grade} Stream {stream} - {subject} Report", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Add metadata with consistent formatting
    metadata = [
        f"<b>Education Level:</b> {education_level.replace('_', ' ').title()}",
        f"<b>Term:</b> {term.replace('_', ' ').title()}",
        f"<b>Assessment Type:</b> {assessment_type.replace('_', ' ').title()}",
        f"<b>Total Marks:</b> {total_marks}",
        f"<b>Mean Score:</b> {mean_score:.2f}"
    ]
    
    for item in metadata:
        elements.append(Paragraph(item, normal_style))
        elements.append(Spacer(1, 6))
    
    elements.append(Spacer(1, 12))
    
    # Create table with student data - ensure consistent structure
    if marks_data:
        data = [["Student Name", "Marks"]]
        data.extend(marks_data)
        
        # Create table with fixed column widths for consistency
        table = Table(data, colWidths=[4*inch, 1.5*inch])
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),  # Center align marks column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertically center all content
        ]))
        
        elements.append(table)
    else:
        elements.append(Paragraph("No student data available", normal_style))
    
    # Add spacer before footer
    elements.append(Spacer(1, 30))
    
    # Add the required footer
    elements.append(Paragraph("Hillview school powered by CbcTeachkit", footer_style))
    
    # Build the PDF with consistent styling
    doc.build(elements)
    
    return send_file(pdf_file, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)