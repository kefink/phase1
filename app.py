from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

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

# Store submitted marks and report data per grade+stream+subject
reports_data = {}

# Map education level codes to display names
education_level_names = {
    "lower_primary": "Lower Primary",
    "upper_primary": "Upper Primary",
    "junior_secondary": "Junior Secondary"
}

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
                session['username'] = username
                session['role'] = 'headteacher'
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
                session['username'] = username
                session['role'] = 'teacher'
                return redirect(url_for("teacher"))
            return "Invalid credentials for Teacher"
        return "Invalid credentials"
    return render_template("teacher_login.html")

@app.route("/teacher", methods=["GET", "POST"])
def teacher():
    # Check if user is logged in
    if 'username' not in session or session['role'] != 'teacher':
        return redirect(url_for('teacher_login'))

    grades = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    error_message = None
    show_students = False
    students = []
    education_level = ""
    subject = ""
    grade = ""
    stream = ""
    term = ""
    assessment_type = ""
    total_marks = 0
    show_download_button = False
    report_key = None

    if request.method == "POST":
        # Add detailed debugging
        print("\n=== TEACHER ROUTE - POST REQUEST ===")
        print("Form data received:", request.form)

        # Get common form data for both submission types
        education_level = request.form.get("education_level", "")
        subject = request.form.get("subject", "")
        grade = request.form.get("grade", "")
        stream = request.form.get("stream", "")
        term = request.form.get("term", "")
        assessment_type = request.form.get("assessment_type", "")
        try:
            total_marks = int(request.form.get("total_marks", 0))
        except ValueError:
            total_marks = 0

        # Check if this is the initial form submission
        if "upload_marks" in request.form:
            print("Processing upload_marks submission")

            # Validate all required fields are present
            if not all([education_level, subject, grade, stream, term, assessment_type, total_marks > 0]):
                error_message = "Please fill in all fields before uploading marks"
                print(f"ERROR: {error_message}")
            else:
                print(f"Selected grade: {grade}, stream: {stream}")

                # Extract stream letter (e.g., "9G" -> "G")
                if stream and len(stream) > 0:
                    stream_letter = stream[-1]  # Get the last character (the letter)
                    print(f"Stream letter extracted: {stream_letter}")

                    # Get students for selected grade and stream
                    if grade in students_data and stream_letter in students_data[grade]:
                        students = students_data[grade][stream_letter]
                        show_students = True
                        print(f"Found {len(students)} students")
                    else:
                        error_message = f"No students found for grade {grade} stream {stream_letter}"
                        print(f"WARNING: {error_message}")
                        students = []
                else:
                    error_message = "Please select a valid stream"
                    print(f"ERROR: {error_message}")

        elif "submit_marks" in request.form:
            # Process marks submission
            print("Processing submit_marks submission")

            # Validate all required fields are present
            if not all([education_level, subject, grade, stream, term, assessment_type, total_marks > 0]):
                error_message = "Please fill in all fields before submitting marks"
                print(f"ERROR: {error_message}")
            else:
                # Process marks for each student
                marks_data = []
                stream_letter = stream[-1] if stream else ''

                if grade in students_data and stream_letter in students_data[grade]:
                    students = students_data[grade][stream_letter]

                    # Check if any marks were submitted
                    any_marks_submitted = False

                    for student in students:
                        mark_key = f"mark_{student.replace(' ', '_')}"
                        mark_value = request.form.get(mark_key, '')

                        # Validate mark input
                        if mark_value and mark_value.isdigit():
                            mark = int(mark_value)
                            if 0 <= mark <= total_marks:
                                # Calculate percentage
                                percentage = (mark / total_marks) * 100
                                # Store both raw mark and percentage
                                marks_data.append([student, mark, round(percentage, 1)])
                                any_marks_submitted = True
                            else:
                                error_message = f"Invalid mark for {student}. Must be between 0 and {total_marks}."
                                break
                        else:
                            error_message = f"Missing or invalid mark for {student}"
                            break

                    if any_marks_submitted and not error_message:
                        # Calculate mean score
                        mean_score = sum(mark[1] for mark in marks_data) / len(marks_data) if marks_data else 0
                        mean_percentage = (mean_score / total_marks) * 100 if total_marks > 0 else 0

                        # Create a unique key for this report that includes the subject
                        report_key = f"{grade}_{stream_letter}_{subject.replace(' ', '_')}"

                        # Store report data using the unique key
                        reports_data[report_key] = {
                            "marks_data": marks_data,  # Now includes [student, mark, percentage]
                            "mean_score": mean_score,
                            "mean_percentage": mean_percentage,
                            "education_level": education_level,
                            "education_level_display": education_level_names.get(education_level, education_level),
                            "subject": subject,
                            "grade": grade,
                            "stream": stream,
                            "term": term,
                            "assessment_type": assessment_type,
                            "total_marks": total_marks,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                        # Debug report data to ensure it's being stored correctly
                        print(f"Stored report_data with key {report_key}:", reports_data[report_key])

                        # Redirect to report view with proper parameters
                        return render_template(
                            "report.html",
                            data=marks_data,
                            mean_score=mean_score,
                            mean_percentage=mean_percentage,
                            education_level=education_level_names.get(education_level, education_level),
                            subject=subject,
                            grade=grade,
                            stream=stream,
                            term=term,
                            assessment_type=assessment_type,
                            total_marks=total_marks
                        )
                else:
                    error_message = f"Could not find students for grade {grade} stream {stream_letter}"

    # Show download button only if report data exists for this grade/stream/subject
    if grade and stream and subject and len(stream) > 0:
        stream_letter = stream[-1]
        report_key = f"{grade}_{stream_letter}_{subject.replace(' ', '_')}"
        show_download_button = report_key in reports_data

    # Default rendering for both GET requests and unsuccessful POST requests
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
        show_students=show_students,
        error_message=error_message,
        show_download_button=show_download_button
    )

