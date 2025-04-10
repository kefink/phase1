from flask import Flask, render_template, request, redirect, url_for, send_file
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
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
    "2": {
        "B": [f"Student {i} Grade 2B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 2G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 2Y" for i in range(1, 16)],
    },
    "3": {
        "B": [f"Student {i} Grade 3B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 3G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 3Y" for i in range(1, 16)],
    },
    "4": {
        "B": [f"Student {i} Grade 4B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 4G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 4Y" for i in range(1, 16)],
    },
    "5": {
        "B": [f"Student {i} Grade 5B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 5G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 5Y" for i in range(1, 16)],
    },
    "6": {
        "B": [f"Student {i} Grade 6B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 6G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 6Y" for i in range(1, 16)],
    },
    "7": {
        "B": [f"Student {i} Grade 7B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 7G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 7Y" for i in range(1, 16)],
    },
    "8": {
        "B": [
            "ALVIN BLESSED .", "ALVIN NGANGA WANJIKU", "AMARA SAU MGHANGA", "CASEY RAPHAELA OWUOR",
            "CECILINE MBOO KANURI", "CELLINE MUTHONI GITHIEYA", "CLAIRE NJERI GIKONYO", "DIDUMO OJUAK OKELLO",
            "ETHAN MWANGI KINYUA", "FAITH WANGECHI KAGIRI", "GIBSON NGARI MUNENE", "GOY PETER MAJOK",
            "HARVEY MUGO MACHARIA", "JAMILA KANIRI NTOITI", "JAYDEN NJAGI MUNGA"
        ],
        "G": [
            "BRIDGETTE WAIRIMU MUTONGA", "BRYTON KOSGEI KISANG", "CALEB MUTIE MUTEMI", "CASTROL CHERUIYOT KORIR",
            "DELANE MAKORI MOREMA", "FAITH WANGARI WAMBUGU", "FAITH WANJIKU KINYUA", "FRANKLIN MURIUKI MWANGI",
            "HABIB MUMO MWENDWA", "IVY WAMBUI GICHOBI", "JAMES MATHINA GITHUA", "JAYDEN KIMATHI KOOME",
            "JOY GILGER KENDI NYAGA", "KRISTA KENDI MURIITHI", "LUCY WANJIRU NDUNGU"
        ],
        "Y": [
            "ABBY TATYANA MUKABI", "ADRIAN MBAU MWANGI", "ALISHA WANJIKU NJUBI", "ALVIN NDORO WAIRAGU",
            "ALVIN OWEIN MBUGUA", "ANGELA NYAKIO MUNENE", "ASHLYN WAYUA JULIA", "BAKHITA WANGECHI GACHOKA",
            "BIANCA WAMBUI NJERI", "BIANKA ANON MULUAL", "CARL KINYUA IKE", "CHERISE NJOKI WAIRAGU",
            "CHRISTINE WANGECHI MAINA", "CHRISTINE WANJA NJERU", "DANIELLA NYAMBURA MWANGI"
        ]
    },
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
        # Add debugging
        print("POST request received")
        print("Form data:", request.form)

        # Check if this is the initial form submission
        if "upload_marks" in request.form:
            print("Processing upload_marks submission")
            education_level = request.form.get("education_level")
            subject = request.form.get("subject")
            grade = request.form.get("grade")
            stream = request.form.get("stream")
            term = request.form.get("term")
            assessment_type = request.form.get("assessment_type")
            total_marks = int(request.form.get("total_marks", 0))

            print(f"Selected grade: {grade}, stream: {stream}")

            # Extract stream letter (e.g., "9G" -> "G")
            stream_letter = stream[-1] if stream else ''
            print(f"Stream letter: {stream_letter}")

            # Get students for selected grade and stream
            students = students_data.get(grade, {}).get(stream_letter, [])
            print(f"Found {len(students)} students")

            # DEBUG: Print first few students to verify data
            if students:
                print("Sample students:", students[:3])

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
                show_students=True  # Make sure this is True!
            )

        # The rest of your function remains the same
        elif "submit_marks" in request.form:
            # Process marks submission
            education_level = request.form.get("education_level")
            subject = request.form.get("subject")
            grade = request.form.get("grade")
            stream = request.form.get("stream")
            term = request.form.get("term")
            assessment_type = request.form.get("assessment_type")
            total_marks = int(request.form.get("total_marks", 0))

            # Process marks for each student
            marks_data = []
            stream_letter = stream[-1] if stream else ''
            students = students_data.get(grade, {}).get(stream_letter, [])

            for student in students:
                mark_key = f"mark_{student.replace(' ', '_')}"
                mark = request.form.get(mark_key, 0)
                if mark and str(mark).isdigit():
                    marks_data.append([student, int(mark)])

            # Calculate mean score
            mean_score = sum(mark[1] for mark in marks_data) / len(marks_data) if marks_data else 0

            # Store marks and metadata for report generation
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

    # Add a diagnostic test route
    return render_template("teacher.html", grades=grades, show_students=False)

# Add this diagnostic route
@app.route("/test_students/<grade>/<stream_letter>")
def test_students(grade, stream_letter):
    students = students_data.get(grade, {}).get(stream_letter, [])
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
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Extract data from report_data
    marks_data = report_data.get("marks_data", [])
    mean_score = report_data.get("mean_score", 0)
    education_level = report_data.get("education_level", "")
    subject = report_data.get("subject", "")
    term = report_data.get("term", "")
    assessment_type = report_data.get("assessment_type", "")
    total_marks = report_data.get("total_marks", 0)
    
    # Add title and school information
    elements.append(Paragraph("Hill View School", title_style))
    elements.append(Paragraph(f"Grade {grade} Stream {stream} - {subject} Report", subtitle_style))
    elements.append(Spacer(1, 12))
    
    # Add metadata
    elements.append(Paragraph(f"Education Level: {education_level}", normal_style))
    elements.append(Paragraph(f"Term: {term}", normal_style))
    elements.append(Paragraph(f"Assessment Type: {assessment_type}", normal_style))
    elements.append(Paragraph(f"Total Marks: {total_marks}", normal_style))
    elements.append(Paragraph(f"Mean Score: {mean_score:.2f}", normal_style))
    elements.append(Spacer(1, 24))
    
    # Create table with student data
    data = [["Student Name", "Marks"]] + marks_data
    table = Table(data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)
    return send_file(pdf_file, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)