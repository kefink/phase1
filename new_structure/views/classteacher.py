"""
Class Teacher views for the Hillview School Management System.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, jsonify, make_response
from werkzeug.security import generate_password_hash
import pandas as pd
import os
from werkzeug.utils import secure_filename
from ..models import Grade, Stream, Subject, Term, AssessmentType, Student, Mark, Teacher, TeacherSubjectAssignment
from ..utils.constants import educational_level_mapping
from ..services import is_authenticated, get_role, get_class_report_data, generate_individual_report, generate_class_report_pdf
from ..extensions import db
from ..utils import get_performance_category
from functools import wraps

# Create a blueprint for class teacher routes
classteacher_bp = Blueprint('classteacher', __name__, url_prefix='/classteacher')

# Decorator for requiring class teacher authentication
def classteacher_required(f):
    """Decorator to require class teacher authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session) or get_role(session) != 'classteacher':
            return redirect(url_for('auth.classteacher_login'))
        return f(*args, **kwargs)
    return decorated_function

@classteacher_bp.route('/')
@classteacher_required
def dashboard():
    """Route for the class teacher dashboard."""
    # Get the teacher
    teacher_id = session.get('teacher_id')
    teacher = Teacher.query.get(teacher_id)

    if not teacher:
        flash("Teacher not found.", "error")
        return render_template("classteacher.html")

    # Get teacher's subject assignments and class teacher status
    try:
        # Get only this teacher's assignments
        teacher_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher.id).all()

        # Get class teacher assignments
        class_teacher_assignments = []
        for assignment in teacher_assignments:
            if assignment.is_class_teacher:
                current_teacher = Teacher.query.get(assignment.teacher_id)
                grade = Grade.query.get(assignment.grade_id)
                stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

                class_teacher_assignments.append({
                    "id": assignment.id,
                    "teacher_username": current_teacher.username if current_teacher else "Unknown",
                    "grade_level": grade.level if grade else "Unknown",
                    "stream_name": stream.name if stream else None
                })

        # Get subject assignments
        subject_assignments = []
        for assignment in teacher_assignments:
            teacher = Teacher.query.get(assignment.teacher_id)
            subject = Subject.query.get(assignment.subject_id)
            grade = Grade.query.get(assignment.grade_id)
            stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

            subject_assignments.append({
                "id": assignment.id,
                "teacher_username": teacher.username if teacher else "Unknown",
                "subject_name": subject.name if subject else "Unknown",
                "education_level": subject.education_level if subject else None,
                "grade_level": grade.level if grade else "Unknown",
                "stream_name": stream.name if stream else None
            })
    except Exception as e:
        # If there's an error (like the table doesn't exist), use empty lists
        print(f"Error fetching teacher assignments: {str(e)}")
        teacher_assignments = []
        class_teacher_assignments = []
        subject_assignments = []

    # Initialize variables for teacher's assigned stream/grade (if any)
    stream = None
    grade = None
    grade_level = ""
    stream_name = ""

    # Check if teacher is assigned to a stream
    if teacher.stream_id:
        stream = Stream.query.get(teacher.stream_id)
        if stream:
            grade = Grade.query.get(stream.grade_id)
            if grade:
                grade_level = grade.level
                stream_name = f"Stream {stream.name}"

    # Get data for the form
    grades = [grade.level for grade in Grade.query.all()]
    grades_dict = {grade.level: grade.id for grade in Grade.query.all()}
    terms = [term.name for term in Term.query.all()]
    assessment_types = [assessment_type.name for assessment_type in AssessmentType.query.all()]
    streams = [f"Stream {stream.name}" for stream in Stream.query.all()]
    subjects = [subject.name for subject in Subject.query.all()]

    # Initialize variables
    error_message = None
    show_students = False
    students = []
    education_level = ""
    grade_level = grade.level if grade else ""
    stream_name = f"Stream {stream.name}" if stream else ""
    term = ""
    assessment_type = ""
    total_marks = 0
    show_download_button = False
    show_individual_report_button = False
    class_data = []
    stats = {}

    # Fetch recent reports
    recent_reports = []
    marks = Mark.query.join(Student).join(Stream).join(Grade).join(Term).join(AssessmentType).all()
    seen_combinations = set()
    for mark in marks:
        combination = (mark.student.stream.grade.level, mark.student.stream.name, mark.term.name, mark.assessment_type.name)
        if combination not in seen_combinations:
            seen_combinations.add(combination)
            recent_reports.append({
                'grade': mark.student.stream.grade.level,
                'stream': f"Stream {mark.student.stream.name}",
                'term': mark.term.name,
                'assessment_type': mark.assessment_type.name,
                'date': mark.created_at.strftime('%Y-%m-%d') if mark.created_at else 'N/A'
            })
            if len(recent_reports) >= 5:  # Limit to 5 recent reports
                break

    # Handle form submission
    if request.method == "POST":
        # Process form data here
        pass

    # Render the class teacher dashboard
    return render_template(
        "classteacher.html",
        grades=grades,
        grades_dict=grades_dict,
        terms=terms,
        assessment_types=assessment_types,
        streams=streams,
        students=students,
        education_level=education_level,
        grade=grade_level,
        stream=stream_name,
        term=term,
        assessment_type=assessment_type,
        total_marks=total_marks,
        show_students=show_students,
        error_message=error_message,
        show_download_button=show_download_button,
        show_individual_report_button=show_individual_report_button,
        subjects=subjects,
        stats=stats,
        class_data=class_data,
        recent_reports=recent_reports,
        class_teacher_assignments=class_teacher_assignments,
        subject_assignments=subject_assignments
    )

