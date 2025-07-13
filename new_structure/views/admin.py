"""
Admin/Headteacher views for the Hillview School Management System.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, abort
from ..models import Teacher, Student, Grade, Stream, Subject, Term, AssessmentType, Mark, TeacherSubjectAssignment, SchoolConfiguration
from ..services import is_authenticated, get_role
from ..services.school_config_service import SchoolConfigService
from ..extensions import db
from ..services.admin_cache_service import (
    cache_dashboard_stats, get_cached_dashboard_stats,
    cache_subject_list, get_cached_subject_list,
    invalidate_admin_cache
)
from ..security.sql_injection_protection import sql_injection_protection, SQLInjectionProtection
from ..security.rce_protection import RCEProtection
from functools import wraps
import os
import pandas as pd
import re

# Create a blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/headteacher')

# Input validation functions
def validate_admin_input(value, field_name, max_length=100):
    """Validate admin input for security."""
    if not value:
        return True  # Allow empty values

    # Length validation
    if len(str(value)) > max_length:
        return False

    # SQL injection protection
    if not SQLInjectionProtection.validate_input(value, field_name):
        return False

    # Command injection protection
    if RCEProtection.detect_code_injection(str(value)):
        return False

    return True

def sanitize_search_query(query):
    """Sanitize search query for safe database operations."""
    if not query:
        return ""

    # Remove dangerous characters
    sanitized = re.sub(r'[<>"\';\\&|`$]', '', str(query))

    # Limit length
    sanitized = sanitized[:100]

    # Remove multiple spaces
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    return sanitized

# Decorator for requiring admin authentication
def admin_required(f):
    """Decorator to require admin authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session) or get_role(session) != 'headteacher':
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/analytics')
@admin_required
def analytics_dashboard():
    """Dedicated analytics page for headteachers."""
    try:
        # Get comprehensive analytics data - prioritize report-based analytics
        try:
            from ..services.report_based_analytics_service import ReportBasedAnalyticsService

            # Try report-based analytics first
            analytics_data = ReportBasedAnalyticsService.get_analytics_dashboard_data(
                role='headteacher',
                teacher_id=None
            )

            # If no report data available, fall back to traditional analytics
            if not analytics_data.get('has_data', False):
                from ..services.analytics_service import AnalyticsService
                fallback_data = AnalyticsService.get_headteacher_analytics()

                # Merge the data, prioritizing report-based structure
                analytics_data.update({
                    'grade_performance': fallback_data.get('grade_performance', []),
                    'subject_performance': fallback_data.get('subject_performance', []),
                    'top_students': fallback_data.get('top_students', []),
                    'teacher_performance': fallback_data.get('teacher_performance', []),
                    'summary': fallback_data.get('summary', {}),
                    'has_data': fallback_data.get('has_data', False),
                    'data_source': 'live_calculation'
                })

                flash('Analytics based on live data calculation. Encourage teachers to generate reports for more accurate insights.', 'info')
            else:
                flash('Analytics based on teacher-generated reports - reflecting actual academic workflow.', 'success')

        except Exception as e:
            print(f"Error loading report-based analytics: {e}")
            # Fall back to traditional analytics
            from ..services.analytics_service import AnalyticsService
            analytics_data = AnalyticsService.get_headteacher_analytics()

        if 'error' in analytics_data:
            flash(f'Error loading analytics: {analytics_data["error"]}', 'error')
            analytics_data = {'has_data': False, 'summary': {}, 'grade_performance': [], 'subject_performance': [], 'data_source': 'error'}

        # Get filter options
        terms = [term.name for term in Term.query.all()]
        assessment_types = [at.name for at in AssessmentType.query.all()]
        grades = [grade.name for grade in Grade.query.all()]

        return render_template('headteacher_analytics.html',
                             analytics_data=analytics_data,
                             terms=terms,
                             assessment_types=assessment_types,
                             grades=grades,
                             page_title="School-Wide Academic Analytics")

    except Exception as e:
        print(f"Error loading analytics dashboard: {e}")
        flash('Error loading analytics dashboard.', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/')
@admin_required
@sql_injection_protection
def dashboard():
    """Route for the admin/headteacher dashboard."""
    # Temporarily disable cache to ensure fresh data
    # cached_stats = get_cached_dashboard_stats()
    # if cached_stats:
    #     return render_template('headteacher.html', **cached_stats)

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
            # Filter out marks with zero or null values
            valid_marks = [mark.mark for mark in stream_marks if mark.mark is not None and mark.mark > 0]
            if valid_marks:  # Only calculate if there are valid marks
                stream_avg = round(sum(valid_marks) / len(valid_marks), 2)
                stream_name = f"{stream.grade.name} {stream.name}" if stream.grade else stream.name
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
            # Filter out marks with zero or null values
            valid_marks = [mark.mark for mark in grade_marks if mark.mark is not None and mark.mark > 0]
            if valid_marks:  # Only calculate if there are valid marks
                grade_avg = round(sum(valid_marks) / len(valid_marks), 2)
                grade_performances[grade.name] = grade_avg
    if grade_performances:
        least_performing_grade = min(grade_performances, key=grade_performances.get)
        least_grade_score = grade_performances[least_performing_grade]

    # Learners per grade with stream and gender breakdown
    learners_per_grade = {}
    gender_per_grade = {}
    streams_per_grade = {}

    students = Student.query.all()
    for student in students:
        grade = student.stream.grade.name if student.stream and student.stream.grade else "No Grade"
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
            # Get marks with valid percentages
            marks_with_percentage = [m for m in subject_marks if m.percentage is not None and m.percentage > 0]

            if marks_with_percentage:  # Only calculate if there are valid marks
                subject_avg = round(sum(mark.percentage for mark in marks_with_percentage) / len(marks_with_percentage), 2)
                subject_performance[subject.name] = {
                    'average': subject_avg,
                    'total_assessments': len(subject_marks),
                    'valid_assessments': len(marks_with_percentage),
                    'education_level': subject.education_level
                }
            else:
                # Handle case where no valid marks exist
                subject_performance[subject.name] = {
                    'average': 0,
                    'total_assessments': len(subject_marks),
                    'valid_assessments': 0,
                    'education_level': subject.education_level
                }

    # Generate performance assessment data
    performance_data = generate_performance_assessment_data()

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

    # Academic calendar overview
    current_term = Term.query.first()  # Get current term
    upcoming_assessments = get_upcoming_assessments()

    # System alerts
    system_alerts = generate_system_alerts()

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
        'performance_alerts': performance_alerts,
        'performance_distribution': performance_distribution,
        'performance_data': performance_data,
        'current_term': current_term,
        'upcoming_assessments': upcoming_assessments,
        'system_alerts': system_alerts
    }

    # Get school configuration for dynamic display
    school_info = SchoolConfigService.get_school_info_dict()

    # Merge school info with dashboard stats
    dashboard_stats.update(school_info)

    # Temporarily disable caching for debugging
    # cache_dashboard_stats(dashboard_stats)

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
                try:
                    from ..utils.database_utils import safe_delete_teacher

                    result = safe_delete_teacher(teacher_id)

                    if result['success']:
                        # Invalidate admin cache since data has changed
                        invalidate_admin_cache()
                        success_message = result['message']
                        # Refresh teachers list
                        teachers = Teacher.query.all()
                    else:
                        error_message = result['message']

                except ImportError:
                    # Fallback to original method if utils not available
                    teacher = Teacher.query.get(teacher_id)
                    if teacher:
                        try:
                            # First, manually delete related records to avoid cascade issues
                            from sqlalchemy import text

                            # Delete from teacher_subjects table if it exists
                            try:
                                db.session.execute(text("DELETE FROM teacher_subjects WHERE teacher_id = :teacher_id"),
                                                 {"teacher_id": teacher_id})
                            except Exception as e:
                                print(f"Note: teacher_subjects table cleanup: {e}")

                            # Delete from teacher_subject_assignment table
                            try:
                                db.session.execute(text("DELETE FROM teacher_subject_assignment WHERE teacher_id = :teacher_id"),
                                                 {"teacher_id": teacher_id})
                            except Exception as e:
                                print(f"Note: teacher_subject_assignment table cleanup: {e}")

                            # Now delete the teacher
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
                    else:
                        error_message = "Teacher not found."

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

                        grade_name = existing_grade.name if existing_grade else "Unknown Grade"
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
                            success_message = f"Teacher '{teacher.username}' assigned as class teacher to {grade.name} {stream_text}."
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
                        error_message = f"Teacher '{teacher.username}' is already assigned to teach {subject.name} for {grade.name} {stream_text}."
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
                            success_message = f"Teacher '{teacher.username}' assigned to teach {subject.name} for {grade.name} {stream_text}."
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

    # Get all teacher assignments using utility functions
    try:
        from ..utils.database_utils import get_teacher_assignments_safely, get_database_health

        # Get assignments safely
        assignments = get_teacher_assignments_safely()

        # If no assignments and this is a GET request, check database health
        if not assignments and request.method == 'GET':
            health = get_database_health()

            if health['status'] == 'needs_migration':
                # Only show error message if there are actually missing tables
                if 'teacher_subject_assignment' in health['missing_tables']:
                    error_message = "Teacher assignment data is being initialized. Please refresh the page if this message persists."
            elif health['status'] == 'critical':
                error_message = "Database connection issue. Please check the system configuration."

    except ImportError:
        # Fallback to original method if utils not available
        assignments = []
        try:
            assignments = TeacherSubjectAssignment.query.all()
        except Exception as e:
            print(f"Error querying teacher assignments: {e}")
            if "no such table" in str(e).lower() and request.method == 'GET':
                error_message = "Teacher assignment table not found. Please run database migration."

    # Enhance teacher data with computed attributes
    enhanced_teachers = []
    for teacher in teachers:
        # Get teacher's assignments
        teacher_assignments = [a for a in assignments if a.teacher_id == teacher.id]

        # Calculate total assignments
        total_assignments = len(teacher_assignments)

        # Get subjects taught
        subjects_taught = []
        class_assignments = []
        is_class_teacher = False

        for assignment in teacher_assignments:
            # Get subject info
            subject = next((s for s in subjects if s.id == assignment.subject_id), None)
            if subject and subject.name not in subjects_taught:
                subjects_taught.append(subject.name)

            # Get class assignments (for class teachers)
            if assignment.is_class_teacher:
                is_class_teacher = True
                grade = next((g for g in grades if g.id == assignment.grade_id), None)
                stream = next((s for s in streams if s.id == assignment.stream_id), None) if assignment.stream_id else None

                if grade:
                    class_assignment = {
                        'grade': grade.name,
                        'stream': stream.name if stream else 'All Streams'
                    }
                    class_assignments.append(class_assignment)

        # Add computed attributes to teacher object
        teacher.total_assignments = total_assignments
        teacher.subjects_taught = subjects_taught
        teacher.class_assignments = class_assignments
        teacher.is_class_teacher = is_class_teacher

        enhanced_teachers.append(teacher)

    # Render the template with enhanced data
    return render_template('manage_teachers.html',
                          teachers=enhanced_teachers,
                          grades=grades,
                          streams=streams,
                          subjects=subjects,
                          assignments=assignments,
                          error_message=error_message,
                          success_message=success_message)

