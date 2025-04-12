from flask import Flask, render_template, request, redirect, url_for, send_file, session
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# User credentials - expanded to include class teachers
users = {
    "teacher1": "pass123",
    "headteacher": "admin123",
    "classteacher1": "class123"
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
        return "E.E"  # Exceeding Expectation
    elif percentage >= 50:
        return "M.E"  # Meeting Expectation
    elif percentage >= 30:
        return "A.E"  # Approaching Expectation
    else:
        return "B.E"  # Below Expectation

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

@app.route("/classteacher_login", methods=["GET", "POST"])
def classteacher_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username] == password:
            if username == "classteacher1":
                session['username'] = username
                session['role'] = 'classteacher'
                return redirect(url_for("classteacher"))
            return "Invalid credentials for Class Teacher"
        return "Invalid credentials"
    return render_template("classteacher_login.html")

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

@app.route("/classteacher", methods=["GET", "POST"])
def classteacher():
    if 'username' not in session or session['role'] != 'classteacher':
        return redirect(url_for('classteacher_login'))

    grades = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    error_message = None
    show_students = False
    students = []
    education_level = ""
    grade = ""
    stream = ""
    term = ""
    assessment_type = ""
    total_marks = 0
    show_download_button = False
    report_key = None
    subjects = []
    stats = None
    class_data = None

    # Define subjects based on education level (filtered and ordered as requested)
    subject_mapping = {
        "lower_primary": [
            "Mathematics", "English", "Kiswahili", "Integrated Science and Health Education",
            "Agriculture", "Pre-Technical Studies", "Visual Arts", "Religious Education",
            "Social Studies"
        ],
        "upper_primary": [
            "Mathematics", "English", "Kiswahili", "Integrated Science and Health Education",
            "Agriculture", "Pre-Technical Studies", "Visual Arts", "Religious Education",
            "Social Studies"
        ],
        "junior_secondary": [
            "Mathematics", "English", "Kiswahili", "Integrated Science and Health Education",
            "Agriculture", "Pre-Technical Studies", "Visual Arts", "Religious Education",
            "Social Studies"
        ]
    }

    if request.method == "POST":
        education_level = request.form.get("education_level", "")
        grade = request.form.get("grade", "")
        stream = request.form.get("stream", "")
        term = request.form.get("term", "")
        assessment_type = request.form.get("assessment_type", "")
        try:
            total_marks = int(request.form.get("total_marks", 0))
        except ValueError:
            total_marks = 0

        # Set subjects based on education level
        subjects = subject_mapping.get(education_level, [])

        if "upload_marks" in request.form:
            if not all([education_level, grade, stream, term, assessment_type, total_marks > 0]):
                error_message = "Please fill in all fields before uploading marks"
            else:
                stream_letter = stream[-1] if stream else ''
                if grade in students_data and stream_letter in students_data[grade]:
                    students = students_data[grade][stream_letter]
                    show_students = True
                else:
                    error_message = f"No students found for grade {grade} stream {stream_letter}"

        elif "submit_marks" in request.form:
            if not all([education_level, grade, stream, term, assessment_type, total_marks > 0]):
                error_message = "Please fill in all fields before submitting marks"
            else:
                stream_letter = stream[-1] if stream else ''
                if grade in students_data and stream_letter in students_data[grade]:
                    students = students_data[grade][stream_letter]
                    marks_data = []
                    any_marks_submitted = False
                    subject_marks = {subject: {} for subject in subjects}

                    # Collect marks for all students and subjects
                    for student in students:
                        student_marks = {}
                        valid_student = True
                        for subject in subjects:
                            mark_key = f"mark_{student.replace(' ', '_')}_{subject.replace(' ', '_')}"
                            mark_value = request.form.get(mark_key, '')
                            if mark_value and mark_value.replace('.', '').isdigit():
                                mark = float(mark_value)
                                if 0 <= mark <= total_marks:
                                    subject_marks[subject][student] = mark
                                    student_marks[subject] = mark
                                    any_marks_submitted = True
                                else:
                                    error_message = f"Invalid mark for {student} in {subject}. Must be between 0 and {total_marks}."
                                    valid_student = False
                                    break
                            else:
                                error_message = f"Missing or invalid mark for {student} in {subject}"
                                valid_student = False
                                break
                        if valid_student:
                            marks_data.append([student, student_marks])

                    if any_marks_submitted and not error_message:
                        # Calculate class data (marks, totals, averages, rankings)
                        class_data = []
                        for student, student_marks in marks_data:
                            total = sum(student_marks.values())
                            avg_percentage = (total / (len(subjects) * total_marks)) * 100
                            class_data.append({
                                'student': student,
                                'marks': student_marks,
                                'total_marks': total,
                                'average_percentage': avg_percentage
                            })

                        # Sort by total marks for ranking
                        class_data.sort(key=lambda x: x['total_marks'], reverse=True)
                        for i, student_data in enumerate(class_data, 1):
                            student_data['rank'] = i

                        # Calculate stats based on average percentage
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

                        # Store the report data
                        report_key = f"{grade}_{stream_letter}_class_report_{term}_{assessment_type}"
                        reports_data[report_key] = {
                            "marks_data": marks_data,
                            "class_data": class_data,
                            "stats": stats,
                            "education_level": education_level,
                            "education_level_display": education_level_names.get(education_level, education_level),
                            "grade": grade,
                            "stream": stream,
                            "term": term,
                            "assessment_type": assessment_type,
                            "total_marks": total_marks,
                            "subjects": subjects,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                        show_download_button = True

    if grade and stream and len(stream) > 0:
        stream_letter = stream[-1]
        report_key = f"{grade}_{stream_letter}_class_report_{term}_{assessment_type}"
        if report_key in reports_data:
            show_download_button = True
            stats = reports_data[report_key]["stats"]
            class_data = reports_data[report_key]["class_data"]
            subjects = reports_data[report_key]["subjects"]
            total_marks = reports_data[report_key]["total_marks"]

    return render_template(
        "classteacher.html",
        grades=grades,
        students=students,
        education_level=education_level,
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        total_marks=total_marks,
        show_students=show_students,
        error_message=error_message,
        show_download_button=show_download_button,
        subjects=subjects,
        stats=stats,
        class_data=class_data
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
    elements.append(Paragraph(f"E.E: {performance_summary.get('E.E', 0)} students", normal_style))
    elements.append(Paragraph(f"M.E: {performance_summary.get('M.E', 0)} students", normal_style))
    elements.append(Paragraph(f"A.E: {performance_summary.get('A.E', 0)} students", normal_style))
    elements.append(Paragraph(f"B.E: {performance_summary.get('B.E', 0)} students", normal_style))
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
        if performance == "E.E":
            table_style.append(('BACKGROUND', (3, i), (3, i), colors.green))
        elif performance == "M.E":
            table_style.append(('BACKGROUND', (3, i), (3, i), colors.lightblue))
        elif performance == "A.E":
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

@app.route("/generate_class_pdf/<grade>/<stream>/<term>/<assessment_type>")
def generate_class_pdf(grade, stream, term, assessment_type):
    stream_letter = stream[-1] if stream else ''
    report_key = f"{grade}_{stream_letter}_class_report_{term}_{assessment_type}"
    
    if report_key not in reports_data:
        return "No data available for this report. Please submit marks first.", 404

    report_data = reports_data[report_key]
    pdf_file = f"class_report_{grade}_{stream}_{term}_{assessment_type}.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=landscape(letter))  # Use landscape orientation
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    heading3_style = styles['Heading3']

    class_data = report_data.get("class_data", [])
    stats = report_data.get("stats", {})
    education_level = report_data.get("education_level_display", "")
    term = report_data.get("term", "")
    assessment_type = report_data.get("assessment_type", "")
    total_marks = report_data.get("total_marks", 0)
    subjects = report_data.get("subjects", [])

    # Define subject abbreviations
    subject_abbreviations = {
        "Mathematics": "MATH",
        "English": "ENG",
        "Kiswahili": "KISW",
        "Integrated Science and Health Education": "ISHE",
        "Agriculture": "AGR",
        "Pre-Technical Studies": "PTS",
        "Visual Arts": "VA",
        "Religious Education": "RE",
        "Social Studies": "SS"
    }

    # Map subjects to their abbreviations
    abbreviated_subjects = [subject_abbreviations.get(subject, subject[:4].upper()) for subject in subjects]

    # Title and header information
    title_style.alignment = 1  # Center align
    subtitle_style.alignment = 1
    elements.append(Paragraph("HILL VIEW SCHOOL", title_style))
    elements.append(Paragraph(f"GRADE {grade} - {education_level.upper()} MARKSHEET: AVERAGE SCORE", subtitle_style))
    elements.append(Paragraph(f"STREAM: {stream}  TERM: {term.replace('_', ' ').upper()}  ASSESSMENT: {assessment_type.upper()}", subtitle_style))
    elements.append(Spacer(1, 12))

    # Student marks table
    headers = ["S/N", "STUDENT NAME"] + abbreviated_subjects + ["TOTAL", "AVG %", "GRD", "RANK"]
    data = [headers]
    for idx, student_data in enumerate(class_data, 1):
        row = [
            str(idx),  # Serial number
            student_data['student'].upper()  # Student name in uppercase
        ]
        for subject in subjects:
            mark = student_data['marks'].get(subject, 0)
            row.append(str(int(mark)))  # Only the mark, no percentage
        total = student_data['total_marks']
        avg_percentage = student_data['average_percentage']
        grade = get_performance_category(avg_percentage)
        row.extend([
            str(int(total)),
            f"{avg_percentage:.0f}%",  # Round to nearest integer
            grade,  # E.E, M.E, A.E, B.E
            str(student_data['rank'])
        ])
        data.append(row)
    
    table = Table(data)
    
    # Table styling
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    # Adjust column widths
    col_widths = [30, 150] + [40] * len(abbreviated_subjects) + [50, 50, 40, 40]  # S/N, Name, Subjects, Total, Avg %, Grade, Rank
    table._argW = col_widths

    table.setStyle(TableStyle(table_style))
    elements.append(table)

    # Performance summary section
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Performance Summary:", heading3_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"E.E (Exceeding Expectation, ≥75%): {stats.get('exceeding', 0)} learners", normal_style))
    elements.append(Paragraph(f"M.E (Meeting Expectation, 50-74%): {stats.get('meeting', 0)} learners", normal_style))
    elements.append(Paragraph(f"A.E (Approaching Expectation, 30-49%): {stats.get('approaching', 0)} learners", normal_style))
    elements.append(Paragraph(f"B.E (Below Expectation, <30%): {stats.get('below', 0)} learners", normal_style))

    # Footer
    elements.append(Spacer(1, 20))
    footer_style = styles['Normal']
    footer_style.alignment = 1  # Center align
    footer_style.fontSize = 8
    current_date = datetime.now().strftime("%Y-%m-%d")
    elements.append(Paragraph(f"Generated on: {current_date}", footer_style))
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