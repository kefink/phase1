"""
Admin/Headteacher views for the Hillview School Management System.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..models import Teacher, Student, Grade, Stream, Subject, Term, AssessmentType, Mark, TeacherSubjectAssignment
from ..services import is_authenticated, get_role
from ..extensions import db
from ..services.admin_cache_service import (
    cache_dashboard_stats, get_cached_dashboard_stats,
    cache_subject_list, get_cached_subject_list,
    invalidate_admin_cache
)
from functools import wraps
import os
import pandas as pd

# Create a blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/headteacher')

# Decorator for requiring admin authentication
def admin_required(f):
    """Decorator to require admin authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session) or get_role(session) != 'headteacher':
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    """Route for the admin/headteacher dashboard."""
    # Check if we have cached dashboard stats
    cached_stats = get_cached_dashboard_stats()
    if cached_stats:
        return render_template('headteacher.html', **cached_stats)

    # If no cache or cache miss, generate the dashboard stats
    # Total students
    total_students = Student.query.count()

    # Total teachers
    total_teachers = Teacher.query.count()

    # Total classes (number of streams)
    total_classes = Stream.query.count()

    # Average performance (compute from marks if available)
    marks = Mark.query.all()
    if marks:
        total_marks = sum(mark.mark for mark in marks if mark.mark is not None)
        count_marks = len([mark for mark in marks if mark.mark is not None])
        avg_performance = round(total_marks / count_marks, 2) if count_marks > 0 else 0
    else:
        avg_performance = 75  # Placeholder

    # Top performing class (stream-level performance)
    top_class = "N/A"
    top_class_score = 0
    stream_performances = {}
    for stream in Stream.query.all():
        stream_marks = Mark.query.join(Student, Mark.student_id == Student.id).filter(Student.stream_id == stream.id).all()
        if stream_marks:
            stream_avg = round(sum(mark.mark for mark in stream_marks) / len(stream_marks), 2)
            stream_name = f"{stream.grade.level} {stream.name}" if stream.grade else stream.name
            stream_performances[stream_name] = stream_avg
    if stream_performances:
        top_class = max(stream_performances, key=stream_performances.get)
        top_class_score = stream_performances[top_class]

    # Least performing grade
    least_performing_grade = "N/A"
    least_grade_score = 0
    grade_performances = {}
    for grade in Grade.query.all():
        grade_marks = Mark.query.join(Student, Mark.student_id == Student.id).join(Stream, Student.stream_id == Stream.id).filter(Stream.grade_id == grade.id).all()
        if grade_marks:
            grade_avg = round(sum(mark.mark for mark in grade_marks) / len(grade_marks), 2)
            grade_performances[grade.level] = grade_avg
    if grade_performances:
        least_performing_grade = min(grade_performances, key=grade_performances.get)
        least_grade_score = grade_performances[least_performing_grade]

    # Learners per grade with stream and gender breakdown
    learners_per_grade = {}
    gender_per_grade = {}
    streams_per_grade = {}

    students = Student.query.all()
    for student in students:
        grade = student.stream.grade.level if student.stream and student.stream.grade else "No Grade"
        stream_name = student.stream.name if student.stream else "No Stream"

        # Initialize grade-level data
        if grade not in learners_per_grade:
            learners_per_grade[grade] = 0
            gender_per_grade[grade] = {'Male': 0, 'Female': 0}
            streams_per_grade[grade] = {}

        # Initialize stream-level data for this grade
        if stream_name not in streams_per_grade[grade]:
            streams_per_grade[grade][stream_name] = {'total': 0, 'Male': 0, 'Female': 0}

        # Update counts
        learners_per_grade[grade] += 1
        streams_per_grade[grade][stream_name]['total'] += 1

        # Handle gender with more flexibility
        gender = student.gender.strip() if student.gender else None
        if gender:
            gender_lower = gender.lower()
            if gender_lower in ['male', 'm', 'boy']:
                gender_per_grade[grade]['Male'] += 1
                streams_per_grade[grade][stream_name]['Male'] += 1
            elif gender_lower in ['female', 'f', 'girl']:
                gender_per_grade[grade]['Female'] += 1
                streams_per_grade[grade][stream_name]['Female'] += 1

    # Sort grades and streams for consistent display
    learners_per_grade = dict(sorted(learners_per_grade.items()))
    gender_per_grade = dict(sorted(gender_per_grade.items()))
    streams_per_grade = {grade: dict(sorted(streams.items())) for grade, streams in sorted(streams_per_grade.items())}

    # Enhanced analytics for better insights
    # Subject performance analysis
    subject_performance = {}
    for subject in Subject.query.all():
        subject_marks = Mark.query.filter_by(subject_id=subject.id).all()
        if subject_marks:
            subject_avg = round(sum(mark.percentage for mark in subject_marks if mark.percentage) / len([m for m in subject_marks if m.percentage]), 2)
            subject_performance[subject.name] = {
                'average': subject_avg,
                'total_assessments': len(subject_marks),
                'education_level': subject.education_level
            }

    # Recent activities (last 10 mark entries)
    recent_activities = []
    recent_marks = Mark.query.order_by(Mark.id.desc()).limit(10).all()
    for mark in recent_marks:
        if mark.student and mark.subject:
            recent_activities.append({
                'type': 'mark_entry',
                'description': f"Marks entered for {mark.student.name} in {mark.subject.name}",
                'grade': mark.student.stream.grade.level if mark.student.stream and mark.student.stream.grade else 'N/A',
                'stream': mark.student.stream.name if mark.student.stream else 'N/A',
                'percentage': mark.percentage
            })

    # Performance alerts
    performance_alerts = []

    # Check for classes with low performance
    for grade_name, avg_score in grade_performances.items():
        if avg_score < 50:  # Below 50% average
            performance_alerts.append({
                'type': 'warning',
                'title': 'Low Grade Performance',
                'message': f"{grade_name} has an average performance of {avg_score}%",
                'action': 'Review teaching strategies and provide additional support'
            })

    # Check for subjects with low performance
    for subject_name, data in subject_performance.items():
        if data['average'] < 45:  # Below 45% average
            performance_alerts.append({
                'type': 'alert',
                'title': 'Subject Performance Concern',
                'message': f"{subject_name} has an average performance of {data['average']}%",
                'action': 'Consider additional training or resources for this subject'
            })

    # Quick stats for enhanced dashboard
    total_subjects = Subject.query.count()
    total_assessments = Mark.query.count()

    # Performance distribution
    performance_distribution = {'E.E': 0, 'M.E': 0, 'A.E': 0, 'B.E': 0}
    all_marks = Mark.query.all()
    for mark in all_marks:
        if mark.percentage:
            if mark.percentage >= 75:
                performance_distribution['E.E'] += 1
            elif mark.percentage >= 50:
                performance_distribution['M.E'] += 1
            elif mark.percentage >= 30:
                performance_distribution['A.E'] += 1
            else:
                performance_distribution['B.E'] += 1

    # Prepare enhanced dashboard stats for caching
    dashboard_stats = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'avg_performance': avg_performance,
        'total_classes': total_classes,
        'total_subjects': total_subjects,
        'total_assessments': total_assessments,
        'top_class': top_class,
        'top_class_score': top_class_score,
        'least_performing_grade': least_performing_grade,
        'least_grade_score': least_grade_score,
        'learners_per_grade': learners_per_grade,
        'gender_per_grade': gender_per_grade,
        'streams_per_grade': streams_per_grade,
        'subject_performance': subject_performance,
        'recent_activities': recent_activities,
        'performance_alerts': performance_alerts,
        'performance_distribution': performance_distribution
    }

    # Cache the dashboard stats
    cache_dashboard_stats(dashboard_stats)

    # Render the admin dashboard
    return render_template('headteacher.html', **dashboard_stats)

