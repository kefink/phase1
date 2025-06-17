"""
Class Teacher views for the Hillview School Management System.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, jsonify, make_response
from werkzeug.security import generate_password_hash
from sqlalchemy import text
import pandas as pd
import os
from io import BytesIO
from werkzeug.utils import secure_filename
from ..models import Grade, Stream, Subject, Term, AssessmentType, Student, Mark, Teacher, TeacherSubjectAssignment
from ..models.academic import SubjectMarksStatus
from ..utils.constants import educational_level_mapping
from ..services import is_authenticated, get_role, get_class_report_data, generate_individual_report, generate_class_report_pdf, RoleBasedDataService
from ..services.report_service import generate_class_report_pdf_from_html
from ..services.mark_conversion_service import MarkConversionService
from ..extensions import db
from ..utils import get_performance_category, get_performance_remarks
from ..services.cache_service import (
    cache_marksheet, get_cached_marksheet,
    cache_report, get_cached_report,
    cache_pdf, get_cached_pdf,
    invalidate_cache
)
from ..services.collaborative_marks_service import CollaborativeMarksService
from ..services.grade_report_service import GradeReportService
from ..services.enhanced_permission_service import EnhancedPermissionService, function_permission_required
from ..services.report_config_service import ReportConfigService
from ..utils.database_health import check_database_health, create_missing_tables, safe_table_operation
from ..services.permission_service import PermissionService
from ..models.function_permission import DefaultFunctionPermissions
from functools import wraps

# Create a blueprint for class teacher routes
classteacher_bp = Blueprint('classteacher', __name__, url_prefix='/classteacher')

# Register template filter for education level
@classteacher_bp.app_template_filter('get_education_level')
def get_education_level_blueprint(grade):
    """Filter to determine the education level for a grade (blueprint version)."""
    education_level_mapping = {
        'lower_primary': ['Grade 1', 'Grade 2', 'Grade 3'],
        'upper_primary': ['Grade 4', 'Grade 5', 'Grade 6'],
        'junior_secondary': ['Grade 7', 'Grade 8', 'Grade 9']
    }

    for level, grades in education_level_mapping.items():
        if grade in grades:
            return level
    return ''

# Enhanced decorator for requiring class teacher authentication with function permissions
def classteacher_required(f):
    """
    Enhanced decorator to require class teacher authentication with function-level permissions.
    Only allows marks upload and report generation by default. Other functions require explicit permission.
    Headteachers have universal access to all classteacher functions.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session):
            # Check if this is an AJAX/API request
            if request.is_json or request.headers.get('Content-Type') == 'application/json' or 'api' in request.endpoint or request.path.startswith('/classteacher/get_'):
                return jsonify({"success": False, "message": "Authentication required", "redirect": url_for('auth.classteacher_login')}), 401
            return redirect(url_for('auth.classteacher_login'))

        role = get_role(session)

        # HEADTEACHER UNIVERSAL ACCESS - Always allow headteachers to access all classteacher functions
        if role == 'headteacher':
            # Set the universal access flag if not already set
            if not session.get('headteacher_universal_access'):
                session['headteacher_universal_access'] = True
                session.permanent = True  # Ensure session persists
            return f(*args, **kwargs)

        # For classteachers, check function-level permissions
        if role == 'classteacher':
            teacher_id = session.get('teacher_id')
            function_name = f.__name__  # Get the function name

            # Check if this function has permission
            has_permission = EnhancedPermissionService.check_function_permission(
                teacher_id, function_name
            )

            if has_permission:
                return f(*args, **kwargs)
            else:
                # Special case: If teacher has any class permissions, allow management functions
                if DefaultFunctionPermissions.is_management_function(function_name):
                    # Check if teacher has any class permissions
                    class_permissions = PermissionService.get_teacher_assigned_classes(teacher_id)
                    if class_permissions and len(class_permissions) > 0:
                        # Teacher has class permissions, allow management functions
                        return f(*args, **kwargs)

                # Function requires permission that teacher doesn't have
                if request.is_json or request.headers.get('Content-Type') == 'application/json' or 'api' in request.endpoint or request.path.startswith('/classteacher/get_'):
                    return jsonify({"success": False, "message": f"Permission denied for function: {function_name}"}), 403
                return redirect(url_for('classteacher.permission_denied', function_name=function_name))

        # Final fallback for non-classteacher/non-headteacher roles
        if request.is_json or request.headers.get('Content-Type') == 'application/json' or 'api' in request.endpoint or request.path.startswith('/classteacher/get_'):
            return jsonify({"success": False, "message": "Access denied", "redirect": url_for('auth.classteacher_login')}), 403
        return redirect(url_for('auth.classteacher_login'))
    return decorated_function