@classteacher_bp.route('/manage_students', methods=['GET', 'POST'])
@classteacher_required
def manage_students():
    """Route for managing students."""
    print("Entering manage_students route")

    # Get the teacher
    teacher_id = session.get('teacher_id')
    print(f"Teacher ID: {teacher_id}")

    teacher = Teacher.query.get(teacher_id)
    print(f"Teacher: {teacher}")

    if not teacher:
        print("Teacher not found")
        flash("Teacher not found.", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Initialize variables
    stream = None
    grade = None
    stream_id = None

    # Check if teacher is assigned to a stream
    if teacher.stream_id:
        stream = Stream.query.get(teacher.stream_id)
        if stream:
            grade = Grade.query.get(stream.grade_id)
            stream_id = stream.id
            print(f"Stream: {stream}")
            print(f"Grade: {grade}")

    # Get filter parameters
    educational_level = request.args.get('educational_level', '')
    grade_id = request.args.get('grade_id', '')
    stream_id_filter = request.args.get('stream_id', '')
    search_query = request.args.get('search', '').strip()

    # If a stream_id is provided in the URL, use it instead of the teacher's assigned stream
    if stream_id_filter:
        stream_id = stream_id_filter
        stream = Stream.query.get(stream_id)
        if stream:
            grade = Grade.query.get(stream.grade_id)

    # If a grade_id is provided in the URL, use it for filtering
    if grade_id:
        grade = Grade.query.get(grade_id)

    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of students per page

    # Build the query based on filters
    students_query = Student.query

    # Apply search if provided
    if search_query:
        # Search by name or admission number
        students_query = students_query.filter(
            (Student.name.ilike(f'%{search_query}%')) |
            (Student.admission_number.ilike(f'%{search_query}%'))
        )

    # Filter by stream if specified
    if stream_id:
        students_query = students_query.filter_by(stream_id=stream_id)

    # Filter by grade if specified (and not already filtered by stream)
    elif grade and not stream_id:
        # Get all streams for this grade
        grade_streams = Stream.query.filter_by(grade_id=grade.id).all()
        stream_ids = [s.id for s in grade_streams]
        if stream_ids:
            students_query = students_query.filter(Student.stream_id.in_(stream_ids))

    # Filter by educational level if specified
    if educational_level:
        # Get all grades for this educational level
        allowed_grades = educational_level_mapping.get(educational_level, [])
        grades = Grade.query.filter(Grade.level.in_(allowed_grades)).all()
        grade_ids = [g.id for g in grades]

        # Get all streams for these grades
        streams = Stream.query.filter(Stream.grade_id.in_(grade_ids)).all()
        stream_ids = [s.id for s in streams]

        if stream_ids:
            students_query = students_query.filter(Student.stream_id.in_(stream_ids))

    # Count total students matching the filters
    total_students = students_query.count()
    print(f"Number of students matching filters: {total_students}")

    # Apply pagination
    students_paginated = students_query.order_by(Student.name).paginate(page=page, per_page=per_page, error_out=False)
    students = students_paginated.items

    # Get all grades for the template
    grades = [{"id": grade.id, "level": grade.level} for grade in Grade.query.all()]

    # Define educational level mapping
    educational_level_mapping = {
        "lower_primary": ["Grade 1", "Grade 2", "Grade 3"],
        "upper_primary": ["Grade 4", "Grade 5", "Grade 6"],
        "junior_secondary": ["Grade 7", "Grade 8", "Grade 9"]
    }

    # Handle form submissions
    if request.method == 'POST':
        action = request.form.get('action', '')

        # Add new student
        if action == 'add_student':
            name = request.form.get('name', '').strip()
            admission_number = request.form.get('admission_number', '').strip()
            gender = request.form.get('gender', '').strip()

            if not name or not admission_number:
                flash("Name and admission number are required.", "error")
            else:
                # Check if admission number already exists
                existing_student = Student.query.filter_by(admission_number=admission_number).first()
                if existing_student:
                    flash(f"Admission number '{admission_number}' is already in use.", "error")
                else:
                    # Get stream_id from form if teacher is not assigned to a stream
                    selected_stream_id = request.form.get('stream')

                    # Use the teacher's assigned stream if available, otherwise use the selected stream
                    final_stream_id = stream_id if stream_id else selected_stream_id

                    # Stream is now optional, so we don't need to check if it's provided

                    # Add new student
                    student = Student(
                        name=name,
                        admission_number=admission_number,
                        stream_id=final_stream_id if final_stream_id else None,
                        gender=gender.lower() if gender else "unknown"
                    )
                    db.session.add(student)
                    db.session.commit()
                    flash(f"Student '{name}' added successfully.", "success")
                    return redirect(url_for('classteacher.manage_students'))

        # Delete student
        elif action == 'delete_student':
            student_id = request.form.get('student_id')
            if student_id:
                student = Student.query.get(student_id)
                if student:
                    # Delete associated marks
                    Mark.query.filter_by(student_id=student.id).delete()
                    # Delete the student
                    db.session.delete(student)
                    db.session.commit()
                    flash(f"Student '{student.name}' deleted successfully.", "success")
                    return redirect(url_for('classteacher.manage_students'))

        # Bulk delete students
        elif action == 'bulk_delete_students':
            student_ids = request.form.getlist('student_ids')
            if student_ids:
                deleted_count = 0
                for student_id in student_ids:
                    student = Student.query.get(student_id)
                    if student:
                        # Delete associated marks
                        Mark.query.filter_by(student_id=student.id).delete()
                        # Delete the student
                        db.session.delete(student)
                        deleted_count += 1

                if deleted_count > 0:
                    db.session.commit()
                    flash(f"Successfully deleted {deleted_count} student(s).", "success")
                else:
                    flash("No students were deleted.", "error")

                return redirect(url_for('classteacher.manage_students'))

        # Bulk update genders
        elif action == 'bulk_update_genders':
            updated_count = 0
            for key, value in request.form.items():
                if key.startswith('gender_') and value:
                    student_id = key.replace('gender_', '')
                    student = Student.query.get(student_id)
                    if student and student.gender != value.lower():
                        student.gender = value.lower()
                        updated_count += 1

            if updated_count > 0:
                db.session.commit()
                flash(f"Successfully updated gender for {updated_count} student(s).", "success")
            else:
                flash("No gender information was updated.", "info")

            return redirect(url_for('classteacher.manage_students'))

        # Bulk edit students
        elif action == 'bulk_edit_students':
            student_ids = request.form.getlist('student_ids')
            if not student_ids:
                flash('No students selected for editing.', 'error')
                return redirect(url_for('classteacher.manage_students'))

            edit_type = request.form.get('bulk_edit_type')

            if edit_type == 'gender':
                # Update gender for selected students
                gender = request.form.get('bulk_gender')
                if not gender:
                    flash('Please select a gender.', 'error')
                    return redirect(url_for('classteacher.manage_students'))

                updated_count = 0
                for student_id in student_ids:
                    student = Student.query.get(student_id)
                    if student:
                        student.gender = gender.lower()
                        updated_count += 1

                if updated_count > 0:
                    db.session.commit()
                    flash(f'Successfully updated gender for {updated_count} student(s).', 'success')
                else:
                    flash('No students were updated.', 'info')

            elif edit_type == 'stream':
                # Move students to a different stream
                grade_id = request.form.get('bulk_grade')
                stream_id = request.form.get('bulk_stream')

                if not grade_id or not stream_id:
                    flash('Please select both grade and stream.', 'error')
                    return redirect(url_for('classteacher.manage_students'))

                # Verify that the stream belongs to the selected grade
                stream = Stream.query.get(stream_id)
                if not stream or str(stream.grade_id) != grade_id:
                    flash('Invalid stream selected.', 'error')
                    return redirect(url_for('classteacher.manage_students'))

                updated_count = 0
                for student_id in student_ids:
                    student = Student.query.get(student_id)
                    if student:
                        student.stream_id = stream_id
                        updated_count += 1

                if updated_count > 0:
                    db.session.commit()
                    flash(f'Successfully moved {updated_count} student(s) to {stream.name}.', 'success')
                else:
                    flash('No students were moved.', 'info')

            else:
                flash('Invalid edit type.', 'error')

            return redirect(url_for('classteacher.manage_students'))

        # Bulk upload students
        elif action == 'bulk_upload_students':
            print("Processing bulk upload of students")
            if 'student_file' not in request.files:
                flash("No file part", "error")
                return redirect(request.url)

            file = request.files['student_file']
            if file.filename == '':
                flash("No selected file", "error")
                return redirect(request.url)

            if file:
                try:
                    # Check file extension
                    filename = secure_filename(file.filename)
                    file_ext = os.path.splitext(filename)[1].lower()

                    if file_ext == '.csv':
                        df = pd.read_csv(file)
                    elif file_ext in ['.xlsx', '.xls']:
                        df = pd.read_excel(file)
                    else:
                        flash("Unsupported file format. Please upload a CSV or Excel file.", "error")
                        return redirect(request.url)

                    # Check required columns
                    required_columns = ['name', 'admission_number']
                    for col in required_columns:
                        if col not in df.columns:
                            flash(f"Missing required column: {col}", "error")
                            return redirect(request.url)

                    # Process each row
                    success_count = 0
                    error_count = 0

                    for _, row in df.iterrows():
                        name = str(row['name']).strip()
                        admission_number = str(row['admission_number']).strip()

                        # Optional fields
                        gender = str(row.get('gender', '')).strip().lower() if pd.notna(row.get('gender', '')) else 'unknown'

                        # Skip empty rows
                        if not name or not admission_number:
                            error_count += 1
                            continue

                        # Check if admission number already exists
                        existing_student = Student.query.filter_by(admission_number=admission_number).first()
                        if existing_student:
                            error_count += 1
                            continue

                        # Get stream_id from form if teacher is not assigned to a stream
                        selected_stream_id = request.form.get('stream')

                        # Use the teacher's assigned stream if available, otherwise use the selected stream
                        final_stream_id = stream_id if stream_id else selected_stream_id

                        # Stream is now optional

                        # Add new student
                        student = Student(
                            name=name,
                            admission_number=admission_number,
                            stream_id=final_stream_id if final_stream_id else None,
                            gender=gender
                        )
                        db.session.add(student)
                        success_count += 1

                    db.session.commit()

                    if success_count > 0:
                        flash(f"Successfully added {success_count} students. {error_count} errors encountered.", "success")
                    else:
                        flash(f"No students added. {error_count} errors encountered.", "error")

                    return redirect(url_for('classteacher.manage_students'))

                except Exception as e:
                    flash(f"An error occurred: {str(e)}", "error")
                    print(f"Error processing file: {str(e)}")
                    return redirect(request.url)

    print("Rendering manage_students.html template")
    return render_template(
        'manage_students.html',
        students=students,
        pagination=students_paginated,
        total_students=total_students,
        grade=grade.level if grade else "",
        stream=stream.name if stream else "",
        grades=grades,
        educational_level_mapping=educational_level_mapping,
        educational_levels=list(educational_level_mapping.keys())
    )

@classteacher_bp.route('/preview_class_report/<grade>/<stream>/<term>/<assessment_type>')
@classteacher_required
def preview_class_report(grade, stream, term, assessment_type):
    """Route for previewing class reports."""
    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Get class report data
    report_data = get_class_report_data(stream_obj.id, term_obj.id, assessment_type_obj.id)

    if not report_data:
        flash(f"No marks found for {grade} Stream {stream[-1]} in {term} {assessment_type}", "error")
        return redirect(url_for('classteacher.dashboard'))

    return render_template(
        'preview_class_report.html',
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        report_data=report_data
    )

@classteacher_bp.route('/download_class_report/<grade>/<stream>/<term>/<assessment_type>')
@classteacher_required
def download_class_report(grade, stream, term, assessment_type):
    """Route for downloading class reports as PDF."""
    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Generate PDF report
    pdf_file = generate_class_report_pdf(stream_obj.id, term_obj.id, assessment_type_obj.id)

    if not pdf_file:
        flash(f"Failed to generate report for {grade} Stream {stream[-1]} in {term} {assessment_type}", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Return the PDF file
    filename = f"{grade}_Stream_{stream[-1]}_{term}_{assessment_type}_Report.pdf"
    return send_file(
        pdf_file,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@classteacher_bp.route('/preview_individual_report/<grade>/<stream>/<term>/<assessment_type>/<student_name>')
@classteacher_required
def preview_individual_report(grade, stream, term, assessment_type, student_name):
    """Route for previewing individual student reports."""
    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('classteacher.dashboard'))

    student = Student.query.filter_by(name=student_name, stream_id=stream_obj.id).first()
    if not student:
        flash(f"No data available for student {student_name}.", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Generate individual report data
    report_data = generate_individual_report(student.id, term_obj.id, assessment_type_obj.id)

    if not report_data:
        flash(f"No marks found for {student_name} in {term} {assessment_type}", "error")
        return redirect(url_for('classteacher.dashboard'))

    return render_template(
        'preview_individual_report.html',
        student=student,
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        report_data=report_data
    )

@classteacher_bp.route('/generate_grade_marksheet/<grade>/<term>/<assessment_type>/<action>')
@classteacher_required
def generate_grade_marksheet(grade, term, assessment_type, action):
    """Route for generating grade marksheets (preview or download)."""
    # Fetch grade and related data
    grade_obj = Grade.query.filter_by(level=grade).first()
    if not grade_obj:
        flash(f"Grade {grade} not found", "error")
        return redirect(url_for('classteacher.dashboard'))

    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()
    if not term_obj or not assessment_type_obj:
        flash("Invalid term or assessment type", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Fetch all streams for the grade
    streams = Stream.query.filter_by(grade_id=grade_obj.id).all()
    if not streams:
        flash(f"No streams found for grade {grade}", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Fetch all subjects
    subjects = Subject.query.all()
    if not subjects:
        flash("No subjects found", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Prepare data for the marksheet
    all_data = []
    for stream in streams:
        students = Student.query.filter_by(stream_id=stream.id).all()
        for student in students:
            student_marks = {}
            student_total = 0
            subject_count = 0

            # Get marks for each subject
            for subject in subjects:
                mark = Mark.query.filter_by(
                    student_id=student.id,
                    subject_id=subject.id,
                    term_id=term_obj.id,
                    assessment_type_id=assessment_type_obj.id
                ).first()

                if mark:
                    student_marks[subject.name] = mark.mark
                    student_total += mark.mark
                    subject_count += 1
                else:
                    student_marks[subject.name] = "-"

            # Calculate average percentage
            total_marks = 100  # Assuming total marks is 100 for each subject
            average_percentage = (student_total / (subject_count * total_marks)) * 100 if total_marks and subject_count > 0 else 0
            grade_label = get_performance_category(average_percentage)

            # Include stream name with student name for clarity
            student_data = {
                'name': f"{student.name} ({stream.name})",
                'marks': student_marks,
                'total': student_total,
                'percentage': average_percentage,
                'grade': grade_label
            }
            all_data.append(student_data)

    if not all_data:
        flash(f"No marks found for grade {grade}, term {term}, assessment {assessment_type}", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Sort data by percentage (descending)
    all_data.sort(key=lambda x: x['percentage'], reverse=True)

    # Handle preview or download action
    if action == 'preview':
        return render_template(
            'preview_grade_marksheet.html',
            grade=grade,
            term=term,
            assessment_type=assessment_type,
            subjects=subjects,
            data=all_data
        )
    elif action == 'download':
        # Generate PDF and send it
        # This would be implemented in a service function
        flash("Download functionality not implemented yet", "warning")
        return redirect(url_for('classteacher.dashboard'))
    else:
        flash("Invalid action", "error")
        return redirect(url_for('classteacher.dashboard'))

@classteacher_bp.route('/preview_grade_marksheet/<grade>/<term>/<assessment_type>')
@classteacher_required
def preview_grade_marksheet(grade, term, assessment_type):
    """Shortcut route for previewing grade marksheets."""
    return redirect(url_for('classteacher.generate_grade_marksheet',
                           grade=grade,
                           term=term,
                           assessment_type=assessment_type,
                           action='preview'))

@classteacher_bp.route('/download_grade_marksheet/<grade>/<term>/<assessment_type>')
@classteacher_required
def download_grade_marksheet(grade, term, assessment_type):
    """Shortcut route for downloading grade marksheets."""
    return redirect(url_for('classteacher.generate_grade_marksheet',
                           grade=grade,
                           term=term,
                           assessment_type=assessment_type,
                           action='download'))

@classteacher_bp.route('/get_streams/<grade_id>', methods=['GET'])
@classteacher_required
def get_streams(grade_id):
    """API endpoint to get streams for a specific grade."""
    try:
        grade_id = int(grade_id)
        streams = Stream.query.filter_by(grade_id=grade_id).all()
        return jsonify({"streams": [{"id": stream.id, "name": stream.name} for stream in streams]})
    except ValueError:
        return jsonify({"error": "Invalid grade ID"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@classteacher_bp.route('/download_class_list', methods=['GET'])
@classteacher_required
def download_class_list():
    """Route to download class lists as CSV files."""
    # Get filter parameters
    educational_level = request.args.get('educational_level', '')
    grade_id = request.args.get('grade_id', '')
    stream_id = request.args.get('stream_id', '')
    all_grades = request.args.get('all_grades', '')
    search_query = request.args.get('search', '').strip()

    # Build the query based on filters
    students_query = Student.query

    # Apply search if provided
    if search_query:
        # Search by name or admission number
        students_query = students_query.filter(
            (Student.name.ilike(f'%{search_query}%')) |
            (Student.admission_number.ilike(f'%{search_query}%'))
        )

    # Filter by stream if specified
    if stream_id:
        students_query = students_query.filter_by(stream_id=stream_id)
        stream = Stream.query.get(stream_id)
        grade = Grade.query.get(stream.grade_id) if stream else None
        filename = f"Class_List_{grade.level if grade else 'Unknown'}_{stream.name if stream else 'Unknown'}.csv"

    # Filter by grade if specified (and not already filtered by stream)
    elif grade_id:
        grade = Grade.query.get(grade_id)
        # Get all streams for this grade
        grade_streams = Stream.query.filter_by(grade_id=grade_id).all()
        stream_ids = [s.id for s in grade_streams]
        if stream_ids:
            students_query = students_query.filter(Student.stream_id.in_(stream_ids))
        filename = f"Class_List_{grade.level if grade else 'Unknown'}_All_Streams.csv"

    # Filter by educational level if specified
    elif educational_level:
        # Get all grades for this educational level
        allowed_grades = educational_level_mapping.get(educational_level, [])
        grades = Grade.query.filter(Grade.level.in_(allowed_grades)).all()
        grade_ids = [g.id for g in grades]

        # Get all streams for these grades
        streams = Stream.query.filter(Stream.grade_id.in_(grade_ids)).all()
        stream_ids = [s.id for s in streams]

        if stream_ids:
            students_query = students_query.filter(Student.stream_id.in_(stream_ids))

        filename = f"Class_List_{educational_level.replace('_', ' ').title()}.csv"

    # Download all students if specified
    elif all_grades:
        filename = "All_Students.csv"

    # Default filename if no filters are applied
    else:
        filename = "Class_List.csv"

    # Get all students matching the filters
    students = students_query.order_by(Student.name).all()

    # Create a CSV string
    csv_data = "ID,Name,Admission Number,Grade,Stream,Gender\n"

    for student in students:
        grade_name = student.stream.grade.level if student.stream else "N/A"
        stream_name = student.stream.name if student.stream else "No Stream"
        gender = student.gender.capitalize() if student.gender else "Not Set"

        csv_data += f"{student.id},{student.name},{student.admission_number},{grade_name},{stream_name},{gender}\n"

    # Create a response with the CSV data
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-Type"] = "text/csv"

    return response

@classteacher_bp.route('/manage_subjects', methods=['GET', 'POST'])
@classteacher_required
def manage_subjects():
    """Route for managing subjects."""
    error_message = None
    success_message = None

    # Get filter and pagination parameters
    education_level = request.args.get('education_level', '')
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of subjects per page

    # Build the query based on filters
    subjects_query = Subject.query

    # Apply search if provided
    if search_query:
        subjects_query = subjects_query.filter(Subject.name.ilike(f'%{search_query}%'))

    # Apply education level filter if specified
    if education_level and education_level != 'all':
        subjects_query = subjects_query.filter_by(education_level=education_level)

    # Order by education level and name
    subjects_query = subjects_query.order_by(Subject.education_level, Subject.name)

    # Paginate the results
    pagination = subjects_query.paginate(page=page, per_page=per_page, error_out=False)
    subjects = pagination.items

    # Get all unique education levels for the filter dropdown
    all_education_levels = db.session.query(Subject.education_level).distinct().all()
    education_levels = [level[0] for level in all_education_levels if level[0]]

    if request.method == 'POST':
        action = request.form.get("action")

        if "add_subject" in request.form:
            subject_name = request.form.get("name")
            education_level = request.form.get("education_level")

            if not subject_name:
                error_message = "Please fill in the subject name."
            elif not education_level:
                error_message = "Please select an education level."
            else:
                # Check if subject with same name and education level already exists
                existing_subject = Subject.query.filter_by(name=subject_name, education_level=education_level).first()
                if existing_subject:
                    error_message = f"Subject '{subject_name}' already exists for {education_level.replace('_', ' ').title()}."
                else:
                    new_subject = Subject(name=subject_name, education_level=education_level)
                    db.session.add(new_subject)
                    db.session.commit()
                    success_message = f"Subject '{subject_name}' added successfully for {education_level.replace('_', ' ').title()}!"

        elif "delete_subject" in request.form:
            subject_id = request.form.get("subject_id")
            subject = Subject.query.get(subject_id)
            if subject:
                # Check if subject has marks
                marks = Mark.query.filter_by(subject_id=subject.id).all()
                if marks:
                    error_message = f"Cannot delete subject '{subject.name}' because it has marks associated with it."
                else:
                    db.session.delete(subject)
                    db.session.commit()
                    success_message = f"Subject '{subject.name}' deleted successfully!"
            else:
                error_message = "Subject not found."

        elif action == "edit_subject":
            subject_id = request.form.get("subject_id")
            subject_name = request.form.get("name")
            education_level = request.form.get("education_level")

            if not subject_id or not subject_name or not education_level:
                error_message = "Please fill in all fields."
            else:
                subject = Subject.query.get(subject_id)
                if not subject:
                    error_message = "Subject not found."
                else:
                    # Check if another subject with the same name and education level already exists
                    existing_subject = Subject.query.filter(
                        Subject.name == subject_name,
                        Subject.education_level == education_level,
                        Subject.id != subject.id
                    ).first()

                    if existing_subject:
                        error_message = f"Subject '{subject_name}' already exists for {education_level.replace('_', ' ').title()}."
                    else:
                        # Update the subject
                        subject.name = subject_name
                        subject.education_level = education_level
                        db.session.commit()
                        success_message = f"Subject '{subject_name}' updated successfully!"

        elif action == "delete_selected_subjects":
            subject_ids = request.form.getlist("subject_ids")
            if not subject_ids:
                error_message = "No subjects selected for deletion."
            else:
                deleted_count = 0
                not_deleted_count = 0

                for subject_id in subject_ids:
                    subject = Subject.query.get(subject_id)
                    if subject:
                        # Check if subject has marks
                        marks = Mark.query.filter_by(subject_id=subject.id).all()
                        if marks:
                            not_deleted_count += 1
                        else:
                            db.session.delete(subject)
                            deleted_count += 1

                if deleted_count > 0:
                    db.session.commit()
                    success_message = f"Successfully deleted {deleted_count} subject(s)."

                if not_deleted_count > 0:
                    if success_message:
                        success_message += f" {not_deleted_count} subject(s) could not be deleted because they have marks associated with them."
                    else:
                        error_message = f"Could not delete {not_deleted_count} subject(s) because they have marks associated with them."

    return render_template(
        'manage_subjects.html',
        subjects=subjects,
        pagination=pagination,
        education_levels=education_levels,
        current_education_level=education_level,
        search_query=search_query,
        error_message=error_message,
        success_message=success_message
    )

@classteacher_bp.route('/manage_grades_streams', methods=['GET', 'POST'])
@classteacher_required
def manage_grades_streams():
    """Route for managing grades and streams."""
    error_message = None
    success_message = None

    if request.method == 'POST':
        if "add_grade" in request.form:
            grade_level = request.form.get("grade_level")
            if grade_level:
                existing_grade = Grade.query.filter_by(level=grade_level).first()
                if existing_grade:
                    error_message = f"Grade '{grade_level}' already exists."
                else:
                    new_grade = Grade(level=grade_level)
                    db.session.add(new_grade)
                    db.session.commit()
                    success_message = f"Grade '{grade_level}' added successfully!"
            else:
                error_message = "Please fill in the grade level."

        elif "add_stream" in request.form:
            stream_name = request.form.get("stream_name")
            grade_id = request.form.get("grade_id")
            if stream_name and grade_id:
                grade = Grade.query.get(grade_id)
                if not grade:
                    error_message = "Selected grade not found."
                else:
                    existing_stream = Stream.query.filter_by(name=stream_name, grade_id=grade_id).first()
                    if existing_stream:
                        error_message = f"Stream '{stream_name}' already exists for Grade {grade.level}."
                    else:
                        new_stream = Stream(name=stream_name, grade_id=grade_id)
                        db.session.add(new_stream)
                        db.session.commit()
                        success_message = f"Stream '{stream_name}' added to Grade {grade.level} successfully!"
            else:
                error_message = "Please fill in all fields."

        elif "delete_grade" in request.form:
            grade_id = request.form.get("grade_id")
            grade = Grade.query.get(grade_id)
            if grade:
                # Check if grade has streams
                if grade.streams:
                    # Delete all streams associated with this grade
                    for stream in grade.streams:
                        # Check if stream has students
                        students = Student.query.filter_by(stream_id=stream.id).all()
                        if students:
                            # Unassign all students from this stream
                            for student in students:
                                student.stream_id = None
                        # Delete the stream
                        db.session.delete(stream)

                # Now delete the grade
                db.session.delete(grade)
                db.session.commit()
                success_message = f"Grade '{grade.level}' and all its streams deleted successfully!"
            else:
                error_message = "Grade not found."

        elif "delete_stream" in request.form:
            stream_id = request.form.get("stream_id")
            stream = Stream.query.get(stream_id)
            if stream:
                # Check if stream has students
                students = Student.query.filter_by(stream_id=stream.id).all()
                if students:
                    # Unassign all students from this stream
                    for student in students:
                        student.stream_id = None

                # Delete the stream
                db.session.delete(stream)
                db.session.commit()
                success_message = f"Stream '{stream.name}' deleted successfully!"
            else:
                error_message = "Stream not found."

    grades = Grade.query.all()
    return render_template("manage_grades_streams.html", grades=grades, error_message=error_message, success_message=success_message)

@classteacher_bp.route('/manage_teacher_assignments', methods=['GET', 'POST'])
@classteacher_required
def manage_teacher_assignments():
    """Route for managing teacher assignments, transfers, and reassignments."""
    error_message = None
    success_message = None

    # Get all teachers
    teachers = Teacher.query.all()

    # Get all subjects and grades
    subjects = Subject.query.all()
    grades = Grade.query.all()

    # Get all class teacher assignments
    class_teacher_assignments = []
    try:
        # Get the current teacher ID
        current_teacher_id = session.get('teacher_id')
        current_teacher = Teacher.query.get(current_teacher_id)

        # Show all class teacher assignments
        # This is for the "Manage Teacher Transfers" page where admins need to see all assignments
        assignments = TeacherSubjectAssignment.query.filter_by(
            is_class_teacher=True
        ).all()

        for assignment in assignments:
            teacher = Teacher.query.get(assignment.teacher_id)
            grade = Grade.query.get(assignment.grade_id)
            stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

            # Determine education level based on grade
            education_level = ""
            grade_num = 0
            try:
                # Extract grade number
                if grade.level.startswith("Grade "):
                    grade_num = int(grade.level[6:])
                else:
                    # Try to extract just the number
                    grade_num = int(''.join(filter(str.isdigit, grade.level)))

                # Assign education level
                if 1 <= grade_num <= 3:
                    education_level = "lower_primary"
                elif 4 <= grade_num <= 6:
                    education_level = "upper_primary"
                elif 7 <= grade_num <= 9:
                    education_level = "junior_secondary"
            except:
                education_level = ""

            class_teacher_assignments.append({
                "id": assignment.id,
                "teacher_id": assignment.teacher_id,
                "teacher_username": teacher.username if teacher else "Unknown",
                "grade_id": assignment.grade_id,
                "grade_level": grade.level if grade else "Unknown",
                "stream_id": assignment.stream_id,
                "stream_name": stream.name if stream else None,
                "education_level": education_level
            })
    except Exception as e:
        print(f"Error fetching class teacher assignments: {str(e)}")

    # Get all subject assignments
    subject_assignments = []
    try:
        # Show all subject assignments
        # This is for the "Manage Teacher Transfers" page where admins need to see all assignments
        assignments = TeacherSubjectAssignment.query.filter_by(
            is_class_teacher=False
        ).all()

        for assignment in assignments:
            teacher = Teacher.query.get(assignment.teacher_id)
            subject = Subject.query.get(assignment.subject_id)
            grade = Grade.query.get(assignment.grade_id)
            stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

            subject_assignments.append({
                "id": assignment.id,
                "teacher_id": assignment.teacher_id,
                "teacher_username": teacher.username if teacher else "Unknown",
                "subject_id": assignment.subject_id,
                "subject_name": subject.name if subject else "Unknown",
                "grade_id": assignment.grade_id,
                "grade_level": grade.level if grade else "Unknown",
                "stream_id": assignment.stream_id,
                "stream_name": stream.name if stream else None,
                "education_level": subject.education_level if subject else ""
            })
    except Exception as e:
        print(f"Error fetching subject assignments: {str(e)}")

    # Check if we need to clear session variables after displaying them
    clear_session = False
    if 'assignment_success' in session:
        clear_session = True

    response = render_template(
        'manage_teacher_assignments.html',
        teachers=teachers,
        subjects=subjects,
        grades=grades,
        class_teacher_assignments=class_teacher_assignments,
        subject_assignments=subject_assignments,
        error_message=error_message,
        success_message=success_message
    )

    # Clear session variables after rendering the template
    if clear_session:
        session.pop('assignment_success', None)
        session.pop('assignment_message', None)
        session.pop('assigned_teacher_id', None)
        session.pop('assignment_count', None)
        session.pop('assignment_timestamp', None)

    return response

@classteacher_bp.route('/reassign_class_teacher', methods=['POST'])
@classteacher_required
def reassign_class_teacher():
    """Route for reassigning a class teacher."""
    assignment_id = request.form.get('assignment_id')
    new_teacher_id = request.form.get('new_teacher_id')

    if not assignment_id or not new_teacher_id:
        flash("Missing required information for reassignment.", "error")
        return redirect(url_for('classteacher.manage_teacher_assignments'))

    try:
        # Get the assignment
        assignment = TeacherSubjectAssignment.query.get(assignment_id)
        if not assignment:
            flash("Assignment not found.", "error")
            return redirect(url_for('classteacher.manage_teacher_assignments'))

        # Get the old and new teachers
        old_teacher = Teacher.query.get(assignment.teacher_id)
        new_teacher = Teacher.query.get(new_teacher_id)

        if not new_teacher:
            flash("New teacher not found.", "error")
            return redirect(url_for('classteacher.manage_teacher_assignments'))

        # Get grade and stream info for the message
        grade = Grade.query.get(assignment.grade_id)
        stream_text = ""
        if assignment.stream_id:
            stream = Stream.query.get(assignment.stream_id)
            stream_text = f" Stream {stream.name}"

        # Update the assignment
        assignment.teacher_id = new_teacher_id
        db.session.commit()

        flash(f"Class teacher for Grade {grade.level}{stream_text} changed from {old_teacher.username} to {new_teacher.username}.", "success")
    except Exception as e:
        print(f"Error reassigning class teacher: {str(e)}")
        flash("Error reassigning class teacher. Please try again.", "error")

    return redirect(url_for('classteacher.manage_teacher_assignments'))

@classteacher_bp.route('/reassign_subject_teacher', methods=['POST'])
@classteacher_required
def reassign_subject_teacher():
    """Route for reassigning a subject teacher."""
    assignment_id = request.form.get('assignment_id')
    new_teacher_id = request.form.get('new_teacher_id')

    if not assignment_id or not new_teacher_id:
        flash("Missing required information for reassignment.", "error")
        return redirect(url_for('classteacher.manage_teacher_assignments'))

    try:
        # Get the assignment
        assignment = TeacherSubjectAssignment.query.get(assignment_id)
        if not assignment:
            flash("Assignment not found.", "error")
            return redirect(url_for('classteacher.manage_teacher_assignments'))

        # Get the old and new teachers
        old_teacher = Teacher.query.get(assignment.teacher_id)
        new_teacher = Teacher.query.get(new_teacher_id)

        if not new_teacher:
            flash("New teacher not found.", "error")
            return redirect(url_for('classteacher.manage_teacher_assignments'))

        # Get subject, grade and stream info for the message
        subject = Subject.query.get(assignment.subject_id)
        grade = Grade.query.get(assignment.grade_id)
        stream_text = ""
        if assignment.stream_id:
            stream = Stream.query.get(assignment.stream_id)
            stream_text = f" Stream {stream.name}"

        # Update the assignment
        assignment.teacher_id = new_teacher_id
        db.session.commit()

        flash(f"Teacher for {subject.name} in Grade {grade.level}{stream_text} changed from {old_teacher.username} to {new_teacher.username}.", "success")
    except Exception as e:
        print(f"Error reassigning subject teacher: {str(e)}")
        flash("Error reassigning subject teacher. Please try again.", "error")

    return redirect(url_for('classteacher.manage_teacher_assignments'))

@classteacher_bp.route('/clear_assignment_session', methods=['POST'])
@classteacher_required
def clear_assignment_session():
    """Clear the assignment session variables."""
    if 'assignment_success' in session:
        session.pop('assignment_success', None)
    if 'assignment_message' in session:
        session.pop('assignment_message', None)
    if 'assigned_teacher_id' in session:
        session.pop('assigned_teacher_id', None)
    return '', 204  # No content response

@classteacher_bp.route('/manage_teacher_subjects/<int:teacher_id>', methods=['GET', 'POST'])
@classteacher_required
def manage_teacher_subjects(teacher_id):
    """Route for managing a teacher's subject assignments."""
    # Check for highlight parameter
    highlight = request.args.get('highlight', '0') == '1'
    error_message = None
    success_message = None

    # Get the teacher
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        flash("Teacher not found.", "error")
        return redirect(url_for('classteacher.manage_teacher_assignments'))

    # Get all subjects, grades, and streams
    subjects = Subject.query.all()
    grades = Grade.query.all()
    streams = Stream.query.all()

    # Get the teacher's subject assignments
    subject_assignments = []
    try:
        assignments = TeacherSubjectAssignment.query.filter_by(
            teacher_id=teacher_id,
            is_class_teacher=False
        ).all()

        # Check if we're coming from a bulk assignment or if highlight parameter is set
        highlight_new = False
        if (session.get('assignment_success') and str(session.get('assigned_teacher_id')) == str(teacher_id)) or highlight:
            highlight_new = True

        for assignment in assignments:
            subject = Subject.query.get(assignment.subject_id)
            grade = Grade.query.get(assignment.grade_id)
            stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

            # Determine if this is a new assignment to highlight
            is_new = False
            if highlight_new:
                # In a real application, you would check the creation timestamp
                # Here we'll just mark all as potentially new
                is_new = True

            subject_assignments.append({
                "id": assignment.id,
                "subject_id": assignment.subject_id,
                "subject_name": subject.name if subject else "Unknown",
                "grade_id": assignment.grade_id,
                "grade_level": grade.level if grade else "Unknown",
                "stream_id": assignment.stream_id,
                "stream_name": stream.name if stream else None,
                "education_level": subject.education_level if subject else "",
                "is_new": is_new
            })
    except Exception as e:
        print(f"Error fetching subject assignments: {str(e)}")

    # Handle form submissions
    if request.method == 'POST':
        # Remove subject assignment
        if "remove_subject" in request.form:
            assignment_id = request.form.get("assignment_id")

            try:
                assignment = TeacherSubjectAssignment.query.get(assignment_id)
                if assignment and assignment.teacher_id == teacher_id:
                    subject = Subject.query.get(assignment.subject_id)
                    grade = Grade.query.get(assignment.grade_id)
                    stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

                    stream_text = f" Stream {stream.name}" if stream else ""

                    db.session.delete(assignment)
                    db.session.commit()

                    success_message = f"Removed {subject.name} assignment for Grade {grade.level}{stream_text}."
                else:
                    error_message = "Assignment not found or does not belong to this teacher."
            except Exception as e:
                print(f"Error removing subject assignment: {str(e)}")
                error_message = "Error removing subject assignment."

        # Change subject assignment
        elif "change_subject" in request.form:
            assignment_id = request.form.get("change_assignment_id")
            new_subject_id = request.form.get("new_subject_id")

            if not assignment_id or not new_subject_id:
                error_message = "Missing required information."
            else:
                try:
                    assignment = TeacherSubjectAssignment.query.get(assignment_id)
                    if assignment and assignment.teacher_id == teacher_id:
                        old_subject = Subject.query.get(assignment.subject_id)
                        new_subject = Subject.query.get(new_subject_id)
                        grade = Grade.query.get(assignment.grade_id)
                        stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

                        stream_text = f" Stream {stream.name}" if stream else ""

                        assignment.subject_id = new_subject_id
                        db.session.commit()

                        success_message = f"Changed subject from {old_subject.name} to {new_subject.name} for Grade {grade.level}{stream_text}."
                    else:
                        error_message = "Assignment not found or does not belong to this teacher."
                except Exception as e:
                    print(f"Error changing subject assignment: {str(e)}")
                    error_message = "Error changing subject assignment."

        # Add new subject assignments
        elif "add_subjects" in request.form:
            education_level = request.form.get("education_level")
            grade_id = request.form.get("grade_id")
            stream_id = request.form.get("stream_id") or None
            subject_ids = request.form.getlist("subject_ids")

            if not education_level or not grade_id or not subject_ids:
                error_message = "Please select education level, grade, and at least one subject."
            else:
                try:
                    grade = Grade.query.get(grade_id)
                    stream = Stream.query.get(stream_id) if stream_id else None

                    stream_text = f" Stream {stream.name}" if stream else ""
                    added_count = 0

                    for subject_id in subject_ids:
                        # Check if assignment already exists
                        existing = TeacherSubjectAssignment.query.filter_by(
                            teacher_id=teacher_id,
                            subject_id=subject_id,
                            grade_id=grade_id,
                            stream_id=stream_id,
                            is_class_teacher=False
                        ).first()

                        if not existing:
                            new_assignment = TeacherSubjectAssignment(
                                teacher_id=teacher_id,
                                subject_id=subject_id,
                                grade_id=grade_id,
                                stream_id=stream_id,
                                is_class_teacher=False
                            )
                            db.session.add(new_assignment)
                            added_count += 1

                    if added_count > 0:
                        db.session.commit()
                        success_message = f"Added {added_count} subject assignments for Grade {grade.level}{stream_text}."
                    else:
                        error_message = "No new assignments added. They may already exist."
                except Exception as e:
                    print(f"Error adding subject assignments: {str(e)}")
                    error_message = "Error adding subject assignments."

    return render_template(
        'manage_teacher_subjects.html',
        teacher=teacher,
        subjects=subjects,
        grades=grades,
        streams=streams,
        subject_assignments=subject_assignments,
        error_message=error_message,
        success_message=success_message
    )

@classteacher_bp.route('/bulk_transfer_assignments', methods=['POST'])
@classteacher_required
def bulk_transfer_assignments():
    """Route for bulk transferring assignments from one teacher to another."""
    from_teacher_id = request.form.get('from_teacher_id')
    to_teacher_id = request.form.get('to_teacher_id')
    transfer_class_teacher = 'transfer_class_teacher' in request.form
    transfer_subject_assignments = 'transfer_subject_assignments' in request.form

    if not from_teacher_id or not to_teacher_id:
        flash("Please select both source and destination teachers.", "error")
        return redirect(url_for('classteacher.manage_teacher_assignments'))

    if from_teacher_id == to_teacher_id:
        flash("Source and destination teachers cannot be the same.", "error")
        return redirect(url_for('classteacher.manage_teacher_assignments'))

    if not transfer_class_teacher and not transfer_subject_assignments:
        flash("Please select at least one type of assignment to transfer.", "error")
        return redirect(url_for('classteacher.manage_teacher_assignments'))

    try:
        # Get the teachers
        from_teacher = Teacher.query.get(from_teacher_id)
        to_teacher = Teacher.query.get(to_teacher_id)

        if not from_teacher or not to_teacher:
            flash("One or both teachers not found.", "error")
            return redirect(url_for('classteacher.manage_teacher_assignments'))

        # Track statistics
        class_teacher_count = 0
        subject_count = 0

        # Transfer class teacher assignments if selected
        if transfer_class_teacher:
            class_teacher_assignments = TeacherSubjectAssignment.query.filter_by(
                teacher_id=from_teacher_id,
                is_class_teacher=True
            ).all()

            for assignment in class_teacher_assignments:
                assignment.teacher_id = to_teacher_id
                class_teacher_count += 1

        # Transfer subject assignments if selected
        if transfer_subject_assignments:
            subject_assignments = TeacherSubjectAssignment.query.filter_by(
                teacher_id=from_teacher_id,
                is_class_teacher=False
            ).all()

            for assignment in subject_assignments:
                assignment.teacher_id = to_teacher_id
                subject_count += 1

        # Commit the changes
        db.session.commit()

        # Create success message
        message = f"Successfully transferred assignments from {from_teacher.username} to {to_teacher.username}: "
        if transfer_class_teacher:
            message += f"{class_teacher_count} class teacher assignments"
        if transfer_class_teacher and transfer_subject_assignments:
            message += " and "
        if transfer_subject_assignments:
            message += f"{subject_count} subject assignments"

        flash(message, "success")
    except Exception as e:
        print(f"Error transferring assignments: {str(e)}")
        flash("Error transferring assignments. Please try again.", "error")

    return redirect(url_for('classteacher.manage_teacher_assignments'))

@classteacher_bp.route('/manage_teachers', methods=['GET', 'POST'])
@classteacher_required
def manage_teachers():
    """Route for managing teachers."""
    error_message = None
    success_message = None

    # Get the current teacher
    teacher_id = session.get('teacher_id')
    current_teacher = Teacher.query.get(teacher_id)

    # Get teacher's subject assignments and class teacher status
    try:
        teacher_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=current_teacher.id).all()

        # Get class teacher assignments
        class_teacher_assignments = [assignment for assignment in teacher_assignments if assignment.is_class_teacher]

        # Get subject assignments
        subject_assignments = []
        for assignment in teacher_assignments:
            subject_name = assignment.subject.name
            grade_level = assignment.grade.level
            stream_name = assignment.stream.name if assignment.stream else "All Streams"
            subject_assignments.append({
                "subject": subject_name,
                "grade": grade_level,
                "stream": stream_name
            })
    except Exception as e:
        # If there's an error (like the table doesn't exist), use empty lists
        print(f"Error fetching teacher assignments: {str(e)}")
        teacher_assignments = []
        class_teacher_assignments = []
        subject_assignments = []

    # Get all teachers
    teachers = Teacher.query.all()

    # Get all subjects and grades for the form
    subjects = Subject.query.all()
    grades = Grade.query.all()

    if request.method == 'POST':
        if "add_teacher" in request.form:
            username = request.form.get("username")
            password = request.form.get("password")
            role = request.form.get("role")

            if not username or not password or not role:
                error_message = "Please fill in all required fields."
            else:
                # Check if teacher with same username already exists
                if Teacher.query.filter_by(username=username).first():
                    error_message = f"A teacher with username '{username}' already exists."
                else:
                    new_teacher = Teacher(username=username, password=password, role=role)
                    db.session.add(new_teacher)
                    db.session.commit()
                    success_message = f"Teacher '{username}' added successfully! You can now assign subjects to this teacher using the Bulk Assignments feature."

        elif "update_teacher" in request.form:
            teacher_id = request.form.get("edit_teacher_id")
            new_role = request.form.get("edit_role")
            new_password = request.form.get("edit_password")

            teacher = Teacher.query.get(teacher_id)

            if teacher:
                # Update role
                teacher.role = new_role

                # Update password if provided
                if new_password and new_password.strip():
                    teacher.password = generate_password_hash(new_password)

                db.session.commit()
                success_message = f"Teacher '{teacher.username}' updated successfully!"
            else:
                error_message = "Teacher not found."

        elif "delete_teacher" in request.form:
            teacher_id = request.form.get("teacher_id")
            teacher = Teacher.query.get(teacher_id)

            if teacher:
                db.session.delete(teacher)
                db.session.commit()
                success_message = f"Teacher '{teacher.username}' deleted successfully!"
            else:
                error_message = "Teacher not found."

        elif "delete_assignment" in request.form:
            assignment_id = request.form.get("assignment_id")
            assignment_type = request.form.get("assignment_type")

            if assignment_id:
                try:
                    assignment = TeacherSubjectAssignment.query.get(assignment_id)
                    if assignment:
                        teacher = Teacher.query.get(assignment.teacher_id)

                        if assignment_type == "class_teacher":
                            grade = Grade.query.get(assignment.grade_id)
                            stream_text = ""
                            if assignment.stream_id:
                                stream = Stream.query.get(assignment.stream_id)
                                stream_text = f" Stream {stream.name}"

                            message = f"Class teacher assignment for {teacher.username} in Grade {grade.level}{stream_text} removed successfully."
                        else:
                            subject = Subject.query.get(assignment.subject_id)
                            grade = Grade.query.get(assignment.grade_id)
                            stream_text = ""
                            if assignment.stream_id:
                                stream = Stream.query.get(assignment.stream_id)
                                stream_text = f" Stream {stream.name}"

                            message = f"Subject assignment of {subject.name} to {teacher.username} for Grade {grade.level}{stream_text} removed successfully."

                        db.session.delete(assignment)
                        db.session.commit()
                        success_message = message
                    else:
                        error_message = "Assignment not found."
                except Exception as e:
                    print(f"Error removing assignment: {str(e)}")
                    error_message = "Error removing assignment."

    return render_template(
        'manage_teachers_simple.html',
        teachers=teachers,
        error_message=error_message,
        success_message=success_message
    )

@classteacher_bp.route('/assign_subjects', methods=['GET', 'POST'])
@classteacher_required
def assign_subjects():
    """Route for assigning subjects to teachers."""
    error_message = None
    success_message = None

    # Get all teachers, subjects, grades
    teachers = Teacher.query.all()
    subjects = Subject.query.all()
    grades = Grade.query.all()

    # Get all current assignments
    try:
        assignments = TeacherSubjectAssignment.query.join(Teacher).join(Subject).join(Grade).all()
    except Exception as e:
        print(f"Error fetching teacher assignments: {str(e)}")
        assignments = []

    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id')
        subject_id = request.form.get('subject_id')
        grade_id = request.form.get('grade_id')
        stream_id = request.form.get('stream_id') or None  # Handle empty string
        is_class_teacher = 'is_class_teacher' in request.form

        if not teacher_id or not subject_id or not grade_id:
            error_message = "Please fill in all required fields."
        else:
            # First, check if the table exists and create it if it doesn't
            try:
                # Try to access the table to see if it exists
                TeacherSubjectAssignment.query.first()
            except Exception as e:
                print(f"Table check error: {str(e)}")
                # Table doesn't exist, create it
                try:
                    # SQL to create the teacher_subject_assignment table
                    from sqlalchemy import text
                    create_table_sql = text('''
                    CREATE TABLE IF NOT EXISTS teacher_subject_assignment (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        teacher_id INTEGER NOT NULL,
                        subject_id INTEGER NOT NULL,
                        grade_id INTEGER NOT NULL,
                        stream_id INTEGER,
                        is_class_teacher BOOLEAN DEFAULT 0,
                        FOREIGN KEY (teacher_id) REFERENCES teacher (id),
                        FOREIGN KEY (subject_id) REFERENCES subject (id),
                        FOREIGN KEY (grade_id) REFERENCES grade (id),
                        FOREIGN KEY (stream_id) REFERENCES stream (id)
                    );
                    ''')

                    # Execute the SQL
                    db.session.execute(create_table_sql)
                    db.session.commit()

                    success_message = "Created teacher_subject_assignment table."
                except Exception as table_error:
                    print(f"Error creating table: {str(table_error)}")
                    error_message = "Error creating teacher_subject_assignment table."
                    return render_template(
                        'teacher_assignments.html',
                        teachers=teachers,
                        subjects=subjects,
                        grades=grades,
                        assignments=[],
                        error_message=error_message,
                        success_message=success_message
                    )

            # Now check if this assignment already exists
            try:
                existing = TeacherSubjectAssignment.query.filter_by(
                    teacher_id=teacher_id,
                    subject_id=subject_id,
                    grade_id=grade_id,
                    stream_id=stream_id
                ).first()

                if existing:
                    error_message = "This assignment already exists."
                    return render_template(
                        'teacher_assignments.html',
                        teachers=teachers,
                        subjects=subjects,
                        grades=grades,
                        assignments=assignments,
                        error_message=error_message,
                        success_message=success_message
                    )
            except Exception as e:
                print(f"Error checking for existing assignment: {str(e)}")
                # Continue since we've already tried to create the table

            # If this is a class teacher, check if there's already one for this grade/stream
            if is_class_teacher and stream_id:
                try:
                    existing_class_teacher = TeacherSubjectAssignment.query.filter_by(
                        grade_id=grade_id,
                        stream_id=stream_id,
                        is_class_teacher=True
                    ).first()

                    if existing_class_teacher:
                        teacher = Teacher.query.get(existing_class_teacher.teacher_id)
                        error_message = f"There is already a class teacher assigned to this class: {teacher.username}"
                        return render_template(
                            'teacher_assignments.html',
                            teachers=teachers,
                            subjects=subjects,
                            grades=grades,
                            assignments=assignments,
                            error_message=error_message,
                            success_message=success_message
                        )
                except Exception as e:
                    print(f"Error checking for existing class teacher: {str(e)}")
                    # Continue with the assignment since we've already tried to create the table

            # Create the new assignment
            try:
                new_assignment = TeacherSubjectAssignment(
                    teacher_id=teacher_id,
                    subject_id=subject_id,
                    grade_id=grade_id,
                    stream_id=stream_id,
                    is_class_teacher=is_class_teacher
                )

                db.session.add(new_assignment)
                db.session.commit()

                teacher = Teacher.query.get(teacher_id)
                subject = Subject.query.get(subject_id)
                grade = Grade.query.get(grade_id)

                success_message = f"Successfully assigned {subject.name} to {teacher.username} for Grade {grade.level}"
                if stream_id:
                    stream = Stream.query.get(stream_id)
                    success_message += f" Stream {stream.name}"

                # Refresh assignments list
                try:
                    assignments = TeacherSubjectAssignment.query.join(Teacher).join(Subject).join(Grade).all()
                except Exception as e:
                    print(f"Error refreshing assignments: {str(e)}")
                    assignments = []
            except Exception as e:
                print(f"Error creating assignment: {str(e)}")
                error_message = "Error creating assignment. The teacher_subject_assignment table may not exist. Please run the migration script to create it."

    return render_template(
        'teacher_assignments.html',
        teachers=teachers,
        subjects=subjects,
        grades=grades,
        assignments=assignments,
        error_message=error_message,
        success_message=success_message
    )

@classteacher_bp.route('/bulk_assign_subjects', methods=['POST'])
@classteacher_required
def bulk_assign_subjects():
    """Route for bulk assigning subjects to teachers."""
    error_message = None
    success_message = None

    # Get form data
    teacher_id = request.form.get('bulk_teacher_id')
    subject_ids = request.form.getlist('bulk_subjects')
    grade_ids = request.form.getlist('bulk_grades')
    is_class_teacher = 'bulk_is_class_teacher' in request.form

    # Validate input
    if not teacher_id or not subject_ids or not grade_ids:
        flash("Please select a teacher, at least one subject, and at least one grade.", "error")
        return redirect(url_for('classteacher.assign_subjects'))

    # First, check if the table exists and create it if it doesn't
    try:
        # Try to access the table to see if it exists
        TeacherSubjectAssignment.query.first()
    except Exception as e:
        print(f"Table check error: {str(e)}")
        # Table doesn't exist, create it
        try:
            # SQL to create the teacher_subject_assignment table
            from sqlalchemy import text
            create_table_sql = text('''
            CREATE TABLE IF NOT EXISTS teacher_subject_assignment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                grade_id INTEGER NOT NULL,
                stream_id INTEGER,
                is_class_teacher BOOLEAN DEFAULT 0,
                FOREIGN KEY (teacher_id) REFERENCES teacher (id),
                FOREIGN KEY (subject_id) REFERENCES subject (id),
                FOREIGN KEY (grade_id) REFERENCES grade (id),
                FOREIGN KEY (stream_id) REFERENCES stream (id)
            );
            ''')

            # Execute the SQL
            db.session.execute(create_table_sql)
            db.session.commit()

            flash("Created teacher_subject_assignment table.", "success")
        except Exception as table_error:
            print(f"Error creating table: {str(table_error)}")
            flash("Error creating teacher_subject_assignment table.", "error")
            return redirect(url_for('classteacher.assign_subjects'))

    # Get the teacher
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        flash("Teacher not found.", "error")
        return redirect(url_for('classteacher.assign_subjects'))

    # Track statistics for the flash message
    assignments_created = 0
    assignments_skipped = 0
    class_teacher_conflicts = 0

    # Create assignments for each subject and grade combination
    for subject_id in subject_ids:
        subject = Subject.query.get(subject_id)
        if not subject:
            continue

        for grade_id in grade_ids:
            grade = Grade.query.get(grade_id)
            if not grade:
                continue

            # Get streams for this grade
            streams = Stream.query.filter_by(grade_id=grade_id).all()

            # If there are no streams, create an assignment for the whole grade
            if not streams:
                try:
                    # Check if assignment already exists
                    existing = TeacherSubjectAssignment.query.filter_by(
                        teacher_id=teacher_id,
                        subject_id=subject_id,
                        grade_id=grade_id,
                        stream_id=None
                    ).first()

                    if existing:
                        assignments_skipped += 1
                        continue

                    # Create the assignment
                    new_assignment = TeacherSubjectAssignment(
                        teacher_id=teacher_id,
                        subject_id=subject_id,
                        grade_id=grade_id,
                        stream_id=None,
                        is_class_teacher=is_class_teacher
                    )

                    db.session.add(new_assignment)
                    assignments_created += 1

                except Exception as e:
                    print(f"Error creating assignment: {str(e)}")
                    continue
            else:
                # Create an assignment for each stream
                for stream in streams:
                    try:
                        # Check if assignment already exists
                        existing = TeacherSubjectAssignment.query.filter_by(
                            teacher_id=teacher_id,
                            subject_id=subject_id,
                            grade_id=grade_id,
                            stream_id=stream.id
                        ).first()

                        if existing:
                            assignments_skipped += 1
                            continue

                        # If this is a class teacher, check if there's already one for this grade/stream
                        if is_class_teacher:
                            existing_class_teacher = TeacherSubjectAssignment.query.filter_by(
                                grade_id=grade_id,
                                stream_id=stream.id,
                                is_class_teacher=True
                            ).first()

                            if existing_class_teacher and int(existing_class_teacher.teacher_id) != int(teacher_id):
                                class_teacher_conflicts += 1
                                continue

                        # Create the assignment
                        new_assignment = TeacherSubjectAssignment(
                            teacher_id=teacher_id,
                            subject_id=subject_id,
                            grade_id=grade_id,
                            stream_id=stream.id,
                            is_class_teacher=is_class_teacher
                        )

                        db.session.add(new_assignment)
                        assignments_created += 1

                    except Exception as e:
                        print(f"Error creating assignment: {str(e)}")
                        continue

    # Commit all the new assignments
    try:
        db.session.commit()

        # Create a summary message
        message = f"Created {assignments_created} new assignments for {teacher.username}. "
        if assignments_skipped > 0:
            message += f"Skipped {assignments_skipped} existing assignments. "
        if class_teacher_conflicts > 0:
            message += f"Skipped {class_teacher_conflicts} class teacher assignments due to conflicts."

        flash(message, "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error committing assignments: {str(e)}")
        flash("Error creating assignments. Please try again.", "error")

    return redirect(url_for('classteacher.assign_subjects'))

@classteacher_bp.route('/remove_assignment', methods=['POST'])
@classteacher_required
def remove_assignment():
    """Route for removing a teacher subject assignment."""
    assignment_id = request.form.get('assignment_id')

    if assignment_id:
        try:
            assignment = TeacherSubjectAssignment.query.get(assignment_id)
            if assignment:
                teacher = Teacher.query.get(assignment.teacher_id)
                subject = Subject.query.get(assignment.subject_id)
                grade = Grade.query.get(assignment.grade_id)

                message = f"Assignment of {subject.name} to {teacher.username} for Grade {grade.level}"
                if assignment.stream_id:
                    stream = Stream.query.get(assignment.stream_id)
                    message += f" Stream {stream.name}"
                message += " removed successfully."

                db.session.delete(assignment)
                db.session.commit()

                flash(message, "success")
        except Exception as e:
            print(f"Error removing assignment: {str(e)}")
            flash("Error removing assignment. The teacher_subject_assignment table may not exist.", "error")

    return redirect(url_for('classteacher.assign_subjects'))

@classteacher_bp.route('/get_grade_streams/<int:grade_id>', methods=['GET'])
@classteacher_required
def get_grade_streams(grade_id):
    """API endpoint to get streams for a grade."""
    streams = Stream.query.filter_by(grade_id=grade_id).all()
    return jsonify({
        'streams': [{'id': stream.id, 'name': stream.name} for stream in streams]
    })

@classteacher_bp.route('/teacher_streams/<int:grade_id>', methods=['GET'])
@classteacher_required
def teacher_streams(grade_id):
    """API endpoint to get streams for a grade (for manage_teachers page)."""
    streams = Stream.query.filter_by(grade_id=grade_id).all()
    return jsonify({
        'streams': [{'id': stream.id, 'name': stream.name} for stream in streams]
    })

@classteacher_bp.route('/get_teacher_assignments/<int:teacher_id>', methods=['GET'])
@classteacher_required
def get_teacher_assignments(teacher_id):
    """API endpoint to get all assignments for a specific teacher."""
    try:
        # Check if the teacher exists
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            return jsonify({'error': 'Teacher not found'}), 404

        # Get all assignments for the teacher
        assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).all()

        # Format the assignments for the response
        formatted_assignments = []
        for assignment in assignments:
            subject = Subject.query.get(assignment.subject_id)
            grade = Grade.query.get(assignment.grade_id)
            stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

            formatted_assignments.append({
                'id': assignment.id,
                'subject': subject.name if subject else 'Unknown Subject',
                'grade': grade.level if grade else 'Unknown Grade',
                'stream': stream.name if stream else None,
                'is_class_teacher': assignment.is_class_teacher
            })

        return jsonify({
            'teacher': teacher.username,
            'assignments': formatted_assignments
        })
    except Exception as e:
        print(f"Error fetching teacher assignments: {str(e)}")
        return jsonify({'error': 'Failed to fetch assignments'}), 500

@classteacher_bp.route('/api/check_stream_status/<grade>/<term>/<assessment_type>')
@classteacher_required
def check_stream_status(grade, term, assessment_type):
    """API endpoint to check if all streams in a grade have reports generated."""
    grade_obj = Grade.query.filter_by(level=grade).first()
    if not grade_obj:
        return jsonify({"error": f"Grade {grade} not found"}), 404

    streams = Stream.query.filter_by(grade_id=grade_obj.id).all()
    if not streams:
        return jsonify({"error": f"No streams found for grade {grade}"}), 404

    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()
    if not term_obj or not assessment_type_obj:
        return jsonify({"error": "Invalid term or assessment type"}), 404

    # Check each stream for marks
    stream_status = {}
    for stream in streams:
        # Check if any marks exist for this stream
        marks = Mark.query.join(Student).filter(
            Student.stream_id == stream.id,
            Mark.term_id == term_obj.id,
            Mark.assessment_type_id == assessment_type_obj.id
        ).first()

        stream_status[stream.name] = marks is not None

    return jsonify({
        "grade": grade,
        "term": term,
        "assessment_type": assessment_type,
        "streams": stream_status
    })