@admin_bp.route('/manage_subjects', methods=['GET', 'POST'])
@admin_required
@sql_injection_protection
def manage_subjects():
    """Route for managing subjects."""
    error_message = None
    success_message = None

    # Disable caching temporarily to fix pagination issue
    # if request.method == 'GET':
    #     cached_subjects = get_cached_subject_list()
    #     if cached_subjects:
    #         return render_template('manage_subjects.html', **cached_subjects)

    # Get pagination parameters with validation
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of subjects per page

    # Validate and sanitize search query
    search_query = request.args.get('search', '')
    if search_query and not validate_admin_input(search_query, "search", 100):
        flash("Invalid search query", "error")
        search_query = ""
    search_query = sanitize_search_query(search_query)

    # Validate education level filter
    education_level_filter = request.args.get('education_level', '')
    if education_level_filter and not validate_admin_input(education_level_filter, "education_level", 50):
        flash("Invalid education level filter", "error")
        education_level_filter = ""

    # Build query with filters
    query = Subject.query

    if search_query:
        query = query.filter(Subject.name.contains(search_query))

    if education_level_filter:
        query = query.filter(Subject.education_level == education_level_filter)

    # Get paginated subjects
    pagination_obj = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    subjects = pagination_obj.items

    # Create a simple pagination dict for template
    pagination = {
        'page': pagination_obj.page,
        'pages': pagination_obj.pages,
        'per_page': pagination_obj.per_page,
        'total': pagination_obj.total,
        'has_prev': pagination_obj.has_prev,
        'has_next': pagination_obj.has_next,
        'prev_num': pagination_obj.prev_num,
        'next_num': pagination_obj.next_num,
        'iter_pages': list(pagination_obj.iter_pages(left_edge=2, left_current=2, right_current=3, right_edge=2))
    }

    # Get all subjects for education levels (not filtered)
    all_subjects = Subject.query.all()
    education_levels = list(set([subject.education_level for subject in all_subjects]))

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
                        # Refresh subjects list with pagination
                        query = Subject.query
                        if search_query:
                            query = query.filter(Subject.name.contains(search_query))
                        if education_level_filter:
                            query = query.filter(Subject.education_level == education_level_filter)
                        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
                        subjects = pagination.items
                        # Update education levels
                        all_subjects = Subject.query.all()
                        education_levels = list(set([subject.education_level for subject in all_subjects]))
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
                            # Refresh subjects list with pagination
                            query = Subject.query
                            if search_query:
                                query = query.filter(Subject.name.contains(search_query))
                            if education_level_filter:
                                query = query.filter(Subject.education_level == education_level_filter)
                            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
                            subjects = pagination.items
                            # Update education levels
                            all_subjects = Subject.query.all()
                            education_levels = list(set([subject.education_level for subject in all_subjects]))
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
        'pagination': pagination,
        'search_query': search_query,
        'current_education_level': education_level_filter,
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
                existing_grade = Grade.query.filter_by(name=grade_level).first()
                if existing_grade:
                    error_message = f"Grade '{grade_level}' already exists."
                else:
                    # Determine education level based on grade
                    education_level = "lower_primary"
                    if "4" in grade_level or "5" in grade_level or "6" in grade_level:
                        education_level = "upper_primary"
                    elif "7" in grade_level or "8" in grade_level or "9" in grade_level:
                        education_level = "junior_secondary"

                    # Create new grade
                    new_grade = Grade(name=grade_level, education_level=education_level)
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
                    error_message = f"Stream '{stream_name}' already exists for {grade.name if grade else 'this grade'}."
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
                    try:
                        # Delete all streams associated with this grade first
                        streams_in_grade = Stream.query.filter_by(grade_id=grade_id).all()
                        for stream in streams_in_grade:
                            db.session.delete(stream)

                        # Now delete the grade
                        grade_name = grade.name
                        db.session.delete(grade)
                        db.session.commit()
                        success_message = f"Grade '{grade_name}' and its streams deleted successfully."
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
                    if grade_level != grade.name:
                        existing_grade = Grade.query.filter_by(name=grade_level).first()
                        if existing_grade:
                            error_message = f"Grade '{grade_level}' already exists."
                            return render_template('manage_grades_streams.html',
                                                grades=grades,
                                                streams=streams,
                                                error_message=error_message,
                                                success_message=success_message)

                    # Update grade
                    grade.name = grade_level

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
                            error_message = f"Stream '{stream_name}' already exists for {grade.name if grade else 'this grade'}."
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