# Decorator for requiring class teacher OR teacher authentication (for shared routes)
def teacher_or_classteacher_required(f):
    """Decorator to require teacher or class teacher authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session):
            return redirect(url_for('auth.teacher_login'))

        role = get_role(session)

        # HEADTEACHER UNIVERSAL ACCESS - Always allow headteachers
        if role == 'headteacher':
            # Set the universal access flag if not already set
            if not session.get('headteacher_universal_access'):
                session['headteacher_universal_access'] = True
                session.permanent = True  # Ensure session persists
            return f(*args, **kwargs)

        if role not in ['teacher', 'classteacher']:
            # Redirect to appropriate login based on current role attempt
            if role == 'teacher':
                return redirect(url_for('auth.teacher_login'))
            else:
                return redirect(url_for('auth.classteacher_login'))
        return f(*args, **kwargs)
    return decorated_function

@classteacher_bp.route('/permission_denied')
def permission_denied():
    """Enhanced permission denied page with guidance."""
    function_name = request.args.get('function_name', 'unknown function')
    teacher_id = session.get('teacher_id')

    # Get teacher info
    teacher = Teacher.query.get(teacher_id) if teacher_id else None

    # Get function category and description
    function_category = DefaultFunctionPermissions.get_function_category(function_name)

    # Check if function is restricted or unknown
    is_restricted = DefaultFunctionPermissions.is_restricted(function_name)
    is_default_allowed = DefaultFunctionPermissions.is_default_allowed(function_name)

    # Get teacher's current permissions
    current_permissions = []
    if teacher_id:
        current_permissions = EnhancedPermissionService.get_teacher_function_summary(teacher_id)

    return render_template('permission_denied.html',
                         function_name=function_name,
                         function_category=function_category,
                         is_restricted=is_restricted,
                         is_default_allowed=is_default_allowed,
                         teacher=teacher,
                         current_permissions=current_permissions)

@classteacher_bp.route('/test_components')
@classteacher_required
def test_components():
    """Test route to display components."""
    from ..models.academic import Subject

    # Get all subjects
    subjects = Subject.query.all()

    return render_template('test_components.html', subjects=subjects)

@classteacher_bp.route('/test_edit_marks', methods=['GET', 'POST'])
@classteacher_required
def test_edit_marks():
    """Test route to display edit marks page."""
    from ..models.academic import Subject

    # Get all subjects
    subject_objects = Subject.query.all()

    # Handle form submission
    if request.method == 'POST':
        # Process the form data
        flash("Form submitted successfully! This is just a test page.", "success")
        return redirect(url_for('classteacher.test_edit_marks'))

    return render_template('test_edit_marks.html',
                          grade="Grade 7",
                          stream="Stream Y",
                          term="Term 1",
                          assessment_type="Mid Term",
                          subject_objects=subject_objects)


@classteacher_bp.route('/analytics')
@classteacher_required
def analytics_dashboard():
    """Dedicated analytics page for classteachers."""
    try:
        teacher_id = session.get('teacher_id')
        if not teacher_id:
            flash('Please log in to access analytics.', 'error')
            return redirect(url_for('auth.classteacher_login'))

        # Get teacher information
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            flash('Teacher not found.', 'error')
            return redirect(url_for('auth.classteacher_login'))

        # Get analytics data - prioritize report-based analytics
        try:
            from ..services.report_based_analytics_service import ReportBasedAnalyticsService

            # Try report-based analytics first
            analytics_data = ReportBasedAnalyticsService.get_analytics_dashboard_data(
                role='classteacher',
                teacher_id=teacher_id
            )

            # If no report data available, fall back to traditional analytics
            if not analytics_data.get('has_data', False):
                from ..services.analytics_service import AnalyticsService
                fallback_data = AnalyticsService.get_classteacher_analytics(teacher_id)

                # Merge the data, prioritizing report-based structure
                analytics_data.update({
                    'top_students': fallback_data.get('top_students', []),
                    'subject_performance': fallback_data.get('subject_performance', []),
                    'summary': fallback_data.get('summary', {}),
                    'has_data': fallback_data.get('has_data', False),
                    'data_source': 'live_calculation'
                })

                flash('Analytics based on live data calculation. Generate reports for more accurate insights.', 'info')
            else:
                flash('Analytics based on generated reports - reflecting actual academic workflow.', 'success')

        except Exception as e:
            print(f"Error loading analytics: {e}")
            flash(f'Error loading analytics: {str(e)}', 'error')
            analytics_data = {'has_data': False, 'summary': {}, 'top_students': [], 'subject_performance': [], 'data_source': 'error'}

        # Get filter options
        terms = [term.name for term in Term.query.all()]
        assessment_types = [at.name for at in AssessmentType.query.all()]

        return render_template('classteacher_analytics.html',
                             teacher=teacher,
                             analytics_data=analytics_data,
                             terms=terms,
                             assessment_types=assessment_types,
                             page_title="Academic Performance Analytics")

    except Exception as e:
        print(f"Error loading analytics dashboard: {e}")
        flash('Error loading analytics dashboard.', 'error')
        return redirect(url_for('classteacher.dashboard'))


@classteacher_bp.route('/', methods=['GET', 'POST'])
@classteacher_required
def dashboard():
    """Route for the class teacher dashboard."""
    # Get the teacher
    teacher_id = session.get('teacher_id')
    teacher = Teacher.query.get(teacher_id)

    if not teacher:
        flash("Teacher not found.", "error")
        return render_template("classteacher.html")

    # Get role-based assignment summary for classteacher
    teacher_id = session.get('teacher_id')
    role = session.get('role', 'classteacher')

    assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, role)

    if 'error' in assignment_summary:
        flash(f"Error loading assignments: {assignment_summary['error']}", "error")
        assignment_summary = {
            'teacher': teacher,
            'role': role,
            'subject_assignments': [],
            'class_teacher_assignments': [],
            'total_subjects_taught': 0,
            'can_manage_classes': False
        }

    # Extract assignments for backward compatibility
    class_teacher_assignments = assignment_summary.get('class_teacher_assignments', [])
    subject_assignments = assignment_summary.get('subject_assignments', [])

    # Initialize variables for teacher's assigned stream/grade (if any)
    stream = None
    grade = None
    grade_level = ""
    stream_name = ""

    # Check if teacher is assigned to a stream (direct assignment)
    if teacher.stream_id:
        stream = Stream.query.get(teacher.stream_id)
        if stream:
            grade = Grade.query.get(stream.grade_id)
            if grade:
                grade_level = grade.name
                stream_name = f"Stream {stream.name}"

    # If no direct stream assignment, check if teacher has subject assignments
    if not stream and assignment_summary.get('subject_assignments'):
        # Teacher has subject assignments, so they are assigned
        # Use the first assignment to show assignment status
        first_assignment = assignment_summary['subject_assignments'][0]
        if first_assignment.get('grade_name') and first_assignment.get('stream_name'):
            grade_level = first_assignment['grade_name']
            stream_name = f"Stream {first_assignment['stream_name']}"
            # Create a mock stream object for template compatibility
            stream = type('MockStream', (), {'name': first_assignment['stream_name']})()
            grade = type('MockGrade', (), {'name': first_assignment['grade_name']})()

    # If teacher has class teacher assignments, use those
    if not stream and assignment_summary.get('class_teacher_assignments'):
        first_class_assignment = assignment_summary['class_teacher_assignments'][0]
        if first_class_assignment.get('grade_name') and first_class_assignment.get('stream_name'):
            grade_level = first_class_assignment['grade_name']
            stream_name = f"Stream {first_class_assignment['stream_name']}"
            # Create a mock stream object for template compatibility
            stream = type('MockStream', (), {'name': first_class_assignment['stream_name']})()
            grade = type('MockGrade', (), {'name': first_class_assignment['grade_name']})()

    # Check if teacher has any assignments at all
    has_assignments = (
        assignment_summary.get('subject_assignments') or
        assignment_summary.get('class_teacher_assignments') or
        teacher.stream_id
    )

    # Get data for the form
    grades = [grade.name for grade in Grade.query.all()]
    grades_dict = {grade.name: grade.id for grade in Grade.query.all()}
    terms = [term.name for term in Term.query.all()]
    assessment_types = [assessment_type.name for assessment_type in AssessmentType.query.all()]
    streams = []  # Empty list - streams will be populated via JavaScript
    subjects = [subject.name for subject in Subject.query.all()]

    # Initialize variables
    error_message = None
    show_students = False
    students = []
    education_level = ""
    grade_level = grade.name if grade else ""
    stream_name = f"Stream {stream.name}" if stream else ""
    term = ""
    assessment_type = ""
    total_marks = 0
    show_download_button = False
    show_individual_report_button = False
    class_data = []
    stats = {}

    # Fetch recent reports with improved sorting and more entries
    recent_reports = []
    # Get the sort parameter from the request, default to date
    sort_by = request.args.get('sort', 'date')
    filter_grade = request.args.get('filter_grade', '')
    filter_term = request.args.get('filter_term', '')

    # Check if we should show the download button and individual report button
    show_download_button = request.args.get('show_download', type=int, default=0) == 1
    show_individual_report_button = request.args.get('show_individual', type=int, default=0) == 1

    # Build the query with joins
    marks_query = Mark.query.join(Student).join(Stream).join(Grade).join(Term).join(AssessmentType)

    # Apply filters if provided
    if filter_grade:
        marks_query = marks_query.filter(Grade.name == filter_grade)
    if filter_term:
        marks_query = marks_query.filter(Term.name == filter_term)

    # Apply sorting
    if sort_by == 'grade':
        marks_query = marks_query.order_by(Grade.name)
    elif sort_by == 'term':
        marks_query = marks_query.order_by(Term.name)
    else:  # Default to date
        marks_query = marks_query.order_by(Mark.created_at.desc())

    # Execute the query
    marks = marks_query.all()

    # Process the results
    seen_combinations = set()
    for mark in marks:
        combination = (mark.student.stream.grade.name, mark.student.stream.name, mark.term.name, mark.assessment_type.name)
        if combination not in seen_combinations:
            seen_combinations.add(combination)
            # Get the count of marks for this combination
            mark_count = Mark.query.join(Student).join(Stream).join(Grade).join(Term).join(AssessmentType).filter(
                Grade.name == mark.student.stream.grade.name,
                Stream.name == mark.student.stream.name,
                Term.name == mark.term.name,
                AssessmentType.name == mark.assessment_type.name
            ).count()

            # Calculate class average for this grade/stream/term/assessment combination
            class_marks = Mark.query.filter_by(
                term_id=mark.term.id,
                assessment_type_id=mark.assessment_type.id
            ).join(Student).join(Stream).join(Grade).filter(
                Grade.name == mark.student.stream.grade.name,
                Stream.name == mark.student.stream.name
            ).all()

            # Calculate the class average percentage
            if class_marks:
                total_percentage = sum(m.percentage for m in class_marks if m.percentage is not None)
                class_average = round(total_percentage / len(class_marks), 1) if class_marks else 0
            else:
                class_average = 0

            recent_reports.append({
                'grade': mark.student.stream.grade.name,
                'stream': f"Stream {mark.student.stream.name}",
                'term': mark.term.name,
                'assessment_type': mark.assessment_type.name,
                'date': mark.created_at.strftime('%Y-%m-%d') if mark.created_at else 'N/A',
                'mark_count': mark_count,
                'class_average': class_average,  # Add the real class average
                'id': len(recent_reports) + 1  # Add an ID for easier reference
            })
            if len(recent_reports) >= 10:  # Increased limit to 10 recent reports
                break

    # Handle form submission
    if request.method == "POST":
        # Handle upload marks request
        if "upload_marks" in request.form:
            education_level = request.form.get("education_level")
            grade_level = request.form.get("grade")
            stream_name = request.form.get("stream")
            term = request.form.get("term")
            assessment_type = request.form.get("assessment_type")
            total_marks = request.form.get("total_marks", type=int, default=0)

            if not all([education_level, grade_level, stream_name, term, assessment_type, total_marks > 0]):
                error_message = "Please fill in all fields before loading students and subjects"
            else:
                # Extract stream letter from "Stream X" format
                stream_letter = stream_name.replace("Stream ", "") if stream_name.startswith("Stream ") else stream_name

                # Get the stream object
                stream_obj = Stream.query.join(Grade).filter(Grade.name == grade_level, Stream.name == stream_letter).first()

                if stream_obj:
                    # Get students for this stream
                    students = Student.query.filter_by(stream_id=stream_obj.id).order_by(Student.name).all()

                    # Get subjects for this education level
                    all_subjects = Subject.query.filter_by(education_level=education_level).all()

                    # Define core subjects that should appear first
                    core_subjects = ["Mathematics", "English", "Kiswahili", "Science", "Integrated Science",
                                    "Science and Technology", "Integrated Science and Health Education"]

                    # Sort subjects with core subjects first
                    sorted_subjects = []

                    # First add core subjects in the specified order
                    for core_subject in core_subjects:
                        for subject in all_subjects:
                            if subject.name == core_subject or subject.name.upper() == core_subject.upper():
                                sorted_subjects.append(subject)

                    # Then add remaining subjects alphabetically
                    remaining_subjects = [s for s in all_subjects if s not in sorted_subjects]
                    remaining_subjects.sort(key=lambda x: x.name)
                    sorted_subjects.extend(remaining_subjects)

                    # Use the full Subject objects instead of just names
                    subjects = sorted_subjects

                    if students and subjects:
                        show_students = True
                        show_download_button = False
                        show_individual_report_button = False
                    else:
                        if not students:
                            error_message = f"No students found for grade {grade_level} stream {stream_letter}"
                        else:
                            error_message = f"No subjects found for {education_level}"
                else:
                    error_message = f"Stream {stream_letter} not found for grade {grade_level}"

        # Handle submit marks request
        elif "submit_marks" in request.form:
            education_level = request.form.get("education_level")
            grade_level = request.form.get("grade")
            stream_name = request.form.get("stream")
            term = request.form.get("term")
            assessment_type = request.form.get("assessment_type")
            total_marks = request.form.get("total_marks", type=int, default=0)

            if not all([education_level, grade_level, stream_name, term, assessment_type, total_marks > 0]):
                error_message = "Missing required information"
            else:
                # Extract stream letter from "Stream X" format
                stream_letter = stream_name.replace("Stream ", "") if stream_name.startswith("Stream ") else stream_name

                # Get the stream, term, and assessment type objects
                stream_obj = Stream.query.join(Grade).filter(Grade.name == grade_level, Stream.name == stream_letter).first()
                term_obj = Term.query.filter_by(name=term).first()
                assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

                if not (stream_obj and term_obj and assessment_type_obj):
                    error_message = "Invalid stream, term, or assessment type"
                else:
                    # Get students for this stream
                    students = Student.query.filter_by(stream_id=stream_obj.id).all()

                    # Get subjects for this education level
                    all_subjects = Subject.query.filter_by(education_level=education_level).all()

                    # Define core subjects that should appear first
                    core_subjects = ["Mathematics", "English", "Kiswahili", "Science", "Integrated Science",
                                    "Science and Technology", "Integrated Science and Health Education"]

                    # Sort subjects with core subjects first
                    sorted_subjects = []

                    # First add core subjects in the specified order
                    for core_subject in core_subjects:
                        for subject in all_subjects:
                            if subject.name == core_subject or subject.name.upper() == core_subject.upper():
                                sorted_subjects.append(subject)

                    # Then add remaining subjects alphabetically
                    remaining_subjects = [s for s in all_subjects if s not in sorted_subjects]
                    remaining_subjects.sort(key=lambda x: x.name)
                    sorted_subjects.extend(remaining_subjects)

                    # Get the selected subjects from the form
                    selected_subjects = request.form.getlist('selected_subjects')
                    if not selected_subjects:
                        error_message = "Please select at least one subject"
                    else:
                        # Filter subjects to only include selected ones
                        selected_subject_ids = [int(subject_id) for subject_id in selected_subjects]
                        subjects = [subject for subject in sorted_subjects if subject.id in selected_subject_ids]

                        # Store selected subjects in session for report generation
                        session['selected_subjects'] = selected_subject_ids

                        if not (students and subjects):
                            error_message = "No students or subjects found"
                        else:
                            # Process marks for each student and subject
                            marks_added = 0
                            marks_updated = 0

                            for student in students:
                                for subject in subjects:
                                    # Check if this is a composite subject
                                    if subject.is_composite:
                                        # Get the components for this subject
                                        components = subject.get_components()

                                        # First, create or update the overall mark for the subject
                                        mark_key = f"mark_{student.name.replace(' ', '_')}_{subject.id}"
                                        mark_value = request.form.get(mark_key, '')

                                        # Get the percentage value (calculated by JavaScript)
                                        percentage_key = f"hidden_percentage_{student.name.replace(' ', '_')}_{subject.id}"
                                        percentage_value = request.form.get(percentage_key, type=float, default=0.0)

                                        # Also try the overall mark field
                                        overall_mark_key = f"overall_mark_{student.name.replace(' ', '_')}_{subject.id}"
                                        overall_mark_value = request.form.get(overall_mark_key, type=float, default=0.0)

                                        # Use the overall mark value if percentage is 0
                                        if percentage_value == 0.0 and overall_mark_value > 0:
                                            percentage_value = overall_mark_value

                                        # Check if overall mark already exists
                                        existing_mark = Mark.query.filter_by(
                                            student_id=student.id,
                                            subject_id=subject.id,
                                            term_id=term_obj.id,
                                            assessment_type_id=assessment_type_obj.id
                                        ).first()

                                        if existing_mark:
                                            # Update existing mark
                                            existing_mark.percentage = percentage_value
                                            # For backward compatibility, set raw_mark based on percentage
                                            existing_mark.raw_mark = (percentage_value / 100) * total_marks
                                            existing_mark.mark = existing_mark.raw_mark  # Update old field name too
                                            marks_updated += 1
                                        else:
                                            # Create new mark
                                            new_mark = Mark(
                                                student_id=student.id,
                                                subject_id=subject.id,
                                                term_id=term_obj.id,
                                                assessment_type_id=assessment_type_obj.id,
                                                percentage=percentage_value,
                                                raw_mark=(percentage_value / 100) * total_marks,
                                                max_raw_mark=total_marks
                                            )
                                            db.session.add(new_mark)
                                            db.session.flush()  # Flush to get the ID of the new mark
                                            marks_added += 1

                                        # Now process each component mark
                                        component_marks_added = 0
                                        component_marks_updated = 0

                                        # Get the mark ID (either existing or newly created)
                                        mark_id = existing_mark.id if existing_mark else new_mark.id

                                        # Import ComponentMark model
                                        from ..models.academic import ComponentMark

                                        for component in components:
                                            # Get the component mark value
                                            component_mark_key = f"component_mark_{student.name.replace(' ', '_')}_{subject.id}_{component.id}"
                                            component_mark_value = request.form.get(component_mark_key, '')

                                            if component_mark_value and component_mark_value.isdigit():
                                                try:
                                                    component_raw_mark = int(component_mark_value)
                                                    component_max_mark = component.max_raw_mark or total_marks

                                                    # Sanitize the raw mark
                                                    component_raw_mark, component_max_mark = MarkConversionService.sanitize_raw_mark(
                                                        component_raw_mark, component_max_mark)

                                                    # Calculate percentage
                                                    component_percentage = MarkConversionService.calculate_percentage(
                                                        component_raw_mark, component_max_mark)

                                                    # Check if component mark already exists
                                                    existing_component_mark = ComponentMark.query.filter_by(
                                                        mark_id=mark_id,
                                                        component_id=component.id
                                                    ).first()

                                                    if existing_component_mark:
                                                        # Update existing component mark
                                                        existing_component_mark.raw_mark = component_raw_mark
                                                        existing_component_mark.max_raw_mark = component_max_mark
                                                        existing_component_mark.percentage = component_percentage
                                                        component_marks_updated += 1
                                                    else:
                                                        # Create new component mark
                                                        new_component_mark = ComponentMark(
                                                            mark_id=mark_id,
                                                            component_id=component.id,
                                                            raw_mark=component_raw_mark,
                                                            max_raw_mark=component_max_mark,
                                                            percentage=component_percentage
                                                        )
                                                        db.session.add(new_component_mark)
                                                        component_marks_added += 1
                                                except Exception as e:
                                                    print(f"Error processing component mark: {e}")
                                                    continue

                                        # Add component marks to the total
                                        marks_added += component_marks_added
                                        marks_updated += component_marks_updated
                                    else:
                                        # Regular subject processing
                                        # Get the mark value and subject-specific total marks from the form
                                        mark_key = f"mark_{student.name.replace(' ', '_')}_{subject.id}"
                                        mark_value = request.form.get(mark_key, '')

                                        # Get the subject-specific total marks
                                        subject_index = subjects.index(subject)
                                        total_marks_key = f"total_marks_{subject_index}"
                                        subject_total_marks = request.form.get(total_marks_key, type=int, default=total_marks)

                                        # Get the percentage value (calculated by JavaScript)
                                        percentage_key = f"percentage_{student.name.replace(' ', '_')}_{subject.id}"
                                        percentage_value = request.form.get(percentage_key, type=float, default=0.0)

                                        if mark_value and mark_value.isdigit():
                                            try:
                                                raw_mark = int(mark_value)

                                                # Sanitize the raw mark and total marks to ensure they're within acceptable ranges
                                                raw_mark, subject_total_marks = MarkConversionService.sanitize_raw_mark(raw_mark, subject_total_marks)

                                                # Calculate percentage using our service
                                                percentage_value = MarkConversionService.calculate_percentage(raw_mark, subject_total_marks)

                                                # Check if mark already exists
                                                existing_mark = Mark.query.filter_by(
                                                    student_id=student.id,
                                                    subject_id=subject.id,
                                                    term_id=term_obj.id,
                                                    assessment_type_id=assessment_type_obj.id
                                                ).first()

                                                if existing_mark:
                                                    # Update existing mark with both old and new field names
                                                    existing_mark.mark = raw_mark  # Old field name
                                                    existing_mark.total_marks = subject_total_marks  # Old field name
                                                    existing_mark.raw_mark = raw_mark  # New field name
                                                    existing_mark.max_raw_mark = subject_total_marks  # New field name
                                                    existing_mark.percentage = percentage_value
                                                    marks_updated += 1
                                                else:
                                                    # Create new mark with both old and new field names
                                                    new_mark = Mark(
                                                        student_id=student.id,
                                                        subject_id=subject.id,
                                                        term_id=term_obj.id,
                                                        assessment_type_id=assessment_type_obj.id,
                                                        mark=raw_mark,  # Old field name
                                                        total_marks=subject_total_marks,  # Old field name
                                                        raw_mark=raw_mark,  # New field name
                                                        max_raw_mark=subject_total_marks,  # New field name
                                                        percentage=percentage_value
                                                    )
                                                    db.session.add(new_mark)
                                                    marks_added += 1
                                            except Exception as e:
                                                print(f"Error processing mark: {e}")
                                                continue

                        # Commit changes to the database
                        db.session.commit()

                        # Invalidate any existing cache for this grade/stream/term/assessment combination
                        invalidate_cache(grade_level, stream_name, term, assessment_type)

                        # Update collaborative marks status
                        current_teacher_id = session.get('teacher_id')
                        if current_teacher_id and subjects:
                            # Update status for each subject that was uploaded
                            for subject in subjects:
                                CollaborativeMarksService.update_marks_status_after_upload(
                                    stream_obj.grade_id, stream_obj.id, subject.id, term_obj.id, assessment_type_obj.id, current_teacher_id
                                )

                        # Show success message
                        flash(f"Successfully saved {marks_added} new marks and updated {marks_updated} existing marks.", "success")

                        # Enable download and individual report buttons
                        show_download_button = True
                        show_individual_report_button = True

                        # Keep the form values for reference
                        education_level = education_level
                        grade = grade_level
                        stream = stream_name
                        term = term
                        assessment_type = assessment_type
                        total_marks = total_marks

                        # Redirect to the dashboard with success parameters
                        return redirect(url_for('classteacher.dashboard',
                                              grade=grade_level,
                                              stream=stream_name,
                                              term=term,
                                              assessment_type=assessment_type,
                                              show_download=1,
                                              show_individual=1))

        # Handle bulk upload marks request
        elif "bulk_upload_marks" in request.form:
            if 'marks_file' not in request.files:
                flash("No file selected.", "error")
                return redirect(url_for('classteacher.dashboard'))

            file = request.files['marks_file']

            if file.filename == '':
                flash("No file selected.", "error")
                return redirect(url_for('classteacher.dashboard'))

            # Get form data
            education_level = request.form.get("education_level")
            grade_level = request.form.get("grade")
            stream_name = request.form.get("stream")
            term = request.form.get("term")
            assessment_type = request.form.get("assessment_type")
            total_marks = request.form.get("total_marks", type=int, default=100)

            if not all([education_level, grade_level, stream_name, term, assessment_type]):
                flash("Please fill in all required fields.", "error")
                return redirect(url_for('classteacher.dashboard'))

            # Extract stream letter from "Stream X" format
            stream_letter = stream_name.replace("Stream ", "") if stream_name.startswith("Stream ") else stream_name

            # Get the stream, term, and assessment type objects
            stream_obj = Stream.query.join(Grade).filter(Grade.name == grade_level, Stream.name == stream_letter).first()
            term_obj = Term.query.filter_by(name=term).first()
            assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

            if not (stream_obj and term_obj and assessment_type_obj):
                flash("Invalid stream, term, or assessment type.", "error")
                return redirect(url_for('classteacher.dashboard'))

            try:
                # Check file extension
                file_ext = os.path.splitext(file.filename)[1].lower()

                if file_ext == '.csv':
                    df = pd.read_csv(file)
                elif file_ext in ['.xlsx', '.xls']:
                    df = pd.read_excel(file)
                else:
                    flash("Unsupported file format. Please upload a CSV or Excel file.", "error")
                    return redirect(url_for('classteacher.dashboard'))

                # Process the file
                marks_added = 0
                marks_updated = 0
                errors = 0

                # Get all students in this stream
                students = {student.name: student for student in Student.query.filter_by(stream_id=stream_obj.id).all()}

                # Get all subjects for this education level
                all_subjects = Subject.query.filter_by(education_level=education_level).all()

                # Define core subjects that should appear first
                core_subjects = ["Mathematics", "English", "Kiswahili", "Science", "Integrated Science",
                                "Science and Technology", "Integrated Science and Health Education"]

                # Sort subjects with core subjects first
                sorted_subjects = []

                # First add core subjects in the specified order
                for core_subject in core_subjects:
                    for subject in all_subjects:
                        if subject.name == core_subject or subject.name.upper() == core_subject.upper():
                            sorted_subjects.append(subject)

                # Then add remaining subjects alphabetically
                remaining_subjects = [s for s in all_subjects if s not in sorted_subjects]
                remaining_subjects.sort(key=lambda x: x.name)
                sorted_subjects.extend(remaining_subjects)

                # Create a dictionary of subject name to subject object
                subjects = {subject.name: subject for subject in sorted_subjects}

                # Check if we have the required columns
                if 'Student Name' not in df.columns and 'Admission Number' not in df.columns:
                    flash("File must contain either 'Student Name' or 'Admission Number' column.", "error")
                    return redirect(url_for('classteacher.dashboard'))

                # Process each row (student)
                for _, row in df.iterrows():
                    # Identify the student
                    student = None

                    if 'Student Name' in df.columns and row['Student Name'] in students:
                        student = students[row['Student Name']]
                    elif 'Admission Number' in df.columns:
                        # Find student by admission number
                        student_obj = Student.query.filter_by(
                            admission_number=str(row['Admission Number']),
                            stream_id=stream_obj.id
                        ).first()
                        if student_obj:
                            student = student_obj

                    if not student:
                        errors += 1
                        continue

                    # Process each subject column
                    for subject_name in subjects.keys():
                        if subject_name in df.columns:
                            mark_value = row[subject_name]

                            # Skip empty or non-numeric values
                            if pd.isna(mark_value) or not (isinstance(mark_value, (int, float)) or (isinstance(mark_value, str) and mark_value.isdigit())):
                                continue

                            try:
                                # Convert to integer
                                raw_mark = int(float(mark_value))

                                # Sanitize the raw mark and total marks to ensure they're within acceptable ranges
                                raw_mark, sanitized_total_marks = MarkConversionService.sanitize_raw_mark(raw_mark, total_marks)

                                # Calculate percentage using our service
                                percentage = MarkConversionService.calculate_percentage(raw_mark, sanitized_total_marks)

                                # Check if mark already exists
                                existing_mark = Mark.query.filter_by(
                                    student_id=student.id,
                                    subject_id=subjects[subject_name].id,
                                    term_id=term_obj.id,
                                    assessment_type_id=assessment_type_obj.id
                                ).first()

                                if existing_mark:
                                    # Update existing mark with both old and new field names
                                    existing_mark.mark = raw_mark  # Old field name
                                    existing_mark.total_marks = sanitized_total_marks  # Old field name
                                    existing_mark.raw_mark = raw_mark  # New field name
                                    existing_mark.max_raw_mark = sanitized_total_marks  # New field name
                                    existing_mark.percentage = percentage
                                    marks_updated += 1
                                else:
                                    # Create new mark with both old and new field names
                                    new_mark = Mark(
                                        student_id=student.id,
                                        subject_id=subjects[subject_name].id,
                                        term_id=term_obj.id,
                                        assessment_type_id=assessment_type_obj.id,
                                        mark=raw_mark,  # Old field name
                                        total_marks=sanitized_total_marks,  # Old field name
                                        raw_mark=raw_mark,  # New field name
                                        max_raw_mark=sanitized_total_marks,  # New field name
                                        percentage=percentage
                                    )
                                    db.session.add(new_mark)
                                    marks_added += 1
                            except Exception as e:
                                print(f"Error processing bulk mark: {e}")
                                errors += 1

                # Commit changes to the database
                db.session.commit()

                # Invalidate any existing cache for this grade/stream/term/assessment combination
                invalidate_cache(grade_level, stream_name, term, assessment_type)

                # Show success message
                if marks_added > 0 or marks_updated > 0:
                    flash(f"Successfully processed {marks_added + marks_updated} marks ({marks_added} new, {marks_updated} updated). {errors} errors encountered.", "success")

                    # Redirect to the dashboard with success parameters
                    return redirect(url_for('classteacher.dashboard',
                                          grade=grade_level,
                                          stream=stream_name,
                                          term=term,
                                          assessment_type=assessment_type,
                                          show_download=1,
                                          show_individual=1))
                else:
                    flash(f"No marks were processed. {errors} errors encountered.", "error")
                    return redirect(url_for('classteacher.dashboard'))

            except Exception as e:
                flash(f"Error processing file: {str(e)}", "error")
                return redirect(url_for('classteacher.dashboard'))

        # Handle generate grade marksheet request
        elif "generate_stream_marksheet" in request.form or "download_stream_marksheet" in request.form:
            grade = request.form.get("stream_grade")
            term = request.form.get("stream_term")
            assessment_type = request.form.get("stream_assessment_type")

            if not all([grade, term, assessment_type]):
                flash("Please select grade, term, and assessment type.", "error")
                return redirect(url_for('classteacher.dashboard'))

            action = "preview" if "generate_stream_marksheet" in request.form else "download"

            # Redirect to the grade marksheet route
            return redirect(url_for('classteacher.generate_grade_marksheet',
                                   grade=grade,
                                   term=term,
                                   assessment_type=assessment_type,
                                   action=action))

    # Check if a marksheet was just deleted
    marksheet_deleted = session.pop('marksheet_deleted', False)
    deleted_marksheet_info = session.pop('deleted_marksheet_info', None)

    # If a marksheet was deleted, add a special confirmation message
    if marksheet_deleted and deleted_marksheet_info:
        grade_info = deleted_marksheet_info.get('grade', '')
        stream_info = deleted_marksheet_info.get('stream', '')
        term_info = deleted_marksheet_info.get('term', '')
        assessment_info = deleted_marksheet_info.get('assessment_type', '')
        count_info = deleted_marksheet_info.get('count', 0)

        # Add a special confirmation message
        confirmation_message = f"""
        <div class="deletion-confirmation">
            <h3>Marksheet Deleted Successfully</h3>
            <p>The marksheet for <strong>{grade_info} {stream_info}</strong> in <strong>{term_info} {assessment_info}</strong> has been permanently deleted.</p>
            <p>A total of <strong>{count_info} marks</strong> were removed from the database.</p>
            <p>If you need to recreate this marksheet, you will need to enter all the marks again.</p>
        </div>
        """
    else:
        confirmation_message = ""

    # Determine which tab should be active
    active_tab = "recent-reports"  # Default tab

    # If students are being loaded or marks are being submitted, set the active tab to upload-marks
    if show_students or "upload_marks" in request.form or "submit_marks" in request.form or "bulk_upload_marks" in request.form:
        active_tab = "upload-marks"
        # Store in session that we're showing students
        session['show_students_tab'] = True
    # If generating marksheets, set the active tab to generate-marksheet
    elif "generate_stream_marksheet" in request.form or "download_stream_marksheet" in request.form:
        active_tab = "generate-marksheet"
    # Check if we have a tab preference in the session
    elif session.get('show_students_tab'):
        active_tab = "upload-marks"
        # Clear the session preference
        session.pop('show_students_tab', None)

    # Get management statistics for the dashboard
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_subjects = Subject.query.count()
    total_grades = Grade.query.count()

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
        subject_assignments=subject_assignments,
        confirmation_message=confirmation_message,
        total_students=total_students,
        total_teachers=total_teachers,
        total_subjects=total_subjects,
        total_grades=total_grades,
        active_tab=active_tab,  # Pass the active tab to the template
        # Role-based assignment data
        assignment_summary=assignment_summary,
        total_subjects_taught=assignment_summary.get('total_subjects_taught', 0),
        can_manage_classes=assignment_summary.get('can_manage_classes', False),
        grades_involved=assignment_summary.get('grades_involved', []),
        streams_involved=assignment_summary.get('streams_involved', []),
        subjects_involved=assignment_summary.get('subjects_involved', []),
        has_assignments=has_assignments  # Pass assignment status to template
    )

@classteacher_bp.route('/all_reports', methods=['GET'])
@classteacher_required
def all_reports():
    """Route for viewing all reports with advanced filtering and efficient database-level pagination."""
    # Get filter and sort parameters
    sort_by = request.args.get('sort', 'date')
    filter_grade = request.args.get('filter_grade', '')
    filter_term = request.args.get('filter_term', '')
    filter_assessment = request.args.get('filter_assessment', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of reports per page

    # Import SQLAlchemy functions for advanced queries
    from sqlalchemy import func, distinct
    from sqlalchemy.sql import text

    # Create a subquery to get unique combinations with the most recent date
    # This uses a Common Table Expression (CTE) approach for better performance
    subquery = db.session.query(
        Grade.name.label('grade_level'),
        Stream.name.label('stream_name'),
        Term.name.label('term_name'),
        AssessmentType.name.label('assessment_name'),
        func.max(Mark.created_at).label('latest_date')
    ).join(
        Student, Mark.student_id == Student.id
    ).join(
        Stream, Student.stream_id == Stream.id
    ).join(
        Grade, Stream.grade_id == Grade.id
    ).join(
        Term, Mark.term_id == Term.id
    ).join(
        AssessmentType, Mark.assessment_type_id == AssessmentType.id
    )

    # Apply filters
    if filter_grade:
        subquery = subquery.filter(Grade.name == filter_grade)
    if filter_term:
        subquery = subquery.filter(Term.name == filter_term)
    if filter_assessment:
        subquery = subquery.filter(AssessmentType.name == filter_assessment)

    # Group by the combination fields to get unique combinations
    subquery = subquery.group_by(
        Grade.name,
        Stream.name,
        Term.name,
        AssessmentType.name
    )

    # Apply sorting to the subquery
    if sort_by == 'grade':
        subquery = subquery.order_by(Grade.name)
    elif sort_by == 'term':
        subquery = subquery.order_by(Term.name)
    else:  # Default to date
        subquery = subquery.order_by(func.max(Mark.created_at).desc())

    # Convert to a subquery object
    subquery = subquery.subquery()

    # Main query to get the report data with counts
    main_query = db.session.query(
        subquery.c.grade_level,
        subquery.c.stream_name,
        subquery.c.term_name,
        subquery.c.assessment_name,
        subquery.c.latest_date,
        func.count(Mark.id).label('mark_count')
    ).join(
        Student, Mark.student_id == Student.id
    ).join(
        Stream, Student.stream_id == Stream.id
    ).join(
        Grade, Stream.grade_id == Grade.id
    ).join(
        Term, Mark.term_id == Term.id
    ).join(
        AssessmentType, Mark.assessment_type_id == AssessmentType.id
    ).filter(
        Grade.name == subquery.c.grade_level,
        Stream.name == subquery.c.stream_name,
        Term.name == subquery.c.term_name,
        AssessmentType.name == subquery.c.assessment_name
    ).group_by(
        subquery.c.grade_level,
        subquery.c.stream_name,
        subquery.c.term_name,
        subquery.c.assessment_name,
        subquery.c.latest_date
    )

    # Apply the same sorting to the main query
    if sort_by == 'grade':
        main_query = main_query.order_by(subquery.c.grade_level)
    elif sort_by == 'term':
        main_query = main_query.order_by(subquery.c.term_name)
    else:  # Default to date
        main_query = main_query.order_by(subquery.c.latest_date.desc())

    # Get the total count for pagination
    total_count = main_query.count()

    # Apply pagination at the database level
    paginated_query = main_query.paginate(page=page, per_page=per_page, error_out=False)

    # Format the results
    reports = []
    for idx, (grade_level, stream_name, term_name, assessment_name, created_at, mark_count) in enumerate(paginated_query.items, start=1):
        reports.append({
            'id': (page - 1) * per_page + idx,
            'grade': grade_level,
            'stream': f"Stream {stream_name}",
            'term': term_name,
            'assessment_type': assessment_name,
            'date': created_at.strftime('%Y-%m-%d') if created_at else 'N/A',
            'mark_count': mark_count
        })

    # Get all grades, terms, and assessment types for the filter dropdowns
    grades = [grade.name for grade in Grade.query.all()]
    terms = [term.name for term in Term.query.all()]
    assessment_types = [assessment_type.name for assessment_type in AssessmentType.query.all()]

    return render_template(
        'all_reports.html',
        reports=reports,
        pagination=paginated_query,
        total_reports=total_count,
        page=page,
        per_page=per_page,
        total_pages=paginated_query.pages,
        has_next=paginated_query.has_next,
        has_prev=paginated_query.has_prev,
        next_page=paginated_query.next_num,
        prev_page=paginated_query.prev_num,
        grades=grades,
        terms=terms,
        assessment_types=assessment_types,
        sort_by=sort_by,
        filter_grade=filter_grade,
        filter_term=filter_term,
        filter_assessment=filter_assessment
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
        grades = Grade.query.filter(Grade.name.in_(allowed_grades)).all()
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
    grades = [{"id": grade.id, "name": grade.name} for grade in Grade.query.all()]

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

                    # Normalize column names to handle variations
                    df.columns = df.columns.str.strip().str.lower()

                    # Map common column name variations
                    column_mapping = {
                        'student_name': 'name',
                        'student name': 'name',
                        'full_name': 'name',
                        'full name': 'name',
                        'addmission_number': 'admission_number',
                        'addmission number': 'admission_number',
                        'admission_no': 'admission_number',
                        'admission no': 'admission_number',
                        'adm_number': 'admission_number',
                        'adm number': 'admission_number',
                        'adm_no': 'admission_number',
                        'adm no': 'admission_number',
                        'reg_number': 'admission_number',
                        'reg number': 'admission_number',
                        'registration_number': 'admission_number',
                        'registration number': 'admission_number'
                    }

                    # Apply column mapping
                    df.rename(columns=column_mapping, inplace=True)

                    # Check required columns after mapping
                    required_columns = ['name']
                    missing_columns = []
                    for col in required_columns:
                        if col not in df.columns:
                            missing_columns.append(col)

                    if missing_columns:
                        available_columns = list(df.columns)
                        flash(f"Missing required column(s): {', '.join(missing_columns)}. Available columns: {', '.join(available_columns)}. Please ensure your file has a 'name' column.", "error")
                        return redirect(request.url)

                    # Process each row
                    success_count = 0
                    error_count = 0
                    error_details = []

                    for index, row in df.iterrows():
                        try:
                            name = str(row['name']).strip()

                            # Handle admission number (might be missing or have different column name)
                            admission_number = None
                            if 'admission_number' in row and pd.notna(row['admission_number']):
                                admission_number = str(row['admission_number']).strip()

                            # If no admission number, generate one
                            if not admission_number or admission_number == 'nan':
                                # Generate admission number based on name and index
                                name_part = ''.join(c for c in name.replace(' ', '')[:3] if c.isalnum()).upper()
                                admission_number = f"ADM{name_part}{index+1:03d}"

                            # Optional fields
                            gender = str(row.get('gender', '')).strip().lower() if pd.notna(row.get('gender', '')) else 'unknown'

                            # Handle grade and stream from Excel file
                            excel_grade = None
                            excel_stream = None

                            if 'grade' in row and pd.notna(row['grade']):
                                excel_grade = str(row['grade']).strip()

                            if 'stream' in row and pd.notna(row['stream']):
                                excel_stream = str(row['stream']).strip().upper()

                            # Skip empty rows
                            if not name:
                                error_details.append(f"Row {index+1}: Missing student name")
                                error_count += 1
                                continue

                            # Check if admission number already exists
                            existing_student = Student.query.filter_by(admission_number=admission_number).first()
                            if existing_student:
                                error_details.append(f"Row {index+1}: Student with admission number {admission_number} already exists")
                                error_count += 1
                                continue

                            # Determine stream_id
                            final_stream_id = None

                            # Priority 1: Use grade and stream from Excel file
                            if excel_grade and excel_stream:
                                # Find the stream based on grade and stream from Excel
                                grade_obj = Grade.query.filter_by(name=excel_grade).first()
                                if not grade_obj:
                                    # Try variations like "Grade 1", "1", etc.
                                    grade_variations = [
                                        f"Grade {excel_grade}",
                                        excel_grade.replace("Grade ", ""),
                                        excel_grade
                                    ]
                                    for variation in grade_variations:
                                        grade_obj = Grade.query.filter_by(name=variation).first()
                                        if grade_obj:
                                            break

                                if grade_obj:
                                    stream_obj = Stream.query.filter_by(grade_id=grade_obj.id, name=excel_stream).first()
                                    if stream_obj:
                                        final_stream_id = stream_obj.id
                                    else:
                                        error_details.append(f"Row {index+1}: Stream '{excel_stream}' not found for grade '{excel_grade}'")
                                else:
                                    error_details.append(f"Row {index+1}: Grade '{excel_grade}' not found")

                            # Priority 2: Use teacher's assigned stream
                            if not final_stream_id and stream_id:
                                final_stream_id = stream_id

                            # Priority 3: Use selected stream from form
                            if not final_stream_id:
                                selected_stream_id = request.form.get('stream')
                                if selected_stream_id:
                                    final_stream_id = selected_stream_id

                            # Add new student
                            student = Student(
                                name=name,
                                admission_number=admission_number,
                                stream_id=final_stream_id if final_stream_id else None,
                                gender=gender
                            )
                            db.session.add(student)
                            success_count += 1

                        except Exception as e:
                            error_details.append(f"Row {index+1}: Error processing student - {str(e)}")
                            error_count += 1
                            continue

                    db.session.commit()

                    # Provide detailed feedback
                    if success_count > 0:
                        success_msg = f"Successfully added {success_count} students."
                        if error_count > 0:
                            success_msg += f" {error_count} errors encountered."
                        flash(success_msg, "success")

                        # Show first few error details if any
                        if error_details:
                            error_summary = "; ".join(error_details[:3])  # Show first 3 errors
                            if len(error_details) > 3:
                                error_summary += f" ... and {len(error_details) - 3} more errors"
                            flash(f"Error details: {error_summary}", "warning")
                    else:
                        error_msg = f"No students added. {error_count} errors encountered."
                        if error_details:
                            error_summary = "; ".join(error_details[:5])  # Show first 5 errors
                            error_msg += f" Details: {error_summary}"
                        flash(error_msg, "error")

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
        grade=grade.name if grade else "",
        stream=stream.name if stream else "",
        grades=grades,
        educational_level_mapping=educational_level_mapping,
        educational_levels=list(educational_level_mapping.keys())
    )

@classteacher_bp.route('/preview_class_report/<grade>/<stream>/<term>/<assessment_type>', methods=['GET', 'POST'])
@teacher_or_classteacher_required
def preview_class_report(grade, stream, term, assessment_type):
    """Route for previewing class reports."""
    # Check if this is a form submission for subject selection
    if request.method == 'POST':
        # Get the selected subjects from the form
        selected_subjects = []
        for key, value in request.form.items():
            if key.startswith('include_subject_') and value:
                try:
                    subject_id = int(value)
                    selected_subjects.append(subject_id)
                except (ValueError, TypeError):
                    pass

        # Store the selected subjects in the session
        session['selected_subjects'] = selected_subjects

    # Get the selected subjects from the session if available
    selected_subjects = session.get('selected_subjects', [])

    # Check if this is a subject teacher (role = 'teacher') and filter subjects accordingly
    current_role = get_role(session)
    if current_role == 'teacher':
        # For subject teachers, only show subjects they are assigned to teach
        teacher_id = session.get('teacher_id')
        if teacher_id:
            # Get the grade and stream objects
            stream_obj_temp = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream[-1]).first()

            if stream_obj_temp:
                grade_obj_temp = stream_obj_temp.grade

                # Get subjects assigned to this teacher for this grade/stream
                teacher_assignments = TeacherSubjectAssignment.query.filter_by(
                    teacher_id=teacher_id,
                    grade_id=grade_obj_temp.id
                ).filter(
                    (TeacherSubjectAssignment.stream_id == stream_obj_temp.id) |
                    (TeacherSubjectAssignment.stream_id == None)  # Assignments for all streams
                ).all()

                # Get subject IDs from assignments
                teacher_subject_ids = [assignment.subject_id for assignment in teacher_assignments]

                # Override selected_subjects to only include teacher's assigned subjects
                selected_subjects = teacher_subject_ids

                # Store in session for consistency
                session['selected_subjects'] = selected_subjects

    stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Get class report data with selected subjects
    report_data = get_class_report_data(grade, stream, term, assessment_type, selected_subject_ids=selected_subjects)

    if not report_data or report_data.get("error"):
        error_msg = report_data.get("error") if report_data and report_data.get("error") else f"No marks found for {grade} Stream {stream[-1]} in {term} {assessment_type}"
        flash(error_msg, "error")
        return redirect(url_for('classteacher.dashboard'))

    # Get education level from report_data or determine based on grade
    if report_data.get("education_level"):
        education_level_code = report_data.get("education_level")
        if education_level_code == "lower_primary":
            education_level = "lower primary"
        elif education_level_code == "upper_primary":
            education_level = "upper primary"
        elif education_level_code == "junior_secondary":
            education_level = "junior secondary"
        else:
            education_level = ""
    else:
        # Fallback to determining education level based on grade
        education_level = ""
        grade_num = int(grade.split()[1]) if len(grade.split()) > 1 else int(grade)
        if 1 <= grade_num <= 3:
            education_level = "lower primary"
        elif 4 <= grade_num <= 6:
            education_level = "upper primary"
        elif 7 <= grade_num <= 9:
            education_level = "junior secondary"

    # Get current date for the report
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Get the class data from the report
    class_data = report_data.get("class_data", [])

    # Get subjects for this grade based on education level
    grade_obj = Grade.query.filter_by(name=grade).first()

    # Get all subjects that have marks for this grade/stream/term/assessment
    stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if grade_obj and stream_obj and term_obj and assessment_type_obj:
        # Get students in this stream
        students = Student.query.filter_by(stream_id=stream_obj.id).all()
        student_ids = [student.id for student in students]

        # First, get subjects for this education level
        if education_level == "lower primary":
            education_level_code = "lower_primary"
        elif education_level == "upper primary":
            education_level_code = "upper_primary"
        elif education_level == "junior secondary":
            education_level_code = "junior_secondary"
        else:
            education_level_code = ""

        # Get subjects for this education level
        if education_level_code:
            all_education_subjects = Subject.query.filter_by(education_level=education_level_code).all()
        else:
            all_education_subjects = Subject.query.all()

        # Filter subjects based on selected subjects if available
        if selected_subjects:
            # Only include subjects that are both in the education level and selected
            filtered_subjects = [subject for subject in all_education_subjects if subject.id in selected_subjects]
        else:
            # If no subjects selected, use all subjects for this education level
            filtered_subjects = all_education_subjects

        # Get subject IDs for filtering marks
        filtered_subject_ids = [subject.id for subject in filtered_subjects]

        # Get all marks for these students in this term/assessment for the filtered subjects
        all_marks = Mark.query.filter(
            Mark.student_id.in_(student_ids),
            Mark.subject_id.in_(filtered_subject_ids),
            Mark.term_id == term_obj.id,
            Mark.assessment_type_id == assessment_type_obj.id
        ).all()

        # Get subject names
        subject_names = [subject.name for subject in filtered_subjects]

        # Create a dictionary of marks by student_id and subject_id for quick lookup
        marks_dict = {}
        for mark in all_marks:
            if mark.student_id not in marks_dict:
                marks_dict[mark.student_id] = {}

            # Use percentage if available, otherwise use raw mark
            if hasattr(mark, 'percentage') and mark.percentage is not None:
                marks_dict[mark.student_id][mark.subject_id] = mark.percentage
            else:
                # Calculate percentage from raw mark
                raw_mark = mark.raw_mark if hasattr(mark, 'raw_mark') and mark.raw_mark is not None else mark.mark
                max_raw_mark = mark.max_raw_mark if hasattr(mark, 'max_raw_mark') and mark.max_raw_mark is not None else (mark.total_marks if mark.total_marks > 0 else 100)
                percentage = (raw_mark / max_raw_mark) * 100

                # Ensure percentage doesn't exceed 100%
                if percentage > 100:
                    percentage = 100.0

                marks_dict[mark.student_id][mark.subject_id] = percentage

        # Filter class data to only include these subjects
        for student_data in class_data:
            student = Student.query.filter_by(name=student_data["student"]).first()
            if student:
                # Add student ID to the data
                student_data["student_id"] = student.id

                # Get marks for this student from the database
                filtered_marks = {}
                subject_count = 0
                total_marks_value = 0

                for subject in filtered_subjects:
                    if student.id in marks_dict and subject.id in marks_dict[student.id]:
                        mark_value = marks_dict[student.id][subject.id]
                        # Convert raw mark to percentage
                        mark_obj = Mark.query.filter_by(
                            student_id=student.id,
                            subject_id=subject.id,
                            term_id=term_obj.id,
                            assessment_type_id=assessment_type_obj.id
                        ).first()

                        if mark_obj and hasattr(mark_obj, 'percentage') and mark_obj.percentage is not None:
                            # Use the percentage value directly
                            percentage_value = mark_obj.percentage
                        else:
                            # Calculate percentage from raw mark
                            total_marks = mark_obj.total_marks if mark_obj and mark_obj.total_marks > 0 else 100
                            percentage_value = (mark_value / total_marks) * 100

                        # Ensure percentage doesn't exceed 100%
                        if percentage_value > 100:
                            percentage_value = 100.0

                        filtered_marks[subject.name] = percentage_value
                        subject_count += 1
                        total_marks_value += percentage_value
                    else:
                        filtered_marks[subject.name] = 0
            else:
                # Fallback to report data if student not found
                student_data["student_id"] = 0
                filtered_marks = {}
                subject_count = 0
                total_marks_value = 0

                for subject_name in subject_names:
                    mark_value = student_data["marks"].get(subject_name, 0)
                    filtered_marks[subject_name] = mark_value
                    if mark_value > 0:
                        subject_count += 1
                        total_marks_value += mark_value

            student_data["filtered_marks"] = filtered_marks
            student_data["filtered_total"] = total_marks_value

            # Calculate total possible marks based on number of subjects
            total_possible = report_data.get("total_marks", 100)
            total_possible_marks = len(subject_names) * total_possible
            student_data["total_possible_marks"] = total_possible_marks

            # Recalculate average percentage
            if subject_count > 0 and total_possible > 0:
                student_data["filtered_average"] = (total_marks_value / (subject_count * total_possible)) * 100
            else:
                student_data["filtered_average"] = 0
    else:
        # Use subjects from report data if grade not found
        subject_names = report_data.get("subjects", [])

    # Create abbreviated subject names for the report header
    abbreviated_subjects = []
    for subject in subject_names:
        words = subject.split()
        if len(words) > 1:
            abbreviated = ''.join(word[0].upper() for word in words)
        else:
            abbreviated = subject[:3].upper()
        abbreviated_subjects.append(abbreviated)

    # Sort students by filtered_total in descending order
    class_data.sort(key=lambda x: x.get("filtered_total", 0), reverse=True)

    # Add performance category and rank to each student's data
    for i, student_data in enumerate(class_data, 1):
        student_data["index"] = i
        student_data["rank"] = i  # Assign rank based on sorted position

        avg = student_data.get("filtered_average", 0)
        if avg >= 90:
            student_data["performance_category"] = "EE1"
        elif avg >= 75:
            student_data["performance_category"] = "EE2"
        elif avg >= 58:
            student_data["performance_category"] = "ME1"
        elif avg >= 41:
            student_data["performance_category"] = "ME2"
        elif avg >= 31:
            student_data["performance_category"] = "AE1"
        elif avg >= 21:
            student_data["performance_category"] = "AE2"
        elif avg >= 11:
            student_data["performance_category"] = "BE1"
        else:
            student_data["performance_category"] = "BE2"

    # Debug: Print class_data to see what's being passed to the template
    print("\n\nDEBUG - Class Data:")
    for student in class_data:
        print(f"Student: {student['student']}")
        print(f"Filtered Marks: {student['filtered_marks']}")
        print(f"Filtered Total: {student['filtered_total']}")
        print(f"Filtered Average: {student['filtered_average']}")
        print("---")

    # Debug: Print subject names
    print("\nDEBUG - Subject Names:", subject_names)

    # Calculate subject averages here in Python code for debugging
    subject_averages = {}
    for subject in subject_names:
        subject_total = 0
        subject_count = 0
        for student_data in class_data:
            mark = student_data['filtered_marks'].get(subject, 0)
            if mark > 0:
                subject_total += mark
                subject_count += 1

        if subject_count > 0:
            subject_averages[subject] = round(subject_total / subject_count, 2)
        else:
            subject_averages[subject] = 0

    # Debug: Print calculated subject averages
    print("\nDEBUG - Calculated Subject Averages:", subject_averages)

    # Calculate class average
    class_total = 0
    student_count = 0
    for student_data in class_data:
        if student_data['filtered_total'] > 0:
            class_total += student_data['filtered_total']
            student_count += 1

    class_average = round(class_total / student_count, 2) if student_count > 0 else 0
    print("\nDEBUG - Calculated Class Average:", class_average)

    # Get all subjects for the subject selection form
    all_subjects = []
    if education_level_code:
        all_subjects = Subject.query.filter_by(education_level=education_level_code).all()
    else:
        all_subjects = Subject.query.all()

    # Get component data for composite subjects
    subject_components = {}
    component_marks_data = {}
    component_averages = {}

    for subject in filtered_subjects:
        if subject.is_composite:
            components = subject.get_components()
            subject_components[subject.name] = components

            # Initialize component averages for this subject
            component_averages[subject.name] = {}
            for component in components:
                component_averages[subject.name][component.name] = 0

            # Get component marks for each student
            component_totals = {}
            component_counts = {}

            for student_data in class_data:
                student = Student.query.filter_by(name=student_data["student"]).first()
                if student:
                    student_id = student.id
                    if student_id not in component_marks_data:
                        component_marks_data[student_id] = {}

                    component_marks_data[student_id][subject.name] = {}

                    for component in components:
                        # Get component mark from database
                        from ..models.academic import ComponentMark
                        component_mark = ComponentMark.query.filter_by(
                            component_id=component.id
                        ).join(
                            Mark, ComponentMark.mark_id == Mark.id
                        ).filter(
                            Mark.student_id == student_id,
                            Mark.term_id == term_obj.id,
                            Mark.assessment_type_id == assessment_type_obj.id
                        ).first()

                        if component_mark:
                            # Display the raw mark, not the percentage
                            raw_mark = component_mark.raw_mark
                            component_marks_data[student_id][subject.name][component.name] = raw_mark

                            # Add to totals for average calculation
                            if component.name not in component_totals:
                                component_totals[component.name] = 0
                                component_counts[component.name] = 0
                            component_totals[component.name] += raw_mark
                            component_counts[component.name] += 1
                        else:
                            component_marks_data[student_id][subject.name][component.name] = 0

            # Calculate component averages
            for component in components:
                if component.name in component_counts and component_counts[component.name] > 0:
                    component_averages[subject.name][component.name] = round(
                        component_totals[component.name] / component_counts[component.name], 1
                    )

    # Get staff information for the report
    from ..services.staff_assignment_service import StaffAssignmentService
    staff_info = StaffAssignmentService.get_report_staff_info(grade, stream)

    # Get school information for dynamic display
    from ..services.school_config_service import SchoolConfigService
    school_info = SchoolConfigService.get_school_info_dict()

    return render_template(
        'preview_class_report.html',
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        report_data=report_data,
        education_level=education_level,
        current_date=current_date,
        subjects=all_subjects,  # Pass all subjects for the selection form
        subject_names=subject_names,
        abbreviated_subjects=abbreviated_subjects,
        class_data=class_data,
        stats=report_data.get("stats", {}),
        subject_averages=subject_averages,  # Pass pre-calculated subject averages
        class_average=class_average,  # Pass pre-calculated class average
        subject_components=subject_components,  # Pass component data
        component_marks_data=component_marks_data,  # Pass component marks
        component_averages=component_averages,  # Pass component averages
        filtered_subjects=filtered_subjects,  # Pass filtered subject objects
        staff_info=staff_info,  # Pass staff information
        school_info=school_info  # Pass school information
    )

@classteacher_bp.route('/edit_class_marks/<grade>/<stream>/<term>/<assessment_type>')
@classteacher_required
def edit_class_marks(grade, stream, term, assessment_type):
    """Route for editing class marks."""
    stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Get the selected subjects from the form
    selected_subjects = []
    for key, value in request.form.items():
        if key.startswith('include_subject_') and value:
            try:
                subject_id = int(value)
                selected_subjects.append(subject_id)
            except (ValueError, TypeError):
                pass

    # Get class report data
    report_data = get_class_report_data(grade, stream, term, assessment_type, selected_subject_ids=selected_subjects)

    if not report_data or report_data.get("error"):
        error_msg = report_data.get("error") if report_data and report_data.get("error") else f"No marks found for {grade} Stream {stream[-1]} in {term} {assessment_type}"
        flash(error_msg, "error")
        return redirect(url_for('classteacher.dashboard'))

    # Get the class data from the report
    class_data = report_data.get("class_data", [])

    # Get education level from report_data or determine based on grade
    if report_data.get("education_level"):
        education_level_code = report_data.get("education_level")
        if education_level_code == "lower_primary":
            education_level = "lower primary"
        elif education_level_code == "upper_primary":
            education_level = "upper primary"
        elif education_level_code == "junior_secondary":
            education_level = "junior secondary"
        else:
            education_level = ""
    else:
        # Fallback to determining education level based on grade
        education_level = ""
        grade_num = int(grade.split()[1]) if len(grade.split()) > 1 else int(grade)
        if 1 <= grade_num <= 3:
            education_level = "lower primary"
        elif 4 <= grade_num <= 6:
            education_level = "upper primary"
        elif 7 <= grade_num <= 9:
            education_level = "junior secondary"

    # Get subjects for this grade based on education level
    grade_obj = Grade.query.filter_by(name=grade).first()
    if grade_obj:
        # Filter subjects by education level
        if education_level == "lower primary":
            filtered_subjects = Subject.query.filter_by(education_level="lower_primary").all()
        elif education_level == "upper primary":
            filtered_subjects = Subject.query.filter_by(education_level="upper_primary").all()
        elif education_level == "junior secondary":
            filtered_subjects = Subject.query.filter_by(education_level="junior_secondary").all()
        else:
            filtered_subjects = Subject.query.all()

        # Get subject names, IDs, and objects
        subject_names = [subject.name for subject in filtered_subjects]
        subject_ids = [subject.id for subject in filtered_subjects]
        subject_objects = filtered_subjects  # Pass the actual subject objects

        # Debug: Print subject IDs and composite status
        print("\n=== SUBJECTS BEING PASSED TO TEMPLATE ===")
        for subject in filtered_subjects:
            print(f"Subject: {subject.name}, ID: {subject.id}, Is Composite: {subject.is_composite}")
            if subject.is_composite:
                components = subject.get_components()
                print(f"  Components: {[comp.name for comp in components]}")
        print("=========================================")
    else:
        # Use subjects from report data if grade not found
        subject_names = report_data.get("subjects", [])
        subject_ids = []
        for subject_name in subject_names:
            subject = Subject.query.filter_by(name=subject_name).first()
            if subject:
                subject_ids.append(subject.id)
            else:
                subject_ids.append(0)

    # Get subject total marks from the database
    subject_total_marks = {}
    for subject_name, subject_id in zip(subject_names, subject_ids):
        # Check if any marks exist for this subject to get the total_marks
        mark = Mark.query.filter_by(
            subject_id=subject_id,
            term_id=term_obj.id,
            assessment_type_id=assessment_type_obj.id
        ).first()

        if mark:
            subject_total_marks[subject_name] = mark.total_marks
        else:
            # Default to 100 if no marks exist
            subject_total_marks[subject_name] = 100

    # Get student IDs for the form and fetch actual marks from the database
    for student_data in class_data:
        student = Student.query.filter_by(name=student_data["student"]).first()
        if student:
            student_data["student_id"] = student.id

            # Get actual marks from the database for this student
            filtered_marks = {}
            filtered_raw_marks = {}
            for subject_name in subject_names:
                subject = Subject.query.filter_by(name=subject_name).first()
                if subject:
                    # Check if mark exists in database
                    mark = Mark.query.filter_by(
                        student_id=student.id,
                        subject_id=subject.id,
                        term_id=term_obj.id,
                        assessment_type_id=assessment_type_obj.id
                    ).first()

                    if mark:
                        # Store both the standardized mark (out of 100) and the raw mark
                        total_marks = mark.total_marks if mark.total_marks > 0 else 100
                        raw_mark = mark.mark

                        # Calculate standardized mark (out of 100)
                        standardized_mark = (raw_mark / total_marks) * 100

                        filtered_marks[subject_name] = standardized_mark
                        filtered_raw_marks[subject_name] = raw_mark
                    else:
                        # If no mark in database, use the one from report data if available
                        filtered_marks[subject_name] = student_data["marks"].get(subject_name, 0)
                        filtered_raw_marks[subject_name] = student_data["marks"].get(subject_name, 0)
                else:
                    filtered_marks[subject_name] = student_data["marks"].get(subject_name, 0)
                    filtered_raw_marks[subject_name] = student_data["marks"].get(subject_name, 0)
        else:
            student_data["student_id"] = 0
            # Filter marks to only include these subjects
            filtered_marks = {subject: student_data["marks"].get(subject, 0) for subject in subject_names}
            filtered_raw_marks = {subject: student_data["marks"].get(subject, 0) for subject in subject_names}

        student_data["filtered_marks"] = filtered_marks
        student_data["filtered_raw_marks"] = filtered_raw_marks

    # Helper function to get component marks
    def get_component_mark(student_id, component_id):
        """Get the component mark for a student and component."""
        from ..models.academic import ComponentMark

        try:
            # Find the mark in the database
            component_mark = ComponentMark.query.filter_by(
                component_id=component_id
            ).join(
                Mark, ComponentMark.mark_id == Mark.id
            ).filter(
                Mark.student_id == student_id,
                Mark.term_id == term_obj.id,
                Mark.assessment_type_id == assessment_type_obj.id
            ).first()

            # Debug output
            if component_mark:
                print(f"Found component mark: student_id={student_id}, component_id={component_id}, raw_mark={component_mark.raw_mark}, max_raw_mark={component_mark.max_raw_mark}, percentage={component_mark.percentage}")

            return component_mark
        except Exception as e:
            print(f"Error getting component mark: {e}")
            return None

    return render_template(
        'edit_class_marks.html',
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        class_data=class_data,
        subject_names=subject_names,
        subject_ids=subject_ids,
        subject_objects=subject_objects,
        subject_total_marks=subject_total_marks,
        education_level=education_level,
        get_component_mark=get_component_mark
    )

@classteacher_bp.route('/update_class_marks/<grade>/<stream>/<term>/<assessment_type>', methods=['POST'])
@classteacher_required
def update_class_marks(grade, stream, term, assessment_type):
    """Route for updating class marks."""
    stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Determine education level based on grade
    education_level = ""
    grade_num = int(grade.split()[1]) if len(grade.split()) > 1 else int(grade)
    if 1 <= grade_num <= 3:
        education_level = "lower primary"
    elif 4 <= grade_num <= 6:
        education_level = "upper primary"
    elif 7 <= grade_num <= 9:
        education_level = "junior secondary"

    # Get subjects for this grade based on education level
    if education_level == "lower primary":
        filtered_subjects = Subject.query.filter_by(education_level="lower_primary").all()
    elif education_level == "upper primary":
        filtered_subjects = Subject.query.filter_by(education_level="upper_primary").all()
    elif education_level == "junior secondary":
        filtered_subjects = Subject.query.filter_by(education_level="junior_secondary").all()
    else:
        filtered_subjects = Subject.query.all()

    # Get students in this stream
    students = Student.query.filter_by(stream_id=stream_obj.id).all()

    # Process form data
    marks_updated = 0
    component_marks_updated = 0

    for student in students:
        for subject in filtered_subjects:
            # Check if this is a composite subject
            if subject.is_composite:
                # Get the components for this subject
                components = subject.get_components()

                # Process each component
                component_marks = []
                for component in components:
                    component_mark_key = f"component_mark_{student.id}_{component.id}"
                    component_max_key = f"component_max_{student.id}_{component.id}"

                    if component_mark_key in request.form and component_max_key in request.form:
                        try:
                            # Get the raw mark and max raw mark from the form
                            raw_mark = int(request.form[component_mark_key])
                            max_raw_mark = int(request.form[component_max_key])

                            # Sanitize the values
                            raw_mark, max_raw_mark = MarkConversionService.sanitize_raw_mark(raw_mark, max_raw_mark)

                            # Calculate percentage
                            percentage = MarkConversionService.calculate_percentage(raw_mark, max_raw_mark)

                            # Store the component mark data
                            component_marks.append({
                                'component_id': component.id,
                                'raw_mark': raw_mark,
                                'max_raw_mark': max_raw_mark,
                                'percentage': percentage,
                                'weight': component.weight
                            })
                        except ValueError:
                            # Skip invalid values
                            pass

                # If we have component marks, calculate the overall mark
                if component_marks:
                    # Calculate weighted percentage
                    total_weighted_percentage = 0
                    total_weight = 0

                    for cm in component_marks:
                        # Calculate percentage from raw mark and max raw mark
                        component_percentage = (cm['raw_mark'] / cm['max_raw_mark']) * 100 if cm['max_raw_mark'] > 0 else 0
                        # Cap at 100%
                        component_percentage = min(component_percentage, 100)
                        total_weighted_percentage += component_percentage * cm['weight']
                        total_weight += cm['weight']

                    if total_weight > 0:
                        overall_percentage = total_weighted_percentage / total_weight
                    else:
                        overall_percentage = 0

                    # Find existing mark or create new one
                    mark = Mark.query.filter_by(
                        student_id=student.id,
                        subject_id=subject.id,
                        term_id=term_obj.id,
                        assessment_type_id=assessment_type_obj.id
                    ).first()

                    if mark:
                        # Update existing mark
                        mark.percentage = overall_percentage

                        # Calculate raw mark based on percentage (for backward compatibility)
                        # Use 100 as the default max_raw_mark for the overall mark
                        mark.raw_mark = (overall_percentage / 100) * 100
                        mark.max_raw_mark = 100
                        mark.mark = mark.raw_mark  # Old field name
                        mark.total_marks = mark.max_raw_mark  # Old field name
                    else:
                        # Create new mark
                        mark = Mark(
                            student_id=student.id,
                            subject_id=subject.id,
                            term_id=term_obj.id,
                            assessment_type_id=assessment_type_obj.id,
                            percentage=overall_percentage,
                            raw_mark=(overall_percentage / 100) * 100,
                            max_raw_mark=100,
                            mark=(overall_percentage / 100) * 100,  # Old field name
                            total_marks=100  # Old field name
                        )
                        db.session.add(mark)

                    # Save the mark to get its ID
                    db.session.flush()

                    # Now save the component marks
                    for cm in component_marks:
                        # Find existing component mark or create new one
                        from ..models.academic import ComponentMark
                        component_mark = ComponentMark.query.filter_by(
                            mark_id=mark.id,
                            component_id=cm['component_id']
                        ).first()

                        if component_mark:
                            # Update existing component mark
                            component_mark.raw_mark = cm['raw_mark']
                            component_mark.max_raw_mark = cm['max_raw_mark']
                            component_mark.percentage = cm['percentage']
                        else:
                            # Create new component mark
                            component_mark = ComponentMark(
                                mark_id=mark.id,
                                component_id=cm['component_id'],
                                raw_mark=cm['raw_mark'],
                                max_raw_mark=cm['max_raw_mark'],
                                percentage=cm['percentage']
                            )
                            db.session.add(component_mark)

                        component_marks_updated += 1

                    marks_updated += 1
            else:
                # Regular subject (not composite)
                mark_key = f"mark_{student.id}_{subject.id}"
                total_marks_key = f"total_marks_{subject.id}"

                if mark_key in request.form and total_marks_key in request.form:
                    try:
                        # Get the raw mark and total marks from the form
                        raw_mark = int(request.form[mark_key])
                        max_raw_mark = int(request.form[total_marks_key])

                        # Sanitize the raw mark and total marks to ensure they're within acceptable ranges
                        raw_mark, max_raw_mark = MarkConversionService.sanitize_raw_mark(raw_mark, max_raw_mark)

                        # Calculate percentage using our service
                        percentage = MarkConversionService.calculate_percentage(raw_mark, max_raw_mark)

                        # Find existing mark or create new one
                        mark = Mark.query.filter_by(
                            student_id=student.id,
                            subject_id=subject.id,
                            term_id=term_obj.id,
                            assessment_type_id=assessment_type_obj.id
                        ).first()

                        if mark:
                            # Update existing mark with both old and new field names
                            mark.mark = raw_mark  # Old field name
                            mark.total_marks = max_raw_mark  # Old field name
                            mark.raw_mark = raw_mark  # New field name
                            mark.max_raw_mark = max_raw_mark  # New field name
                            mark.percentage = percentage
                        else:
                            # Create new mark with both old and new field names
                            mark = Mark(
                                student_id=student.id,
                                subject_id=subject.id,
                                term_id=term_obj.id,
                                assessment_type_id=assessment_type_obj.id,
                                mark=raw_mark,  # Old field name
                                total_marks=max_raw_mark,  # Old field name
                                raw_mark=raw_mark,  # New field name
                                max_raw_mark=max_raw_mark,  # New field name
                                percentage=percentage
                            )
                            db.session.add(mark)

                        marks_updated += 1
                    except ValueError:
                        # Skip invalid values
                        pass

    # Commit changes to database
    try:
        db.session.commit()
        if component_marks_updated > 0:
            flash(f"Successfully updated {marks_updated} marks and {component_marks_updated} component marks.", "success")
        else:
            flash(f"Successfully updated {marks_updated} marks.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating marks: {str(e)}", "error")

    return redirect(url_for('classteacher.dashboard'))

@classteacher_bp.route('/download_class_report/<grade>/<stream>/<term>/<assessment_type>')
@teacher_or_classteacher_required
def download_class_report(grade, stream, term, assessment_type):
    """Route for downloading class reports as PDF."""
    # Check if we have a cached PDF
    cached_pdf = get_cached_pdf(grade, stream, term, assessment_type, "class_report")
    if cached_pdf:
        return send_file(
            cached_pdf,
            as_attachment=True,
            download_name=f"{grade}_{stream}_{term}_{assessment_type}_Class_Report.pdf",
            mimetype='application/pdf'
        )

    # If no cache or cache miss, generate the report
    stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Get the selected subjects from the session if available
    selected_subjects = session.get('selected_subjects', [])

    # Check if this is a subject teacher (role = 'teacher') and filter subjects accordingly
    current_role = get_role(session)
    if current_role == 'teacher':
        # For subject teachers, only show subjects they are assigned to teach
        teacher_id = session.get('teacher_id')
        if teacher_id:
            # Get the grade object
            grade_obj_temp = stream_obj.grade

            # Get subjects assigned to this teacher for this grade/stream
            teacher_assignments = TeacherSubjectAssignment.query.filter_by(
                teacher_id=teacher_id,
                grade_id=grade_obj_temp.id
            ).filter(
                (TeacherSubjectAssignment.stream_id == stream_obj.id) |
                (TeacherSubjectAssignment.stream_id == None)  # Assignments for all streams
            ).all()

            # Get subject IDs from assignments
            teacher_subject_ids = [assignment.subject_id for assignment in teacher_assignments]

            # Override selected_subjects to only include teacher's assigned subjects
            selected_subjects = teacher_subject_ids

    # Get class report data first with selected subjects
    report_data = get_class_report_data(grade, stream, term, assessment_type, selected_subject_ids=selected_subjects)

    if not report_data or report_data.get("error"):
        error_msg = report_data.get("error") if report_data and report_data.get("error") else f"No marks found for {grade} Stream {stream[-1]} in {term} {assessment_type}"
        flash(error_msg, "error")
        return redirect(url_for('classteacher.dashboard'))

    # Get education level from report_data or determine based on grade
    if report_data.get("education_level"):
        education_level_code = report_data.get("education_level")
        if education_level_code == "lower_primary":
            education_level = "lower primary"
        elif education_level_code == "upper_primary":
            education_level = "upper primary"
        elif education_level_code == "junior_secondary":
            education_level = "junior secondary"
        else:
            education_level = ""
    else:
        # Fallback to determining education level based on grade
        education_level = ""
        grade_num = int(grade.split()[1]) if len(grade.split()) > 1 else int(grade)
        if 1 <= grade_num <= 3:
            education_level = "lower primary"
        elif 4 <= grade_num <= 6:
            education_level = "upper primary"
        elif 7 <= grade_num <= 9:
            education_level = "junior secondary"

    # Calculate subject averages for the PDF
    subject_averages = {}
    for subject in report_data["subjects"]:
        subject_total = 0
        subject_count = 0
        for student_data in report_data["class_data"]:
            mark = student_data['marks'].get(subject, 0)
            if mark > 0:
                subject_total += mark
                subject_count += 1

        if subject_count > 0:
            subject_averages[subject] = round(subject_total / subject_count, 2)
        else:
            subject_averages[subject] = 0

    # Calculate class average for the PDF
    class_total = 0
    student_count = 0
    for student_data in report_data["class_data"]:
        if student_data['total_marks'] > 0:
            class_total += student_data['total_marks']
            student_count += 1

    class_average = round(class_total / student_count, 2) if student_count > 0 else 0

    # Get staff information for the report
    from ..services.staff_assignment_service import StaffAssignmentService
    staff_info = StaffAssignmentService.get_report_staff_info(grade, stream)

    # Generate PDF report using HTML-to-PDF conversion for better formatting
    pdf_file = generate_class_report_pdf_from_html(
        grade,
        stream,
        term,
        assessment_type,
        report_data["class_data"],
        report_data["stats"],
        report_data["total_marks"],
        report_data["subjects"],
        education_level,
        subject_averages,
        class_average,
        selected_subject_ids=selected_subjects,
        staff_info=staff_info
    )

    # Notify parents if report generation was successful and notification is requested
    notify_parents = request.form.get('notify_parents') == 'on'
    if pdf_file and notify_parents:
        try:
            from ..services.parent_notification_service import ParentNotificationService
            notification_result = ParentNotificationService.notify_parents_of_new_results(
                grade=grade,
                stream=stream,
                term=term,
                assessment_type=assessment_type,
                report_file_path=pdf_file
            )

            if notification_result.get('success'):
                if notification_result.get('notifications_sent', 0) > 0:
                    flash(f"✅ Report generated and {notification_result['notifications_sent']} parent(s) notified via email", 'success')
                else:
                    flash("✅ Report generated successfully (no parents to notify)", 'success')

                if notification_result.get('notifications_failed', 0) > 0:
                    flash(f"⚠️ {notification_result['notifications_failed']} parent notification(s) failed", 'warning')
            else:
                flash(f"✅ Report generated successfully. Parent notification failed: {notification_result.get('error', 'Unknown error')}", 'warning')

        except Exception as e:
            flash(f"✅ Report generated successfully. Parent notification error: {str(e)}", 'warning')

    if not pdf_file:
        flash(f"Failed to generate report for {grade} Stream {stream[-1]} in {term} {assessment_type}", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Cache the report data
    cache_report(grade, stream, term, assessment_type, report_data)

    # Cache the PDF file
    with open(pdf_file, 'rb') as f:
        pdf_data = f.read()
    cache_pdf(grade, stream, term, assessment_type, "class_report", pdf_data)

    # Return the PDF file
    filename = f"{grade}_Stream_{stream[-1]}_{term}_{assessment_type}_Report.pdf"
    return send_file(
        pdf_file,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@classteacher_bp.route('/print_individual_report/<grade>/<stream>/<term>/<assessment_type>/<student_name>')
@classteacher_required
def print_individual_report(grade, stream, term, assessment_type, student_name):
    """Route for printing individual student reports with a clean format."""
    stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('classteacher.dashboard'))

    student = Student.query.filter_by(name=student_name, stream_id=stream_obj.id).first()
    if not student:
        flash(f"No data available for student {student_name}.", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Get education level based on grade
    education_level = ""
    grade_num = int(grade.split()[1]) if len(grade.split()) > 1 else int(grade)
    if 1 <= grade_num <= 3:
        education_level = "lower primary"
    elif 4 <= grade_num <= 6:
        education_level = "upper primary"
    elif 7 <= grade_num <= 9:
        education_level = "junior secondary"

    # Get class report data first
    class_data_result = get_class_report_data(grade, stream, term, assessment_type)

    if class_data_result.get("error"):
        flash(class_data_result.get("error"), "error")
        return redirect(url_for('classteacher.dashboard'))

    # Find student data in the class report
    student_data = None
    for data in class_data_result["class_data"]:
        if data["student"] == student.name:
            student_data = data
            break

    if not student_data:
        flash(f"No marks found for {student_name} in {term} {assessment_type}", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Calculate class averages for each subject
    class_data = class_data_result["class_data"]
    subjects = class_data_result["subjects"]
    subject_averages = {}

    for subject in subjects:
        subject_total = 0
        subject_count = 0
        for data in class_data:
            mark = data.get("marks", {}).get(subject, 0)
            if mark != 0 and mark != "-":
                subject_total += mark
                subject_count += 1

        if subject_count > 0:
            subject_averages[subject] = round(subject_total / subject_count, 2)
        else:
            subject_averages[subject] = 0

    # Calculate overall class average
    overall_total = 0
    overall_count = 0
    for data in class_data:
        overall_total += data.get("total_marks", 0)
        overall_count += 1

    class_average = 0
    if overall_count > 0:
        class_average = round((overall_total / overall_count) / len(subjects) * 100, 2) if subjects else 0

    # Calculate mean grade and points
    avg_percentage = student_data.get("average_percentage", 0)
    from ..utils import get_grade_and_points
    mean_grade, mean_points = get_grade_and_points(avg_percentage)

    # Prepare table data for the report
    table_data = []
    for subject in class_data_result.get("subjects", []):
        mark = student_data.get("marks", {}).get(subject, 0)
        # For now, we'll use the same mark for all assessment types
        table_data.append({
            "subject": subject,
            "entrance": mark,
            "mid_term": mark,
            "end_term": mark,
            "avg": mark,
            "remarks": get_performance_remarks(mark, class_data_result.get("total_marks", 100))
        })

    # Calculate total marks and points
    total_marks = student_data.get("total_marks", 0)
    total_possible_marks = len(class_data_result.get("subjects", [])) * class_data_result.get("total_marks", 100)
    total_points = mean_points * len(class_data_result.get("subjects", []))

    # Generate admission number if not available
    admission_no = student.admission_number if hasattr(student, 'admission_number') and student.admission_number else f"KPS{grade}{stream[-1]}{student.id}"

    # Get academic year
    academic_year = term_obj.academic_year if hasattr(term_obj, 'academic_year') and term_obj.academic_year else "2023"

    # Get current date for the report
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Get logo URL
    logo_url = url_for('static', filename='images/kirima_logo.png')

    # Get school information for dynamic display
    from ..services.school_config_service import SchoolConfigService
    school_info = SchoolConfigService.get_school_info_dict()

    return render_template(
        'print_individual_report.html',
        student_name=student.name,
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        education_level=education_level,
        current_date=current_date,
        table_data=table_data,
        total=total_marks,
        avg_percentage=avg_percentage,
        mean_grade=mean_grade,
        mean_points=mean_points,
        total_possible_marks=total_possible_marks,
        total_points=total_points,
        admission_no=admission_no,
        academic_year=academic_year,
        logo_url=logo_url,
        subject_averages=subject_averages,
        class_average=class_average,
        class_size=overall_count,
        school_info=school_info  # Pass school information
    )

@classteacher_bp.route('/preview_individual_report/<grade>/<stream>/<term>/<assessment_type>/<student_name>')
@classteacher_required
def preview_individual_report(grade, stream, term, assessment_type, student_name):
    # Check if this is a print request
    print_mode = request.args.get('print', '0') == '1'
    if print_mode:
        return redirect(url_for('classteacher.print_individual_report',
                               grade=grade,
                               stream=stream,
                               term=term,
                               assessment_type=assessment_type,
                               student_name=student_name))
    """Route for previewing individual student reports."""
    stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('classteacher.dashboard'))

    student = Student.query.filter_by(name=student_name, stream_id=stream_obj.id).first()
    if not student:
        flash(f"No data available for student {student_name}.", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Get education level based on grade
    education_level = ""
    grade_num = int(grade.split()[1]) if len(grade.split()) > 1 else int(grade)
    if 1 <= grade_num <= 3:
        education_level = "lower primary"
    elif 4 <= grade_num <= 6:
        education_level = "upper primary"
    elif 7 <= grade_num <= 9:
        education_level = "junior secondary"

    # Get class report data first
    class_data_result = get_class_report_data(grade, stream, term, assessment_type)

    if class_data_result.get("error"):
        flash(class_data_result.get("error"), "error")
        return redirect(url_for('classteacher.dashboard'))

    # Find student data in the class report
    student_data = None
    for data in class_data_result["class_data"]:
        if data["student"] == student.name:
            student_data = data
            break

    if not student_data:
        flash(f"No marks found for {student_name} in {term} {assessment_type}", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Calculate mean grade and points
    avg_percentage = student_data.get("average_percentage", 0)
    from ..utils import get_grade_and_points
    mean_grade, mean_points = get_grade_and_points(avg_percentage)

    # Prepare table data for the report with composite subject handling
    table_data = []
    composite_data = {}

    # Get only subjects that have marks in the class report data
    subjects_with_marks = class_data_result.get("subjects", [])

    # Define subject order - core subjects first (with variations)
    subject_order = [
        "Mathematics", "MATHEMATICS", "Math", "MATH",
        "English", "ENGLISH", "English Language", "ENGLISH LANGUAGE",
        "Kiswahili", "KISWAHILI", "Kiswahili Language", "KISWAHILI LANGUAGE",
        "Religious", "RELIGIOUS", "Religious Education", "RELIGIOUS EDUCATION", "CRE", "IRE",
        "Integrated Science", "INTEGRATED SCIENCE", "Science", "SCIENCE",
        "Social Studies", "SOCIAL STUDIES", "Social Science", "SOCIAL SCIENCE",
        "Agriculture", "AGRICULTURE", "Agricultural Science", "AGRICULTURAL SCIENCE",
        "Creative Art and Sports", "CREATIVE ART AND SPORTS", "Creative Arts", "CREATIVE ARTS"
    ]

    # Sort subjects according to the defined order, but only include those with marks
    ordered_subject_names = []
    # First add subjects in the specified order if they have marks
    for subject_name in subject_order:
        if subject_name in subjects_with_marks and subject_name not in ordered_subject_names:
            ordered_subject_names.append(subject_name)

    # Then add any remaining subjects with marks alphabetically
    remaining_subject_names = [s for s in subjects_with_marks if s not in ordered_subject_names]
    remaining_subject_names.sort()
    ordered_subject_names.extend(remaining_subject_names)

    from ..models.academic import Subject, ComponentMark

    for subject_name in ordered_subject_names:
        # Get the subject object
        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            continue
        mark = student_data.get("marks", {}).get(subject.name, 0)

        # Skip subjects with no marks (0 or None)
        if not mark or mark == 0:
            continue

        # Clean up decimal precision and show whole numbers
        if isinstance(mark, float):
            mark = int(round(mark)) if mark == int(mark) else round(mark, 1)
        else:
            mark = int(mark)

        # Check if this is a composite subject
        if hasattr(subject, 'is_composite') and subject.is_composite:
            # Get component marks for this student
            components = subject.get_components()
            component_marks = {}

            # Get the mark record for this subject
            mark_record = Mark.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                term_id=term_obj.id,
                assessment_type_id=assessment_type_obj.id
            ).first()

            if mark_record:
                # Get component marks
                for component in components:
                    component_mark = ComponentMark.query.filter_by(
                        component_id=component.id,
                        mark_id=mark_record.id
                    ).first()

                    if component_mark:
                        # Clean component name (remove any prefixes like "L ")
                        clean_component_name = component.name
                        if clean_component_name.startswith("L "):
                            clean_component_name = clean_component_name[2:]

                        # Get the component's maximum mark from the component_mark record or component definition
                        component_max_mark = component_mark.max_raw_mark if component_mark.max_raw_mark else (component.max_raw_mark if hasattr(component, 'max_raw_mark') and component.max_raw_mark else 100)

                        # Convert component mark to percentage for proper grading
                        component_percentage = (component_mark.raw_mark / component_max_mark) * 100

                        # Show whole numbers for component marks
                        component_raw_mark = component_mark.raw_mark
                        if isinstance(component_raw_mark, float):
                            component_raw_mark = int(round(component_raw_mark)) if component_raw_mark == int(component_raw_mark) else round(component_raw_mark, 1)
                        else:
                            component_raw_mark = int(component_raw_mark)

                        component_marks[clean_component_name] = {
                            'mark': component_raw_mark,
                            'max_mark': int(component_max_mark),
                            'percentage': round(component_percentage, 1),
                            'remarks': get_performance_remarks(component_percentage, 100)
                        }
                    else:
                        # Clean component name (remove any prefixes like "L ")
                        clean_component_name = component.name
                        if clean_component_name.startswith("L "):
                            clean_component_name = clean_component_name[2:]

                        # Get the component's maximum mark from component definition (default to 100 if not set)
                        component_max_mark = component.max_raw_mark if hasattr(component, 'max_raw_mark') and component.max_raw_mark else 100

                        component_marks[clean_component_name] = {
                            'mark': 0,
                            'max_mark': component_max_mark,
                            'percentage': 0,
                            'remarks': get_performance_remarks(0, 100)
                        }

            # Store composite data for template
            composite_data[subject.name] = {
                'components': component_marks,
                'total': mark
            }

        # Add to table data
        # Initialize marks for all assessment types
        entrance_mark = 0
        mid_term_mark = 0
        end_term_mark = 0

        # If this is an end-term report, fetch marks from all assessment types for comparison
        if assessment_type.lower() in ['end_term', 'endterm']:
            # Get all assessment types for this term
            all_assessment_types = AssessmentType.query.all()

            # Fetch marks for each assessment type
            for at in all_assessment_types:
                mark_record = Mark.query.filter_by(
                    student_id=student.id,
                    subject_id=subject.id,
                    term_id=term_obj.id,
                    assessment_type_id=at.id
                ).first()

                if mark_record:
                    mark_value = mark_record.percentage or 0

                    # Map to appropriate assessment type
                    if at.name.lower() in ['entrance', 'opener']:
                        entrance_mark = mark_value
                    elif at.name.lower() in ['mid_term', 'midterm']:
                        mid_term_mark = mark_value
                    elif at.name.lower() in ['end_term', 'endterm']:
                        end_term_mark = mark_value

            # Calculate average of available marks
            available_marks = [m for m in [entrance_mark, mid_term_mark, end_term_mark] if m > 0]
            avg_mark = sum(available_marks) / len(available_marks) if available_marks else 0
        else:
            # For single assessment types, show only current assessment
            if assessment_type.lower() in ['entrance', 'opener']:
                entrance_mark = mark
            elif assessment_type.lower() in ['mid_term', 'midterm']:
                mid_term_mark = mark
            elif assessment_type.lower() in ['end_term', 'endterm']:
                end_term_mark = mark

            avg_mark = mark

        table_data.append({
            "subject": subject.name,
            "entrance": entrance_mark,
            "mid_term": mid_term_mark,
            "end_term": end_term_mark,
            "current_assessment": mark,  # Always show the current assessment mark
            "avg": avg_mark,
            "remarks": get_performance_remarks(avg_mark if assessment_type.lower() in ['end_term', 'endterm'] else mark, class_data_result.get("total_marks", 100))
        })

    # Calculate total marks and points based on subjects with marks
    total_marks = student_data.get("total_marks", 0)
    total_possible_marks = len(subjects_with_marks) * class_data_result.get("total_marks", 100)
    total_points = mean_points * len(subjects_with_marks)

    # Generate admission number if not available
    admission_no = student.admission_number if hasattr(student, 'admission_number') and student.admission_number else f"KPS{grade}{stream[-1]}{student.id}"

    # Get academic year
    academic_year = term_obj.academic_year if hasattr(term_obj, 'academic_year') and term_obj.academic_year else "2023"

    # Get current date for the report
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")

    return render_template(
        'preview_individual_report.html',
        student=student,
        student_data=student_data,
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        education_level=education_level,
        current_date=current_date,
        table_data=table_data,
        composite_data=composite_data,  # Add composite subject data
        total=total_marks,
        avg_percentage=avg_percentage,
        mean_grade=mean_grade,
        mean_points=mean_points,
        total_possible_marks=total_possible_marks,
        total_points=total_points,
        admission_no=admission_no,
        academic_year=academic_year,
        print_mode=print_mode
    )

@classteacher_bp.route('/api/check_stream_status/<grade>/<term>/<assessment_type>', methods=['GET'])
@classteacher_required
def check_stream_status(grade, term, assessment_type):
    """API route to check if all streams in a grade have marks for a term and assessment type."""
    try:
        # Get the grade object
        grade_obj = Grade.query.filter_by(name=grade).first()

        if not grade_obj:
            return jsonify({"success": False, "message": f"Grade {grade} not found", "streams": []})

        # Get the term and assessment type objects
        term_obj = Term.query.filter_by(name=term).first()
        assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

        if not term_obj or not assessment_type_obj:
            return jsonify({"success": False, "message": "Invalid term or assessment type", "streams": []})

        # Get streams for this grade
        streams = Stream.query.filter_by(grade_id=grade_obj.id).all()

        # Check if each stream has marks for this term and assessment type
        streams_data = []
        for stream in streams:
            # Get students in this stream
            students = Student.query.filter_by(stream_id=stream.id).all()

            # Check if there are marks for any student in this stream
            has_report = False
            if students:
                for student in students:
                    mark = Mark.query.filter_by(
                        student_id=student.id,
                        term_id=term_obj.id,
                        assessment_type_id=assessment_type_obj.id
                    ).first()

                    if mark:
                        has_report = True
                        break

            streams_data.append({
                "id": stream.id,
                "name": stream.name,
                "has_report": has_report
            })

        return jsonify({"success": True, "streams": streams_data})
    except Exception as e:
        print(f"Error checking stream status: {str(e)}")
        return jsonify({"success": False, "message": str(e), "streams": []})

@classteacher_bp.route('/get_streams_by_level/<grade>', methods=['GET'])
@classteacher_required
def get_streams_by_level(grade):
    """API route to get streams for a grade by grade level."""
    try:
        # Get current teacher info for debugging
        teacher_id = session.get('teacher_id')
        current_role = get_role(session)
        print(f"=== STREAM FETCH DEBUG ===")
        print(f"Teacher ID: {teacher_id}, Role: {current_role}")
        print(f"Requested grade: {grade}")

        # Handle both "Grade X" format and just "X" format
        if grade.isdigit():
            grade_name = f"Grade {grade}"
        else:
            grade_name = grade

        print(f"Looking for grade: {grade_name}")

        # Get the grade object by name
        grade_obj = Grade.query.filter_by(name=grade_name).first()

        if not grade_obj:
            print(f"Grade {grade_name} not found in database")
            # Try alternative formats
            if grade_name.startswith("Grade "):
                alt_grade = grade_name.replace("Grade ", "")
                grade_obj = Grade.query.filter_by(name=alt_grade).first()
                print(f"Trying alternative format: {alt_grade}")

            if not grade_obj:
                # List all available grades for debugging
                all_grades = Grade.query.all()
                available_grades = [g.name for g in all_grades]
                print(f"Available grades in database: {available_grades}")
                return jsonify({"success": False, "message": f"Grade {grade} not found. Available: {available_grades}", "streams": []})

        print(f"Found grade: {grade_obj.name} (ID: {grade_obj.id})")

        # Get streams for this grade
        streams = Stream.query.filter_by(grade_id=grade_obj.id).all()
        print(f"Found {len(streams)} streams for grade {grade_obj.name}")

        # Debug: List all streams
        for stream in streams:
            print(f"  Stream: {stream.name} (ID: {stream.id})")

        # Check if teacher has access to these streams (for role-based filtering)
        accessible_streams = streams  # Default: all streams

        if current_role in ['teacher', 'classteacher']:
            # Check teacher assignments
            teacher_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).all()
            print(f"Teacher has {len(teacher_assignments)} assignments")

            # Get assigned stream IDs
            assigned_stream_ids = []
            for assignment in teacher_assignments:
                if assignment.stream_id:
                    assigned_stream_ids.append(assignment.stream_id)
                    print(f"  Assigned to stream ID: {assignment.stream_id}")
                else:
                    print(f"  Assigned to all streams in grade {assignment.grade_id}")

            # If teacher has specific stream assignments, filter streams
            if assigned_stream_ids:
                accessible_streams = [s for s in streams if s.id in assigned_stream_ids]
                print(f"Filtered to {len(accessible_streams)} accessible streams")
            else:
                # If no specific stream assignments, check if teacher has any assignments for this grade
                grade_assignments = [a for a in teacher_assignments if a.grade_id == grade_obj.id]
                if grade_assignments:
                    print(f"Teacher has {len(grade_assignments)} assignments for this grade - allowing all streams")
                    accessible_streams = streams
                else:
                    print(f"Teacher has no assignments for grade {grade_obj.name}")
                    # For now, still allow all streams - we can restrict this later if needed
                    accessible_streams = streams

        # Format streams for JSON response
        streams_data = [{"id": stream.id, "name": stream.name} for stream in accessible_streams]
        print(f"Returning {len(streams_data)} streams: {[s['name'] for s in streams_data]}")

        return jsonify({"success": True, "streams": streams_data})
    except Exception as e:
        print(f"Error fetching streams: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e), "streams": []})

@classteacher_bp.route('/get_subjects_by_education_level/<education_level>', methods=['GET'])
@classteacher_required
def get_subjects_by_education_level(education_level):
    """API route to get subjects for a specific education level."""
    try:
        # Get subjects for this education level
        all_subjects = Subject.query.filter_by(education_level=education_level).all()

        if not all_subjects:
            return jsonify({"success": True, "message": f"No subjects found for {education_level}", "subjects": []})

        # Define core subjects that should appear first
        core_subjects = ["Mathematics", "English", "Kiswahili", "Science", "Integrated Science",
                        "Science and Technology", "Integrated Science and Health Education"]

        # Sort subjects with core subjects first
        sorted_subjects = []

        # First add core subjects in the specified order
        for core_subject in core_subjects:
            for subject in all_subjects:
                if subject.name == core_subject or subject.name.upper() == core_subject.upper():
                    sorted_subjects.append(subject)

        # Then add remaining subjects alphabetically
        remaining_subjects = [s for s in all_subjects if s not in sorted_subjects]
        remaining_subjects.sort(key=lambda x: x.name)
        sorted_subjects.extend(remaining_subjects)

        # Convert to list of dictionaries
        subjects_data = [{"id": subject.id, "name": subject.name} for subject in sorted_subjects]

        return jsonify({"success": True, "subjects": subjects_data})
    except Exception as e:
        print(f"Error fetching subjects: {str(e)}")
        return jsonify({"success": False, "message": str(e), "subjects": []})

@classteacher_bp.route('/download_marks_template', methods=['GET'])
@classteacher_required
def download_marks_template():
    """Route to download the marks upload template."""
    # Get parameters from the request
    education_level = request.args.get('education_level', '')
    grade_level = request.args.get('grade', '')
    stream_name = request.args.get('stream', '')
    term = request.args.get('term', '')
    assessment_type = request.args.get('assessment_type', '')
    file_format = request.args.get('format', 'xlsx')

    # If specific parameters are provided, generate a customized template
    if education_level and grade_level and stream_name:
        # Extract stream letter from "Stream X" format
        stream_letter = stream_name.replace("Stream ", "") if stream_name.startswith("Stream ") else stream_name[-1]

        # Get the stream object
        stream_obj = Stream.query.join(Grade).filter(Grade.name == grade_level, Stream.name == stream_letter).first()

        if stream_obj:
            # Get students for this stream
            students = Student.query.filter_by(stream_id=stream_obj.id).order_by(Student.name).all()

            # Get subjects for this education level
            subjects = [subject.name for subject in Subject.query.filter_by(education_level=education_level).all()]

            if students and subjects:
                try:
                    # Import the template generator
                    from ..static.templates.marks_upload_template import create_marks_upload_template

                    # Get term and assessment type objects
                    term_obj = Term.query.filter_by(name=term).first()
                    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

                    # Default total marks value
                    default_total_marks = 100

                    # Get total marks for each subject
                    subject_total_marks = {}
                    for subject_name in subjects:
                        subject = Subject.query.filter_by(name=subject_name).first()
                        if subject:
                            # Check if any marks exist for this subject to get the total_marks
                            mark = Mark.query.filter_by(
                                subject_id=subject.id,
                                term_id=term_obj.id,
                                assessment_type_id=assessment_type_obj.id
                            ).first()

                            if mark:
                                subject_total_marks[subject_name] = mark.total_marks
                            else:
                                # Default to default_total_marks if no marks exist
                                subject_total_marks[subject_name] = default_total_marks

                    # Create a custom template
                    template_path = create_marks_upload_template(
                        students=students,
                        subjects=subjects,
                        total_marks=default_total_marks,
                        grade=grade_level,
                        stream=stream_name,
                        term=term,
                        assessment_type=assessment_type,
                        subject_total_marks=subject_total_marks
                    )

                    # Return the template file
                    return send_file(
                        template_path,
                        as_attachment=True,
                        download_name=f"marks_template_{grade_level}_{stream_letter}_{term}_{assessment_type}.xlsx",
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                except Exception as e:
                    flash(f"Error creating template: {str(e)}", "error")
                    return redirect(url_for('classteacher.dashboard'))

    # If no specific parameters or an error occurred, return a generic template
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static',
        'templates',
        f"marks_upload_template_example_{education_level if education_level else 'upper_primary'}.{file_format}"
    )

    # Check if the template file exists
    if not os.path.exists(template_path):
        # If not, create it
        try:
            from ..static.templates.marks_upload_template import create_empty_marks_template
            create_empty_marks_template(education_level if education_level else 'upper_primary')
        except Exception as e:
            flash(f"Error creating template: {str(e)}", "error")
            return redirect(url_for('classteacher.dashboard'))

    # Set the appropriate mimetype based on the file format
    if file_format == 'csv':
        mimetype = 'text/csv'
        filename = f"marks_template_example_{education_level if education_level else 'general'}.csv"
    else:
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = f"marks_template_example_{education_level if education_level else 'general'}.xlsx"

    return send_file(
        template_path,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )

@classteacher_bp.route('/generate_grade_marksheet/<grade>/<term>/<assessment_type>/<action>')
@classteacher_required
def generate_grade_marksheet(grade, term, assessment_type, action):
    """Route for generating grade marksheets (preview or download)."""
    # Check if we have a cached version
    cached_marksheet = get_cached_marksheet(grade, "all", term, assessment_type)
    if cached_marksheet and action == 'preview':
        # Use the cached marksheet data
        return render_template(
            'preview_grade_marksheet.html',
            grade=grade,
            term=term,
            assessment_type=assessment_type,
            subjects=cached_marksheet['subjects'],
            data=cached_marksheet['data'],
            statistics=cached_marksheet['statistics']
        )
    elif cached_marksheet and action == 'download':
        # Check if we have a cached PDF
        cached_pdf = get_cached_pdf(grade, "all", term, assessment_type, "marksheet")
        if cached_pdf:
            return send_file(
                cached_pdf,
                as_attachment=True,
                download_name=f"{grade}_{term}_{assessment_type}_Grade_Marksheet.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

    # If no cache or cache miss, generate the marksheet
    # Fetch grade and related data
    grade_obj = Grade.query.filter_by(name=grade).first()
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
            student_standardized_total = 0
            for subject in subjects:
                mark = Mark.query.filter_by(
                    student_id=student.id,
                    subject_id=subject.id,
                    term_id=term_obj.id,
                    assessment_type_id=assessment_type_obj.id
                ).first()

                if mark:
                    # Store the raw mark
                    student_marks[subject.name] = mark.mark

                    # Calculate standardized mark (out of 100)
                    total_marks = mark.total_marks if mark.total_marks > 0 else 100
                    standardized_mark = (mark.mark / total_marks) * 100

                    # Add to standardized total for average calculation
                    student_standardized_total += standardized_mark
                    subject_count += 1
                else:
                    student_marks[subject.name] = "-"

            # Calculate average percentage (already standardized to 100)
            average_percentage = student_standardized_total / subject_count if subject_count > 0 else 0
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

    # Calculate statistics for the marksheet
    stream_data = {}
    subject_totals = {subject.name: 0 for subject in subjects}
    subject_counts = {subject.name: 0 for subject in subjects}
    overall_total = 0
    overall_count = 0

    # Collect statistics for each stream
    for stream in streams:
        stream_students = [s for s in all_data if s['name'].endswith(f"({stream.name})")]
        stream_total = sum(s['total'] for s in stream_students)
        stream_count = len(stream_students) * len(subjects)  # Total possible marks

        # Calculate stream average
        stream_average = stream_total / stream_count if stream_count > 0 else 0

        # Calculate subject averages for this stream
        stream_subject_totals = {subject.name: 0 for subject in subjects}
        stream_subject_counts = {subject.name: 0 for subject in subjects}

        for student in stream_students:
            for subject in subjects:
                mark = student['marks'].get(subject.name)
                if mark != "-":
                    stream_subject_totals[subject.name] += mark
                    stream_subject_counts[subject.name] += 1

                    # Update overall subject totals
                    subject_totals[subject.name] += mark
                    subject_counts[subject.name] += 1

                    # Update overall totals
                    overall_total += mark
                    overall_count += 1

        # Calculate stream subject averages
        stream_subject_averages = {}
        for subject_name in stream_subject_totals:
            if stream_subject_counts[subject_name] > 0:
                stream_subject_averages[subject_name] = round(stream_subject_totals[subject_name] / stream_subject_counts[subject_name], 1)
            else:
                stream_subject_averages[subject_name] = 0

        # Store stream statistics
        stream_data[stream.name] = {
            'total': stream_total,
            'count': len(stream_students),
            'average': round(stream_average, 1),
            'subject_averages': stream_subject_averages
        }

    # Calculate overall subject averages
    subject_averages = {}
    for subject_name in subject_totals:
        if subject_counts[subject_name] > 0:
            subject_averages[subject_name] = round(subject_totals[subject_name] / subject_counts[subject_name], 1)
        else:
            subject_averages[subject_name] = 0

    # Calculate overall average
    overall_average = overall_total / overall_count if overall_count > 0 else 0

    # Calculate performance statistics
    performance_counts = {}
    for category in ['Excellent', 'Very Good', 'Good', 'Average', 'Below Average', 'Poor']:
        performance_counts[category] = len([d for d in all_data if d['grade'] == category])

    # Calculate gender statistics
    gender_counts = {
        'male': 0,
        'female': 0,
        'other': 0
    }

    # Add rank to each student
    for i, student_data in enumerate(all_data):
        student_data['rank'] = i + 1

    # Prepare statistics for the template
    statistics = {
        'total_students': len(all_data),
        'overall_average': round(overall_average, 1),
        'subject_averages': subject_averages,
        'stream_data': stream_data,
        'performance_counts': performance_counts,
        'gender_counts': gender_counts
    }

    # Cache the marksheet data
    marksheet_data = {
        'subjects': subjects,
        'data': all_data,
        'statistics': statistics
    }
    cache_marksheet(grade, "all", term, assessment_type, marksheet_data)

    # Handle preview or download action
    if action == 'preview':
        return render_template(
            'preview_grade_marksheet.html',
            grade=grade,
            term=term,
            assessment_type=assessment_type,
            subjects=subjects,
            data=all_data,
            statistics=statistics
        )
    elif action == 'download':
        try:
            # Import the Excel export service
            from ..services.excel_export import generate_grade_marksheet_excel

            # Generate Excel file
            excel_file = generate_grade_marksheet_excel(
                grade=grade,
                term=term,
                assessment_type=assessment_type,
                subjects=subjects,
                data=all_data,
                statistics=statistics
            )

            # Cache the Excel file
            cached_file = cache_pdf(grade, "all", term, assessment_type, "marksheet", open(excel_file, 'rb').read())

            # Return the Excel file
            return send_file(
                excel_file,
                as_attachment=True,
                download_name=f"{grade}_{term}_{assessment_type}_Grade_Marksheet.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        except Exception as e:
            flash(f"Error generating Excel file: {str(e)}", "error")
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

@classteacher_bp.route('/delete_marksheet/<grade>/<stream>/<term>/<assessment_type>', methods=['POST'])
@classteacher_required
def delete_marksheet(grade, stream, term, assessment_type):
    """Route for deleting a class marksheet (all marks for a grade/stream/term/assessment combination)."""
    try:
        # Get the stream object
        stream_letter = stream[-1] if stream.startswith("Stream ") else stream[-1]
        stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream_letter).first()

        if not stream_obj:
            flash(f"Stream {stream} not found for grade {grade}", "error")
            return redirect(url_for('classteacher.dashboard'))

        # Get the term and assessment type objects
        term_obj = Term.query.filter_by(name=term).first()
        assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

        if not (term_obj and assessment_type_obj):
            flash("Invalid term or assessment type", "error")
            return redirect(url_for('classteacher.dashboard'))

        # Get all students in this stream
        students = Student.query.filter_by(stream_id=stream_obj.id).all()
        student_ids = [student.id for student in students]

        if not student_ids:
            flash(f"No students found in {grade} Stream {stream_letter}", "error")
            return redirect(url_for('classteacher.dashboard'))

        # Determine education level based on grade
        grade_num = int(grade.split()[1]) if len(grade.split()) > 1 else int(grade)
        if 1 <= grade_num <= 3:
            education_level_code = "lower_primary"
        elif 4 <= grade_num <= 6:
            education_level_code = "upper_primary"
        elif 7 <= grade_num <= 9:
            education_level_code = "junior_secondary"
        else:
            education_level_code = ""

        # Get subjects for this education level
        if education_level_code:
            subjects = Subject.query.filter_by(education_level=education_level_code).all()
        else:
            subjects = Subject.query.all()

        subject_ids = [subject.id for subject in subjects]

        # Delete all marks for these students, subjects, term, and assessment type
        deleted_count = Mark.query.filter(
            Mark.student_id.in_(student_ids),
            Mark.subject_id.in_(subject_ids),
            Mark.term_id == term_obj.id,
            Mark.assessment_type_id == assessment_type_obj.id
        ).delete(synchronize_session=False)

        # Commit the changes
        db.session.commit()

        # Invalidate the cache for this grade/stream/term/assessment combination
        invalidate_cache(grade, stream, term, assessment_type)

        # Create a detailed success message
        if deleted_count > 0:
            success_message = f"Successfully deleted {deleted_count} marks for {grade} Stream {stream_letter} in {term} {assessment_type}. The marksheet has been completely removed."
            # Store a session variable to indicate a successful deletion
            session['marksheet_deleted'] = True
            session['deleted_marksheet_info'] = {
                'grade': grade,
                'stream': stream,
                'term': term,
                'assessment_type': assessment_type,
                'count': deleted_count
            }
            flash(success_message, "success")
        else:
            flash(f"No marks were found to delete for {grade} Stream {stream_letter} in {term} {assessment_type}.", "info")

        return redirect(url_for('classteacher.dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting marksheet: {str(e)}", "error")
        return redirect(url_for('classteacher.dashboard'))

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

@classteacher_bp.route('/download_student_template', methods=['GET'])
@classteacher_required
def download_student_template():
    """Route to download the student upload template with enhanced options."""
    file_format = request.args.get('format', 'xlsx')
    template_type = request.args.get('type', 'full')  # full, minimal, headers_only

    # Determine template filename based on type and format
    if template_type == 'minimal':
        base_filename = 'student_upload_template_minimal'
    elif template_type == 'headers_only' and file_format == 'csv':
        base_filename = 'student_upload_template_headers_only'
    else:
        base_filename = 'student_upload_template'

    if file_format == 'csv':
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'templates', f'{base_filename}.csv')
        mimetype = 'text/csv'
        filename = f'{base_filename}.csv'
    else:
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'templates', f'{base_filename}.xlsx')
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = f'{base_filename}.xlsx'

    # Check if the template file exists
    if not os.path.exists(template_path):
        # If not, create it
        try:
            from ..static.templates.student_upload_template import create_student_upload_template, create_minimal_student_template

            if template_type == 'minimal':
                create_minimal_student_template()
            else:
                create_student_upload_template()

            # Check again if file was created
            if not os.path.exists(template_path):
                flash("Template file could not be created. Please try again.", "error")
                return redirect(url_for('classteacher.manage_students'))

        except Exception as e:
            print(f"Error creating template: {str(e)}")
            flash("Error creating template file. Please try again.", "error")
            return redirect(url_for('classteacher.manage_students'))

    # Set appropriate download filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d")
    download_filename = f"hillview_student_template_{template_type}_{timestamp}.{file_format}"

    return send_file(
        template_path,
        as_attachment=True,
        download_name=download_filename,
        mimetype=mimetype
    )

@classteacher_bp.route('/view_student_reports/<grade>/<stream>/<term>/<assessment_type>')
@classteacher_required
def view_student_reports(grade, stream, term, assessment_type):
    """Route for viewing a list of students with options to view their individual reports."""
    # Get the stream object
    stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of students per page
    search_query = request.args.get('search', '')

    # Get students in this stream with optional search filter
    query = Student.query.filter_by(stream_id=stream_obj.id)
    if search_query:
        query = query.filter(Student.name.ilike(f'%{search_query}%'))

    # Get paginated students
    students_pagination = query.order_by(Student.name).paginate(page=page, per_page=per_page, error_out=False)
    students = students_pagination.items

    # Get marks for each student to calculate averages
    for student in students:
        marks = Mark.query.filter_by(
            student_id=student.id,
            term_id=term_obj.id,
            assessment_type_id=assessment_type_obj.id
        ).all()

        if marks:
            total_marks = sum(mark.mark for mark in marks)
            total_possible = len(marks) * marks[0].total_marks if marks[0].total_marks else 100
            student.average = (total_marks / total_possible) * 100 if total_possible > 0 else 0
        else:
            student.average = None

    return render_template(
        'view_student_reports.html',
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        students=students,
        page=page,
        per_page=per_page,
        total_pages=students_pagination.pages,
        search_query=search_query
    )

@classteacher_bp.route('/download_individual_report/<grade>/<stream>/<term>/<assessment_type>/<student_name>')
@classteacher_required
def download_individual_report(grade, stream, term, assessment_type, student_name):
    """Route for downloading an individual student report as PDF using the same format as preview."""
    # Check if we have a cached PDF for this student
    cached_pdf = get_cached_pdf(grade, stream, term, assessment_type, f"student_{student_name.replace(' ', '_')}")
    if cached_pdf:
        return send_file(
            cached_pdf,
            as_attachment=True,
            download_name=f"Individual_Report_{grade}_{stream}_{student_name.replace(' ', '_')}.pdf",
            mimetype='application/pdf'
        )

    # If no cache or cache miss, generate the report
    stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('classteacher.dashboard'))

    student = Student.query.filter_by(name=student_name, stream_id=stream_obj.id).first()
    if not student:
        flash(f"No data available for student {student_name}.", "error")
        return redirect(url_for('classteacher.dashboard'))

    # Generate PDF using the same format as preview
    pdf_file = generate_individual_report_pdf_like_preview(
        student, grade, stream, term, assessment_type,
        stream_obj, term_obj, assessment_type_obj
    )

    if not pdf_file:
        flash(f"No marks found for {student_name} in {term} {assessment_type}", "error")
        return redirect(url_for('classteacher.view_student_reports', grade=grade, stream=stream, term=term, assessment_type=assessment_type))

    # Cache the PDF file
    with open(pdf_file, 'rb') as f:
        pdf_data = f.read()
    cache_pdf(grade, stream, term, assessment_type, f"student_{student_name.replace(' ', '_')}", pdf_data)

    # Return the PDF file
    return send_file(
        pdf_file,
        as_attachment=True,
        download_name=f"Individual_Report_{grade}_{stream}_{student_name.replace(' ', '_')}.pdf",
        mimetype='application/pdf'
    )

def generate_individual_report_pdf_like_preview(student, grade, stream, term, assessment_type, stream_obj, term_obj, assessment_type_obj):
    """Generate individual report PDF using the same format as the preview."""
    try:
        import tempfile
        import os
        from datetime import datetime
        from flask import render_template_string
        import pdfkit

        # Get education level based on grade
        education_level = ""
        grade_num = int(grade.split()[1]) if len(grade.split()) > 1 else int(grade)
        if 1 <= grade_num <= 3:
            education_level = "lower primary"
        elif 4 <= grade_num <= 6:
            education_level = "upper primary"
        elif 7 <= grade_num <= 9:
            education_level = "junior secondary"

        # Get class report data first (same as preview)
        class_data_result = get_class_report_data(grade, stream, term, assessment_type)

        if class_data_result.get("error"):
            return None

        # Find student data in the class report
        student_data = None
        for data in class_data_result["class_data"]:
            if data["student"] == student.name:
                student_data = data
                break

        if not student_data:
            return None

        # Calculate mean grade and points (same as preview)
        avg_percentage = student_data.get("average_percentage", 0)
        from ..utils import get_grade_and_points, get_performance_remarks
        mean_grade, mean_points = get_grade_and_points(avg_percentage)

        # Prepare table data for the report with composite subject handling (same as preview)
        table_data = []
        composite_data = {}

        # Get only subjects that have marks in the class report data
        subjects_with_marks = class_data_result.get("subjects", [])

        # Define subject order - core subjects first (same as preview)
        subject_order = [
            "Mathematics", "MATHEMATICS", "Math", "MATH",
            "English", "ENGLISH", "English Language", "ENGLISH LANGUAGE",
            "Kiswahili", "KISWAHILI", "Kiswahili Language", "KISWAHILI LANGUAGE",
            "Religious", "RELIGIOUS", "Religious Education", "RELIGIOUS EDUCATION", "CRE", "IRE",
            "Integrated Science", "INTEGRATED SCIENCE", "Science", "SCIENCE",
            "Social Studies", "SOCIAL STUDIES", "Social Science", "SOCIAL SCIENCE",
            "Agriculture", "AGRICULTURE", "Agricultural Science", "AGRICULTURAL SCIENCE",
            "Creative Art and Sports", "CREATIVE ART AND SPORTS", "Creative Arts", "CREATIVE ARTS"
        ]

        # Sort subjects according to the defined order (same as preview)
        ordered_subject_names = []
        for subject_name in subject_order:
            if subject_name in subjects_with_marks and subject_name not in ordered_subject_names:
                ordered_subject_names.append(subject_name)

        remaining_subject_names = [s for s in subjects_with_marks if s not in ordered_subject_names]
        remaining_subject_names.sort()
        ordered_subject_names.extend(remaining_subject_names)

        from ..models.academic import Subject, ComponentMark

        # Process subjects (same logic as preview)
        for subject_name in ordered_subject_names:
            subject = Subject.query.filter_by(name=subject_name).first()
            if not subject:
                continue
            mark = student_data.get("marks", {}).get(subject.name, 0)

            if not mark or mark == 0:
                continue

            # Clean up decimal precision
            if isinstance(mark, float):
                mark = int(round(mark)) if mark == int(mark) else round(mark, 1)
            else:
                mark = int(mark)

            # Handle composite subjects (same as preview)
            if hasattr(subject, 'is_composite') and subject.is_composite:
                components = subject.get_components()
                component_marks = {}

                mark_record = Mark.query.filter_by(
                    student_id=student.id,
                    subject_id=subject.id,
                    term_id=term_obj.id,
                    assessment_type_id=assessment_type_obj.id
                ).first()

                if mark_record:
                    for component in components:
                        component_mark = ComponentMark.query.filter_by(
                            component_id=component.id,
                            mark_id=mark_record.id
                        ).first()

                        if component_mark:
                            clean_component_name = component.name
                            if clean_component_name.startswith("L "):
                                clean_component_name = clean_component_name[2:]

                            component_max_mark = component_mark.max_raw_mark if component_mark.max_raw_mark else (component.max_raw_mark if hasattr(component, 'max_raw_mark') and component.max_raw_mark else 100)
                            component_percentage = (component_mark.raw_mark / component_max_mark) * 100

                            component_raw_mark = component_mark.raw_mark
                            if isinstance(component_raw_mark, float):
                                component_raw_mark = int(round(component_raw_mark)) if component_raw_mark == int(component_raw_mark) else round(component_raw_mark, 1)
                            else:
                                component_raw_mark = int(component_raw_mark)

                            component_marks[clean_component_name] = {
                                'mark': component_raw_mark,
                                'max_mark': int(component_max_mark),
                                'percentage': round(component_percentage, 1),
                                'remarks': get_performance_remarks(component_percentage, 100)
                            }

                composite_data[subject.name] = {
                    'components': component_marks,
                    'total': mark
                }

            # Add to table data (same logic as preview)
            entrance_mark = 0
            mid_term_mark = 0
            end_term_mark = 0

            if assessment_type.lower() in ['end_term', 'endterm']:
                all_assessment_types = AssessmentType.query.all()
                for at in all_assessment_types:
                    mark_record = Mark.query.filter_by(
                        student_id=student.id,
                        subject_id=subject.id,
                        term_id=term_obj.id,
                        assessment_type_id=at.id
                    ).first()

                    if mark_record:
                        mark_value = mark_record.percentage or 0
                        if at.name.lower() in ['entrance', 'opener']:
                            entrance_mark = mark_value
                        elif at.name.lower() in ['mid_term', 'midterm']:
                            mid_term_mark = mark_value
                        elif at.name.lower() in ['end_term', 'endterm']:
                            end_term_mark = mark_value

                available_marks = [m for m in [entrance_mark, mid_term_mark, end_term_mark] if m > 0]
                avg_mark = sum(available_marks) / len(available_marks) if available_marks else 0
            else:
                if assessment_type.lower() in ['entrance', 'opener']:
                    entrance_mark = mark
                elif assessment_type.lower() in ['mid_term', 'midterm']:
                    mid_term_mark = mark
                elif assessment_type.lower() in ['end_term', 'endterm']:
                    end_term_mark = mark
                avg_mark = mark

            table_data.append({
                "subject": subject.name,
                "entrance": entrance_mark,
                "mid_term": mid_term_mark,
                "end_term": end_term_mark,
                "current_assessment": mark,
                "avg": avg_mark,
                "remarks": get_performance_remarks(avg_mark if assessment_type.lower() in ['end_term', 'endterm'] else mark, class_data_result.get("total_marks", 100))
            })

        # Calculate totals (same as preview)
        total_marks = student_data.get("total_marks", 0)
        total_possible_marks = len(subjects_with_marks) * class_data_result.get("total_marks", 100)
        total_points = mean_points * len(subjects_with_marks)

        # Generate admission number (same as preview)
        admission_no = student.admission_number if hasattr(student, 'admission_number') and student.admission_number else f"KPS{grade}{stream[-1]}{student.id}"

        # Get academic year (same as preview)
        academic_year = term_obj.academic_year if hasattr(term_obj, 'academic_year') and term_obj.academic_year else "2023"

        # Get current date
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Read the template file
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'preview_individual_report.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Add print-specific CSS
        print_css = """
        <style>
        @page {
            size: A4;
            margin: 1cm;
        }
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        .action-buttons, .print-controls, .delete-btn, .modal {
            display: none !important;
        }
        .report-container {
            max-width: none;
            margin: 0;
            padding: 20px;
        }
        </style>
        """
        template_content = template_content.replace('</head>', f'{print_css}</head>')

        # Render the template with the same data as preview
        html_content = render_template_string(
            template_content,
            student=student,
            student_data=student_data,
            grade=grade,
            stream=stream,
            term=term,
            assessment_type=assessment_type,
            education_level=education_level,
            current_date=current_date,
            table_data=table_data,
            composite_data=composite_data,
            total=total_marks,
            avg_percentage=avg_percentage,
            mean_grade=mean_grade,
            mean_points=mean_points,
            total_possible_marks=total_possible_marks,
            total_points=total_points,
            admission_no=admission_no,
            academic_year=academic_year,
            print_mode=True
        )

        # Generate PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Individual_Report_{grade}_{stream}_{student.name.replace(' ', '_')}_{timestamp}.pdf"
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, filename)

        # Configure pdfkit options
        options = {
            'page-size': 'A4',
            'orientation': 'Portrait',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': True,
            'print-media-type': None
        }

        # Convert HTML to PDF
        pdfkit.from_string(html_content, pdf_path, options=options)
        return pdf_path

    except Exception as e:
        print(f"Error generating individual report PDF: {str(e)}")
        return None

def generate_simple_individual_report_pdf(student, grade, stream, term, assessment_type, stream_obj, term_obj, assessment_type_obj, pdf_available=False):
    """Generate individual report PDF using a simpler approach."""
    try:
        import tempfile
        import os
        from datetime import datetime

        # Get class report data first (same as preview)
        class_data_result = get_class_report_data(grade, stream, term, assessment_type)

        if class_data_result.get("error"):
            return None

        # Find student data in the class report
        student_data = None
        for data in class_data_result["class_data"]:
            if data["student"] == student.name:
                student_data = data
                break

        if not student_data:
            return None

        # Calculate mean grade and points
        avg_percentage = student_data.get("average_percentage", 0)
        from ..utils import get_grade_and_points, get_performance_remarks
        mean_grade, mean_points = get_grade_and_points(avg_percentage)

        # Get subjects with marks
        subjects_with_marks = class_data_result.get("subjects", [])

        # Calculate totals
        total_marks = student_data.get("total_marks", 0)
        total_possible_marks = len(subjects_with_marks) * class_data_result.get("total_marks", 100)
        total_points = mean_points * len(subjects_with_marks)

        # Generate admission number
        admission_no = student.admission_number if hasattr(student, 'admission_number') and student.admission_number else f"KPS{grade}{stream[-1]}{student.id}"

        # Get academic year
        academic_year = term_obj.academic_year if hasattr(term_obj, 'academic_year') and term_obj.academic_year else "2023"

        # Get current date
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Create simple HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Individual Report - {student.name}</title>
            <style>
                @page {{ size: A4; margin: 1cm; }}
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .student-info {{ margin-bottom: 20px; }}
                .marks-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                .marks-table th, .marks-table td {{ border: 1px solid #000; padding: 8px; text-align: center; }}
                .marks-table th {{ background-color: #f0f0f0; }}
                .summary {{ margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>KIRIMA PRIMARY SCHOOL</h2>
                <h3>INDIVIDUAL STUDENT REPORT</h3>
                <p>{term} - {assessment_type} - Academic Year {academic_year}</p>
            </div>

            <div class="student-info">
                <p><strong>Student Name:</strong> {student.name}</p>
                <p><strong>Admission Number:</strong> {admission_no}</p>
                <p><strong>Grade:</strong> {grade}</p>
                <p><strong>Stream:</strong> {stream}</p>
                <p><strong>Date:</strong> {current_date}</p>
            </div>

            <table class="marks-table">
                <thead>
                    <tr>
                        <th>Subject</th>
                        <th>Marks</th>
                        <th>Grade</th>
                        <th>Remarks</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Add subject marks
        for subject_name in subjects_with_marks:
            mark = student_data.get("marks", {}).get(subject_name, 0)
            if mark and mark > 0:
                # Clean up decimal precision
                if isinstance(mark, float):
                    mark = int(round(mark)) if mark == int(mark) else round(mark, 1)
                else:
                    mark = int(mark)

                grade_letter, points = get_grade_and_points(mark)
                remarks = get_performance_remarks(mark, 100)

                html_content += f"""
                    <tr>
                        <td>{subject_name}</td>
                        <td>{mark}</td>
                        <td>{grade_letter}</td>
                        <td>{remarks}</td>
                    </tr>
                """

        html_content += f"""
                </tbody>
            </table>

            <div class="summary">
                <p><strong>Total Marks:</strong> {total_marks}/{total_possible_marks}</p>
                <p><strong>Average Percentage:</strong> {avg_percentage:.1f}%</p>
                <p><strong>Mean Grade:</strong> {mean_grade}</p>
                <p><strong>Total Points:</strong> {total_points}</p>
            </div>
        </body>
        </html>
        """

        # Generate PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Individual_Report_{grade.replace(' ', '_')}_{stream}_{student.name.replace(' ', '_')}_{timestamp}.pdf"
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, filename)

        # Try to use pdfkit if available
        if pdf_available:
            try:
                import pdfkit
                options = {
                    'page-size': 'A4',
                    'orientation': 'Portrait',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': 'UTF-8',
                    'no-outline': None
                }
                pdfkit.from_string(html_content, pdf_path, options=options)
                return pdf_path
            except Exception as e:
                print(f"pdfkit failed: {e}")

        # Fallback: Create a simple text-based report
        try:
            text_content = f"""