@app.route("/headteacher")
def headteacher():
    # Check if user is logged in
    if 'username' not in session or session['role'] != 'headteacher':
        return redirect(url_for('admin_login'))

    dashboard_data = [
        {"grade": "8B", "mean": 65},
        {"grade": "8G", "mean": 70},
    ]
    return render_template("headteacher.html", data=dashboard_data)

@app.route("/generate_pdf/<grade>/<stream>/<subject>")
def generate_pdf(grade, stream, subject):
    # Extract stream letter (e.g., "9G" -> "G")
    stream_letter = stream[-1] if stream else ''
    # Include subject in the key
    report_key = f"{grade}_{stream_letter}_{subject.replace(' ', '_')}"
    
    # Check if we have data for this report
    if report_key not in reports_data:
        return "No data available for this report. Please submit marks first.", 404

    # Get the report data for this grade/stream/subject
    report_data = reports_data[report_key]
    
    pdf_file = f"report_{grade}_{stream}_{subject.replace(' ', '_')}.pdf"
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
    mean_percentage = report_data.get("mean_percentage", 0)
    education_level = report_data.get("education_level_display", "")
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
    elements.append(Paragraph(f"Mean Score: {mean_score:.2f} ({mean_percentage:.1f}%)", normal_style))
    elements.append(Spacer(1, 24))

    # Create table with student data
    data = [["Student Name", "Marks", "Percentage (%)"]]
    for student_record in marks_data:
        data.append([student_record[0], student_record[1], f"{student_record[2]}%"])
    
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

    # Add custom footer
    elements.append(Spacer(1, 20))
    footer_style = styles['Normal']
    footer_style.alignment = 1  # Center alignment
    elements.append(Paragraph("Hillview School powered by CbcTeachkit", footer_style))

    doc.build(elements)
    return send_file(pdf_file, as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)