# Removed duplicate analytics route - using analytics_dashboard() instead


def generate_performance_assessment_data():
    """
    Generate dynamic performance assessment data based on actual reports in the database.

    Returns:
        List of dictionaries containing performance data for each grade/stream/term/assessment combination.
    """
    performance_data = []
    print("DEBUG: Starting performance data generation...")

    # Get all unique combinations of grade, stream, term, and assessment type
    # We'll calculate student averages per assessment to avoid counting multiple subjects per student

    # First, get all unique grade/stream/term/assessment combinations
    combinations = db.session.query(
        Grade.name.label('grade'),
        Stream.name.label('stream'),
        Term.name.label('term'),
        AssessmentType.name.label('assessment_type'),
        Term.id.label('term_id'),
        AssessmentType.id.label('assessment_type_id'),
        Grade.id.label('grade_id'),
        Stream.id.label('stream_id')
    ).join(
        Stream, Grade.id == Stream.grade_id
    ).join(
        Student, Stream.id == Student.stream_id
    ).join(
        Mark, Student.id == Mark.student_id
    ).join(
        Term, Mark.term_id == Term.id
    ).join(
        AssessmentType, Mark.assessment_type_id == AssessmentType.id
    ).filter(
        Mark.percentage.isnot(None),
        Mark.raw_mark.isnot(None),
        Mark.raw_total_marks.isnot(None)
    ).distinct().all()

    print(f"DEBUG: Found {len(combinations)} unique combinations")
    for combo in combinations[:3]:  # Show first 3
        print(f"DEBUG: Combo - Grade: {combo.grade}, Stream: {combo.stream}, Term: {combo.term}, Assessment: {combo.assessment_type}")

    # For each combination, calculate student averages to avoid double counting
    for combo in combinations:
        # Get all students in this grade/stream who have marks for this term/assessment
        students_with_marks = db.session.query(
            Student.id,
            db.func.avg(Mark.percentage).label('avg_percentage'),
            db.func.sum(Mark.raw_mark).label('total_raw_marks'),
            db.func.sum(Mark.raw_total_marks).label('total_max_marks'),
            db.func.count(Mark.id).label('subject_count')
        ).join(
            Mark, Student.id == Mark.student_id
        ).join(
            Stream, Student.stream_id == Stream.id
        ).filter(
            Stream.grade_id == combo.grade_id,
            Stream.id == combo.stream_id,
            Mark.term_id == combo.term_id,
            Mark.assessment_type_id == combo.assessment_type_id,
            Mark.percentage.isnot(None),
            Mark.raw_mark.isnot(None),
            Mark.raw_total_marks.isnot(None)
        ).group_by(Student.id).all()

        if not students_with_marks:
            continue

        # Calculate statistics for this combination
        student_percentages = [student.avg_percentage for student in students_with_marks]
        total_raw_marks = sum([student.total_raw_marks for student in students_with_marks])
        total_possible_marks = sum([student.total_max_marks for student in students_with_marks])

        # Calculate mean percentage for performance category (this is the class average)
        mean_percentage = round(sum(student_percentages) / len(student_percentages), 2) if student_percentages else 0

        # Calculate class average as it appears in class teacher reports
        # This should be the average of total raw marks per student (like 649.4), not percentage
        class_average = round(total_raw_marks / len(students_with_marks), 2) if students_with_marks else 0

        print(f"DEBUG: {combo.grade} {combo.stream} {combo.term} {combo.assessment_type}: {len(students_with_marks)} students")
        print(f"DEBUG: Class average: {class_average}, Raw marks: {int(round(total_raw_marks, 0))}/{int(round(total_possible_marks, 0))}")

        # Calculate detailed performance counts using the established grading system
        # Count students, not individual subject marks
        performance_counts = {
            'EE1': 0, 'EE2': 0, 'ME1': 0, 'ME2': 0,
            'AE1': 0, 'AE2': 0, 'BE1': 0, 'BE2': 0
        }

        for student in students_with_marks:
            percentage = student.avg_percentage
            if percentage >= 90:
                performance_counts['EE1'] += 1
            elif percentage >= 75:
                performance_counts['EE2'] += 1
            elif percentage >= 58:
                performance_counts['ME1'] += 1
            elif percentage >= 41:
                performance_counts['ME2'] += 1
            elif percentage >= 31:
                performance_counts['AE1'] += 1
            elif percentage >= 21:
                performance_counts['AE2'] += 1
            elif percentage >= 11:
                performance_counts['BE1'] += 1
            else:
                performance_counts['BE2'] += 1

        # Determine overall performance category
        if mean_percentage >= 75:
            performance_category = "Excellent"
        elif mean_percentage >= 60:
            performance_category = "Good"
        elif mean_percentage >= 45:
            performance_category = "Average"
        else:
            performance_category = "Below Average"

        performance_data.append({
            'grade': combo.grade,
            'stream': combo.stream,
            'term': combo.term,
            'assessment_type': combo.assessment_type,
            'mean_percentage': mean_percentage,
            'class_average': class_average,  # Use class average percentage instead of raw marks
            'total_raw_marks': int(round(total_raw_marks, 0)),  # Show as whole numbers
            'total_possible_marks': int(round(total_possible_marks, 0)),  # Show as whole numbers
            'performance_category': performance_category,
            'performance_counts': performance_counts,
            'total_students': len(students_with_marks)  # Count unique students only
        })

    # Sort by grade, then stream, then term, then assessment type
    performance_data.sort(key=lambda x: (x['grade'], x['stream'], x['term'], x['assessment_type']))

    return performance_data