@admin_bp.route('/manage_teachers', methods=['GET', 'POST'])
@admin_required
def manage_teachers():
    """Route for managing teachers."""
    error_message = None
    success_message = None

    # Get all teachers
    teachers = Teacher.query.all()

    # Get all grades and streams for assignment
    grades = Grade.query.all()
    streams = Stream.query.all()

    # Get all subjects for assignment
    subjects = Subject.query.all()

    # Handle form submissions
    if request.method == 'POST':
        # Add new teacher
        if 'add_teacher' in request.form:
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')

            # Validate input
            if not username or not password or not role:
                error_message = "Please fill in all required fields."
            else:
                # Check if teacher already exists
                existing_teacher = Teacher.query.filter_by(username=username).first()
                if existing_teacher:
                    error_message = f"Teacher with username '{username}' already exists."
                else:
                    # Hash the password
                    from werkzeug.security import generate_password_hash
                    hashed_password = generate_password_hash(password)

                    # Create new teacher
                    new_teacher = Teacher(username=username, password=hashed_password, role=role)
                    db.session.add(new_teacher)

                    try:
                        db.session.commit()
                        # Invalidate admin cache since data has changed
                        invalidate_admin_cache()
                        success_message = f"Teacher '{username}' added successfully."
                        # Refresh teachers list
                        teachers = Teacher.query.all()
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error adding teacher: {str(e)}"

        # Delete teacher
        elif 'delete_teacher' in request.form:
            teacher_id = request.form.get('teacher_id', type=int)
            if teacher_id:
                teacher = Teacher.query.get(teacher_id)
                if teacher:
                    try:
                        db.session.delete(teacher)
                        db.session.commit()
                        # Invalidate admin cache since data has changed
                        invalidate_admin_cache()
                        success_message = f"Teacher '{teacher.username}' deleted successfully."
                        # Refresh teachers list
                        teachers = Teacher.query.all()
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error deleting teacher: {str(e)}"

        # Edit teacher
        elif 'edit_teacher' in request.form:
            teacher_id = request.form.get('teacher_id', type=int)
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')

            if teacher_id and username and role:
                teacher = Teacher.query.get(teacher_id)
                if teacher:
                    # Check if new username already exists (if username is changed)
                    if username != teacher.username:
                        existing_teacher = Teacher.query.filter_by(username=username).first()
                        if existing_teacher:
                            error_message = f"Teacher with username '{username}' already exists."
                            return render_template('manage_teachers.html',
                                                teachers=teachers,
                                                grades=grades,
                                                streams=streams,
                                                subjects=subjects,
                                                error_message=error_message,
                                                success_message=success_message)

                    # Update teacher
                    teacher.username = username
                    teacher.role = role

                    # Update password if provided
                    if password:
                        from werkzeug.security import generate_password_hash
                        teacher.password = generate_password_hash(password)

                    try:
                        db.session.commit()
                        success_message = f"Teacher '{username}' updated successfully."
                        # Refresh teachers list
                        teachers = Teacher.query.all()
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error updating teacher: {str(e)}"

        # Assign teacher to class (as class teacher)
        elif 'assign_class_teacher' in request.form:
            teacher_id = request.form.get('teacher_id', type=int)
            grade_id = request.form.get('grade_id', type=int)
            stream_id = request.form.get('stream_id', type=int)

            if not teacher_id:
                error_message = "Please select a teacher."
            elif not grade_id:
                error_message = "Please select a grade."
            else:
                teacher = Teacher.query.get(teacher_id)
                grade = Grade.query.get(grade_id)
                stream = Stream.query.get(stream_id) if stream_id else None

                if not teacher or not grade:
                    error_message = "Invalid teacher or grade."
                else:
                    # Check if this teacher is already assigned as class teacher to another stream
                    existing_assignment = TeacherSubjectAssignment.query.filter_by(
                        teacher_id=teacher_id,
                        is_class_teacher=True
                    ).first()

                    if existing_assignment:
                        existing_grade = Grade.query.get(existing_assignment.grade_id)
                        existing_stream = Stream.query.get(existing_assignment.stream_id) if existing_assignment.stream_id else None

                        grade_name = existing_grade.level if existing_grade else "Unknown Grade"
                        stream_name = f"Stream {existing_stream.name}" if existing_stream else "All Streams"

                        error_message = f"Teacher '{teacher.username}' is already assigned as class teacher to {grade_name} {stream_name}."
                    else:
                        # Check if this stream already has a class teacher
                        if stream_id:
                            existing_class_teacher = TeacherSubjectAssignment.query.filter_by(
                                grade_id=grade_id,
                                stream_id=stream_id,
                                is_class_teacher=True
                            ).first()

                            if existing_class_teacher and existing_class_teacher.teacher_id != teacher_id:
                                existing_teacher = Teacher.query.get(existing_class_teacher.teacher_id)
                                error_message = f"Stream already has a class teacher: {existing_teacher.username if existing_teacher else 'Unknown Teacher'}"
                                return render_template('manage_teachers.html',
                                                    teachers=teachers,
                                                    grades=grades,
                                                    streams=streams,
                                                    subjects=subjects,
                                                    error_message=error_message,
                                                    success_message=success_message)

                        # Create new assignment
                        new_assignment = TeacherSubjectAssignment(
                            teacher_id=teacher_id,
                            grade_id=grade_id,
                            stream_id=stream_id,
                            is_class_teacher=True,
                            subject_id=1  # Placeholder subject ID, not used for class teacher assignment
                        )

                        db.session.add(new_assignment)

                        try:
                            db.session.commit()
                            stream_text = f"Stream {stream.name}" if stream else "All Streams"
                            success_message = f"Teacher '{teacher.username}' assigned as class teacher to {grade.level} {stream_text}."
                        except Exception as e:
                            db.session.rollback()
                            error_message = f"Error assigning class teacher: {str(e)}"

        # Assign teacher to subject
        elif 'assign_subject' in request.form:
            teacher_id = request.form.get('teacher_id', type=int)
            subject_id = request.form.get('subject_id', type=int)
            grade_id = request.form.get('grade_id', type=int)
            stream_id = request.form.get('stream_id', type=int)

            if not teacher_id:
                error_message = "Please select a teacher."
            elif not subject_id:
                error_message = "Please select a subject."
            elif not grade_id:
                error_message = "Please select a grade."
            else:
                teacher = Teacher.query.get(teacher_id)
                subject = Subject.query.get(subject_id)
                grade = Grade.query.get(grade_id)
                stream = Stream.query.get(stream_id) if stream_id else None

                if not teacher or not subject or not grade:
                    error_message = "Invalid teacher, subject, or grade."
                else:
                    # Check if this assignment already exists
                    existing_assignment = TeacherSubjectAssignment.query.filter_by(
                        teacher_id=teacher_id,
                        subject_id=subject_id,
                        grade_id=grade_id,
                        stream_id=stream_id
                    ).first()

                    if existing_assignment:
                        stream_text = f"Stream {stream.name}" if stream else "All Streams"
                        error_message = f"Teacher '{teacher.username}' is already assigned to teach {subject.name} for {grade.level} {stream_text}."
                    else:
                        # Create new assignment
                        new_assignment = TeacherSubjectAssignment(
                            teacher_id=teacher_id,
                            subject_id=subject_id,
                            grade_id=grade_id,
                            stream_id=stream_id,
                            is_class_teacher=False
                        )

                        db.session.add(new_assignment)

                        try:
                            db.session.commit()
                            stream_text = f"Stream {stream.name}" if stream else "All Streams"
                            success_message = f"Teacher '{teacher.username}' assigned to teach {subject.name} for {grade.level} {stream_text}."
                        except Exception as e:
                            db.session.rollback()
                            error_message = f"Error assigning subject: {str(e)}"

        # Delete assignment
        elif 'delete_assignment' in request.form:
            assignment_id = request.form.get('assignment_id', type=int)
            if assignment_id:
                assignment = TeacherSubjectAssignment.query.get(assignment_id)
                if assignment:
                    try:
                        db.session.delete(assignment)
                        db.session.commit()
                        success_message = "Assignment deleted successfully."
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error deleting assignment: {str(e)}"

    # Get all teacher assignments
    assignments = TeacherSubjectAssignment.query.all()

    # Render the template with data
    return render_template('manage_teachers.html',
                          teachers=teachers,
                          grades=grades,
                          streams=streams,
                          subjects=subjects,
                          assignments=assignments,
                          error_message=error_message,
                          success_message=success_message)

