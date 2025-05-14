"""
Enhanced teacher assignment functionality for the Hillview School Management System.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask import session
from sqlalchemy import text
from ..extensions import db
from ..models import Teacher, Subject, Grade, Stream, TeacherSubjectAssignment
from .classteacher import classteacher_required

# Create a blueprint for structured assignments
structured_assignments_bp = Blueprint('structured_assignments', __name__)

@structured_assignments_bp.route('/advanced_assignments', methods=['GET'])
@classteacher_required
def structured_assignments():
    """Route for the structured teacher assignments page."""
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
        'teacher_assignments_updated.html',
        teachers=teachers,
        subjects=subjects,
        grades=grades,
        assignments=assignments,
        error_message=None,
        success_message=None
    )

@structured_assignments_bp.route('/structured_bulk_assign', methods=['POST'])
@classteacher_required
def structured_bulk_assign():
    """Route for structured bulk assignment of subjects to teachers."""
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

    # Get the teacher ID
    teacher_id = request.form.get('bulk_teacher_id')
    if not teacher_id:
        flash("Please select a teacher.", "error")
        return redirect(url_for('structured_assignments.structured_assignments'))

    # Check if the teacher exists
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        flash("Teacher not found.", "error")
        return redirect(url_for('structured_assignments.structured_assignments'))

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
            return redirect(url_for('structured_assignments.structured_assignments'))

    # Get class teacher status
    is_class_teacher = 'bulk_is_class_teacher' in request.form

    # Track statistics
    assignments_created = 0
    assignments_skipped = 0
    class_teacher_conflicts = 0

    # Process each education level
    for level in ['lower_primary', 'upper_primary', 'junior_secondary']:
        # Get subjects for this level
        subject_ids = request.form.getlist(f'{level}_subjects')
        if not subject_ids:
            continue

        # Get grades for this level
        grade_ids = request.form.getlist(f'{level}_grades')
        if not grade_ids:
            continue

        # Process each grade
        for grade_id in grade_ids:
            # Get streams for this grade
            stream_ids = request.form.getlist(f'{level}_streams_{grade_id}')

            # If no streams selected, assign to the whole grade
            if not stream_ids:
                for subject_id in subject_ids:
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
                # Process each stream
                for stream_id in stream_ids:
                    for subject_id in subject_ids:
                        try:
                            # Check if assignment already exists
                            existing = TeacherSubjectAssignment.query.filter_by(
                                teacher_id=teacher_id,
                                subject_id=subject_id,
                                grade_id=grade_id,
                                stream_id=stream_id
                            ).first()

                            if existing:
                                assignments_skipped += 1
                                continue

                            # If this is a class teacher, check if there's already one for this grade/stream
                            if is_class_teacher:
                                existing_class_teacher = TeacherSubjectAssignment.query.filter_by(
                                    grade_id=grade_id,
                                    stream_id=stream_id,
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
                                stream_id=stream_id,
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

    return redirect(url_for('structured_assignments.structured_assignments'))

def register_blueprint(app):
    """Register the blueprint with the app."""
    app.register_blueprint(structured_assignments_bp, url_prefix='/classteacher')