def get_upcoming_assessments():
    """
    Get upcoming assessment information.

    Returns:
        List of upcoming assessments or assessment-related information.
    """
    # For now, return basic assessment type information
    # In a real implementation, this would include dates and schedules
    assessment_types = AssessmentType.query.all()
    upcoming = []

    for assessment in assessment_types:
        upcoming.append({
            'name': assessment.name,
            'weight': assessment.weight,
            'status': 'Active'
        })

    return upcoming


def generate_system_alerts():
    """
    Generate system alerts for incomplete assessments or missing data.

    Returns:
        List of system alerts.
    """
    alerts = []

    # Check for grades without any marks
    grades_with_marks = db.session.query(Grade.id).join(
        Stream, Grade.id == Stream.grade_id
    ).join(
        Student, Stream.id == Student.stream_id
    ).join(
        Mark, Student.id == Mark.student_id
    ).distinct().all()

    grades_with_marks_ids = [g[0] for g in grades_with_marks]
    all_grades = Grade.query.all()

    for grade in all_grades:
        if grade.id not in grades_with_marks_ids:
            alerts.append({
                'type': 'warning',
                'title': 'No Assessment Data',
                'message': f"Grade {grade.name} has no assessment data recorded",
                'action': 'Add marks for this grade'
            })

    # Check for students without marks in current term
    current_term = Term.query.first()
    if current_term:
        students_without_marks = db.session.query(Student).outerjoin(
            Mark, (Student.id == Mark.student_id) & (Mark.term_id == current_term.id)
        ).filter(Mark.id.is_(None)).count()

        if students_without_marks > 0:
            alerts.append({
                'type': 'info',
                'title': 'Students Without Current Term Marks',
                'message': f"{students_without_marks} students have no marks for {current_term.name}",
                'action': 'Review and add missing marks'
            })

    return alerts


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

    # Get school information
    from ..services.school_config_service import SchoolConfigService
    school_info = SchoolConfigService.get_school_info_dict()

    return render_template('reports.html', report_types=report_types, school_info=school_info)