@admin_bp.route('/manage_subjects', methods=['GET', 'POST'])
@admin_required
def manage_subjects():
    """Route for managing subjects."""
    error_message = None
    success_message = None

    # Check if we're just viewing (GET request) and have cached subject data
    if request.method == 'GET':
        cached_subjects = get_cached_subject_list()
        if cached_subjects:
            return render_template('manage_subjects.html', **cached_subjects)

    # Get all subjects
    subjects = Subject.query.all()

    # Get education levels for filtering
    education_levels = list(set([subject.education_level for subject in subjects]))

    # Handle form submissions
    if request.method == 'POST':
        # Add new subject
        if 'add_subject' in request.form:
            subject_name = request.form.get('subject_name')
            education_level = request.form.get('education_level')

            # Validate input
            if not subject_name:
                error_message = "Please fill in the subject name."
            elif not education_level:
                error_message = "Please select an education level."
            else:
                # Check if subject already exists with the same name and education level
                existing_subject = Subject.query.filter_by(name=subject_name, education_level=education_level).first()
                if existing_subject:
                    error_message = f"Subject '{subject_name}' already exists for {education_level}."
                else:
                    # Create new subject
                    new_subject = Subject(name=subject_name, education_level=education_level)
                    db.session.add(new_subject)

                    try:
                        db.session.commit()
                        # Invalidate admin cache since data has changed
                        invalidate_admin_cache()
                        success_message = f"Subject '{subject_name}' added successfully."
                        # Refresh subjects list
                        subjects = Subject.query.all()
                        # Update education levels
                        education_levels = list(set([subject.education_level for subject in subjects]))
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error adding subject: {str(e)}"

        # Delete subject
        elif 'delete_subject' in request.form:
            subject_id = request.form.get('subject_id', type=int)
            if subject_id:
                subject = Subject.query.get(subject_id)
                if subject:
                    # Check if subject is used in any marks
                    marks_with_subject = Mark.query.filter_by(subject_id=subject_id).first()
                    if marks_with_subject:
                        error_message = f"Cannot delete subject '{subject.name}' because it is used in student marks."
                    else:
                        try:
                            db.session.delete(subject)
                            db.session.commit()
                            # Invalidate admin cache since data has changed
                            invalidate_admin_cache()
                            success_message = f"Subject '{subject.name}' deleted successfully."
                            # Refresh subjects list
                            subjects = Subject.query.all()
                            # Update education levels
                            education_levels = list(set([subject.education_level for subject in subjects]))
                        except Exception as e:
                            db.session.rollback()
                            error_message = f"Error deleting subject: {str(e)}"

        # Edit subject
        elif 'edit_subject' in request.form:
            subject_id = request.form.get('subject_id', type=int)
            subject_name = request.form.get('subject_name')
            education_level = request.form.get('education_level')

            if subject_id and subject_name and education_level:
                subject = Subject.query.get(subject_id)
                if subject:
                    # Check if new name already exists (if name or education level is changed)
                    if subject_name != subject.name or education_level != subject.education_level:
                        existing_subject = Subject.query.filter_by(name=subject_name, education_level=education_level).first()
                        if existing_subject and existing_subject.id != subject_id:
                            error_message = f"Subject '{subject_name}' already exists for {education_level}."
                            return render_template('manage_subjects.html',
                                                subjects=subjects,
                                                education_levels=education_levels,
                                                error_message=error_message,
                                                success_message=success_message)

                    # Update subject
                    subject.name = subject_name
                    subject.education_level = education_level

                    try:
                        db.session.commit()
                        success_message = f"Subject '{subject_name}' updated successfully."
                        # Refresh subjects list
                        subjects = Subject.query.all()
                        # Update education levels
                        education_levels = list(set([subject.education_level for subject in subjects]))
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error updating subject: {str(e)}"

        # Bulk upload subjects
        elif 'bulk_upload_subjects' in request.form:
            if 'subjects_file' not in request.files:
                error_message = "No file selected."
            else:
                file = request.files['subjects_file']

                if file.filename == '':
                    error_message = "No file selected."
                else:
                    try:
                        # Check file extension
                        file_ext = os.path.splitext(file.filename)[1].lower()

                        if file_ext == '.csv':
                            import pandas as pd
                            df = pd.read_csv(file)
                        elif file_ext in ['.xlsx', '.xls']:
                            import pandas as pd
                            df = pd.read_excel(file)
                        else:
                            error_message = "Unsupported file format. Please upload a CSV or Excel file."
                            return render_template('manage_subjects.html',
                                                subjects=subjects,
                                                education_levels=education_levels,
                                                error_message=error_message,
                                                success_message=success_message)

                        # Check if required columns exist
                        if 'name' not in df.columns or 'education_level' not in df.columns:
                            error_message = "File must contain 'name' and 'education_level' columns."
                            return render_template('manage_subjects.html',
                                                subjects=subjects,
                                                education_levels=education_levels,
                                                error_message=error_message,
                                                success_message=success_message)

                        # Process the file
                        subjects_added = 0
                        subjects_updated = 0
                        errors = 0

                        for _, row in df.iterrows():
                            subject_name = row['name']
                            education_level = row['education_level']

                            if not subject_name or not education_level:
                                errors += 1
                                continue

                            # Check if subject already exists
                            existing_subject = Subject.query.filter_by(name=subject_name, education_level=education_level).first()

                            if existing_subject:
                                # Subject already exists, skip
                                subjects_updated += 1
                            else:
                                # Create new subject
                                new_subject = Subject(name=subject_name, education_level=education_level)
                                db.session.add(new_subject)
                                subjects_added += 1

                        # Commit changes
                        db.session.commit()

                        # Show success message
                        success_message = f"Successfully processed {subjects_added + subjects_updated} subjects ({subjects_added} new, {subjects_updated} existing). {errors} errors encountered."

                        # Refresh subjects list
                        subjects = Subject.query.all()
                        # Update education levels
                        education_levels = list(set([subject.education_level for subject in subjects]))

                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error processing file: {str(e)}"

    # Prepare subject data for caching
    subject_data = {
        'subjects': subjects,
        'education_levels': education_levels,
        'error_message': error_message,
        'success_message': success_message
    }

    # Cache the subject data (only if it's a GET request or a successful POST)
    if request.method == 'GET' or success_message:
        cache_subject_list(subject_data)

    # Render the template with data
    return render_template('manage_subjects.html', **subject_data)