KIRIMA PRIMARY SCHOOL
INDIVIDUAL STUDENT REPORT
{term} - {assessment_type} - Academic Year {academic_year}

Student Name: {student.name}
Admission Number: {admission_no}
Grade: {grade}
Stream: {stream}
Date: {current_date}

SUBJECT MARKS:
{'='*50}
"""

            # Add subject marks in text format
            for subject_name in subjects_with_marks:
                mark = student_data.get("marks", {}).get(subject_name, 0)
                if mark and mark > 0:
                    # Clean up decimal precision
                    if isinstance(mark, float):
                        mark = int(round(mark)) if mark == int(mark) else round(mark, 1)
                    else:
                        mark = int(mark)

                    grade_letter, points = get_grade_and_points(mark)
                    remarks = get_performance_remarks(mark, 100)

                    text_content += f"{subject_name:<30} {mark:>5} {grade_letter:>3} {remarks}\n"

            text_content += f"""
{'='*50}
SUMMARY:
Total Marks: {total_marks}/{total_possible_marks}
Average Percentage: {avg_percentage:.1f}%
Mean Grade: {mean_grade}
Total Points: {total_points}

Report generated on {current_date}
"""

            # Save as text file instead of PDF
            txt_path = pdf_path.replace('.pdf', '.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text_content)

            print(f"Created text report: {txt_path}")
            return txt_path

        except Exception as text_error:
            print(f"Text fallback also failed: {text_error}")
            return None

    except Exception as e:
        print(f"Error generating simple individual report PDF: {str(e)}")
        return None

def generate_individual_report_like_preview_for_zip(student, grade, stream, term, assessment_type, stream_obj, term_obj, assessment_type_obj, pdf_available=False):
    """Generate individual report using the exact same format as the preview template."""
    try:
        import tempfile
        import os
        from datetime import datetime
        from flask import render_template_string

        # Get class report data first (same as preview)
        class_data_result = get_class_report_data(grade, stream, term, assessment_type)

        if class_data_result.get("error"):
            return None

        # Find student data in the class report
        student_data = None
        for data in class_data_result["class_data"]:
            if data["student"] == student.name:
                student_data = data
                break

        if not student_data:
            return None

        # Get education level based on grade (same as preview)
        education_level = ""
        grade_num = int(grade.split()[1]) if len(grade.split()) > 1 else int(grade)
        if 1 <= grade_num <= 3:
            education_level = "lower primary"
        elif 4 <= grade_num <= 6:
            education_level = "upper primary"
        elif 7 <= grade_num <= 9:
            education_level = "junior secondary"

        # Calculate mean grade and points (same as preview)
        avg_percentage = student_data.get("average_percentage", 0)
        from ..utils import get_grade_and_points, get_performance_remarks
        mean_grade, mean_points = get_grade_and_points(avg_percentage)

        # Prepare table data for the report with composite subject handling (same as preview)
        table_data = []
        composite_data = {}

        # Get only subjects that have marks in the class report data
        subjects_with_marks = class_data_result.get("subjects", [])

        for subject_name in subjects_with_marks:
            mark = student_data.get("marks", {}).get(subject_name, 0)
            if mark and mark > 0:
                # Clean up decimal precision
                if isinstance(mark, float):
                    mark = int(round(mark)) if mark == int(mark) else round(mark, 1)
                else:
                    mark = int(mark)

                grade_letter, points = get_grade_and_points(mark)
                remarks = get_performance_remarks(mark, 100)

                # Create table row data (same structure as preview)
                row_data = {
                    'subject': subject_name.upper(),
                    'entrance': 0,  # Not used for single assessments
                    'mid_term': 0,  # Not used for single assessments
                    'end_term': mark if assessment_type.lower() in ['end_term', 'endterm'] else 0,
                    'current_assessment': mark,
                    'avg': mark,
                    'remarks': remarks
                }
                table_data.append(row_data)

        # Calculate totals (same as preview)
        total_marks = student_data.get("total_marks", 0)
        total_possible_marks = len(subjects_with_marks) * class_data_result.get("total_marks", 100)
        total_points = mean_points * len(subjects_with_marks)

        # Generate admission number (same as preview)
        admission_no = student.admission_number if hasattr(student, 'admission_number') and student.admission_number else f"KPS{grade}{stream[-1]}{student.id}"

        # Get academic year (same as preview)
        academic_year = term_obj.academic_year if hasattr(term_obj, 'academic_year') and term_obj.academic_year else "2023"

        # Get current date
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Read the template file and render it (same as preview)
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'preview_individual_report.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Render the template with the same data as preview
        rendered_html = render_template_string(
            template_content,
            student=student,
            student_data=student_data,
            grade=grade,
            stream=stream,
            term=term,
            assessment_type=assessment_type,
            education_level=education_level,
            current_date=current_date,
            table_data=table_data,
            composite_data=composite_data,
            total=total_marks,
            avg_percentage=avg_percentage,
            mean_grade=mean_grade,
            mean_points=mean_points,
            total_possible_marks=total_possible_marks,
            total_points=total_points,
            admission_no=admission_no,
            academic_year=academic_year,
            print_mode=True  # Enable print mode for clean output
        )

        # Generate file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = tempfile.gettempdir()

        if pdf_available:
            # Try to generate PDF
            try:
                import pdfkit
                filename = f"Individual_Report_{grade.replace(' ', '_')}_{stream}_{student.name.replace(' ', '_')}_{timestamp}.pdf"
                pdf_path = os.path.join(temp_dir, filename)

                # Add print-specific CSS for PDF
                print_css = """
                <style>
                @page { size: A4; margin: 1cm; }
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
                .action-buttons, .print-controls, .delete-btn, .modal { display: none !important; }
                .report-container { max-width: none; margin: 0; padding: 20px; }
                </style>
                """
                html_with_css = rendered_html.replace('</head>', f'{print_css}</head>')

                options = {
                    'page-size': 'A4',
                    'orientation': 'Portrait',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': 'UTF-8',
                    'no-outline': None
                }
                pdfkit.from_string(html_with_css, pdf_path, options=options)
                return pdf_path
            except Exception as e:
                print(f"PDF generation failed: {e}")
                # Fall through to HTML generation

        # Generate HTML file as fallback
        filename = f"Individual_Report_{grade.replace(' ', '_')}_{stream}_{student.name.replace(' ', '_')}_{timestamp}.html"
        html_path = os.path.join(temp_dir, filename)

        # Add some basic styling for standalone HTML
        standalone_css = """
        <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .action-buttons, .print-controls, .delete-btn, .modal { display: none !important; }
        .report-container { max-width: 800px; margin: 0 auto; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        th { background-color: #f2f2f2; }
        .header { text-align: center; margin-bottom: 20px; }
        .student-details { margin: 20px 0; }
        .remarks { margin: 20px 0; }
        .footer { margin-top: 20px; text-align: center; font-size: 12px; color: #666; }
        </style>
        """
        html_with_css = rendered_html.replace('</head>', f'{standalone_css}</head>')

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_with_css)

        print(f"Created HTML report: {html_path}")
        return html_path

    except Exception as e:
        print(f"Error generating individual report like preview: {str(e)}")
        return None

@classteacher_bp.route('/generate_all_individual_reports/<grade>/<stream>/<term>/<assessment_type>')
@classteacher_required
def generate_all_individual_reports(grade, stream, term, assessment_type):
    """Route for generating and downloading all individual reports as a ZIP file using the same format as preview."""
    try:
        print(f"🚀 Starting ZIP generation for {grade} {stream} {term} {assessment_type}")

        stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream[-1]).first()
        term_obj = Term.query.filter_by(name=term).first()
        assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

        if not (stream_obj and term_obj and assessment_type_obj):
            flash("Invalid grade, stream, term, or assessment type", "error")
            return redirect(url_for('classteacher.dashboard'))

        # Get students in this stream
        students = Student.query.filter_by(stream_id=stream_obj.id).all()
        print(f"📊 Found {len(students)} students in {grade} Stream {stream[-1]}")

        if not students:
            flash(f"No students found for {grade} Stream {stream[-1]}", "error")
            return redirect(url_for('classteacher.dashboard'))

        # Check if we can generate PDFs (optional - will fallback to text if not available)
        pdf_available = False
        try:
            import pdfkit
            import os
            # Test if wkhtmltopdf is working
            test_html = "<html><body><h1>Test</h1></body></html>"
            temp_test_file = os.path.join(tempfile.gettempdir(), "wkhtmltopdf_test.pdf")
            pdfkit.from_string(test_html, temp_test_file, options={'page-size': 'A4'})
            if os.path.exists(temp_test_file):
                os.remove(temp_test_file)
                pdf_available = True
                print("✅ PDF generation available")
            else:
                print("⚠️ wkhtmltopdf not working, will use text fallback")
        except Exception as e:
            print(f"⚠️ PDF generation not available: {e}, will use text fallback")

        # Import necessary modules
        import zipfile
        import tempfile
        import os
        from datetime import datetime

        # Create a temporary directory to store the PDFs
        temp_dir = tempfile.mkdtemp()
        print(f"📁 Created temp directory: {temp_dir}")

        # Create a ZIP file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"Individual_Reports_{grade.replace(' ', '_')}_{stream}_{term}_{assessment_type}_{timestamp}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        print(f"📦 Creating ZIP file: {zip_filename}")

        # Generate PDFs for each student and add them to the ZIP file
        successful_reports = 0
        failed_reports = 0

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for i, student in enumerate(students, 1):
                try:
                    print(f"📄 Processing student {i}/{len(students)}: {student.name}")

                    # Use the same format as preview - generate report file (PDF or HTML)
                    report_file = generate_individual_report_like_preview_for_zip(
                        student, grade, stream, term, assessment_type,
                        stream_obj, term_obj, assessment_type_obj, pdf_available
                    )

                    if report_file and os.path.exists(report_file):
                        # Determine file extension from the actual file
                        file_extension = os.path.splitext(report_file)[1]  # Gets .pdf, .html, or .txt
                        report_filename = f"Individual_Report_{grade.replace(' ', '_')}_{stream}_{student.name.replace(' ', '_')}{file_extension}"
                        zipf.write(report_file, report_filename)
                        successful_reports += 1
                        print(f"✅ Generated report for {student.name}")

                        # Clean up individual report file
                        try:
                            os.remove(report_file)
                        except:
                            pass
                    else:
                        failed_reports += 1
                        print(f"⚠️ No report generated for {student.name} (no marks found)")

                except Exception as e:
                    failed_reports += 1
                    print(f"❌ Error generating report for {student.name}: {str(e)}")
                    continue

        print(f"📊 Generation complete: {successful_reports} successful, {failed_reports} failed")

        if successful_reports == 0:
            flash(f"No reports could be generated. Please ensure students have marks for {term} {assessment_type}.", "error")
            return redirect(url_for('classteacher.dashboard'))

        flash(f"Successfully generated {successful_reports} individual reports in ZIP format!", "success")

        # Return the ZIP file
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )

    except Exception as e:
        print(f"💥 Critical error in ZIP generation: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Error generating reports: {str(e)}", "error")
        return redirect(url_for('classteacher.dashboard'))

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
        filename = f"Class_List_{grade.name if grade else 'Unknown'}_{stream.name if stream else 'Unknown'}.csv"

    # Filter by grade if specified (and not already filtered by stream)
    elif grade_id:
        grade = Grade.query.get(grade_id)
        # Get all streams for this grade
        grade_streams = Stream.query.filter_by(grade_id=grade_id).all()
        stream_ids = [s.id for s in grade_streams]
        if stream_ids:
            students_query = students_query.filter(Student.stream_id.in_(stream_ids))
        filename = f"Class_List_{grade.name if grade else 'Unknown'}_All_Streams.csv"

    # Filter by educational level if specified
    elif educational_level:
        # Get all grades for this educational level
        allowed_grades = educational_level_mapping.get(educational_level, [])
        grades = Grade.query.filter(Grade.name.in_(allowed_grades)).all()
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
        grade_name = student.stream.grade.name if student.stream else "N/A"
        stream_name = student.stream.name if student.stream else "No Stream"
        gender = student.gender.capitalize() if student.gender else "Not Set"

        csv_data += f"{student.id},{student.name},{student.admission_number},{grade_name},{stream_name},{gender}\n"

    # Create a response with the CSV data
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-Type"] = "text/csv"

    return response



@classteacher_bp.route('/download_subject_template', methods=['GET'])
@classteacher_required
def download_subject_template():
    """Route to download the subject upload template."""
    file_format = request.args.get('format', 'xlsx')

    if file_format == 'csv':
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'templates', 'subject_upload_template.csv')
        mimetype = 'text/csv'
        filename = 'subject_upload_template.csv'
    else:
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'templates', 'subject_upload_template.xlsx')
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = 'subject_upload_template.xlsx'

    # Check if the template file exists
    if not os.path.exists(template_path):
        # If not, create it
        try:
            from ..static.templates.subject_upload_template import create_subject_upload_template
            create_subject_upload_template()
        except Exception as e:
            print(f"Error creating template: {str(e)}")
            flash("Error creating template file. Please try again.", "error")
            return redirect(url_for('classteacher.manage_subjects'))

    return send_file(
        template_path,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )

@classteacher_bp.route('/export_subjects', methods=['GET'])
@classteacher_required
def export_subjects():
    """Route to export all subjects as CSV or Excel."""
    file_format = request.args.get('format', 'xlsx')
    education_level = request.args.get('education_level', '')

    # Build the query based on filters
    subjects_query = Subject.query

    # Apply education level filter if specified
    if education_level and education_level != 'all':
        subjects_query = subjects_query.filter_by(education_level=education_level)
        filename_prefix = f"subjects_{education_level}"
    else:
        filename_prefix = "all_subjects"

    # Order by education level and name
    subjects = subjects_query.order_by(Subject.education_level, Subject.name).all()

    # Create a DataFrame with the subjects
    data = []
    for subject in subjects:
        data.append({
            'id': subject.id,
            'name': subject.name,
            'education_level': subject.education_level
        })

    df = pd.DataFrame(data)

    # Create a BytesIO object to store the Excel file
    output = BytesIO()

    if file_format == 'csv':
        # Write the DataFrame to a CSV file
        df.to_csv(output, index=False)
        mimetype = 'text/csv'
        filename = f"{filename_prefix}.csv"
    else:
        # Write the DataFrame to an Excel file
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Subjects', index=False)

            # Get the xlsxwriter workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Subjects']

            # Add some formatting
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })

            # Write the column headers with the defined format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Set the column widths
            worksheet.set_column('A:A', 5)  # ID column
            worksheet.set_column('B:B', 30)  # Name column
            worksheet.set_column('C:C', 20)  # Education level column

        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = f"{filename_prefix}.xlsx"

    # Seek to the beginning of the BytesIO object
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )

@classteacher_bp.route('/bulk_import_subjects', methods=['POST'])
@classteacher_required
def bulk_import_subjects():
    """Route for bulk importing subjects."""
    if 'subject_file' not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for('classteacher.manage_subjects'))

    file = request.files['subject_file']

    if file.filename == '':
        flash("No file selected.", "error")
        return redirect(url_for('classteacher.manage_subjects'))

    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()

    try:
        # Read the file into a pandas DataFrame
        if file_ext == '.csv':
            df = pd.read_csv(file)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file)
        else:
            flash("Unsupported file format. Please upload a CSV or Excel file.", "error")
            return redirect(url_for('classteacher.manage_subjects'))

        # Check if the required columns are present
        required_columns = ['name', 'education_level']
        for col in required_columns:
            if col not in df.columns:
                flash(f"Missing required column: {col}", "error")
                return redirect(url_for('classteacher.manage_subjects'))

        # Process the subjects
        added_count = 0
        skipped_count = 0

        for _, row in df.iterrows():
            subject_name = row['name'].strip()
            education_level = row['education_level'].strip()

            # Validate education level
            if education_level not in ['lower_primary', 'upper_primary', 'junior_secondary']:
                skipped_count += 1
                continue

            # Check if subject already exists
            existing_subject = Subject.query.filter_by(name=subject_name, education_level=education_level).first()
            if existing_subject:
                skipped_count += 1
                continue

            # Add the new subject
            new_subject = Subject(name=subject_name, education_level=education_level)
            db.session.add(new_subject)
            added_count += 1

        # Commit the changes
        db.session.commit()

        if added_count > 0:
            flash(f"Successfully added {added_count} new subject(s). {skipped_count} subject(s) were skipped because they already exist or had invalid data.", "success")
        else:
            flash(f"No new subjects were added. {skipped_count} subject(s) were skipped because they already exist or had invalid data.", "info")

        return redirect(url_for('classteacher.manage_subjects'))

    except Exception as e:
        flash(f"Error processing file: {str(e)}", "error")
        return redirect(url_for('classteacher.manage_subjects'))

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

    # Calculate statistics
    total_subjects = Subject.query.count()
    lower_primary_count = Subject.query.filter_by(education_level='lower_primary').count()
    upper_primary_count = Subject.query.filter_by(education_level='upper_primary').count()
    junior_secondary_count = Subject.query.filter_by(education_level='junior_secondary').count()

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
                # Clean and validate subject name
                subject_name = subject_name.strip()
                if not subject_name:
                    error_message = "Subject name cannot be empty."
                else:
                    try:
                        # Check if subject with same name and education level already exists
                        existing_subject = Subject.query.filter_by(name=subject_name, education_level=education_level).first()
                        if existing_subject:
                            error_message = f"Subject '{subject_name}' already exists for {education_level.replace('_', ' ').title()}."
                        else:
                            new_subject = Subject(name=subject_name, education_level=education_level)
                            db.session.add(new_subject)
                            db.session.commit()
                            success_message = f"Subject '{subject_name}' added successfully for {education_level.replace('_', ' ').title()}!"
                    except Exception as e:
                        db.session.rollback()
                        if "UNIQUE constraint failed" in str(e):
                            error_message = f"Subject '{subject_name}' already exists. Please choose a different name."
                        else:
                            error_message = f"Error adding subject: {str(e)}"
                        print(f"Subject creation error: {e}")

        elif "delete_subject" in request.form:
            subject_id = request.form.get("subject_id")
            subject = Subject.query.get(subject_id)
            if subject:
                try:
                    # Check if subject has marks
                    marks = Mark.query.filter_by(subject_id=subject.id).all()
                    if marks:
                        error_message = f"Cannot delete subject '{subject.name}' because it has marks associated with it."
                    else:
                        # Clean up related data before deletion
                        cleanup_count = 0

                        # 1. Remove teacher-subject assignments
                        try:
                            from ..models.assignment import TeacherSubjectAssignment
                            assignments = TeacherSubjectAssignment.query.filter_by(subject_id=subject.id).all()
                            for assignment in assignments:
                                db.session.delete(assignment)
                                cleanup_count += 1
                        except Exception as cleanup_error:
                            print(f"Warning: Could not clean up assignments for subject {subject.id}: {cleanup_error}")

                        # 2. Remove subject components (if table exists)
                        try:
                            from ..models.academic import SubjectComponent
                            components = SubjectComponent.query.filter_by(subject_id=subject.id).all()
                            for component in components:
                                # Remove component marks first
                                try:
                                    from ..models.academic import ComponentMark
                                    component_marks = ComponentMark.query.filter_by(component_id=component.id).all()
                                    for mark in component_marks:
                                        db.session.delete(mark)
                                        cleanup_count += 1
                                except Exception as component_mark_error:
                                    print(f"Warning: Could not clean up component marks for component {component.id}: {component_mark_error}")

                                db.session.delete(component)
                                cleanup_count += 1
                        except Exception as component_error:
                            print(f"Warning: Could not clean up components for subject {subject.id}: {component_error}")

                        # 3. Remove teacher-subject relationships (many-to-many)
                        try:
                            # Clear the many-to-many relationship
                            subject.teachers.clear()
                            cleanup_count += len(subject.teachers)
                        except Exception as teacher_rel_error:
                            print(f"Warning: Could not clear teacher relationships for subject {subject.id}: {teacher_rel_error}")

                        if cleanup_count > 0:
                            print(f"Cleaned up {cleanup_count} related records for subject {subject.id}")

                        # Store subject name before deletion
                        subject_name = subject.name
                        db.session.delete(subject)
                        db.session.commit()
                        success_message = f"Subject '{subject_name}' deleted successfully!"

                except Exception as e:
                    db.session.rollback()
                    error_message = f"Error deleting subject: {str(e)}"
                    print(f"Subject deletion error: {e}")
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

                try:
                    for subject_id in subject_ids:
                        subject = Subject.query.get(subject_id)
                        if subject:
                            # Check if subject has marks
                            marks = Mark.query.filter_by(subject_id=subject.id).all()
                            if marks:
                                not_deleted_count += 1
                            else:
                                # Clean up related data before deletion
                                try:
                                    # Remove teacher-subject assignments
                                    from ..models.assignment import TeacherSubjectAssignment
                                    assignments = TeacherSubjectAssignment.query.filter_by(subject_id=subject.id).all()
                                    for assignment in assignments:
                                        db.session.delete(assignment)

                                    # Remove subject components
                                    try:
                                        from ..models.academic import SubjectComponent
                                        components = SubjectComponent.query.filter_by(subject_id=subject.id).all()
                                        for component in components:
                                            # Remove component marks first
                                            try:
                                                from ..models.academic import ComponentMark
                                                component_marks = ComponentMark.query.filter_by(component_id=component.id).all()
                                                for mark in component_marks:
                                                    db.session.delete(mark)
                                            except Exception:
                                                pass  # Component marks table might not exist
                                            db.session.delete(component)
                                    except Exception:
                                        pass  # Component table might not exist

                                    # Clear teacher relationships
                                    try:
                                        subject.teachers.clear()
                                    except Exception:
                                        pass  # Relationship might not work if tables missing

                                except Exception as cleanup_error:
                                    print(f"Warning: Could not clean up data for subject {subject.id}: {cleanup_error}")

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

                except Exception as e:
                    db.session.rollback()
                    error_message = f"Error during bulk deletion: {str(e)}"
                    print(f"Bulk subject deletion error: {e}")

    # Mark newly added subjects
    for subject in subjects:
        subject.is_new = False
        if request.args.get('highlight') and int(request.args.get('highlight')) == 1:
            if 'new_subject_ids' in session:
                if subject.id in session['new_subject_ids']:
                    subject.is_new = True

    # Clear session data after use
    if 'new_subject_ids' in session:
        session.pop('new_subject_ids')

    return render_template(
        'manage_subjects.html',
        subjects=subjects,
        pagination=pagination,
        education_levels=education_levels,
        current_education_level=education_level,
        search_query=search_query,
        total_subjects=total_subjects,
        lower_primary_count=lower_primary_count,
        upper_primary_count=upper_primary_count,
        junior_secondary_count=junior_secondary_count,
        error_message=error_message,
        success_message=success_message
    )

@classteacher_bp.route('/manage_grades_streams', methods=['GET', 'POST'])
@classteacher_required
def manage_grades_streams():
    """Route for managing grades and streams."""
    error_message = None
    success_message = None
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of grades per page

    if request.method == 'POST':
        if "add_grade" in request.form:
            grade_level = request.form.get("grade_level")
            if grade_level:
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

                    new_grade = Grade(name=grade_level, education_level=education_level)
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
                        error_message = f"Stream '{stream_name}' already exists for Grade {grade.name}."
                    else:
                        new_stream = Stream(name=stream_name, grade_id=grade_id)
                        db.session.add(new_stream)
                        db.session.commit()
                        success_message = f"Stream '{stream_name}' added to Grade {grade.name} successfully!"
            else:
                error_message = "Please fill in all fields."

        elif "delete_grade" in request.form:
            grade_id = request.form.get("grade_id")
            grade = Grade.query.get(grade_id)
            if grade:
                try:
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

                            # Clean up permissions and assignments for this stream
                            try:
                                from ..models.permission import ClassTeacherPermission
                                from ..models.function_permission import FunctionPermission
                                from ..models.assignment import TeacherSubjectAssignment

                                # Remove permissions for this stream
                                class_permissions = ClassTeacherPermission.query.filter_by(stream_id=stream.id).all()
                                for permission in class_permissions:
                                    db.session.delete(permission)

                                function_permissions = FunctionPermission.query.filter_by(stream_id=stream.id).all()
                                for permission in function_permissions:
                                    db.session.delete(permission)

                                # Remove assignments for this stream
                                assignments = TeacherSubjectAssignment.query.filter_by(stream_id=stream.id).all()
                                for assignment in assignments:
                                    db.session.delete(assignment)

                            except Exception as cleanup_error:
                                print(f"Warning: Could not clean up data for stream {stream.id}: {cleanup_error}")

                            # Delete the stream
                            db.session.delete(stream)

                    # Clean up grade-level permissions and assignments
                    try:
                        from ..models.permission import ClassTeacherPermission
                        from ..models.function_permission import FunctionPermission
                        from ..models.assignment import TeacherSubjectAssignment

                        # Remove grade-level permissions
                        grade_class_permissions = ClassTeacherPermission.query.filter_by(grade_id=grade.id).all()
                        for permission in grade_class_permissions:
                            db.session.delete(permission)

                        grade_function_permissions = FunctionPermission.query.filter_by(grade_id=grade.id).all()
                        for permission in grade_function_permissions:
                            db.session.delete(permission)

                        # Remove grade-level assignments
                        grade_assignments = TeacherSubjectAssignment.query.filter_by(grade_id=grade.id).all()
                        for assignment in grade_assignments:
                            db.session.delete(assignment)

                    except Exception as grade_cleanup_error:
                        print(f"Warning: Could not clean up grade-level data for grade {grade.id}: {grade_cleanup_error}")

                    # Now delete the grade
                    grade_name = grade.name
                    db.session.delete(grade)
                    db.session.commit()
                    success_message = f"Grade '{grade_name}' and all its streams deleted successfully!"

                except Exception as e:
                    db.session.rollback()
                    error_message = f"Error deleting grade: {str(e)}"
                    print(f"Grade deletion error: {e}")
            else:
                error_message = "Grade not found."

        elif "delete_stream" in request.form:
            stream_id = request.form.get("stream_id")
            stream = Stream.query.get(stream_id)
            if stream:
                try:
                    # Check if stream has students
                    students = Student.query.filter_by(stream_id=stream.id).all()
                    if students:
                        # Unassign all students from this stream
                        for student in students:
                            student.stream_id = None

                    # Check and clean up related permissions (if tables exist)
                    permissions_cleaned = 0
                    try:
                        from ..models.permission import ClassTeacherPermission
                        from ..models.function_permission import FunctionPermission

                        # Remove class teacher permissions for this stream
                        class_permissions = ClassTeacherPermission.query.filter_by(stream_id=stream.id).all()
                        for permission in class_permissions:
                            db.session.delete(permission)
                            permissions_cleaned += 1

                        # Remove function permissions for this stream
                        function_permissions = FunctionPermission.query.filter_by(stream_id=stream.id).all()
                        for permission in function_permissions:
                            db.session.delete(permission)
                            permissions_cleaned += 1

                        if permissions_cleaned > 0:
                            print(f"Cleaned up {permissions_cleaned} permissions for stream {stream.id}")

                    except Exception as perm_error:
                        # Permission tables might not exist or have issues, continue anyway
                        print(f"Warning: Could not clean up permissions for stream {stream.id}: {perm_error}")

                    # Check and clean up teacher assignments
                    try:
                        from ..models.assignment import TeacherSubjectAssignment
                        assignments = TeacherSubjectAssignment.query.filter_by(stream_id=stream.id).all()
                        for assignment in assignments:
                            db.session.delete(assignment)
                    except Exception as assign_error:
                        print(f"Warning: Could not clean up assignments for stream {stream.id}: {assign_error}")

                    # Delete the stream
                    stream_name = stream.name
                    grade_name = stream.grade.name if stream.grade else "Unknown"
                    db.session.delete(stream)
                    db.session.commit()
                    success_message = f"Stream '{stream_name}' from Grade {grade_name} deleted successfully!"

                except Exception as e:
                    db.session.rollback()
                    error_message = f"Error deleting stream: {str(e)}"
                    print(f"Stream deletion error: {e}")
            else:
                error_message = "Stream not found."

    # Get all grades with pagination
    grades_query = Grade.query
    grades_page = grades_query.paginate(page=page, per_page=per_page, error_out=False)

    # Get all grades for the form dropdowns (no pagination)
    all_grades = Grade.query.all()

    # Calculate statistics
    total_grades = Grade.query.count()
    total_streams = Stream.query.count()
    avg_streams_per_grade = total_streams / total_grades if total_grades > 0 else 0
    total_students = Student.query.count()

    # Add education level to each grade
    for grade in grades_page.items:
        grade_num = 0
        try:
            # Extract grade number
            if grade.name.startswith("Grade "):
                grade_num = int(grade.name[6:])
            else:
                # Try to extract just the number
                grade_num = int(''.join(filter(str.isdigit, grade.name)))

            # Assign education level
            if 1 <= grade_num <= 3:
                grade.education_level = "lower_primary"
            elif 4 <= grade_num <= 6:
                grade.education_level = "upper_primary"
            elif 7 <= grade_num <= 9:
                grade.education_level = "junior_secondary"
            else:
                grade.education_level = "unknown"
        except:
            grade.education_level = "unknown"

    return render_template(
        "manage_grades_streams.html",
        grades=all_grades,
        grades_page=grades_page,
        total_grades=total_grades,
        total_streams=total_streams,
        avg_streams_per_grade=avg_streams_per_grade,
        total_students=total_students,
        error_message=error_message,
        success_message=success_message
    )

@classteacher_bp.route('/edit_grade', methods=['POST'])
@classteacher_required
def edit_grade():
    """Route for editing a grade."""
    grade_id = request.form.get("grade_id")
    grade_level = request.form.get("grade_level")

    if not grade_id or not grade_level:
        flash("Missing required information.", "error")
        return redirect(url_for('classteacher.manage_grades_streams'))

    grade = Grade.query.get(grade_id)
    if not grade:
        flash("Grade not found.", "error")
        return redirect(url_for('classteacher.manage_grades_streams'))

    # Check if another grade with this level already exists
    existing = Grade.query.filter(Grade.name == grade_level, Grade.id != grade_id).first()
    if existing:
        flash(f"Grade '{grade_level}' already exists.", "error")
        return redirect(url_for('classteacher.manage_grades_streams'))

    old_level = grade.name
    grade.name = grade_level
    db.session.commit()

    flash(f"Grade updated from '{old_level}' to '{grade_level}'.", "success")
    return redirect(url_for('classteacher.manage_grades_streams'))

@classteacher_bp.route('/edit_stream', methods=['POST'])
@classteacher_required
def edit_stream():
    """Route for editing a stream."""
    stream_id = request.form.get("stream_id")
    stream_name = request.form.get("stream_name")
    grade_id = request.form.get("grade_id")

    if not stream_id or not stream_name or not grade_id:
        flash("Missing required information.", "error")
        return redirect(url_for('classteacher.manage_grades_streams'))

    stream = Stream.query.get(stream_id)
    if not stream:
        flash("Stream not found.", "error")
        return redirect(url_for('classteacher.manage_grades_streams'))

    grade = Grade.query.get(grade_id)
    if not grade:
        flash("Grade not found.", "error")
        return redirect(url_for('classteacher.manage_grades_streams'))

    # Check if another stream with this name already exists in the selected grade
    existing = Stream.query.filter(Stream.name == stream_name, Stream.grade_id == grade_id, Stream.id != stream_id).first()
    if existing:
        flash(f"Stream '{stream_name}' already exists for Grade {grade.name}.", "error")
        return redirect(url_for('classteacher.manage_grades_streams'))

    old_name = stream.name
    old_grade = Grade.query.get(stream.grade_id)

    stream.name = stream_name
    stream.grade_id = grade_id
    db.session.commit()

    flash(f"Stream updated from '{old_name}' in {old_grade.name} to '{stream_name}' in {grade.name}.", "success")
    return redirect(url_for('classteacher.manage_grades_streams'))

def cleanup_duplicate_assignments():
    """Utility function to remove duplicate teacher assignments."""
    try:
        from ..models.assignment import TeacherSubjectAssignment
        from ..extensions import db

        # Find and remove duplicate class teacher assignments
        # Group by teacher_id, grade_id, stream_id, is_class_teacher
        duplicates = db.session.query(TeacherSubjectAssignment).filter_by(is_class_teacher=True).all()

        seen_combinations = set()
        to_delete = []

        for assignment in duplicates:
            combination_key = (assignment.teacher_id, assignment.grade_id, assignment.stream_id, assignment.is_class_teacher)

            if combination_key in seen_combinations:
                to_delete.append(assignment)
            else:
                seen_combinations.add(combination_key)

        # Delete duplicates
        for assignment in to_delete:
            db.session.delete(assignment)

        # Find and remove duplicate subject assignments
        subject_duplicates = db.session.query(TeacherSubjectAssignment).filter_by(is_class_teacher=False).all()

        seen_subject_combinations = set()
        subject_to_delete = []

        for assignment in subject_duplicates:
            subject_combination_key = (assignment.teacher_id, assignment.subject_id, assignment.grade_id, assignment.stream_id)

            if subject_combination_key in seen_subject_combinations:
                subject_to_delete.append(assignment)
            else:
                seen_subject_combinations.add(subject_combination_key)

        # Delete subject duplicates
        for assignment in subject_to_delete:
            db.session.delete(assignment)

        db.session.commit()

        total_deleted = len(to_delete) + len(subject_to_delete)
        print(f"Cleaned up {total_deleted} duplicate assignments")
        return total_deleted

    except Exception as e:
        print(f"Error cleaning up duplicates: {str(e)}")
        db.session.rollback()
        return 0

@classteacher_bp.route('/manage_teacher_assignments', methods=['GET', 'POST'])
@classteacher_required
def manage_teacher_assignments():
    """Route for managing teacher assignments, transfers, and reassignments."""
    error_message = None
    success_message = None

    # Clean up any duplicate assignments first
    try:
        duplicates_removed = cleanup_duplicate_assignments()
        if duplicates_removed > 0:
            print(f"Cleaned up {duplicates_removed} duplicate assignments")
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

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

        # Only show class teacher assignments for the current teacher
        # This ensures a teacher only sees their own class teacher assignments
        assignments = TeacherSubjectAssignment.query.filter_by(
            teacher_id=current_teacher_id,
            is_class_teacher=True
        ).all()

        # Use a set to track unique grade-stream combinations to avoid duplicates
        seen_combinations = set()

        for assignment in assignments:
            teacher = Teacher.query.get(assignment.teacher_id)
            grade = Grade.query.get(assignment.grade_id)
            stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

            # Create a unique key for this grade-stream combination
            combination_key = (assignment.grade_id, assignment.stream_id)

            # Skip if we've already seen this combination
            if combination_key in seen_combinations:
                continue

            seen_combinations.add(combination_key)

            # Determine education level based on grade
            education_level = ""
            grade_num = 0
            try:
                # Extract grade number
                if grade.name.startswith("Grade "):
                    grade_num = int(grade.name[6:])
                else:
                    # Try to extract just the number
                    grade_num = int(''.join(filter(str.isdigit, grade.name)))

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
                "grade_level": grade.name if grade else "Unknown",
                "stream_id": assignment.stream_id,
                "stream_name": stream.name if stream else None,
                "education_level": education_level
            })
    except Exception as e:
        print(f"Error fetching class teacher assignments: {str(e)}")

    # Get all subject assignments
    subject_assignments = []
    try:
        # Only show subject assignments for the current teacher
        # This ensures a teacher only sees their own subject assignments
        assignments = TeacherSubjectAssignment.query.filter_by(
            teacher_id=current_teacher_id,
            is_class_teacher=False
        ).all()

        # Use a set to track unique subject-grade-stream combinations to avoid duplicates
        seen_subject_combinations = set()

        for assignment in assignments:
            teacher = Teacher.query.get(assignment.teacher_id)
            subject = Subject.query.get(assignment.subject_id)
            grade = Grade.query.get(assignment.grade_id)
            stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

            # Create a unique key for this subject-grade-stream combination
            subject_combination_key = (assignment.subject_id, assignment.grade_id, assignment.stream_id)

            # Skip if we've already seen this combination
            if subject_combination_key in seen_subject_combinations:
                continue

            seen_subject_combinations.add(subject_combination_key)

            subject_assignments.append({
                "id": assignment.id,
                "teacher_id": assignment.teacher_id,
                "teacher_username": teacher.username if teacher else "Unknown",
                "subject_id": assignment.subject_id,
                "subject_name": subject.name if subject else "Unknown",
                "grade_id": assignment.grade_id,
                "grade_level": grade.name if grade else "Unknown",
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

        flash(f"Class teacher for Grade {grade.name}{stream_text} changed from {old_teacher.username} to {new_teacher.username}.", "success")
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

        flash(f"Teacher for {subject.name} in Grade {grade.name}{stream_text} changed from {old_teacher.username} to {new_teacher.username}.", "success")
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

@classteacher_bp.route('/add_term_ajax', methods=['POST'])
@classteacher_required
def add_term_ajax():
    """AJAX route for adding a new term."""
    term_name = request.form.get("term_name")
    term_start_date = request.form.get("term_start_date")
    term_end_date = request.form.get("term_end_date")
    academic_year = request.form.get("academic_year")
    is_current_term = "is_current_term" in request.form

    if not term_name:
        return jsonify({"success": False, "message": "Please fill in the term name."})

    existing_term = Term.query.filter_by(name=term_name).first()
    if existing_term:
        return jsonify({"success": False, "message": f"Term '{term_name}' already exists."})

    # Create new term with additional fields if they exist in the model
    new_term = Term(name=term_name)

    # Add additional fields if they exist in the model
    if hasattr(Term, 'start_date') and term_start_date:
        new_term.start_date = term_start_date

    if hasattr(Term, 'end_date') and term_end_date:
        new_term.end_date = term_end_date

    if hasattr(Term, 'academic_year') and academic_year:
        new_term.academic_year = academic_year

    if hasattr(Term, 'is_current'):
        # If setting this term as current, unset any other current terms
        if is_current_term:
            current_terms = Term.query.filter_by(is_current=True).all()
            for term in current_terms:
                term.is_current = False
            new_term.is_current = True

    db.session.add(new_term)
    db.session.commit()

    # Get updated statistics
    terms = Term.query.all()
    assessment_types = AssessmentType.query.all()
    current_term = "None"

    # Find the current term if any
    for term in terms:
        if hasattr(term, 'is_current') and term.is_current:
            current_term = term.name
            break

    # Prepare term data for JSON response
    term_data = {
        "id": new_term.id,
        "name": new_term.name,
        "is_current": True if hasattr(new_term, 'is_current') and new_term.is_current else False,
        "academic_year": new_term.academic_year if hasattr(new_term, 'academic_year') and new_term.academic_year else None
    }

    # Find the current academic year
    current_academic_year = "None"
    for t in terms:
        if hasattr(t, 'is_current') and t.is_current and hasattr(t, 'academic_year') and t.academic_year:
            current_academic_year = t.academic_year
            break

    # If no current term has an academic year, try to get the academic year from any term
    if current_academic_year == "None":
        for t in terms:
            if hasattr(t, 'academic_year') and t.academic_year:
                current_academic_year = t.academic_year
                break

    # Prepare statistics for JSON response
    stats = {
        "total_terms": len(terms),
        "total_assessments": len(assessment_types),
        "current_term": current_term,
        "current_academic_year": current_academic_year
    }

    return jsonify({
        "success": True,
        "message": f"Term '{term_name}' added successfully!",
        "term": term_data,
        "stats": stats
    })

@classteacher_bp.route('/delete_term_ajax', methods=['POST'])
@classteacher_required
def delete_term_ajax():
    """AJAX route for deleting a term."""
    term_id = request.form.get("term_id")

    if not term_id:
        return jsonify({"success": False, "message": "Term ID is required."})

    term = Term.query.get(term_id)
    if not term:
        return jsonify({"success": False, "message": "Term not found."})

    # Check if term has marks
    marks = Mark.query.filter_by(term_id=term.id).all()
    if marks:
        return jsonify({"success": False, "message": f"Cannot delete term '{term.name}' because it has marks associated with it."})

    # Store the name for the success message
    term_name = term.name

    # Delete the term
    db.session.delete(term)
    db.session.commit()

    # Get updated statistics
    terms = Term.query.all()
    assessment_types = AssessmentType.query.all()
    current_term = "None"

    # Find the current term if any
    for term in terms:
        if hasattr(term, 'is_current') and term.is_current:
            current_term = term.name
            break

    # Prepare statistics for JSON response
    stats = {
        "total_terms": len(terms),
        "total_assessments": len(assessment_types),
        "current_term": current_term
    }

    return jsonify({
        "success": True,
        "message": f"Term '{term_name}' deleted successfully!",
        "stats": stats
    })

@classteacher_bp.route('/delete_assessment_ajax', methods=['POST'])
@classteacher_required
def delete_assessment_ajax():
    """AJAX route for deleting an assessment type."""
    assessment_id = request.form.get("assessment_id")
    force_delete = request.form.get("force_delete") == "true"

    if not assessment_id:
        return jsonify({"success": False, "message": "Assessment ID is required."})

    assessment = AssessmentType.query.get(assessment_id)
    if not assessment:
        return jsonify({"success": False, "message": "Assessment type not found."})

    # Check if assessment type has marks
    marks = Mark.query.filter_by(assessment_type_id=assessment.id).all()

    # Check if user is headteacher (has universal access)
    is_headteacher = session.get('headteacher_universal_access') or session.get('role') == 'headteacher'

    if marks and not (is_headteacher and force_delete):
        if is_headteacher:
            return jsonify({
                "success": False,
                "message": f"Assessment type '{assessment.name}' has {len(marks)} marks associated with it. Use force delete to remove it along with all marks.",
                "has_marks": True,
                "marks_count": len(marks)
            })
        else:
            return jsonify({"success": False, "message": f"Cannot delete assessment type '{assessment.name}' because it has marks associated with it."})

    try:
        # Store the name for the success message
        assessment_name = assessment.name
        marks_count = len(marks)

        # If force delete and has marks, delete all associated marks first
        if marks and is_headteacher and force_delete:
            for mark in marks:
                db.session.delete(mark)

        # Delete the assessment type
        db.session.delete(assessment)
        db.session.commit()

        # Prepare success message
        if marks and force_delete:
            success_message = f"Assessment type '{assessment_name}' and {marks_count} associated marks deleted successfully!"
        else:
            success_message = f"Assessment type '{assessment_name}' deleted successfully!"

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error deleting assessment type: {str(e)}"})

    # Get updated statistics
    terms = Term.query.all()
    assessment_types = AssessmentType.query.all()
    current_term = "None"

    # Find the current term if any
    for term in terms:
        if hasattr(term, 'is_current') and term.is_current:
            current_term = term.name
            break

    # Prepare statistics for JSON response
    stats = {
        "total_terms": len(terms),
        "total_assessments": len(assessment_types),
        "current_term": current_term
    }

    return jsonify({
        "success": True,
        "message": success_message,
        "stats": stats
    })

@classteacher_bp.route('/edit_term_ajax', methods=['POST'])
@classteacher_required
def edit_term_ajax():
    """AJAX route for editing a term."""
    term_id = request.form.get("term_id")
    term_name = request.form.get("term_name")
    term_start_date = request.form.get("term_start_date")
    term_end_date = request.form.get("term_end_date")
    academic_year = request.form.get("academic_year")
    is_current_term = "is_current_term" in request.form

    if not term_id or not term_name:
        return jsonify({"success": False, "message": "Missing required information."})

    term = Term.query.get(term_id)
    if not term:
        return jsonify({"success": False, "message": "Term not found."})

    # Check if another term with the same name already exists
    existing_term = Term.query.filter(
        Term.name == term_name,
        Term.id != term.id
    ).first()

    if existing_term:
        return jsonify({"success": False, "message": f"Term '{term_name}' already exists."})

    # Update the term
    term.name = term_name

    # Update additional fields if they exist in the model
    if hasattr(Term, 'start_date'):
        term.start_date = term_start_date if term_start_date else None

    if hasattr(Term, 'end_date'):
        term.end_date = term_end_date if term_end_date else None

    if hasattr(Term, 'academic_year'):
        term.academic_year = academic_year if academic_year else None

    if hasattr(Term, 'is_current'):
        # If setting this term as current, unset any other current terms
        if is_current_term:
            current_terms = Term.query.filter(Term.id != term.id).all()
            for t in current_terms:
                if hasattr(t, 'is_current'):
                    t.is_current = False
            term.is_current = True
        else:
            term.is_current = False

    db.session.commit()

    # Get updated statistics
    terms = Term.query.all()
    assessment_types = AssessmentType.query.all()
    current_term = "None"

    # Find the current term if any
    for t in terms:
        if hasattr(t, 'is_current') and t.is_current:
            current_term = t.name
            break

    # Prepare term data for JSON response
    term_data = {
        "id": term.id,
        "name": term.name,
        "is_current": True if hasattr(term, 'is_current') and term.is_current else False,
        "academic_year": term.academic_year if hasattr(term, 'academic_year') and term.academic_year else None
    }

    # Find the current academic year
    current_academic_year = "None"
    for t in terms:
        if hasattr(t, 'is_current') and t.is_current and hasattr(t, 'academic_year') and t.academic_year:
            current_academic_year = t.academic_year
            break

    # If no current term has an academic year, try to get the academic year from any term
    if current_academic_year == "None":
        for t in terms:
            if hasattr(t, 'academic_year') and t.academic_year:
                current_academic_year = t.academic_year
                break

    # Prepare statistics for JSON response
    stats = {
        "total_terms": len(terms),
        "total_assessments": len(assessment_types),
        "current_term": current_term,
        "current_academic_year": current_academic_year
    }

    return jsonify({
        "success": True,
        "message": f"Term '{term_name}' updated successfully!",
        "term": term_data,
        "stats": stats
    })

@classteacher_bp.route('/edit_assessment_ajax', methods=['POST'])
@classteacher_required
def edit_assessment_ajax():
    """AJAX route for editing an assessment type."""
    assessment_id = request.form.get("assessment_id")
    assessment_name = request.form.get("assessment_name")
    assessment_weight = request.form.get("assessment_weight")
    assessment_group = request.form.get("assessment_group")
    show_on_reports = "show_on_reports" in request.form

    if not assessment_id or not assessment_name:
        return jsonify({"success": False, "message": "Missing required information."})

    assessment = AssessmentType.query.get(assessment_id)
    if not assessment:
        return jsonify({"success": False, "message": "Assessment type not found."})

    # Check if another assessment with the same name already exists
    existing_assessment = AssessmentType.query.filter(
        AssessmentType.name == assessment_name,
        AssessmentType.id != assessment.id
    ).first()

    if existing_assessment:
        return jsonify({"success": False, "message": f"Assessment type '{assessment_name}' already exists."})

    # Update the assessment
    assessment.name = assessment_name

    # Update additional fields if they exist in the model
    if hasattr(AssessmentType, 'weight'):
        assessment.weight = assessment_weight if assessment_weight else None

    if hasattr(AssessmentType, 'group'):
        assessment.group = assessment_group if assessment_group else None

    if hasattr(AssessmentType, 'show_on_reports'):
        assessment.show_on_reports = show_on_reports

    db.session.commit()

    # Get updated statistics
    terms = Term.query.all()
    assessment_types = AssessmentType.query.all()
    current_term = "None"

    # Find the current term if any
    for term in terms:
        if hasattr(term, 'is_current') and term.is_current:
            current_term = term.name
            break

    # Prepare assessment data for JSON response
    assessment_data = {
        "id": assessment.id,
        "name": assessment.name,
        "weight": assessment.weight if hasattr(assessment, 'weight') and assessment.weight else None
    }

    # Prepare statistics for JSON response
    stats = {
        "total_terms": len(terms),
        "total_assessments": len(assessment_types),
        "current_term": current_term
    }

    return jsonify({
        "success": True,
        "message": f"Assessment type '{assessment_name}' updated successfully!",
        "assessment": assessment_data,
        "stats": stats
    })

@classteacher_bp.route('/add_assessment_ajax', methods=['POST'])
@classteacher_required
def add_assessment_ajax():
    """AJAX route for adding a new assessment type."""
    assessment_name = request.form.get("assessment_name")
    assessment_weight = request.form.get("assessment_weight")
    assessment_group = request.form.get("assessment_group")
    show_on_reports = "show_on_reports" in request.form

    if not assessment_name:
        return jsonify({"success": False, "message": "Please fill in the assessment type name."})

    existing_assessment = AssessmentType.query.filter_by(name=assessment_name).first()
    if existing_assessment:
        return jsonify({"success": False, "message": f"Assessment type '{assessment_name}' already exists."})

    # Create new assessment with proper field handling
    try:
        # Convert weight to float if provided, otherwise use default
        weight_value = None
        if assessment_weight:
            try:
                weight_value = float(assessment_weight)
            except (ValueError, TypeError):
                weight_value = 100.0  # Default weight
        else:
            weight_value = 100.0  # Default weight if not provided

        new_assessment = AssessmentType(
            name=assessment_name,
            weight=weight_value,
            category=assessment_group if assessment_group else 'General'
        )

        # Add additional fields if they exist in the model
        if hasattr(AssessmentType, 'show_on_reports'):
            new_assessment.show_on_reports = show_on_reports

        db.session.add(new_assessment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error creating assessment type: {str(e)}"})

    # Get updated statistics
    terms = Term.query.all()
    assessment_types = AssessmentType.query.all()
    current_term = "None"

    # Find the current term if any
    for term in terms:
        if hasattr(term, 'is_current') and term.is_current:
            current_term = term.name
            break

    # Prepare assessment data for JSON response
    assessment_data = {
        "id": new_assessment.id,
        "name": new_assessment.name,
        "weight": new_assessment.weight if hasattr(new_assessment, 'weight') and new_assessment.weight else None
    }

    # Prepare statistics for JSON response
    stats = {
        "total_terms": len(terms),
        "total_assessments": len(assessment_types),
        "current_term": current_term
    }

    return jsonify({
        "success": True,
        "message": f"Assessment type '{assessment_name}' added successfully!",
        "assessment": assessment_data,
        "stats": stats
    })

@classteacher_bp.route('/manage_terms_assessments', methods=['GET', 'POST'])
@classteacher_required
def manage_terms_assessments():
    """Route for managing terms and assessment types."""
    error_message = None
    success_message = None

    # Get all terms and assessment types
    terms = Term.query.order_by(Term.id).all()
    assessment_types = AssessmentType.query.order_by(AssessmentType.id).all()

    # Set default values for statistics
    current_academic_year = "None"
    current_term = "None"

    # Find the current term and academic year if any
    for term in terms:
        if hasattr(term, 'is_current') and term.is_current:
            current_term = term.name
            if hasattr(term, 'academic_year') and term.academic_year:
                current_academic_year = term.academic_year
            break

    # If no current term has an academic year, try to get the academic year from any term
    if current_academic_year == "None":
        for term in terms:
            if hasattr(term, 'academic_year') and term.academic_year:
                current_academic_year = term.academic_year
                break

    if request.method == 'POST':
        action = request.form.get("action")

        if "add_term" in request.form:
            term_name = request.form.get("term_name")
            term_start_date = request.form.get("term_start_date")
            term_end_date = request.form.get("term_end_date")
            academic_year = request.form.get("academic_year")
            is_current_term = "is_current_term" in request.form

            if term_name:
                existing_term = Term.query.filter_by(name=term_name).first()
                if existing_term:
                    error_message = f"Term '{term_name}' already exists."
                else:
                    # Create new term with additional fields if they exist in the model
                    new_term = Term(name=term_name)

                    # Add additional fields if they exist in the model
                    if hasattr(Term, 'start_date') and term_start_date:
                        new_term.start_date = term_start_date

                    if hasattr(Term, 'end_date') and term_end_date:
                        new_term.end_date = term_end_date

                    if hasattr(Term, 'academic_year') and academic_year:
                        new_term.academic_year = academic_year

                    if hasattr(Term, 'is_current'):
                        # If setting this term as current, unset any other current terms
                        if is_current_term:
                            for term in terms:
                                if hasattr(term, 'is_current'):
                                    term.is_current = False
                            new_term.is_current = True

                    db.session.add(new_term)
                    db.session.commit()
                    success_message = f"Term '{term_name}' added successfully!"
            else:
                error_message = "Please fill in the term name."

        elif "add_assessment" in request.form:
            assessment_name = request.form.get("assessment_name")
            assessment_weight = request.form.get("assessment_weight")
            assessment_group = request.form.get("assessment_group")
            show_on_reports = "show_on_reports" in request.form

            if assessment_name:
                existing_assessment = AssessmentType.query.filter_by(name=assessment_name).first()
                if existing_assessment:
                    error_message = f"Assessment type '{assessment_name}' already exists."
                else:
                    # Create new assessment with proper field handling
                    try:
                        # Convert weight to float if provided, otherwise use default
                        weight_value = None
                        if assessment_weight:
                            try:
                                weight_value = float(assessment_weight)
                            except (ValueError, TypeError):
                                weight_value = 100.0  # Default weight
                        else:
                            weight_value = 100.0  # Default weight if not provided

                        new_assessment = AssessmentType(
                            name=assessment_name,
                            weight=weight_value,
                            category=assessment_group if assessment_group else 'General'
                        )

                        # Add additional fields if they exist in the model
                        if hasattr(AssessmentType, 'show_on_reports'):
                            new_assessment.show_on_reports = show_on_reports

                        db.session.add(new_assessment)
                        db.session.commit()
                        success_message = f"Assessment type '{assessment_name}' added successfully!"
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error creating assessment type: {str(e)}"
            else:
                error_message = "Please fill in the assessment type name."

        elif "delete_term" in request.form:
            term_id = request.form.get("term_id")
            term = Term.query.get(term_id)
            if term:
                # Check if term has marks
                marks = Mark.query.filter_by(term_id=term.id).all()
                if marks:
                    error_message = f"Cannot delete term '{term.name}' because it has marks associated with it."
                else:
                    db.session.delete(term)
                    db.session.commit()
                    success_message = f"Term '{term.name}' deleted successfully!"
            else:
                error_message = "Term not found."

        elif "delete_assessment" in request.form:
            assessment_id = request.form.get("assessment_id")
            force_delete = request.form.get("force_delete") == "true"
            assessment = AssessmentType.query.get(assessment_id)
            if assessment:
                # Check if assessment type has marks
                marks = Mark.query.filter_by(assessment_type_id=assessment.id).all()

                # Check if user is headteacher (has universal access)
                is_headteacher = session.get('headteacher_universal_access') or session.get('role') == 'headteacher'

                if marks and not (is_headteacher and force_delete):
                    if is_headteacher:
                        error_message = f"Assessment type '{assessment.name}' has {len(marks)} marks associated with it. Use force delete to remove it along with all marks."
                    else:
                        error_message = f"Cannot delete assessment type '{assessment.name}' because it has marks associated with it."
                else:
                    try:
                        # If force delete and has marks, delete all associated marks first
                        if marks and is_headteacher and force_delete:
                            for mark in marks:
                                db.session.delete(mark)

                        db.session.delete(assessment)
                        db.session.commit()

                        if marks and force_delete:
                            success_message = f"Assessment type '{assessment.name}' and {len(marks)} associated marks deleted successfully!"
                        else:
                            success_message = f"Assessment type '{assessment.name}' deleted successfully!"
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error deleting assessment type: {str(e)}"
            else:
                error_message = "Assessment type not found."

        elif action == "edit_term":
            term_id = request.form.get("term_id")
            term_name = request.form.get("term_name")
            term_start_date = request.form.get("term_start_date")
            term_end_date = request.form.get("term_end_date")
            academic_year = request.form.get("academic_year")
            is_current_term = "is_current_term" in request.form

            if not term_id or not term_name:
                error_message = "Missing required information."
            else:
                term = Term.query.get(term_id)
                if not term:
                    error_message = "Term not found."
                else:
                    # Check if another term with the same name already exists
                    existing_term = Term.query.filter(
                        Term.name == term_name,
                        Term.id != term.id
                    ).first()

                    if existing_term:
                        error_message = f"Term '{term_name}' already exists."
                    else:
                        # Update the term
                        term.name = term_name

                        # Update additional fields if they exist in the model
                        if hasattr(Term, 'start_date'):
                            term.start_date = term_start_date if term_start_date else None

                        if hasattr(Term, 'end_date'):
                            term.end_date = term_end_date if term_end_date else None

                        if hasattr(Term, 'academic_year'):
                            term.academic_year = academic_year if academic_year else None

                        if hasattr(Term, 'is_current'):
                            # If setting this term as current, unset any other current terms
                            if is_current_term:
                                for t in terms:
                                    if hasattr(t, 'is_current'):
                                        t.is_current = (t.id == term.id)
                            else:
                                term.is_current = False

                        db.session.commit()
                        success_message = f"Term '{term_name}' updated successfully!"

        elif action == "edit_assessment":
            assessment_id = request.form.get("assessment_id")
            assessment_name = request.form.get("assessment_name")
            assessment_weight = request.form.get("assessment_weight")
            assessment_group = request.form.get("assessment_group")
            show_on_reports = "show_on_reports" in request.form

            if not assessment_id or not assessment_name:
                error_message = "Missing required information."
            else:
                assessment = AssessmentType.query.get(assessment_id)
                if not assessment:
                    error_message = "Assessment type not found."
                else:
                    # Check if another assessment with the same name already exists
                    existing_assessment = AssessmentType.query.filter(
                        AssessmentType.name == assessment_name,
                        AssessmentType.id != assessment.id
                    ).first()

                    if existing_assessment:
                        error_message = f"Assessment type '{assessment_name}' already exists."
                    else:
                        # Update the assessment
                        assessment.name = assessment_name

                        # Update additional fields if they exist in the model
                        if hasattr(AssessmentType, 'weight'):
                            assessment.weight = assessment_weight if assessment_weight else None

                        if hasattr(AssessmentType, 'group'):
                            assessment.group = assessment_group if assessment_group else None

                        if hasattr(AssessmentType, 'show_on_reports'):
                            assessment.show_on_reports = show_on_reports

                        db.session.commit()
                        success_message = f"Assessment type '{assessment_name}' updated successfully!"

    # Add is_current attribute to terms if it doesn't exist in the model
    for term in terms:
        if not hasattr(term, 'is_current'):
            # Check if this is the only term or if it's the latest term
            if len(terms) == 1 or term.id == max(t.id for t in terms):
                term.is_current = True
            else:
                term.is_current = False

    # Add weight attribute to assessment types if it doesn't exist in the model
    for assessment in assessment_types:
        if not hasattr(assessment, 'weight'):
            assessment.weight = None

    return render_template(
        'manage_terms_assessments.html',
        terms=terms,
        assessment_types=assessment_types,
        current_academic_year=current_academic_year,
        current_term=current_term,
        error_message=error_message,
        success_message=success_message
    )

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
                "grade_level": grade.name if grade else "Unknown",
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

                    success_message = f"Removed {subject.name} assignment for Grade {grade.name}{stream_text}."
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

                        success_message = f"Changed subject from {old_subject.name} to {new_subject.name} for Grade {grade.name}{stream_text}."
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
                        success_message = f"Added {added_count} subject assignments for Grade {grade.name}{stream_text}."
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

@classteacher_bp.route('/teacher_management_hub', methods=['GET'])
@classteacher_required
def teacher_management_hub():
    """Route for the Teacher Management Hub - central entry point."""
    from ..models.assignment import TeacherSubjectAssignment

    # Get statistics
    total_teachers = Teacher.query.count()
    total_assignments = TeacherSubjectAssignment.query.count()
    class_teachers = TeacherSubjectAssignment.query.filter_by(is_class_teacher=True).count()
    subject_assignments = TeacherSubjectAssignment.query.filter_by(is_class_teacher=False).count()

    # Sample recent activities (you can expand this with real data)
    recent_activities = [
        {
            'icon': '👨‍🏫',
            'text': 'New teacher profile created',
            'time': '2 hours ago'
        },
        {
            'icon': '📚',
            'text': 'Subject assignment updated',
            'time': '4 hours ago'
        },
        {
            'icon': '🔄',
            'text': 'Teacher reassignment completed',
            'time': '1 day ago'
        }
    ]

    return render_template(
        'teacher_management_hub.html',
        total_teachers=total_teachers,
        total_assignments=total_assignments,
        class_teachers=class_teachers,
        subject_assignments=subject_assignments,
        recent_activities=recent_activities
    )

@classteacher_bp.route('/manage_teachers', methods=['GET', 'POST'])
@classteacher_required
def manage_teachers():
    """Route for managing teachers."""
    # Import TeacherSubjectAssignment at the beginning
    from ..models.assignment import TeacherSubjectAssignment

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
            grade_level = assignment.grade.name
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

    # Get all teachers with their assignment data
    teachers = []
    all_teachers = Teacher.query.all()

    for teacher in all_teachers:
        # Get teacher's assignments
        teacher_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher.id).all()

        # Get subjects taught by this teacher
        subjects_taught = []
        class_assignments = []
        subject_assignments = []

        for assignment in teacher_assignments:
            if assignment.is_class_teacher:
                # Class teacher assignment
                grade = Grade.query.get(assignment.grade_id)
                stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None
                class_assignments.append({
                    'grade': grade.name if grade else 'Unknown',
                    'stream': stream.name if stream else 'All Streams'
                })
            else:
                # Subject assignment
                subject = Subject.query.get(assignment.subject_id)
                grade = Grade.query.get(assignment.grade_id)
                stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

                if subject and subject.name not in subjects_taught:
                    subjects_taught.append(subject.name)

                subject_assignments.append({
                    'subject': subject.name if subject else 'Unknown',
                    'grade': grade.name if grade else 'Unknown',
                    'stream': stream.name if stream else 'All Streams'
                })

        # Create enhanced teacher object
        enhanced_teacher = {
            'id': teacher.id,
            'username': teacher.username,
            'role': teacher.role,
            'subjects_taught': subjects_taught,
            'class_assignments': class_assignments,
            'subject_assignments': subject_assignments,
            'total_assignments': len(teacher_assignments),
            'is_class_teacher': len(class_assignments) > 0
        }

        teachers.append(enhanced_teacher)

    # Get all subjects and grades for the form
    subjects = Subject.query.all()
    grades = Grade.query.all()

    if request.method == 'POST':
        if "add_teacher" in request.form:
            username = request.form.get("username")
            password = request.form.get("password")
            role = request.form.get("role")
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            qualification = request.form.get("qualification", "").strip()
            specialization = request.form.get("specialization", "").strip()

            if not username or not password or not role:
                error_message = "Please fill in all required fields (username, password, role)."
            else:
                # Check if teacher with same username already exists
                if Teacher.query.filter_by(username=username).first():
                    error_message = f"A teacher with username '{username}' already exists."
                else:
                    try:
                        # Generate employee ID
                        cursor = db.session.execute(db.text("SELECT MAX(id) FROM teacher"))
                        max_id = cursor.scalar() or 0
                        employee_id = f"EMP{max_id + 1:03d}"

                        new_teacher = Teacher(
                            username=username,
                            password=generate_password_hash(password),
                            role=role,
                            first_name=first_name if first_name else None,
                            last_name=last_name if last_name else None,
                            email=email if email else None,
                            phone=phone if phone else None,
                            employee_id=employee_id,
                            qualification=qualification if qualification else None,
                            specialization=specialization if specialization else None,
                            date_joined=db.func.current_date(),
                            is_active=True
                        )
                        db.session.add(new_teacher)
                        db.session.commit()
                        success_message = f"Teacher '{username}' added successfully with Employee ID: {employee_id}! You can now assign subjects to this teacher using the Bulk Assignments feature."
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error adding teacher: {str(e)}"

        elif "update_teacher" in request.form:
            teacher_id = request.form.get("edit_teacher_id")
            new_role = request.form.get("edit_role")
            new_password = request.form.get("edit_password")
            first_name = request.form.get("edit_first_name", "").strip()
            last_name = request.form.get("edit_last_name", "").strip()
            email = request.form.get("edit_email", "").strip()
            phone = request.form.get("edit_phone", "").strip()
            qualification = request.form.get("edit_qualification", "").strip()
            specialization = request.form.get("edit_specialization", "").strip()

            teacher = Teacher.query.get(teacher_id)

            if teacher:
                try:
                    # Update basic fields
                    teacher.role = new_role
                    teacher.first_name = first_name if first_name else None
                    teacher.last_name = last_name if last_name else None
                    teacher.email = email if email else None
                    teacher.phone = phone if phone else None
                    teacher.qualification = qualification if qualification else None
                    teacher.specialization = specialization if specialization else None

                    # Update password if provided
                    if new_password and new_password.strip():
                        teacher.password = generate_password_hash(new_password)

                    db.session.commit()
                    success_message = f"Teacher '{teacher.username}' updated successfully!"
                except Exception as e:
                    db.session.rollback()
                    error_message = f"Error updating teacher: {str(e)}"
            else:
                error_message = "Teacher not found."

        elif "delete_teacher" in request.form:
            teacher_id = request.form.get("teacher_id")

            if teacher_id:
                try:
                    from ..utils.database_utils import safe_delete_teacher

                    result = safe_delete_teacher(teacher_id)

                    if result['success']:
                        success_message = result['message']
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
                            success_message = f"Teacher '{teacher.username}' deleted successfully!"

                        except Exception as e:
                            db.session.rollback()
                            print(f"Error deleting teacher: {e}")
                            error_message = f"Error deleting teacher: {str(e)}"
                    else:
                        error_message = "Teacher not found."
            else:
                error_message = "Teacher ID is required."

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

                            message = f"Class teacher assignment for {teacher.username} in Grade {grade.name}{stream_text} removed successfully."
                        else:
                            subject = Subject.query.get(assignment.subject_id)
                            grade = Grade.query.get(assignment.grade_id)
                            stream_text = ""
                            if assignment.stream_id:
                                stream = Stream.query.get(assignment.stream_id)
                                stream_text = f" Stream {stream.name}"

                            message = f"Subject assignment of {subject.name} to {teacher.username} for Grade {grade.name}{stream_text} removed successfully."

                        db.session.delete(assignment)
                        db.session.commit()
                        success_message = message
                    else:
                        error_message = "Assignment not found."
                except Exception as e:
                    print(f"Error removing assignment: {str(e)}")
                    error_message = "Error removing assignment."

    # Get current teacher's assignments for display
    try:
        # Get class teacher assignments for current teacher
        class_teacher_assignments = TeacherSubjectAssignment.query.filter_by(
            teacher_id=current_teacher.id,
            is_class_teacher=True
        ).all()

        # Get subject assignments for current teacher
        subject_assignments = TeacherSubjectAssignment.query.filter_by(
            teacher_id=current_teacher.id,
            is_class_teacher=False
        ).all()

    except Exception as e:
        print(f"Error fetching assignments: {str(e)}")
        class_teacher_assignments = []
        subject_assignments = []

    return render_template(
        'manage_teachers.html',
        teachers=teachers,
        class_teacher_assignments=class_teacher_assignments,
        subject_assignments=subject_assignments,
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

                success_message = f"Successfully assigned {subject.name} to {teacher.username} for Grade {grade.name}"
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

@classteacher_bp.route('/enhanced_bulk_assign_subjects', methods=['POST'])
@classteacher_required
def enhanced_bulk_assign_subjects():
    """Enhanced route for bulk assignment of subjects to teachers with advanced features."""
    from ..models.assignment import TeacherSubjectAssignment

    teacher_id = request.form.get('bulk_teacher_id')
    assignment_mode = request.form.get('assignment_mode', 'simple')

    if not teacher_id:
        flash("Please select a teacher.", "error")
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
    errors = []

    try:
        if assignment_mode == 'simple':
            # Handle enhanced simple bulk assignment with dynamic stream selection
            subject_ids = request.form.getlist('bulk_subjects')
            grade_ids = request.form.getlist('bulk_grades')
            class_teacher_grades = request.form.getlist('class_teacher_grades')

            if not subject_ids or not grade_ids:
                flash("Please select at least one subject and one grade.", "error")
                return redirect(url_for('classteacher.assign_subjects'))

            # Create assignments for each subject and grade combination
            for subject_id in subject_ids:
                subject = Subject.query.get(subject_id)
                if not subject:
                    continue

                for grade_id in grade_ids:
                    grade = Grade.query.get(grade_id)
                    if not grade:
                        continue

                    # Check if this grade should have class teacher designation
                    is_class_teacher_for_grade = grade_id in class_teacher_grades

                    # Check stream selection for this grade
                    all_streams_option = request.form.get(f'stream_option_{grade_id}', 'all')

                    if all_streams_option == 'all':
                        # Assign to all streams or whole grade if no streams exist
                        streams = Stream.query.filter_by(grade_id=grade_id).all()

                        if not streams:
                            # No streams - create assignment for whole grade
                            result = create_single_assignment(
                                teacher_id, subject_id, grade_id, None, is_class_teacher_for_grade
                            )
                            assignments_created += result['created']
                            assignments_skipped += result['skipped']
                            class_teacher_conflicts += result['conflicts']
                            if result['error']:
                                errors.append(result['error'])
                        else:
                            # Has streams - create assignment for each stream
                            for stream in streams:
                                result = create_single_assignment(
                                    teacher_id, subject_id, grade_id, stream.id, is_class_teacher_for_grade
                                )
                                assignments_created += result['created']
                                assignments_skipped += result['skipped']
                                class_teacher_conflicts += result['conflicts']
                                if result['error']:
                                    errors.append(result['error'])
                    else:
                        # Assign to specific streams only
                        specific_stream_ids = request.form.getlist(f'specific_streams_{grade_id}')

                        if specific_stream_ids:
                            for stream_id in specific_stream_ids:
                                stream = Stream.query.get(stream_id)
                                if stream and stream.grade_id == int(grade_id):
                                    result = create_single_assignment(
                                        teacher_id, subject_id, grade_id, stream.id, is_class_teacher_for_grade
                                    )
                                    assignments_created += result['created']
                                    assignments_skipped += result['skipped']
                                    class_teacher_conflicts += result['conflicts']
                                    if result['error']:
                                        errors.append(result['error'])
                        else:
                            # No specific streams selected but specific mode chosen - skip this grade
                            errors.append(f"No specific streams selected for Grade {grade.name}")
                            continue

        else:  # advanced mode
            # Handle advanced precise assignment
            advanced_subjects = request.form.getlist('advanced_subjects[]')
            advanced_grades = request.form.getlist('advanced_grades[]')
            advanced_streams = request.form.getlist('advanced_streams[]')
            advanced_class_teachers = request.form.getlist('advanced_class_teacher[]')

            if not advanced_subjects or not advanced_grades:
                flash("Please add at least one assignment combination.", "error")
                return redirect(url_for('classteacher.assign_subjects'))

            # Process each combination
            for i in range(len(advanced_subjects)):
                if i < len(advanced_subjects) and i < len(advanced_grades):
                    subject_id = advanced_subjects[i]
                    grade_id = advanced_grades[i]
                    stream_id = advanced_streams[i] if i < len(advanced_streams) and advanced_streams[i] else None
                    is_class_teacher = str(i + 1) in advanced_class_teachers

                    if subject_id and grade_id:
                        result = create_single_assignment(
                            teacher_id, subject_id, grade_id, stream_id, is_class_teacher
                        )
                        assignments_created += result['created']
                        assignments_skipped += result['skipped']
                        class_teacher_conflicts += result['conflicts']
                        if result['error']:
                            errors.append(result['error'])

        # Commit all the new assignments
        db.session.commit()

        # Create a comprehensive summary message
        message_parts = []

        if assignments_created > 0:
            message_parts.append(f"✅ Created {assignments_created} new assignments for {teacher.username}")

        if assignments_skipped > 0:
            message_parts.append(f"⏭️ Skipped {assignments_skipped} existing assignments")

        if class_teacher_conflicts > 0:
            message_parts.append(f"⚠️ Skipped {class_teacher_conflicts} class teacher assignments due to conflicts")

        if errors:
            message_parts.append(f"❌ {len(errors)} errors occurred")

        if assignments_created > 0:
            flash(". ".join(message_parts), "success")
        else:
            flash("No new assignments were created. " + ". ".join(message_parts[1:]), "warning")

    except Exception as e:
        db.session.rollback()
        print(f"Error in enhanced bulk assignment: {str(e)}")
        flash(f"Error creating assignments: {str(e)}", "error")

    return redirect(url_for('classteacher.assign_subjects'))

def create_single_assignment(teacher_id, subject_id, grade_id, stream_id, is_class_teacher):
    """Helper function to create a single assignment with error handling."""
    from ..models.assignment import TeacherSubjectAssignment

    result = {
        'created': 0,
        'skipped': 0,
        'conflicts': 0,
        'error': None
    }

    try:
        # Check if assignment already exists
        existing = TeacherSubjectAssignment.query.filter_by(
            teacher_id=teacher_id,
            subject_id=subject_id,
            grade_id=grade_id,
            stream_id=stream_id
        ).first()

        if existing:
            result['skipped'] = 1
            return result

        # If this is a class teacher, check if there's already one for this grade/stream
        if is_class_teacher:
            existing_class_teacher = TeacherSubjectAssignment.query.filter_by(
                grade_id=grade_id,
                stream_id=stream_id,
                is_class_teacher=True
            ).first()

            if existing_class_teacher and int(existing_class_teacher.teacher_id) != int(teacher_id):
                result['conflicts'] = 1
                return result

        # Create the assignment
        new_assignment = TeacherSubjectAssignment(
            teacher_id=teacher_id,
            subject_id=subject_id,
            grade_id=grade_id,
            stream_id=stream_id,
            is_class_teacher=is_class_teacher
        )

        db.session.add(new_assignment)
        result['created'] = 1

    except Exception as e:
        result['error'] = f"Error creating assignment: {str(e)}"

    return result

@classteacher_bp.route('/advanced_assignments', methods=['GET'])
@classteacher_required
def advanced_assignments():
    """Route for the advanced teacher assignments page."""
    from ..models.assignment import TeacherSubjectAssignment

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
        'teacher_assignments.html',
        teachers=teachers,
        subjects=subjects,
        grades=grades,
        assignments=assignments,
        error_message=None,
        success_message=None
    )

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

                message = f"Assignment of {subject.name} to {teacher.username} for Grade {grade.name}"
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
                'grade': grade.name if grade else 'Unknown Grade',
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

@classteacher_bp.route('/api/streams/<grade>')
@classteacher_required
def api_get_streams(grade):
    """API endpoint to get streams for a grade level."""
    grade_obj = Grade.query.filter_by(name=grade).first()
    if grade_obj:
        streams = Stream.query.filter_by(grade_id=grade_obj.id).all()
        stream_names = [stream.name for stream in streams]
        return jsonify({"streams": [f"Stream {name}" for name in stream_names]})
    return jsonify({"streams": []})

@classteacher_bp.route('/view_all_reports')
@classteacher_required
def view_all_reports():
    """Route for viewing all reports with pagination and filtering."""
    # Get filter parameters
    sort_by = request.args.get('sort', 'date')
    filter_grade = request.args.get('filter_grade', '')
    filter_term = request.args.get('filter_term', '')
    filter_assessment = request.args.get('filter_assessment', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of reports per page

    # Build the query with joins
    marks_query = Mark.query.join(Student).join(Stream).join(Grade).join(Term).join(AssessmentType)

    # Apply filters if provided
    if filter_grade:
        marks_query = marks_query.filter(Grade.name == filter_grade)
    if filter_term:
        marks_query = marks_query.filter(Term.name == filter_term)
    if filter_assessment:
        marks_query = marks_query.filter(AssessmentType.name == filter_assessment)

    # Apply sorting
    if sort_by == 'grade':
        marks_query = marks_query.order_by(Grade.name)
    elif sort_by == 'term':
        marks_query = marks_query.order_by(Term.name)
    else:  # Default to date
        marks_query = marks_query.order_by(Mark.created_at.desc())

    # Get unique combinations of grade, stream, term, assessment_type
    from sqlalchemy import func
    unique_combinations = db.session.query(
        Grade.name,
        Stream.name,
        Term.name,
        AssessmentType.name,
        func.count(Mark.id).label('mark_count'),
        func.max(Mark.created_at).label('latest_date')
    ).join(Student, Mark.student_id == Student.id)\
     .join(Stream, Student.stream_id == Stream.id)\
     .join(Grade, Stream.grade_id == Grade.id)\
     .join(Term, Mark.term_id == Term.id)\
     .join(AssessmentType, Mark.assessment_type_id == AssessmentType.id)\
     .group_by(Grade.name, Stream.name, Term.name, AssessmentType.name)

    # Apply filters to the unique combinations query
    if filter_grade:
        unique_combinations = unique_combinations.filter(Grade.name == filter_grade)
    if filter_term:
        unique_combinations = unique_combinations.filter(Term.name == filter_term)
    if filter_assessment:
        unique_combinations = unique_combinations.filter(AssessmentType.name == filter_assessment)

    # Apply sorting to the unique combinations query
    if sort_by == 'grade':
        unique_combinations = unique_combinations.order_by(Grade.name)
    elif sort_by == 'term':
        unique_combinations = unique_combinations.order_by(Term.name)
    else:  # Default to date
        unique_combinations = unique_combinations.order_by(func.max(Mark.created_at).desc())

    # Paginate the results
    pagination = unique_combinations.paginate(page=page, per_page=per_page, error_out=False)

    # Format the results
    reports = []
    for grade, stream, term, assessment_type, mark_count, latest_date in pagination.items:
        reports.append({
            'id': len(reports) + 1,
            'grade': grade,
            'stream': f"Stream {stream}",
            'term': term,
            'assessment_type': assessment_type,
            'date': latest_date.strftime('%Y-%m-%d') if latest_date else 'N/A',
            'mark_count': mark_count
        })

    # Get all grades, terms, and assessment types for filters
    grades = [grade.name for grade in Grade.query.all()]
    terms = [term.name for term in Term.query.all()]
    assessment_types = [assessment_type.name for assessment_type in AssessmentType.query.all()]

    return render_template(
        'all_reports.html',
        reports=reports,
        pagination=pagination,
        sort_by=sort_by,
        filter_grade=filter_grade,
        filter_term=filter_term,
        filter_assessment=filter_assessment,
        grades=grades,
        terms=terms,
        assessment_types=assessment_types
    )

@classteacher_bp.route('/delete_report/<grade>/<stream>/<term>/<assessment_type>', methods=['GET', 'POST'])
@classteacher_required
def delete_report(grade, stream, term, assessment_type):
    """Route for deleting a marksheet and all associated marks."""
    # Extract stream letter from "Stream X" format
    stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream

    # Get the stream, term, and assessment type objects
    stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream_letter).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid stream, term, or assessment type.", "error")
        return redirect(url_for('classteacher.dashboard'))

    try:
        # Get all students in this stream
        students = Student.query.filter_by(stream_id=stream_obj.id).all()
        student_ids = [student.id for student in students]

        # Delete all marks for these students in the specified term and assessment type
        deleted_count = Mark.query.filter(
            Mark.student_id.in_(student_ids),
            Mark.term_id == term_obj.id,
            Mark.assessment_type_id == assessment_type_obj.id
        ).delete(synchronize_session=False)

        # Commit the changes
        db.session.commit()

        # Invalidate any existing cache for this grade/stream/term/assessment combination
        invalidate_cache(grade, stream, term, assessment_type)

        flash(f"Successfully deleted {deleted_count} marks for {grade} {stream} in {term} {assessment_type}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting marks: {str(e)}", "error")

    # Redirect back to the referring page or dashboard
    referrer = request.referrer
    if referrer and ('all_reports' in referrer or 'dashboard' in referrer):
        return redirect(referrer)
    else:
        return redirect(url_for('classteacher.dashboard'))

@classteacher_bp.route('/api/stream_status/<grade>/<term>/<assessment_type>')
@classteacher_required
def api_get_stream_status(grade, term, assessment_type):
    """API endpoint to check if streams have marks for a specific grade, term, and assessment type."""
    grade_obj = Grade.query.filter_by(name=grade).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (grade_obj and term_obj and assessment_type_obj):
        return jsonify({"error": "Invalid grade, term, or assessment type"}), 400

    streams = Stream.query.filter_by(grade_id=grade_obj.id).all()
    result = []

    for stream in streams:
        # Check if there are any marks for this stream
        has_marks = Mark.query.join(Student).filter(
            Student.stream_id == stream.id,
            Mark.term_id == term_obj.id,
            Mark.assessment_type_id == assessment_type_obj.id
        ).first() is not None

        result.append({
            "name": stream.name,
            "has_marks": has_marks
        })

    return jsonify({"streams": result})


# ============================================================================
# COLLABORATIVE MARKS UPLOAD SYSTEM
# ============================================================================

@classteacher_bp.route('/collaborative_marks_dashboard')
@classteacher_required
def collaborative_marks_dashboard():
    """Dashboard showing marks upload status for all classes managed by the class teacher."""
    try:
        current_teacher_id = session.get('teacher_id')
        if not current_teacher_id:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('auth.classteacher_login'))

        # Get dashboard data
        dashboard_data = CollaborativeMarksService.get_class_teacher_dashboard_data(current_teacher_id)

        if 'error' in dashboard_data:
            flash(f"Error loading dashboard: {dashboard_data['error']}", "error")
            return redirect(url_for('classteacher.dashboard'))

        return render_template('collaborative_marks_dashboard.html', **dashboard_data)

    except Exception as e:
        print(f"Error in collaborative marks dashboard: {str(e)}")
        flash("Error loading collaborative marks dashboard.", "error")
        return redirect(url_for('classteacher.dashboard'))


@classteacher_bp.route('/class_marks_status/<int:grade_id>/<int:stream_id>/<int:term_id>/<int:assessment_type_id>')
@classteacher_required
def class_marks_status(grade_id, stream_id, term_id, assessment_type_id):
    """Show detailed marks upload status for a specific class."""
    try:
        current_teacher_id = session.get('teacher_id')
        if not current_teacher_id:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('auth.classteacher_login'))

        # Get class marks status
        status_data = CollaborativeMarksService.get_class_marks_status(
            grade_id, stream_id, term_id, assessment_type_id, current_teacher_id
        )

        if 'error' in status_data:
            flash(f"Error loading class status: {status_data['error']}", "error")
            return redirect(url_for('classteacher.collaborative_marks_dashboard'))

        # Check if current teacher can upload marks for each subject
        for subject in status_data['subjects']:
            subject['can_upload'] = CollaborativeMarksService.can_teacher_upload_subject(
                current_teacher_id, subject['id'], grade_id, stream_id
            )

        # Add navigation data
        status_data['grade_id'] = grade_id
        status_data['stream_id'] = stream_id
        status_data['term_id'] = term_id
        status_data['assessment_type_id'] = assessment_type_id

        return render_template('class_marks_status.html', **status_data)

    except Exception as e:
        print(f"Error in class marks status: {str(e)}")
        flash("Error loading class marks status.", "error")
        return redirect(url_for('classteacher.collaborative_marks_dashboard'))


@classteacher_bp.route('/upload_subject_marks/<int:grade_id>/<int:stream_id>/<int:subject_id>/<int:term_id>/<int:assessment_type_id>')
@classteacher_required
def upload_subject_marks(grade_id, stream_id, subject_id, term_id, assessment_type_id):
    """Upload marks for a specific subject in a class."""
    try:
        current_teacher_id = session.get('teacher_id')
        if not current_teacher_id:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('auth.classteacher_login'))

        # Check if teacher can upload marks for this subject
        if not CollaborativeMarksService.can_teacher_upload_subject(
            current_teacher_id, subject_id, grade_id, stream_id
        ):
            flash("You are not authorized to upload marks for this subject.", "error")
            return redirect(url_for('classteacher.class_marks_status',
                                  grade_id=grade_id, stream_id=stream_id,
                                  term_id=term_id, assessment_type_id=assessment_type_id))

        # Get required objects
        grade = Grade.query.get(grade_id)
        stream = Stream.query.get(stream_id)
        subject = Subject.query.get(subject_id)
        term = Term.query.get(term_id)
        assessment_type = AssessmentType.query.get(assessment_type_id)

        if not all([grade, stream, subject, term, assessment_type]):
            flash("Invalid parameters for marks upload.", "error")
            return redirect(url_for('classteacher.collaborative_marks_dashboard'))

        # Get students in this stream
        students = Student.query.filter_by(stream_id=stream_id).order_by(Student.name).all()

        # Get existing marks for this subject
        existing_marks = {}
        marks = Mark.query.filter_by(
            subject_id=subject_id,
            term_id=term_id,
            assessment_type_id=assessment_type_id
        ).join(Student).filter(Student.stream_id == stream_id).all()

        for mark in marks:
            existing_marks[mark.student_id] = mark

        # Check if subject is composite
        components = subject.get_components() if subject.is_composite else []

        upload_data = {
            'grade': grade,
            'stream': stream,
            'subject': subject,
            'term': term,
            'assessment_type': assessment_type,
            'students': students,
            'existing_marks': existing_marks,
            'components': components,
            'is_composite': subject.is_composite,
            'grade_id': grade_id,
            'stream_id': stream_id,
            'subject_id': subject_id,
            'term_id': term_id,
            'assessment_type_id': assessment_type_id
        }

        return render_template('upload_subject_marks.html', **upload_data)

    except Exception as e:
        print(f"Error in upload subject marks: {str(e)}")
        flash("Error loading marks upload page.", "error")
        return redirect(url_for('classteacher.collaborative_marks_dashboard'))


@classteacher_bp.route('/submit_subject_marks/<int:grade_id>/<int:stream_id>/<int:subject_id>/<int:term_id>/<int:assessment_type_id>', methods=['POST'])
@classteacher_required
def submit_subject_marks(grade_id, stream_id, subject_id, term_id, assessment_type_id):
    """Handle submission of marks for a specific subject."""
    try:
        current_teacher_id = session.get('teacher_id')
        if not current_teacher_id:
            flash("Please log in to submit marks.", "error")
            return redirect(url_for('auth.classteacher_login'))

        # Check if teacher can upload marks for this subject
        if not CollaborativeMarksService.can_teacher_upload_subject(
            current_teacher_id, subject_id, grade_id, stream_id
        ):
            flash("You are not authorized to upload marks for this subject.", "error")
            return redirect(url_for('classteacher.class_marks_status',
                                  grade_id=grade_id, stream_id=stream_id,
                                  term_id=term_id, assessment_type_id=assessment_type_id))

        # Get required objects
        grade = Grade.query.get(grade_id)
        stream = Stream.query.get(stream_id)
        subject = Subject.query.get(subject_id)
        term = Term.query.get(term_id)
        assessment_type = AssessmentType.query.get(assessment_type_id)

        if not all([grade, stream, subject, term, assessment_type]):
            flash("Invalid parameters for marks submission.", "error")
            return redirect(url_for('classteacher.collaborative_marks_dashboard'))

        # Get students in this stream
        students = Student.query.filter_by(stream_id=stream_id).order_by(Student.name).all()

        # Process marks submission
        marks_added = 0
        marks_updated = 0
        total_marks = request.form.get('total_marks', type=int, default=100)

        for student in students:
            # Get mark value from form
            mark_key = f"mark_{student.name.replace(' ', '_')}_{subject.id}"
            mark_value = request.form.get(mark_key, '')

            if mark_value and mark_value.replace('.', '').isdigit():
                try:
                    raw_mark = float(mark_value)

                    # Sanitize the raw mark
                    raw_mark, sanitized_total_marks = MarkConversionService.sanitize_raw_mark(raw_mark, total_marks)

                    # Calculate percentage
                    percentage = MarkConversionService.calculate_percentage(raw_mark, sanitized_total_marks)

                    # Check if mark already exists
                    existing_mark = Mark.query.filter_by(
                        student_id=student.id,
                        subject_id=subject.id,
                        term_id=term.id,
                        assessment_type_id=assessment_type.id
                    ).first()

                    if existing_mark:
                        # Update existing mark
                        existing_mark.mark = raw_mark
                        existing_mark.total_marks = sanitized_total_marks
                        existing_mark.raw_mark = raw_mark
                        existing_mark.max_raw_mark = sanitized_total_marks
                        existing_mark.percentage = percentage
                        marks_updated += 1
                    else:
                        # Create new mark
                        new_mark = Mark(
                            student_id=student.id,
                            subject_id=subject.id,
                            term_id=term.id,
                            assessment_type_id=assessment_type.id,
                            mark=raw_mark,
                            total_marks=sanitized_total_marks,
                            raw_mark=raw_mark,
                            max_raw_mark=sanitized_total_marks,
                            percentage=percentage
                        )
                        db.session.add(new_mark)
                        marks_added += 1

                except Exception as e:
                    print(f"Error processing mark for {student.name}: {str(e)}")
                    continue

        # Commit changes
        db.session.commit()

        # Update collaborative marks status
        status_result = CollaborativeMarksService.update_marks_status_after_upload(
            grade_id, stream_id, subject_id, term_id, assessment_type_id, current_teacher_id
        )

        # Show success message
        if marks_added > 0 or marks_updated > 0:
            flash(f"Successfully saved {marks_added} new marks and updated {marks_updated} existing marks for {subject.name}.", "success")

            # Add completion status to message
            if status_result.get('is_complete'):
                flash(f"All students now have marks for {subject.name}. Subject is marked as complete!", "success")
        else:
            flash("No marks were processed.", "warning")

        # Redirect back to class marks status
        return redirect(url_for('classteacher.class_marks_status',
                              grade_id=grade_id, stream_id=stream_id,
                              term_id=term_id, assessment_type_id=assessment_type_id))

    except Exception as e:
        print(f"Error submitting subject marks: {str(e)}")
        flash("Error submitting marks. Please try again.", "error")
        return redirect(url_for('classteacher.collaborative_marks_dashboard'))


# ============================================================================
# ENHANCED GRADE REPORT GENERATION SYSTEM
# ============================================================================

@classteacher_bp.route('/grade_reports_dashboard')
@classteacher_required
def grade_reports_dashboard():
    """Dashboard for generating grade-level reports with multiple streams."""
    try:
        # Get all grades
        grades = Grade.query.all()
        terms = Term.query.all()
        assessment_types = AssessmentType.query.all()

        return render_template('grade_reports_dashboard.html',
                             grades=grades,
                             terms=terms,
                             assessment_types=assessment_types)

    except Exception as e:
        print(f"Error in grade reports dashboard: {str(e)}")
        flash("Error loading grade reports dashboard.", "error")
        return redirect(url_for('classteacher.dashboard'))


@classteacher_bp.route('/grade_streams_status/<grade_name>/<term>/<assessment_type>')
@classteacher_required
def grade_streams_status(grade_name, term, assessment_type):
    """Show status of all streams in a grade for report generation."""
    try:
        # Get grade streams status
        status_data = GradeReportService.get_grade_streams_status(grade_name, term, assessment_type)

        if 'error' in status_data:
            flash(f"Error loading grade status: {status_data['error']}", "error")
            return redirect(url_for('classteacher.grade_reports_dashboard'))

        return render_template('grade_streams_status.html', **status_data)

    except Exception as e:
        print(f"Error in grade streams status: {str(e)}")
        flash("Error loading grade streams status.", "error")
        return redirect(url_for('classteacher.grade_reports_dashboard'))


@classteacher_bp.route('/generate_individual_stream_report/<grade_name>/<stream_name>/<term>/<assessment_type>')
@classteacher_required
def generate_individual_stream_report(grade_name, stream_name, term, assessment_type):
    """Generate report for a single stream."""
    try:
        pdf_file = GradeReportService.generate_individual_stream_report(
            grade_name, stream_name, term, assessment_type
        )

        if not pdf_file:
            flash(f"Failed to generate report for {grade_name} Stream {stream_name}", "error")
            return redirect(url_for('classteacher.grade_streams_status',
                                  grade_name=grade_name, term=term, assessment_type=assessment_type))

        # Return the PDF file
        filename = f"{grade_name}_Stream_{stream_name}_{term}_{assessment_type}_Report.pdf"
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Error generating individual stream report: {str(e)}")
        flash("Error generating stream report.", "error")
        return redirect(url_for('classteacher.grade_streams_status',
                              grade_name=grade_name, term=term, assessment_type=assessment_type))


@classteacher_bp.route('/generate_consolidated_grade_report/<grade_name>/<term>/<assessment_type>')
@classteacher_required
def generate_consolidated_grade_report(grade_name, term, assessment_type):
    """Generate consolidated report for entire grade."""
    try:
        # Get selected streams from query parameters
        selected_streams = request.args.getlist('streams')

        pdf_file = GradeReportService.generate_consolidated_grade_report(
            grade_name, term, assessment_type, selected_streams if selected_streams else None
        )

        if not pdf_file:
            flash(f"Failed to generate consolidated report for Grade {grade_name}", "error")
            return redirect(url_for('classteacher.grade_streams_status',
                                  grade_name=grade_name, term=term, assessment_type=assessment_type))

        # Return the PDF file
        filename = f"Grade_{grade_name}_Consolidated_{term}_{assessment_type}_Report.pdf"
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Error generating consolidated grade report: {str(e)}")
        flash("Error generating consolidated report.", "error")
        return redirect(url_for('classteacher.grade_streams_status',
                              grade_name=grade_name, term=term, assessment_type=assessment_type))


@classteacher_bp.route('/generate_batch_grade_reports/<grade_name>/<term>/<assessment_type>')
@classteacher_required
def generate_batch_grade_reports(grade_name, term, assessment_type):
    """Generate batch reports for a grade (individual streams + consolidated)."""
    try:
        # Get options from query parameters
        include_individual = request.args.get('individual', 'true').lower() == 'true'
        include_consolidated = request.args.get('consolidated', 'true').lower() == 'true'
        selected_streams = request.args.getlist('streams')

        zip_file = GradeReportService.generate_batch_grade_reports(
            grade_name, term, assessment_type,
            include_individual, include_consolidated,
            selected_streams if selected_streams else None
        )

        if not zip_file:
            flash(f"Failed to generate batch reports for Grade {grade_name}", "error")
            return redirect(url_for('classteacher.grade_streams_status',
                                  grade_name=grade_name, term=term, assessment_type=assessment_type))

        # Return the ZIP file
        filename = f"Grade_{grade_name}_Batch_Reports_{term}_{assessment_type}.zip"
        return send_file(
            zip_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )

    except Exception as e:
        print(f"Error generating batch grade reports: {str(e)}")
        flash("Error generating batch reports.", "error")
        return redirect(url_for('classteacher.grade_streams_status',
                              grade_name=grade_name, term=term, assessment_type=assessment_type))


@classteacher_bp.route('/database_health', methods=['GET', 'POST'])
@classteacher_required
def database_health():
    """Route for checking and maintaining database health."""
    health_results = None
    creation_results = None
    error_message = None
    success_message = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'check_health':
            try:
                health_results = check_database_health()
                if health_results['status'] == 'healthy':
                    success_message = "Database health check passed! All systems operational."
                elif health_results['status'] == 'warning':
                    success_message = f"Database health check completed with warnings: {'; '.join(health_results['warnings'])}"
                else:
                    error_message = f"Database health check failed: {'; '.join(health_results['errors'])}"
            except Exception as e:
                error_message = f"Error during health check: {str(e)}"

        elif action == 'create_missing_tables':
            try:
                creation_results = create_missing_tables()
                if creation_results['success']:
                    if creation_results['tables_created']:
                        success_message = f"Successfully created missing tables: {', '.join(creation_results['tables_created'])}"
                    else:
                        success_message = "All required tables already exist."
                else:
                    error_message = f"Failed to create tables: {'; '.join(creation_results['errors'])}"
            except Exception as e:
                error_message = f"Error creating tables: {str(e)}"

    # Always run a basic health check for display
    try:
        if not health_results:
            health_results = check_database_health()
    except Exception as e:
        error_message = f"Error running health check: {str(e)}"
        health_results = {'status': 'error', 'errors': [str(e)]}

    return render_template(
        'database_health.html',
        health_results=health_results,
        creation_results=creation_results,
        error_message=error_message,
        success_message=success_message
    )

@classteacher_bp.route('/report_configuration', methods=['GET', 'POST'])
@classteacher_required
def report_configuration():
    """Configure report settings including staff assignments and term dates."""
    try:
        if request.method == 'POST':
            # Handle form submission
            term_name = request.form.get('term')
            if not term_name:
                flash('Please select a term.', 'error')
                return redirect(url_for('classteacher.report_configuration'))

            # Get term object
            term = Term.query.filter_by(name=term_name).first()
            if not term:
                flash('Invalid term selected.', 'error')
                return redirect(url_for('classteacher.report_configuration'))

            # Prepare configuration data
            config_data = {
                'academic_year': request.form.get('academic_year'),
                'term_start_date': request.form.get('term_start_date'),
                'term_end_date': request.form.get('term_end_date'),
                'closing_date': request.form.get('closing_date'),
                'opening_date': request.form.get('opening_date'),
                'headteacher_id': request.form.get('headteacher_id') or None,
                'deputy_headteacher_id': request.form.get('deputy_headteacher_id') or None,
                'principal_id': request.form.get('principal_id') or None,
                'show_headteacher': 'show_headteacher' in request.form,
                'show_deputy_headteacher': 'show_deputy_headteacher' in request.form,
                'show_principal': 'show_principal' in request.form,
                'show_class_teacher': 'show_class_teacher' in request.form,
                'school_name': request.form.get('school_name'),
                'school_address': request.form.get('school_address'),
                'school_phone': request.form.get('school_phone'),
                'school_email': request.form.get('school_email'),
                'school_website': request.form.get('school_website'),
                'report_footer': request.form.get('report_footer')
            }

            # Convert date strings to date objects
            from datetime import datetime
            date_fields = ['term_start_date', 'term_end_date', 'closing_date', 'opening_date']
            for field in date_fields:
                if config_data[field]:
                    try:
                        config_data[field] = datetime.strptime(config_data[field], '%Y-%m-%d').date()
                    except ValueError:
                        config_data[field] = None

            # Update configuration
            teacher_id = session.get('teacher_id')
            ReportConfigService.update_report_config(term.id, config_data, teacher_id)

            flash('Report configuration updated successfully!', 'success')
            return redirect(url_for('classteacher.report_configuration'))

        # GET request - show configuration form
        # Get all terms for selection
        terms = Term.query.all()

        # Get current term configuration
        current_term = request.args.get('term')
        if not current_term and terms:
            current_term = terms[0].name

        config = None
        if current_term:
            config = ReportConfigService.get_report_config_for_term(current_term)

        # Get all teachers for selection
        teachers = ReportConfigService.get_all_teachers_for_selection()

        # Organize teachers by role for easier selection
        teachers_by_role = {
            'headteacher': [t for t in teachers if 'head' in t['role'].lower()],
            'deputy': [t for t in teachers if 'deputy' in t['role'].lower()],
            'principal': [t for t in teachers if 'principal' in t['role'].lower()],
            'all': teachers
        }

        return render_template('report_configuration.html',
                             terms=terms,
                             current_term=current_term,
                             config=config,
                             teachers=teachers,
                             teachers_by_role=teachers_by_role)

    except Exception as e:
        print(f"Error in report configuration: {e}")
        flash(f'Error loading report configuration: {str(e)}', 'error')
        return redirect(url_for('classteacher.dashboard'))