# ============================================================================
# STUDENT PROMOTION ROUTES
# ============================================================================


@admin_bp.route('/api/streams/<int:grade_id>')
@admin_required
def get_streams_for_grade(grade_id):
    """API endpoint for headteachers to get streams for a grade."""
    try:
        streams = Stream.query.filter_by(grade_id=grade_id).all()
        return jsonify({
            'streams': [{'id': stream.id, 'name': stream.name} for stream in streams]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/teacher_streams/<int:grade_id>')
@admin_required
def get_teacher_streams(grade_id):
    """API endpoint for headteachers to get streams for a grade (teacher management)."""
    try:
        streams = Stream.query.filter_by(grade_id=grade_id).all()
        return jsonify({
            'streams': [{'id': stream.id, 'name': stream.name} for stream in streams]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/streams_by_level/<grade>')
@admin_required
def get_streams_by_level(grade):
    """API endpoint for headteachers to get streams by grade level."""
    try:
        # Handle both "Grade X" format and just "X" format
        if grade.isdigit():
            grade_name = f"Grade {grade}"
        else:
            grade_name = grade

        grade_obj = Grade.query.filter_by(name=grade_name).first()
        if grade_obj:
            streams = Stream.query.filter_by(grade_id=grade_obj.id).all()
            return jsonify({
                'success': True,
                'streams': [{'id': stream.id, 'name': stream.name} for stream in streams]
            })
        return jsonify({'success': False, 'streams': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/create-test-students')
@admin_required
def create_test_students():
    """Create test students in different grades for promotion testing."""
    try:
        from ..models.academic import Student, Grade, Stream

        # Get grades (excluding Grade 9)
        grades = Grade.query.filter(Grade.name != 'Grade 9').all()
        if not grades:
            return "No grades found (excluding Grade 9)"

        # Get a stream
        stream = Stream.query.first()
        if not stream:
            return "No streams found"

        # Create test students
        test_students = []
        for i, grade in enumerate(grades[:3]):  # Create students in first 3 grades
            for j in range(2):  # 2 students per grade
                student = Student(
                    name=f"Test Student {grade.name} {j+1}",
                    grade_id=grade.id,
                    stream_id=stream.id,
                    is_active=True
                )
                db.session.add(student)
                test_students.append(f"{student.name} - {grade.name}")

        db.session.commit()

        return f"<h2>Test Students Created Successfully!</h2><ul>{''.join([f'<li>{s}</li>' for s in test_students])}</ul><p><a href='/headteacher/student-promotion'>Go to Student Promotion</a></p>"

    except Exception as e:
        return f"Error creating test students: {str(e)}"

@admin_bp.route('/debug-log', methods=['POST'])
@admin_required
def debug_log():
    """Handle debug messages from frontend"""
    try:
        data = request.get_json()
        message = data.get('message', 'Debug message')
        extra_data = data.get('data', {})
        error = data.get('error', '')

        if error:
            print(f"{message}: {error}")
        elif extra_data:
            print(f"{message}: {extra_data}")
        else:
            print(message)

        return jsonify({'status': 'ok'})
    except Exception as e:
        print(f"❌ Debug log error: {str(e)}")
        return jsonify({'status': 'error'})

@admin_bp.route('/student-promotion')
@admin_required
@sql_injection_protection
def student_promotion():
    """Display enhanced student promotion management interface with analytics and batch processing."""
    try:
        from ..services.student_promotion_service import StudentPromotionService
        from ..services.school_config_service import SchoolConfigService

        # Get current academic year (you can make this configurable)
        current_academic_year = "2024-2025"

        # Get filter parameters from request with validation
        education_level = request.args.get('education_level')
        if education_level and not validate_admin_input(education_level, "education_level", 50):
            flash("Invalid education level parameter", "error")
            education_level = None

        grade_id = request.args.get('grade_id', type=int)
        stream_id = request.args.get('stream_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        # Validate numeric parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 200:  # Reasonable limits
            per_page = 50

        # Get promotion preview data with filters and pagination
        promotion_data_raw = StudentPromotionService.get_promotion_preview_data(
            academic_year=current_academic_year,
            education_level=education_level,
            grade_id=grade_id,
            stream_id=stream_id,
            page=page,
            per_page=per_page
        )

        # Keep the raw dictionary for JSON serialization and create DictToObject for template access
        if isinstance(promotion_data_raw, dict):
            from ..services.student_promotion_service import DictToObject
            promotion_data = DictToObject(promotion_data_raw)
            promotion_data_json = promotion_data_raw  # Keep original dict for JSON
        else:
            promotion_data = promotion_data_raw
            promotion_data_json = promotion_data_raw._dict if hasattr(promotion_data_raw, '_dict') else {}

        # Get filter options
        filter_options = StudentPromotionService.get_filter_options()

        # Get school information
        school_info = SchoolConfigService.get_school_info_dict()

        return render_template('student_promotion.html',
                             promotion_data=promotion_data,
                             promotion_data_json=promotion_data_json,
                             filter_options=filter_options,
                             school_info=school_info,
                             academic_year=current_academic_year)

    except Exception as e:
        flash(f'Error loading student promotion data: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/student-promotion/create-sample-data')
@admin_required
def create_sample_promotion_data():
    """Create sample data for testing the enhanced promotion system."""
    try:
        from ..models.academic import Student, Grade, Stream
        from datetime import date
        import random

        # Create sample students for testing
        first_names = ['John', 'Mary', 'Peter', 'Grace', 'David', 'Sarah', 'Michael', 'Faith']
        last_names = ['Kiprotich', 'Wanjiku', 'Mwangi', 'Achieng', 'Kiplagat', 'Njeri']

        admission_counter = 3000
        students_created = 0

        # Get existing grades and streams
        grades = Grade.query.order_by(Grade.level).all()

        if not grades:
            flash('❌ No grades found. Please set up grades first.', 'error')
            return redirect(url_for('admin.student_promotion'))

        for grade in grades:
            streams = Stream.query.filter_by(grade_id=grade.id).all()

            if not streams:
                # Create default streams if none exist
                for stream_name in ['A', 'B']:
                    stream = Stream(
                        name=stream_name,
                        grade_id=grade.id,
                        capacity=40
                    )
                    db.session.add(stream)
                db.session.commit()
                streams = Stream.query.filter_by(grade_id=grade.id).all()

            for stream in streams:
                # Create 5-8 students per stream for testing
                num_students = random.randint(5, 8)

                for i in range(num_students):
                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)
                    full_name = f"{first_name} {last_name} Test{i+1}"

                    # Check if student already exists
                    existing_student = Student.query.filter_by(
                        name=full_name,
                        grade_id=grade.id,
                        stream_id=stream.id
                    ).first()

                    if existing_student:
                        continue

                    admission_counter += 1

                    # Most students are eligible for promotion
                    can_be_promoted = random.choice([True, True, True, False])  # 75% eligible

                    student = Student(
                        name=full_name,
                        admission_number=f"TEST{admission_counter:04d}",
                        grade_id=grade.id,
                        stream_id=stream.id,
                        gender=random.choice(['Male', 'Female']),
                        date_of_birth=date(2010 + grade.level, random.randint(1, 12), random.randint(1, 28)),
                        academic_year="2024-2025",
                        promotion_status='active',
                        is_eligible_for_promotion=can_be_promoted,
                        date_enrolled=date(2024 - grade.level + 1, 1, 15)
                    )

                    db.session.add(student)
                    students_created += 1

        db.session.commit()

        flash(f'✅ Successfully created {students_created} sample students for promotion testing!', 'success')
        return redirect(url_for('admin.student_promotion'))

    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error creating sample data: {str(e)}', 'error')
        return redirect(url_for('admin.student_promotion'))


@admin_bp.route('/debug-students')
@admin_required
def debug_students_simple():
    """Simple debug route to check students."""
    try:
        from ..models.academic import Student, Grade, Stream

        # Get all students
        all_students = Student.query.all()
        students_with_grades = db.session.query(Student, Grade).join(Grade, Student.grade_id == Grade.id).all()

        result = {
            'total_students': len(all_students),
            'students_with_grades': len(students_with_grades),
            'students_list': []
        }

        for student, grade in students_with_grades[:10]:  # Show first 10
            result['students_list'].append({
                'name': student.name,
                'grade': grade.name,
                'promotion_status': getattr(student, 'promotion_status', 'NOT_SET')
            })

        return f"<pre>{result}</pre>"
    except Exception as e:
        return f"Error: {str(e)}"

@admin_bp.route('/student-promotion/debug')
@admin_required
def debug_promotion_data():
    """Debug route to check student data in database."""
    try:
        from ..models.academic import Student, Grade, Stream

        # Get all students with their grades
        students = db.session.query(Student, Grade, Stream).join(
            Grade, Student.grade_id == Grade.id
        ).outerjoin(
            Stream, Student.stream_id == Stream.id
        ).all()

        debug_info = {
            'total_students': len(students),
            'students_by_grade': {},
            'all_grades': [g.name for g in Grade.query.all()],
            'students_list': [],
            'promotion_status_analysis': {}
        }

        # Analyze promotion status
        all_students = Student.query.all()
        promotion_statuses = {}
        for student in all_students:
            status = getattr(student, 'promotion_status', 'NOT_SET')
            if status not in promotion_statuses:
                promotion_statuses[status] = 0
            promotion_statuses[status] += 1

        debug_info['promotion_status_analysis'] = promotion_statuses

        for student, grade, stream in students:
            grade_name = grade.name
            if grade_name not in debug_info['students_by_grade']:
                debug_info['students_by_grade'][grade_name] = 0
            debug_info['students_by_grade'][grade_name] += 1

            debug_info['students_list'].append({
                'name': student.name,
                'admission_number': student.admission_number,
                'grade': grade.name,
                'stream': stream.name if stream else 'No Stream',
                'promotion_status': student.promotion_status,
                'is_eligible': student.is_eligible_for_promotion
            })

        return f"<h1>Debug Info</h1><pre>{debug_info}</pre>"

    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>"


@admin_bp.route('/student-promotion/process', methods=['POST'])
@admin_required
def process_promotion():
    """Process bulk student promotions."""
    try:
        from ..services.student_promotion_service import StudentPromotionService

        # Get form data
        academic_year = request.form.get('academic_year', '2024-2025')
        promotion_actions = {}

        # Parse promotion actions from form
        for key, value in request.form.items():
            if key.startswith('promotion_action_'):
                student_id = int(key.replace('promotion_action_', ''))
                promotion_actions[student_id] = value

        # Get teacher ID from session
        teacher_id = session.get('teacher_id')
        if not teacher_id:
            flash('Authentication error. Please log in again.', 'error')
            return redirect(url_for('auth.admin_login'))

        # Prepare promotion data in the expected format
        promotion_data = {
            'academic_year_to': academic_year,  # Changed from 'academic_year' to 'academic_year_to'
            'students': []
        }

        # Convert promotion actions to the expected format
        for student_id, action in promotion_actions.items():
            promotion_data['students'].append({
                'student_id': int(student_id),  # Ensure student_id is integer
                'action': action
            })

        # Process the promotions
        result = StudentPromotionService.process_bulk_promotion(
            promotion_data=promotion_data,
            promoted_by_teacher_id=teacher_id
        )

        if result['success']:
            flash(f"✅ Successfully processed {result['processed_count']} student promotions!", 'success')
        else:
            flash(f"❌ Error processing promotions: {result['message']}", 'error')

    except Exception as e:
        flash(f'Error processing student promotions: {str(e)}', 'error')

    return redirect(url_for('admin.student_promotion'))