@admin_bp.route('/manage_grades_streams', methods=['GET', 'POST'])
@admin_required
def manage_grades_streams():
    """Route for managing grades and streams."""
    error_message = None
    success_message = None

    # Get all grades and streams
    grades = Grade.query.all()
    streams = Stream.query.all()

    # Handle form submissions
    if request.method == 'POST':
        # Add new grade
        if 'add_grade' in request.form:
            grade_level = request.form.get('grade_level')

            # Validate input
            if not grade_level:
                error_message = "Please enter a grade level."
            else:
                # Check if grade already exists
                existing_grade = Grade.query.filter_by(level=grade_level).first()
                if existing_grade:
                    error_message = f"Grade '{grade_level}' already exists."
                else:
                    # Create new grade
                    new_grade = Grade(level=grade_level)
                    db.session.add(new_grade)

                    try:
                        db.session.commit()
                        success_message = f"Grade '{grade_level}' added successfully."
                        # Refresh grades list
                        grades = Grade.query.all()
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error adding grade: {str(e)}"

        # Add new stream
        elif 'add_stream' in request.form:
            stream_name = request.form.get('stream_name')
            grade_id = request.form.get('grade_id', type=int)

            # Validate input
            if not stream_name:
                error_message = "Please enter a stream name."
            elif not grade_id:
                error_message = "Please select a grade."
            else:
                # Check if stream already exists for this grade
                existing_stream = Stream.query.filter_by(name=stream_name, grade_id=grade_id).first()
                if existing_stream:
                    grade = Grade.query.get(grade_id)
                    error_message = f"Stream '{stream_name}' already exists for {grade.level if grade else 'this grade'}."
                else:
                    # Create new stream
                    new_stream = Stream(name=stream_name, grade_id=grade_id)
                    db.session.add(new_stream)

                    try:
                        db.session.commit()
                        success_message = f"Stream '{stream_name}' added successfully."
                        # Refresh streams list
                        streams = Stream.query.all()
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error adding stream: {str(e)}"

        # Delete grade
        elif 'delete_grade' in request.form:
            grade_id = request.form.get('grade_id', type=int)
            if grade_id:
                grade = Grade.query.get(grade_id)
                if grade:
                    # Check if grade has streams
                    streams_in_grade = Stream.query.filter_by(grade_id=grade_id).first()
                    if streams_in_grade:
                        error_message = f"Cannot delete grade '{grade.level}' because it has streams. Delete the streams first."
                    else:
                        try:
                            db.session.delete(grade)
                            db.session.commit()
                            success_message = f"Grade '{grade.level}' deleted successfully."
                            # Refresh grades list
                            grades = Grade.query.all()
                        except Exception as e:
                            db.session.rollback()
                            error_message = f"Error deleting grade: {str(e)}"

        # Delete stream
        elif 'delete_stream' in request.form:
            stream_id = request.form.get('stream_id', type=int)
            if stream_id:
                stream = Stream.query.get(stream_id)
                if stream:
                    # Check if stream has students
                    students_in_stream = Student.query.filter_by(stream_id=stream_id).first()
                    if students_in_stream:
                        error_message = f"Cannot delete stream '{stream.name}' because it has students. Move the students to another stream first."
                    else:
                        try:
                            db.session.delete(stream)
                            db.session.commit()
                            success_message = f"Stream '{stream.name}' deleted successfully."
                            # Refresh streams list
                            streams = Stream.query.all()
                        except Exception as e:
                            db.session.rollback()
                            error_message = f"Error deleting stream: {str(e)}"

        # Edit grade
        elif 'edit_grade' in request.form:
            grade_id = request.form.get('grade_id', type=int)
            grade_level = request.form.get('grade_level')

            if grade_id and grade_level:
                grade = Grade.query.get(grade_id)
                if grade:
                    # Check if new level already exists (if level is changed)
                    if grade_level != grade.level:
                        existing_grade = Grade.query.filter_by(level=grade_level).first()
                        if existing_grade:
                            error_message = f"Grade '{grade_level}' already exists."
                            return render_template('manage_grades_streams.html',
                                                grades=grades,
                                                streams=streams,
                                                error_message=error_message,
                                                success_message=success_message)

                    # Update grade
                    grade.level = grade_level

                    try:
                        db.session.commit()
                        success_message = f"Grade '{grade_level}' updated successfully."
                        # Refresh grades list
                        grades = Grade.query.all()
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error updating grade: {str(e)}"

        # Edit stream
        elif 'edit_stream' in request.form:
            stream_id = request.form.get('stream_id', type=int)
            stream_name = request.form.get('stream_name')
            grade_id = request.form.get('grade_id', type=int)

            if stream_id and stream_name and grade_id:
                stream = Stream.query.get(stream_id)
                if stream:
                    # Check if new name already exists for this grade (if name or grade is changed)
                    if stream_name != stream.name or grade_id != stream.grade_id:
                        existing_stream = Stream.query.filter_by(name=stream_name, grade_id=grade_id).first()
                        if existing_stream and existing_stream.id != stream_id:
                            grade = Grade.query.get(grade_id)
                            error_message = f"Stream '{stream_name}' already exists for {grade.level if grade else 'this grade'}."
                            return render_template('manage_grades_streams.html',
                                                grades=grades,
                                                streams=streams,
                                                error_message=error_message,
                                                success_message=success_message)

                    # Update stream
                    stream.name = stream_name
                    stream.grade_id = grade_id

                    try:
                        db.session.commit()
                        success_message = f"Stream '{stream_name}' updated successfully."
                        # Refresh streams list
                        streams = Stream.query.all()
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error updating stream: {str(e)}"

    # Render the template with data
    return render_template('manage_grades_streams.html',
                          grades=grades,
                          streams=streams,
                          error_message=error_message,
                          success_message=success_message)
