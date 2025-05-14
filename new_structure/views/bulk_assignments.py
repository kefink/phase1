"""
Bulk teacher assignment functionality for the Hillview School Management System.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask import session
from sqlalchemy import text
from ..extensions import db
from ..models import Teacher, Subject, Grade, Stream, TeacherSubjectAssignment
from .classteacher import classteacher_required
from datetime import datetime
import json

# Create a blueprint for bulk assignments
bulk_assignments_bp = Blueprint('bulk_assignments', __name__)

@bulk_assignments_bp.route('/bulk_assignments', methods=['GET'])
@classteacher_required
def bulk_assignments():
    """Route for the bulk teacher assignments page."""
    # Get all teachers, subjects, and grades
    teachers = Teacher.query.all()
    subjects = Subject.query.all()
    grades = Grade.query.all()

    # Get all current assignments
    try:
        assignments = TeacherSubjectAssignment.query.join(Teacher).join(Subject).join(Grade).all()
    except Exception as e:
        print(f"Error fetching teacher assignments: {str(e)}")
        assignments = []

    return render_template(
        'teacher_bulk_assignment.html',
        teachers=teachers,
        subjects=subjects,
        grades=grades,
        assignments=assignments,
        error_message=None,
        success_message=None
    )

@bulk_assignments_bp.route('/get_subjects_by_level/<education_level>', methods=['GET'])
@classteacher_required
def get_subjects_by_level(education_level):
    """API endpoint to get subjects for a specific education level."""
    # Debug
    print(f"Getting subjects for education level: {education_level}")

    # Try different formats for education level
    possible_formats = [
        education_level,                      # As is (e.g., "lower_primary")
        education_level.lower(),              # Lowercase (e.g., "lower_primary")
        education_level.upper(),              # Uppercase (e.g., "LOWER_PRIMARY")
        education_level.replace('_', ' '),    # Replace underscores with spaces (e.g., "lower primary")
    ]

    subjects = []
    for format in possible_formats:
        print(f"Trying to find subjects with education level: {format}")
        level_subjects = Subject.query.filter_by(education_level=format).all()
        if level_subjects:
            print(f"Found {len(level_subjects)} subjects with education level: {format}")
            subjects = level_subjects
            break

    # If no subjects found, check if we have any subjects at all
    if not subjects:
        all_subjects = Subject.query.all()
        print(f"Total subjects in database: {len(all_subjects)}")
        if all_subjects:
            print(f"Available education levels: {set([s.education_level for s in all_subjects if s.education_level])}")

            # If we have subjects but none match the requested education level,
            # let's try to find subjects with a similar education level
            for subject in all_subjects:
                if subject.education_level and education_level.lower() in subject.education_level.lower():
                    print(f"Found similar education level: {subject.education_level}")
                    similar_subjects = Subject.query.filter_by(education_level=subject.education_level).all()
                    if similar_subjects:
                        print(f"Using {len(similar_subjects)} subjects with similar education level: {subject.education_level}")
                        subjects = similar_subjects
                        break

    return jsonify({
        'subjects': [{'id': subject.id, 'name': subject.name} for subject in subjects]
    })

@bulk_assignments_bp.route('/get_grade_streams_by_level/<grade_level>', methods=['GET'])
@classteacher_required
def get_grade_streams_by_level(grade_level):
    """API endpoint to get streams for a grade by grade level."""
    # Debug
    print(f"Getting streams for grade level: {grade_level}")

    # Try different formats for grade level
    possible_formats = [
        grade_level,                  # As is (e.g., "1")
        f"Grade {grade_level}",       # With "Grade " prefix (e.g., "Grade 1")
        f"grade {grade_level}",       # With lowercase "grade " prefix
        f"Grade{grade_level}",        # Without space (e.g., "Grade1")
    ]

    grade = None
    for format in possible_formats:
        print(f"Trying to find grade with level: {format}")
        grade = Grade.query.filter_by(level=format).first()
        if grade:
            print(f"Found grade with level: {format}")
            break

    if not grade:
        print(f"No grade found for any format of level: {grade_level}")
        return jsonify({'streams': []})

    print(f"Found grade: {grade.level} (ID: {grade.id})")

    # Get streams for this grade
    streams = Stream.query.filter_by(grade_id=grade.id).all()
    print(f"Found {len(streams)} streams for grade {grade.level}")

    return jsonify({
        'streams': [{'id': stream.id, 'name': stream.name} for stream in streams]
    })

@bulk_assignments_bp.route('/bulk_assign_subjects_new', methods=['POST'])
@classteacher_required
def bulk_assign_subjects_new():
    """Route for bulk assigning subjects to teachers with the new interface."""
    # Debug: Print all form data
    print("Form data received:")
    for key, value in request.form.items():
        print(f"{key}: {value}")

    # Debug: Print all form lists
    print("Form lists received:")
    for key in request.form:
        values = request.form.getlist(key)
        if len(values) > 1:
            print(f"{key}: {values}")
        # Also print subjects lists which might have multiple values
        if key.startswith('subjects_'):
            print(f"{key}: {values}")

    # Debug: Check if any subjects_X[] keys exist
    print("Checking for subjects_X[] keys:")
    for i in range(1, 10):  # Check for up to 10 education levels
        key = f'subjects_{i}[]'
        values = request.form.getlist(key)
        print(f"{key}: {values}")

    # Debug: Print request.form.keys()
    print("All form keys:")
    print(list(request.form.keys()))

    # Get the teacher ID
    teacher_id = request.form.get('teacher_id')
    if not teacher_id:
        flash("Please select a teacher.", "error")
        return redirect(url_for('bulk_assignments.bulk_assignments'))

    # Check if the teacher exists
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        flash("Teacher not found.", "error")
        return redirect(url_for('classteacher.manage_teachers'))

    # Check if the table exists and create it if it doesn't
    try:
        TeacherSubjectAssignment.query.first()
    except Exception as e:
        print(f"Table check error: {str(e)}")
        try:
            # Create the table
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
            db.session.execute(create_table_sql)
            db.session.commit()
            flash("Created teacher_subject_assignment table.", "success")
        except Exception as table_error:
            print(f"Error creating table: {str(table_error)}")
            flash("Error creating teacher_subject_assignment table.", "error")
            return redirect(url_for('bulk_assignments.bulk_assignments'))

    # Track statistics
    assignments_created = 0
    assignments_skipped = 0
    class_teacher_conflicts = 0

    # Get the number of education levels
    level_count = int(request.form.get('level_count', 1))

    # Process each education level
    for level_num in range(1, level_count + 1):
        # Check if this level section exists in the form
        education_level_key = f'education_level_{level_num}'
        if education_level_key not in request.form:
            continue

        education_level = request.form.get(education_level_key)
        grade_level = request.form.get(f'grade_id_{level_num}')
        stream_id = request.form.get(f'stream_id_{level_num}') or None
        is_class_teacher = f'is_class_teacher_{level_num}' in request.form

        # Get the grade ID from the grade level
        grade = Grade.query.filter_by(level=grade_level).first()
        if not grade:
            continue

        grade_id = grade.id

        # Get selected subjects for this level
        # The form field name should be 'subjects_1[]'
        field_name = f'subjects_{level_num}[]'
        subject_ids = request.form.getlist(field_name)

        # Debug print to see what's being received
        print(f"Subject IDs for level {level_num} using {field_name}: {subject_ids}")

        if not subject_ids:
            # Try alternate form field name format without brackets
            alternate_field = f'subjects_{level_num}'
            subject_ids = request.form.getlist(alternate_field)
            print(f"Trying alternate field: {alternate_field} = {subject_ids}")

            if not subject_ids:
                print(f"No subjects found for level {level_num} - skipping this level")
                continue

        # Process each subject
        for subject_id in subject_ids:
            try:
                # For hardcoded subject IDs (100+), find or create the subject
                actual_subject_id = subject_id
                if int(subject_id) >= 100:  # This is a hardcoded ID
                    # Extract the name based on the ID range
                    subject_name = None
                    education_level = None

                    if 100 <= int(subject_id) < 200:
                        # Lower primary subjects
                        education_level = "lower_primary"
                        if int(subject_id) == 101: subject_name = "LITERACY ACTIVITIES"
                        elif int(subject_id) == 102: subject_name = "KISWAHILI LANGUAGE ACTIVITIES"
                        elif int(subject_id) == 103: subject_name = "ENGLISH LANGUAGE ACTIVITIES"
                        elif int(subject_id) == 104: subject_name = "MATHEMATICAL ACTIVITIES"
                        elif int(subject_id) == 105: subject_name = "ENVIRONMENTAL ACTIVITIES"
                        elif int(subject_id) == 106: subject_name = "HYGIENE AND NUTRITION ACTIVITIES"
                        elif int(subject_id) == 107: subject_name = "RELIGIOUS EDUCATION ACTIVITIES"
                        elif int(subject_id) == 108: subject_name = "MOVEMENT AND CREATIVE ACTIVITIES"

                    elif 200 <= int(subject_id) < 300:
                        # Upper primary subjects
                        education_level = "upper_primary"
                        if int(subject_id) == 201: subject_name = "ENGLISH"
                        elif int(subject_id) == 202: subject_name = "KISWAHILI"
                        elif int(subject_id) == 203: subject_name = "MATHEMATICS"
                        elif int(subject_id) == 204: subject_name = "SCIENCE AND TECHNOLOGY"
                        elif int(subject_id) == 205: subject_name = "SOCIAL STUDIES"
                        elif int(subject_id) == 206: subject_name = "RELIGIOUS EDUCATION"
                        elif int(subject_id) == 207: subject_name = "CREATIVE ARTS"
                        elif int(subject_id) == 208: subject_name = "PHYSICAL AND HEALTH EDUCATION"
                        elif int(subject_id) == 209: subject_name = "AGRICULTURE"

                    elif 300 <= int(subject_id) < 400:
                        # Junior secondary subjects
                        education_level = "junior_secondary"
                        if int(subject_id) == 301: subject_name = "ENGLISH"
                        elif int(subject_id) == 302: subject_name = "KISWAHILI"
                        elif int(subject_id) == 303: subject_name = "MATHEMATICS"
                        elif int(subject_id) == 304: subject_name = "INTEGRATED SCIENCE"
                        elif int(subject_id) == 305: subject_name = "HEALTH EDUCATION"
                        elif int(subject_id) == 306: subject_name = "PRE-TECHNICAL STUDIES"
                        elif int(subject_id) == 307: subject_name = "SOCIAL STUDIES"
                        elif int(subject_id) == 308: subject_name = "RELIGIOUS EDUCATION"
                        elif int(subject_id) == 309: subject_name = "BUSINESS STUDIES"

                    if subject_name and education_level:
                        # Check if subject exists
                        subject = Subject.query.filter_by(name=subject_name, education_level=education_level).first()
                        if not subject:
                            # Create the subject
                            subject = Subject(name=subject_name, education_level=education_level)
                            db.session.add(subject)
                            db.session.flush()  # Get the ID without committing
                            print(f"Created subject: {subject_name} (ID: {subject.id}) for {education_level}")

                        actual_subject_id = subject.id

                # Check if assignment already exists
                print(f"Checking if assignment exists: teacher_id={teacher_id}, subject_id={actual_subject_id}, grade_id={grade_id}, stream_id={stream_id}")
                existing = TeacherSubjectAssignment.query.filter_by(
                    teacher_id=teacher_id,
                    subject_id=actual_subject_id,
                    grade_id=grade_id,
                    stream_id=stream_id
                ).first()

                if existing:
                    print(f"Assignment already exists: {existing}")
                    assignments_skipped += 1
                    continue
                else:
                    print(f"Assignment does not exist, creating new one")

                # If this is a class teacher, check if there's already one for this grade/stream
                if is_class_teacher and stream_id:
                    print(f"Checking for existing class teacher: grade_id={grade_id}, stream_id={stream_id}")
                    existing_class_teacher = TeacherSubjectAssignment.query.filter_by(
                        grade_id=grade_id,
                        stream_id=stream_id,
                        is_class_teacher=True
                    ).first()

                    if existing_class_teacher:
                        print(f"Found existing class teacher: {existing_class_teacher}")
                        if int(existing_class_teacher.teacher_id) != int(teacher_id):
                            print(f"Conflict: Existing teacher ID {existing_class_teacher.teacher_id} != Current teacher ID {teacher_id}")
                            class_teacher_conflicts += 1
                            continue
                        else:
                            print(f"Same teacher, no conflict")
                    else:
                        print(f"No existing class teacher found")

                # Create the assignment
                try:
                    print(f"Creating new assignment: teacher_id={teacher_id}, subject_id={actual_subject_id}, grade_id={grade_id}, stream_id={stream_id}, is_class_teacher={is_class_teacher}")

                    # Check if the teacher exists
                    teacher_obj = Teacher.query.get(teacher_id)
                    if not teacher_obj:
                        print(f"ERROR: Teacher with ID {teacher_id} not found")
                        continue

                    # Check if the subject exists
                    subject_obj = Subject.query.get(actual_subject_id)
                    if not subject_obj:
                        print(f"ERROR: Subject with ID {actual_subject_id} not found")
                        continue

                    # Check if the grade exists
                    grade_obj = Grade.query.get(grade_id)
                    if not grade_obj:
                        print(f"ERROR: Grade with ID {grade_id} not found")
                        continue

                    # Check if the stream exists (if provided)
                    if stream_id:
                        stream_obj = Stream.query.get(stream_id)
                        if not stream_obj:
                            print(f"ERROR: Stream with ID {stream_id} not found")
                            continue

                    new_assignment = TeacherSubjectAssignment(
                        teacher_id=teacher_id,
                        subject_id=actual_subject_id,
                        grade_id=grade_id,
                        stream_id=stream_id,
                        is_class_teacher=is_class_teacher
                    )

                    print(f"Assignment created: {new_assignment}")
                    db.session.add(new_assignment)
                    print(f"Assignment added to session")
                    assignments_created += 1
                except Exception as e:
                    print(f"ERROR creating assignment: {str(e)}")
                    continue
            except Exception as e:
                print(f"Error creating assignment: {str(e)}")
                continue

    # Commit all the new assignments
    try:
        print(f"Attempting to commit {assignments_created} new assignments to the database")
        db.session.commit()
        print(f"Successfully committed {assignments_created} new assignments to the database")

        # Create a summary message
        message = f"Created {assignments_created} new assignments for {teacher.username}. "
        if assignments_skipped > 0:
            message += f"Skipped {assignments_skipped} existing assignments. "
        if class_teacher_conflicts > 0:
            message += f"Skipped {class_teacher_conflicts} class teacher assignments due to conflicts."

        print(f"Success message: {message}")
        flash(message, "success")

        # Store success in session to display on redirect
        session['assignment_success'] = True
        session['assignment_message'] = message
        session['assigned_teacher_id'] = teacher_id
        session['assignment_count'] = assignments_created
        session['assignment_timestamp'] = str(datetime.now())

        # Redirect to the manage teacher assignments page to see the results
        return redirect(url_for('classteacher.manage_teacher_assignments'))
    except Exception as e:
        db.session.rollback()
        print(f"Error committing assignments: {str(e)}")
        flash("Error creating assignments. Please try again.", "error")

    # Redirect to the manage teacher assignments page to see the results
    return redirect(url_for('classteacher.manage_teacher_assignments'))

@bulk_assignments_bp.route('/edit_assignment/<int:assignment_id>/<assignment_type>', methods=['GET'])
@classteacher_required
def edit_assignment(assignment_id, assignment_type):
    """Route for editing a teacher assignment."""
    error_message = None
    success_message = None

    # Get the assignment
    assignment = TeacherSubjectAssignment.query.get(assignment_id)
    if not assignment:
        flash("Assignment not found.", "error")
        return redirect(url_for('classteacher.manage_teachers'))

    # Get all teachers, subjects, grades, and streams
    teachers = Teacher.query.all()
    subjects = Subject.query.all()
    grades = Grade.query.all()

    # Get streams for the current grade
    streams = Stream.query.filter_by(grade_id=assignment.grade_id).all()

    return render_template(
        'edit_assignment.html',
        assignment=assignment,
        assignment_type=assignment_type,
        teachers=teachers,
        subjects=subjects,
        grades=grades,
        streams=streams,
        error_message=error_message,
        success_message=success_message
    )

@bulk_assignments_bp.route('/update_assignment', methods=['POST'])
@classteacher_required
def update_assignment():
    """Route for updating a teacher assignment."""
    assignment_id = request.form.get('assignment_id')
    assignment_type = request.form.get('assignment_type')

    if not assignment_id:
        flash("Assignment ID is required.", "error")
        return redirect(url_for('classteacher.manage_teachers'))

    # Get the assignment
    assignment = TeacherSubjectAssignment.query.get(assignment_id)
    if not assignment:
        flash("Assignment not found.", "error")
        return redirect(url_for('classteacher.manage_teachers'))

    # Get form data
    teacher_id = request.form.get('teacher_id')
    subject_id = request.form.get('subject_id') if assignment_type == 'subject' else assignment.subject_id
    grade_id = request.form.get('grade_id')
    stream_id = request.form.get('stream_id') or None  # Handle empty string
    is_class_teacher = 'is_class_teacher' in request.form

    # Validate input
    if not teacher_id or not grade_id:
        flash("Please fill in all required fields.", "error")
        return redirect(url_for('bulk_assignments.edit_assignment', assignment_id=assignment_id, assignment_type=assignment_type))

    if assignment_type == 'subject' and not subject_id:
        flash("Please select a subject.", "error")
        return redirect(url_for('bulk_assignments.edit_assignment', assignment_id=assignment_id, assignment_type=assignment_type))

    # If this is a class teacher, check if there's already one for this grade/stream
    if is_class_teacher and stream_id:
        existing_class_teacher = TeacherSubjectAssignment.query.filter_by(
            grade_id=grade_id,
            stream_id=stream_id,
            is_class_teacher=True
        ).first()

        if existing_class_teacher and existing_class_teacher.id != int(assignment_id) and int(existing_class_teacher.teacher_id) != int(teacher_id):
            teacher = Teacher.query.get(existing_class_teacher.teacher_id)
            flash(f"There is already a class teacher assigned to this class: {teacher.username}", "error")
            return redirect(url_for('bulk_assignments.edit_assignment', assignment_id=assignment_id, assignment_type=assignment_type))

    # Update the assignment
    try:
        assignment.teacher_id = teacher_id
        if assignment_type == 'subject':
            assignment.subject_id = subject_id
        assignment.grade_id = grade_id
        assignment.stream_id = stream_id
        assignment.is_class_teacher = is_class_teacher

        db.session.commit()

        # Get the updated entities for the success message
        teacher = Teacher.query.get(teacher_id)
        grade = Grade.query.get(grade_id)

        if assignment_type == 'class_teacher':
            stream_text = ""
            if stream_id:
                stream = Stream.query.get(stream_id)
                stream_text = f" Stream {stream.name}"

            message = f"Class teacher assignment for {teacher.username} in Grade {grade.level}{stream_text} updated successfully."
        else:
            subject = Subject.query.get(subject_id)
            stream_text = ""
            if stream_id:
                stream = Stream.query.get(stream_id)
                stream_text = f" Stream {stream.name}"

            message = f"Subject assignment of {subject.name} to {teacher.username} for Grade {grade.level}{stream_text} updated successfully."

        flash(message, "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error updating assignment: {str(e)}")
        flash("Error updating assignment. Please try again.", "error")

    return redirect(url_for('classteacher.manage_teachers'))

def register_blueprint(app):
    """Register the blueprint with the app."""
    app.register_blueprint(bulk_assignments_bp, url_prefix='/classteacher')
