from flask import Flask, render_template, request, redirect, url_for, send_file, session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# User credentials
users = {
    "teacher1": "pass123",
    "headteacher": "admin123"
}

# Complete student data for all grades
students_data = {
    "1": {
        "B": [f"Student {i} Grade 1B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 1G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 1Y" for i in range(1, 16)]
    },
    "2": {
        "B": [f"Student {i} Grade 2B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 2G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 2Y" for i in range(1, 16)]
    },
    "3": {
        "B": [f"Student {i} Grade 3B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 3G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 3Y" for i in range(1, 16)]
    },
    "4": {
        "B": [f"Student {i} Grade 4B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 4G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 4Y" for i in range(1, 16)]
    },
    "5": {
        "B": [f"Student {i} Grade 5B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 5G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 5Y" for i in range(1, 16)]
    },
    "6": {
        "B": [f"Student {i} Grade 6B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 6G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 6Y" for i in range(1, 16)]
    },
    "7": {
        "B": [f"Student {i} Grade 7B" for i in range(1, 16)],
        "G": [f"Student {i} Grade 7G" for i in range(1, 16)],
        "Y": [f"Student {i} Grade 7Y" for i in range(1, 16)]
    },
    "8": {
        "B": [
            "ALVIN BLESSED .", "ALVIN NGANGA WANJIKU", "AMARA SAU MGHANGA", 
            "CASEY RAPHAELA OWUOR", "CECILINE MBOO KANURI", 
            "CELLINE MUTHONI GITHIEYA", "CLAIRE NJERI GIKONYO", 
            "DIDUMO OJUAK OKELLO", "ETHAN MWANGI KINYUA", 
            "FAITH WANGECHI KAGIRI", "GIBSON NGARI MUNENE", 
            "GOY PETER MAJOK", "HARVEY MUGO MACHARIA", 
            "JAMILA KANIRI NTOITI", "JAYDEN NJAGI MUNGA"
        ],
        "G": [
            "BRIDGETTE WAIRIMU MUTONGA", "BRYTON KOSGEI KISANG", 
            "CALEB MUTIE MUTEMI", "CASTROL CHERUIYOT KORIR", 
            "DELANE MAKORI MOREMA", "FAITH WANGARI WAMBUGU", 
            "FAITH WANJIKU KINYUA", "FRANKLIN MURIUKI MWANGI", 
            "HABIB MUMO MWENDWA", "IVY WAMBUI GICHOBI", 
            "JAMES MATHINA GITHUA", "JAYDEN KIMATHI KOOME", 
            "JOY GILGER KENDI NYAGA", "KRISTA KENDI MURIITHI", 
            "LUCY WANJIRU NDUNGU"
        ],
        "Y": [
            "ABBY TATYANA MUKABI", "ADRIAN MBAU MWANGI", 
            "ALISHA WANJIKU NJUBI", "ALVIN NDORO WAIRAGU", 
            "ALVIN OWEIN MBUGUA", "ANGELA NYAKIO MUNENE", 
            "ASHLYN WAYUA JULIA", "BAKHITA WANGECHI GACHOKA", 
            "BIANCA WAMBUI NJERI", "BIANKA ANON MULUAL", 
            "CARL KINYUA IKE", "CHERISE NJOKI WAIRAGU", 
            "CHRISTINE WANGECHI MAINA", "CHRISTINE WANJA NJERU", 
            "DANIELLA NYAMBURA MWANGI"
        ]
    },
    "9": {
        "B": [
            "ABIGAEL GAKENIA RWAMBA", "ADAU GAI ALONY", 
            "ALLAN CHEGE NJOROGE", "ALPHA ALBERT MUIA", 
            "ANGEL MAKENA KARIUKI", "ANGEL WANGECHI WAMBUI", 
            "ANGELA MUTHONI WANGUI", "ANTONIETT NYAKIO MACHARIA", 
            "ANTONY KARIA WANJOHI", "ASHLEY AMING'A GECHANGA", 
            "BARNABAS MASAU MUTHOKA", "CELINE KENDI MURIITHI", 
            "CHRIS KINYANJUI NJOROGE", "DAVID MUUWO MUSEMBI", 
            "ETHAN ANDERSON NJOROGE"
        ],
        "G": [
            "ADIEL MUREITHI MURIUKI", "ADRIEL WANJIRU THEURI", 
            "ALEX MWARIA KINYINGI", "ALVIN MACHARIA GITAU", 
            "ANSELM CHEGE MUTURI", "BLESSING MIRELL GITHU", 
            "BRIANAH NJERI WANGARI", "CHRISPIN GIVEN WACHIRA", 
            "CORRINE JERONO MARIGAT", "DAK DUT PAL", 
            "ELAINE EASTER NJOKI GICHUKI", "EUGENE MUGUCHU KIPKOECH L", 
            "FARHAT ASANTE KITUMBIKA", "HOPEWELL SHILLOH MAPAYA", 
            "JABARI MWACHONGO"
        ],
        "Y": [
            "AARON KIWELU GIFORO", "ADRIAN KIVUVA KIOKO", 
            "ALEXANDER RANJA MBUTHIA", "AMUOR MANGAR MARIAL", 
            "ANGEL HAWI ODHIAMBO", "ANGELA KINYA .", 
            "ANNITA NYAWIRA MUNENE", "BRIGHT BUYANZI BARASA", 
            "DELVINE WARWARE BARIMBUI", "DENNIS KARIUKI NDUNGU", 
            "EILEEN JEBET MUKABI", "ETHAN MURIITHI GIKUNGU", 
            "GEORGE GITAU MACHOYA", "IAN HUNJA NJERI", 
            "IBRAHIM MWADIME MSHILA"
        ]
    }
}