@admin_bp.route('/manage_terms_assessments', methods=['GET', 'POST'])
@admin_required
def manage_terms_assessments():
    """Route for managing terms and assessment types."""
    error_message = None
    success_message = None

    # Get all terms and assessment types
    terms = Term.query.all()
    assessment_types = AssessmentType.query.all()

    # Get current term and academic year
    current_term = "None"
    current_term_obj = Term.query.filter_by(is_current=True).first()
    if current_term_obj:
        current_term = current_term_obj.name

    # Get current academic year (from current term or default to current year)
    current_academic_year = "2024"  # Default
    if current_term_obj and current_term_obj.academic_year:
        current_academic_year = current_term_obj.academic_year

    # Handle form submissions
    if request.method == 'POST':
        # Add new term
        if 'add_term' in request.form:
            term_name = request.form.get('term_name')
            is_current_term = 'is_current_term' in request.form
            academic_year = request.form.get('academic_year')
            term_start_date = request.form.get('term_start_date') or None
            term_end_date = request.form.get('term_end_date') or None

            # Validate input
            if not term_name:
                error_message = "Please enter a term name."
            else:
                # Check if term already exists
                existing_term = Term.query.filter_by(name=term_name).first()
                if existing_term:
                    error_message = f"Term '{term_name}' already exists."
                else:
                    # If setting as current term, unset any existing current term
                    if is_current_term:
                        Term.query.filter_by(is_current=True).update({'is_current': False})

                    # Create new term
                    new_term = Term(
                        name=term_name,
                        is_current=is_current_term,
                        academic_year=academic_year,
                        start_date=term_start_date,
                        end_date=term_end_date
                    )
                    db.session.add(new_term)

                    try:
                        db.session.commit()
                        success_message = f"Term '{term_name}' added successfully."
                        # Refresh terms list
                        terms = Term.query.all()
                        # Update current term if needed
                        if is_current_term:
                            current_term = term_name
                            current_academic_year = academic_year or current_academic_year
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error adding term: {str(e)}"

        # Add new assessment type
        elif 'add_assessment' in request.form:
            assessment_name = request.form.get('assessment_name')
            assessment_weight = request.form.get('assessment_weight')
            assessment_group = request.form.get('assessment_group')
            show_on_reports = 'show_on_reports' in request.form

            # Validate input
            if not assessment_name:
                error_message = "Please enter an assessment type name."
            else:
                # Check if assessment type already exists
                existing_assessment = AssessmentType.query.filter_by(name=assessment_name).first()
                if existing_assessment:
                    error_message = f"Assessment type '{assessment_name}' already exists."
                else:
                    # Create new assessment type
                    new_assessment = AssessmentType(
                        name=assessment_name,
                        weight=assessment_weight,
                        group=assessment_group,
                        show_on_reports=show_on_reports
                    )
                    db.session.add(new_assessment)

                    try:
                        db.session.commit()
                        success_message = f"Assessment type '{assessment_name}' added successfully."
                        # Refresh assessment types list
                        assessment_types = AssessmentType.query.all()
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error adding assessment type: {str(e)}"

        # Delete term
        elif 'delete_term' in request.form:
            term_id = request.form.get('term_id', type=int)
            if term_id:
                term = Term.query.get(term_id)
                if term:
                    # Check if term is used in any marks
                    marks_with_term = Mark.query.filter_by(term_id=term_id).first()
                    if marks_with_term:
                        error_message = f"Cannot delete term '{term.name}' because it is used in student marks."
                    else:
                        try:
                            db.session.delete(term)
                            db.session.commit()
                            success_message = f"Term '{term.name}' deleted successfully."
                            # Refresh terms list
                            terms = Term.query.all()
                            # Update current term if needed
                            if term.is_current:
                                current_term = "None"
                        except Exception as e:
                            db.session.rollback()
                            error_message = f"Error deleting term: {str(e)}"

        # Delete assessment type
        elif 'delete_assessment' in request.form:
            assessment_id = request.form.get('assessment_id', type=int)
            if assessment_id:
                assessment = AssessmentType.query.get(assessment_id)
                if assessment:
                    # Check if assessment type is used in any marks
                    marks_with_assessment = Mark.query.filter_by(assessment_type_id=assessment_id).first()
                    if marks_with_assessment:
                        error_message = f"Cannot delete assessment type '{assessment.name}' because it is used in student marks."
                    else:
                        try:
                            db.session.delete(assessment)
                            db.session.commit()
                            success_message = f"Assessment type '{assessment.name}' deleted successfully."
                            # Refresh assessment types list
                            assessment_types = AssessmentType.query.all()
                        except Exception as e:
                            db.session.rollback()
                            error_message = f"Error deleting assessment type: {str(e)}"

        # Edit term
        elif 'action' in request.form and request.form.get('action') == 'edit_term':
            term_id = request.form.get('term_id', type=int)
            term_name = request.form.get('term_name')
            is_current_term = 'is_current_term' in request.form
            academic_year = request.form.get('academic_year')
            term_start_date = request.form.get('term_start_date') or None
            term_end_date = request.form.get('term_end_date') or None

            if term_id and term_name:
                term = Term.query.get(term_id)
                if term:
                    # Check if new name already exists (if name is changed)
                    if term_name != term.name:
                        existing_term = Term.query.filter_by(name=term_name).first()
                        if existing_term:
                            error_message = f"Term '{term_name}' already exists."
                            return render_template('manage_terms_assessments.html',
                                                terms=terms,
                                                assessment_types=assessment_types,
                                                error_message=error_message,
                                                success_message=success_message,
                                                current_term=current_term,
                                                current_academic_year=current_academic_year)

                    # If setting as current term, unset any existing current term
                    if is_current_term and not term.is_current:
                        Term.query.filter_by(is_current=True).update({'is_current': False})

                    # Update term
                    term.name = term_name
                    term.is_current = is_current_term
                    term.academic_year = academic_year
                    term.start_date = term_start_date
                    term.end_date = term_end_date

                    try:
                        db.session.commit()
                        success_message = f"Term '{term_name}' updated successfully."
                        # Refresh terms list
                        terms = Term.query.all()
                        # Update current term if needed
                        if is_current_term:
                            current_term = term_name
                            current_academic_year = academic_year or current_academic_year
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error updating term: {str(e)}"

        # Edit assessment type
        elif 'action' in request.form and request.form.get('action') == 'edit_assessment':
            assessment_id = request.form.get('assessment_id', type=int)
            assessment_name = request.form.get('assessment_name')
            assessment_weight = request.form.get('assessment_weight')
            assessment_group = request.form.get('assessment_group')
            show_on_reports = 'show_on_reports' in request.form

            if assessment_id and assessment_name:
                assessment = AssessmentType.query.get(assessment_id)
                if assessment:
                    # Check if new name already exists (if name is changed)
                    if assessment_name != assessment.name:
                        existing_assessment = AssessmentType.query.filter_by(name=assessment_name).first()
                        if existing_assessment:
                            error_message = f"Assessment type '{assessment_name}' already exists."
                            return render_template('manage_terms_assessments.html',
                                                terms=terms,
                                                assessment_types=assessment_types,
                                                error_message=error_message,
                                                success_message=success_message,
                                                current_term=current_term,
                                                current_academic_year=current_academic_year)

                    # Update assessment type
                    assessment.name = assessment_name
                    assessment.weight = assessment_weight
                    assessment.group = assessment_group
                    assessment.show_on_reports = show_on_reports

                    try:
                        db.session.commit()
                        success_message = f"Assessment type '{assessment_name}' updated successfully."
                        # Refresh assessment types list
                        assessment_types = AssessmentType.query.all()
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error updating assessment type: {str(e)}"

    # Render the template with data
    return render_template('manage_terms_assessments.html',
                          terms=terms,
                          assessment_types=assessment_types,
                          error_message=error_message,
                          success_message=success_message,
                          current_term=current_term,
                          current_academic_year=current_academic_year)