reports_data = {}

education_level_names = {
    "lower_primary": "Lower Primary",
    "upper_primary": "Upper Primary",
    "junior_secondary": "Junior Secondary"
}

def get_performance_category(percentage):
    """Categorize percentage into performance levels"""
    if percentage >= 75:
        return "Exceeding Expectation"
    elif percentage >= 50:
        return "Meeting Expectation"
    elif percentage >= 30:
        return "Approaching Expectation"
    else:
        return "Below Expectation"

def get_performance_summary(marks_data):
    """Count students in each performance level"""
    summary = defaultdict(int)
    for student in marks_data:
        summary[student[3]] += 1
    return dict(summary)

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

        if "upload_marks" in request.form:
            if not all([education_level, subject, grade, stream, term, assessment_type, total_marks > 0]):
                error_message = "Please fill in all fields before uploading marks"
            else:
                stream_letter = stream[-1] if stream else ''
                if grade in students_data and stream_letter in students_data[grade]:
                    students = students_data[grade][stream_letter]
                    show_students = True
                else:
                    error_message = f"No students found for grade {grade} stream {stream_letter}"

        elif "submit_marks" in request.form:
            if not all([education_level, subject, grade, stream, term, assessment_type, total_marks > 0]):
                error_message = "Please fill in all fields before submitting marks"
            else:
                marks_data = []
                stream_letter = stream[-1] if stream else ''
                if grade in students_data and stream_letter in students_data[grade]:
                    students = students_data[grade][stream_letter]
                    any_marks_submitted = False

                    for student in students:
                        mark_key = f"mark_{student.replace(' ', '_')}"
                        mark_value = request.form.get(mark_key, '')
                        if mark_value and mark_value.isdigit():
                            mark = int(mark_value)
                            if 0 <= mark <= total_marks:
                                percentage = (mark / total_marks) * 100
                                performance = get_performance_category(percentage)
                                marks_data.append([student, mark, round(percentage, 1), performance])
                                any_marks_submitted = True
                            else:
                                error_message = f"Invalid mark for {student}. Must be between 0 and {total_marks}."
                                break
                        else:
                            error_message = f"Missing or invalid mark for {student}"
                            break

                    if any_marks_submitted and not error_message:
                        mean_score = sum(mark[1] for mark in marks_data) / len(marks_data) if marks_data else 0
                        mean_percentage = (mean_score / total_marks) * 100 if total_marks > 0 else 0
                        mean_performance = get_performance_category(mean_percentage)
                        performance_summary = get_performance_summary(marks_data)
                        report_key = f"{grade}_{stream_letter}_{subject.replace(' ', '_')}"

                        reports_data[report_key] = {
                            "marks_data": marks_data,
                            "mean_score": mean_score,
                            "mean_percentage": mean_percentage,
                            "mean_performance": mean_performance,
                            "performance_summary": performance_summary,
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

                        return render_template(
                            "report.html",
                            data=marks_data,
                            mean_score=mean_score,
                            mean_percentage=mean_percentage,
                            mean_performance=mean_performance,
                            performance_summary=performance_summary,
                            education_level=education_level_names.get(education_level, education_level),
                            subject=subject,
                            grade=grade,
                            stream=stream,
                            term=term,
                            assessment_type=assessment_type,
                            total_marks=total_marks
                        )

    if grade and stream and subject and len(stream) > 0:
        stream_letter = stream[-1]
        report_key = f"{grade}_{stream_letter}_{subject.replace(' ', '_')}"
        show_download_button = report_key in reports_data

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
    if 'username' not in session or session['role'] != 'headteacher':
        return redirect(url_for('admin_login'))
    dashboard_data = [
        {"grade": "8B", "mean": 65},
        {"grade": "8G", "mean": 70},
    ]
    return render_template("headteacher.html", data=dashboard_data)

@app.route("/generate_pdf/<grade>/<stream>/<subject>")
def generate_pdf(grade, stream, subject):
    stream_letter = stream[-1] if stream else ''
    report_key = f"{grade}_{stream_letter}_{subject.replace(' ', '_')}"
    
    if report_key not in reports_data:
        return "No data available for this report. Please submit marks first.", 404

    report_data = reports_data[report_key]
    pdf_file = f"report_{grade}_{stream}_{subject.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    heading3_style = styles['Heading3']

    marks_data = report_data.get("marks_data", [])
    mean_score = report_data.get("mean_score", 0)
    mean_percentage = report_data.get("mean_percentage", 0)
    mean_performance = report_data.get("mean_performance", "")
    performance_summary = report_data.get("performance_summary", {})
    education_level = report_data.get("education_level_display", "")
    subject = report_data.get("subject", "")
    term = report_data.get("term", "")
    assessment_type = report_data.get("assessment_type", "")
    total_marks = report_data.get("total_marks", 0)

    # Title and header information
    elements.append(Paragraph("Hill View School", title_style))
    elements.append(Paragraph(f"Grade {grade} Stream {stream} - {subject} Report", subtitle_style))
    elements.append(Spacer(1, 12))

    # Report metadata
    elements.append(Paragraph(f"Education Level: {education_level}", normal_style))
    elements.append(Paragraph(f"Term: {term.replace('_', ' ').title()}", normal_style))
    elements.append(Paragraph(f"Assessment Type: {assessment_type.title()}", normal_style))
    elements.append(Paragraph(f"Total Marks: {total_marks}", normal_style))
    elements.append(Paragraph(f"Mean Score: {mean_score:.2f} ({mean_percentage:.1f}%) - {mean_performance}", normal_style))
    elements.append(Spacer(1, 12))

    # Performance summary section
    elements.append(Paragraph("Performance Summary:", heading3_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"Exceeding Expectation: {performance_summary.get('Exceeding Expectation', 0)} students", normal_style))
    elements.append(Paragraph(f"Meeting Expectation: {performance_summary.get('Meeting Expectation', 0)} students", normal_style))
    elements.append(Paragraph(f"Approaching Expectation: {performance_summary.get('Approaching Expectation', 0)} students", normal_style))
    elements.append(Paragraph(f"Below Expectation: {performance_summary.get('Below Expectation', 0)} students", normal_style))
    elements.append(Spacer(1, 24))

    # Student marks table
    data = [["Student Name", "Marks", "Percentage (%)", "Performance Level"]]
    for student_record in marks_data:
        data.append([
            student_record[0],  # Name
            str(student_record[1]),  # Mark
            f"{student_record[2]}%",  # Percentage
            student_record[3]   # Performance level
        ])
    
    table = Table(data)
    
    # Table styling
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]

    # Color coding for performance levels
    for i, row in enumerate(data[1:], start=1):
        performance = row[3]
        if performance == "Exceeding Expectation":
            table_style.append(('BACKGROUND', (3, i), (3, i), colors.green))
        elif performance == "Meeting Expectation":
            table_style.append(('BACKGROUND', (3, i), (3, i), colors.lightblue))
        elif performance == "Approaching Expectation":
            table_style.append(('BACKGROUND', (3, i), (3, i), colors.yellow))
        else:
            table_style.append(('BACKGROUND', (3, i), (3, i), colors.pink))

    table.setStyle(TableStyle(table_style))
    elements.append(table)

    # Footer
    elements.append(Spacer(1, 20))
    footer_style = styles['Normal']
    footer_style.alignment = 1
    elements.append(Paragraph("Hillview School powered by CbcTeachkit", footer_style))

    # Generate PDF
    doc.build(elements)
    return send_file(pdf_file, as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)