@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Enhanced analytics dashboard for headteacher."""
    # Get performance trends over time
    performance_trends = {}
    terms = Term.query.all()

    for term in terms:
        term_marks = Mark.query.filter_by(term_id=term.id).all()
        if term_marks:
            term_avg = round(sum(mark.percentage for mark in term_marks if mark.percentage) / len([m for m in term_marks if m.percentage]), 2)
            performance_trends[term.name] = term_avg

    # Subject-wise detailed analysis
    subject_analysis = {}
    for subject in Subject.query.all():
        subject_marks = Mark.query.filter_by(subject_id=subject.id).all()
        if subject_marks:
            grades_performance = {}
            for grade in Grade.query.all():
                grade_subject_marks = [m for m in subject_marks if m.student and m.student.stream and m.student.stream.grade_id == grade.id]
                if grade_subject_marks:
                    grade_avg = round(sum(mark.percentage for mark in grade_subject_marks if mark.percentage) / len([m for m in grade_subject_marks if m.percentage]), 2)
                    grades_performance[grade.level] = grade_avg

            subject_analysis[subject.name] = {
                'overall_average': round(sum(mark.percentage for mark in subject_marks if mark.percentage) / len([m for m in subject_marks if m.percentage]), 2),
                'total_students': len(set([m.student_id for m in subject_marks])),
                'grades_performance': grades_performance,
                'education_level': subject.education_level
            }

    return render_template('analytics.html',
                          performance_trends=performance_trends,
                          subject_analysis=subject_analysis)


@admin_bp.route('/reports')
@admin_required
def reports():
    """Comprehensive reports dashboard."""
    # Get available report types
    report_types = [
        {
            'id': 'school_performance',
            'title': 'School Performance Report',
            'description': 'Comprehensive overview of school academic performance',
            'icon': '📊'
        },
        {
            'id': 'teacher_performance',
            'title': 'Teacher Performance Report',
            'description': 'Individual teacher effectiveness and student outcomes',
            'icon': '👨‍🏫'
        },
        {
            'id': 'student_progress',
            'title': 'Student Progress Report',
            'description': 'Detailed tracking of individual student advancement',
            'icon': '📈'
        },
        {
            'id': 'grade_analysis',
            'title': 'Grade Level Analysis',
            'description': 'Performance breakdown by grade and stream',
            'icon': '🎓'
        },
        {
            'id': 'subject_analysis',
            'title': 'Subject Performance Analysis',
            'description': 'Subject-wise performance across all grades',
            'icon': '📚'
        }
    ]

    return render_template('reports.html', report_types=report_types)