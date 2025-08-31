"""
Teacher views for the Hillview School Management System.
Adapted from proven classteacher functionality for single-subject use.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from ..models import Grade, Stream, Subject, Term, AssessmentType, Student, Mark, Teacher, TeacherSubjectAssignment
from ..services import is_authenticated, get_role, RoleBasedDataService
from ..extensions import db
from ..utils import get_performance_category, get_performance_summary
from functools import wraps
# Security utilities: role/resource checks without changing existing behavior
try:
    from ..security.access_control import AccessControlProtection
except Exception:
    try:
        from security.access_control import AccessControlProtection
    except Exception:
        AccessControlProtection = None  # Fallback if security module unavailable

# Create a blueprint for teacher routes
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

def is_mobile_request(request):
    """Detect if the request is from a mobile device."""
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile_keywords = [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry',
        'windows phone', 'opera mini', 'iemobile', 'wpdesktop'
    ]
    return any(keyword in user_agent for keyword in mobile_keywords)

# Decorator for requiring teacher authentication
def teacher_required(f):
    """Decorator to require teacher authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session) or get_role(session) != 'teacher':
            return redirect(url_for('auth.teacher_login'))
        return f(*args, **kwargs)
    return decorated_function

@teacher_bp.route('/get_grade_mapping')
@teacher_required
def get_grade_mapping():
    """API endpoint to get grade level to ID mapping."""
    try:
        grades = Grade.query.all()
        mapping = {grade.name: grade.id for grade in grades}
        return jsonify({'success': True, 'mapping': mapping})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@teacher_bp.route('/get_subject_info/<subject_name>')
@teacher_required
def get_subject_info(subject_name):
    """API endpoint to get subject information including composite status."""
    try:
        # Ensure the requested subject is among teacher's accessible subjects
        try:
            teacher_id = session.get('teacher_id')
            role = session.get('role', 'teacher')
            accessible_subjects = RoleBasedDataService.get_accessible_subjects(teacher_id, role)
            accessible_subject_names = {s.name for s in accessible_subjects}
            if subject_name not in accessible_subject_names:
                return jsonify({'success': False, 'message': 'Unauthorized subject access'}), 403
        except Exception:
            # If access check fails for any reason, continue without breaking existing flow
            pass
        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            return jsonify({'success': False, 'message': 'Subject not found'})

        subject_data = {
            'id': subject.id,
            'name': subject.name,
            'education_level': subject.education_level,
            'is_composite': subject.is_composite,
            'components': []
        }

        if subject.is_composite:
            components = subject.get_components()
            for component in components:
                subject_data['components'].append({
                    'id': component.id,
                    'name': component.name,
                    'weight': component.weight,
                    'max_raw_mark': component.max_raw_mark
                })

        return jsonify({'success': True, 'subject': subject_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@teacher_bp.route('/get_streams/<int:grade_id>')
@teacher_required
def get_streams(grade_id):
    """API endpoint to get streams for a specific grade."""
    try:
        # Verify teacher has access to this grade (and optionally stream) before listing
        try:
            if AccessControlProtection and not AccessControlProtection.check_class_access(
                user_id=session.get('teacher_id'),
                user_role=session.get('role', 'teacher'),
                grade_id=grade_id,
                stream_id=None,
            ):
                return jsonify({'success': False, 'message': 'Unauthorized class access'}), 403
        except Exception:
            # Do not break if security module raises unexpectedly
            pass
        streams = Stream.query.filter_by(grade_id=grade_id).all()
        stream_data = [{'id': stream.id, 'name': stream.name} for stream in streams]
        return jsonify({'success': True, 'streams': stream_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@teacher_bp.route('/debug_log', methods=['POST'])
@teacher_required
def debug_log():
    """Debug endpoint to log frontend issues."""
    try:
        data = request.get_json()
        message = data.get('message', 'No message')
        debug_data = data.get('data', {})
        timestamp = data.get('timestamp', 'No timestamp')

        print(f"\n🐛 FRONTEND DEBUG [{timestamp}]: {message}")
        if debug_data:
            print(f"📊 Debug Data: {debug_data}")
        print("=" * 50)

        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Debug log error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@teacher_bp.route('/mobile', methods=['GET', 'POST'])
@teacher_required
def mobile_dashboard():
    """Mobile-optimized teacher dashboard."""
    # Force mobile template usage
    request.mobile_override = True
    return dashboard()

@teacher_bp.route('/demo')
def mobile_demo():
    """Mobile responsive design demo page."""
    from ..services.school_config_service import SchoolConfigService
    school_config_service = SchoolConfigService()
    school_info = school_config_service.get_school_info()

    return render_template('mobile_demo.html', school_info=school_info)

@teacher_bp.route('/reset', methods=['GET'])
@teacher_required
def reset_form():
    """Reset the teacher dashboard form by clearing problematic data."""
    try:
        # Clear any incomplete composite marks
        from ..models.academic import ComponentMark

        incomplete_marks = db.session.query(ComponentMark).filter(
            ComponentMark.raw_mark.is_(None)
        ).all()

        for mark in incomplete_marks:
            db.session.delete(mark)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"Error during reset: {e}")

    return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/', methods=['GET', 'POST'])
@teacher_required
def dashboard():
    """Teacher dashboard with role-based assignments and single-subject marks upload functionality."""
    # Get current teacher info
    teacher_id = session.get('teacher_id')
    role = session.get('role', 'teacher')

    # Get role-based assignment summary
    assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, role)

    # DEBUG: Print assignment summary details
    print(f"🔍 DEBUG - Teacher ID: {teacher_id}, Role: {role}")
    print(f"🔍 DEBUG - Assignment summary keys: {list(assignment_summary.keys())}")
    print(f"🔍 DEBUG - Assignment summary teacher: {assignment_summary.get('teacher')}")
    print(f"🔍 DEBUG - Subject assignments count: {len(assignment_summary.get('subject_assignments', []))}")

    # Get recent subject reports for this teacher (persisted history)
    try:
        from ..services.report_history_service import list_subject_reports, build_view_url
        history_entries = list_subject_reports(teacher_id)
        # Map newest 10 entries into a simplified structure for the template
        recent_reports = []
        for e in history_entries[:10]:
            # Normalize stream display as "Stream X" when available
            stream_display = e.get('stream') or ''
            if stream_display and not str(stream_display).lower().startswith('stream '):
                stream_display = f"Stream {stream_display}"

            recent_reports.append({
                'grade': e.get('grade', ''),
                'stream': stream_display,
                'term': e.get('term', ''),
                'assessment_type': e.get('assessment_type', ''),
                'class_average': e.get('class_average'),
                'date': (e.get('generated_at') or '')[:10],
                'view_url': build_view_url(e)
            })
        print(f"🔍 DEBUG: Recent reports (history-backed): {len(recent_reports)} items")
    except Exception as e:
        print(f"⚠️ DEBUG: Failed to load recent reports from history: {e}")
        # Fallback to DB-based recent marks summary
        from ..services.teacher_assignment_service import get_teacher_recent_reports
        recent_reports = get_teacher_recent_reports(teacher_id, limit=10)
        print(f"🔍 DEBUG: Fallback recent reports count: {len(recent_reports)}")

    if 'error' in assignment_summary:
        print(f"❌ DEBUG - Error in assignment summary: {assignment_summary['error']}")
        flash(f"Error loading assignments: {assignment_summary['error']}", "error")
        assignment_summary = {
            'teacher': None,
            'role': role,
            'subject_assignments': [],
            'class_teacher_assignments': [],
            'total_subjects_taught': 0,
            'subjects_involved': []
        }
    else:
        print(f"✅ DEBUG - Assignment summary successful")

    # Get accessible data based on role
    accessible_subjects = RoleBasedDataService.get_accessible_subjects(teacher_id, role)
    accessible_grades = RoleBasedDataService.get_accessible_grades(teacher_id, role)
    accessible_streams = RoleBasedDataService.get_accessible_streams(teacher_id, role)

    # Organize subjects by education level (only accessible ones)
    subjects_by_education_level = {
        'lower_primary': [s.name for s in accessible_subjects if s.education_level == 'lower_primary'],
        'upper_primary': [s.name for s in accessible_subjects if s.education_level == 'upper_primary'],
        'junior_secondary': [s.name for s in accessible_subjects if s.education_level == 'junior_secondary']
    }

    # Get form data (only accessible options)
    grades = accessible_grades  # Pass the actual grade objects, not just names
    grades_dict = {grade.name: grade.id for grade in accessible_grades}
    terms = [term.name for term in Term.query.all()]
    assessment_types = [assessment_type.name for assessment_type in AssessmentType.query.all()]

    # Initialize variables
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
    show_subject_report = False

    # Pagination placeholder (used only for student lists)
    pagination_info = None

    # Handle form submission
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

        # Handle upload marks request (load students)
        if "upload_marks" in request.form:
            if not all([education_level, subject, grade, stream, term, assessment_type, total_marks > 0]):
                error_message = "Please fill in all fields before uploading marks"
            else:
                # Get custom component max marks from form (dynamic configuration)
                grammar_max_marks = request.form.get("grammar_max", request.form.get("grammar_max_marks", "60"))
                composition_max_marks = request.form.get("composition_max", request.form.get("composition_max_marks", "40"))
                lugha_max_marks = request.form.get("lugha_max", request.form.get("lugha_max_marks", "60"))
                insha_max_marks = request.form.get("insha_max", request.form.get("insha_max_marks", "40"))

                # Update database components with new max marks if they changed
                subject_obj = Subject.query.filter_by(name=subject).first()
                if subject_obj and subject_obj.is_composite:
                    components = subject_obj.get_components()
                    for component in components:
                        if component.name == "Grammar" and grammar_max_marks != str(component.max_raw_mark):
                            component.max_raw_mark = int(grammar_max_marks)
                            db.session.add(component)
                        elif component.name == "Composition" and composition_max_marks != str(component.max_raw_mark):
                            component.max_raw_mark = int(composition_max_marks)
                            db.session.add(component)
                        elif component.name == "Lugha" and lugha_max_marks != str(component.max_raw_mark):
                            component.max_raw_mark = int(lugha_max_marks)
                            db.session.add(component)
                        elif component.name == "Insha" and insha_max_marks != str(component.max_raw_mark):
                            component.max_raw_mark = int(insha_max_marks)
                            db.session.add(component)

                    # Commit component updates
                    try:
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        print(f"Error updating component max marks: {e}")

                print(f"🔍 DEBUG: Starting stream validation for stream: {stream}, grade: {grade}")

                # Handle both stream ID (from mobile) and stream name (from desktop)
                stream_obj = None

                # Check if stream is a numeric ID (from mobile form)
                if stream.isdigit():
                    stream_id = int(stream)
                    stream_obj = Stream.query.get(stream_id)
                    print(f"🔍 DEBUG: Looking up stream ID {stream_id}, found: {stream_obj}")

                    # Validate that the stream belongs to the selected grade
                    if stream_obj:
                        # Handle both grade ID (from mobile) and grade name (from desktop)
                        if grade.isdigit():
                            # Mobile form submits grade ID
                            grade_id = int(grade)
                            grade_obj = Grade.query.get(grade_id)
                            print(f"🔍 DEBUG: Looking up grade ID {grade_id}, found: {grade_obj}")
                        else:
                            # Desktop form submits grade name
                            grade_obj = Grade.query.filter_by(name=grade).first()
                            print(f"🔍 DEBUG: Looking up grade name '{grade}', found: {grade_obj}")

                        if not grade_obj or stream_obj.grade_id != grade_obj.id:
                            print(f"❌ DEBUG: Stream validation failed - stream belongs to grade {stream_obj.grade_id}, expected {grade_obj.id if grade_obj else 'None'}")
                            stream_obj = None  # Invalid stream for this grade
                        else:
                            print(f"✅ DEBUG: Stream validation passed - stream {stream_id} belongs to grade {grade_obj.name}")
                    else:
                        print(f"❌ DEBUG: Stream ID {stream_id} not found in database")
                else:
                    # Desktop format: extract stream letter from "Stream X" format
                    stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream

                    # Handle both grade ID and grade name for desktop compatibility
                    if grade.isdigit():
                        # Grade submitted as ID
                        grade_id = int(grade)
                        stream_obj = Stream.query.filter_by(
                            name=stream_letter, grade_id=grade_id
                        ).first()
                    else:
                        # Grade submitted as name (original desktop logic)
                        stream_obj = Stream.query.join(Grade).filter(
                            Grade.name == grade, Stream.name == stream_letter
                        ).first()

                if stream_obj:
                    print(f"✅ DEBUG: Stream object found, getting students for stream_id: {stream_obj.id}")

                    # SECURITY: Verify access to selected class/stream before listing students
                    try:
                        grade_obj_for_access = None
                        if grade.isdigit():
                            grade_obj_for_access = Grade.query.get(int(grade))
                        else:
                            grade_obj_for_access = Grade.query.filter_by(name=grade).first()

                        if AccessControlProtection and grade_obj_for_access:
                            allowed = AccessControlProtection.check_class_access(
                                user_id=session.get('teacher_id'),
                                user_role=session.get('role', 'teacher'),
                                grade_id=grade_obj_for_access.id,
                                stream_id=stream_obj.id,
                            )
                            if not allowed:
                                error_message = "You do not have permission to access this class/stream."
                                stream_obj = None
                    except Exception as sec_err:
                        print(f"⚠️ SECURITY: Class access check failed: {sec_err}")

                    # Get pagination parameters
                    page = request.form.get('page', 1, type=int)
                    per_page = 20  # Students per page

                    # Get students for this stream with pagination
                    students_query = Student.query.filter_by(stream_id=stream_obj.id).order_by(Student.name)
                    students_pagination = students_query.paginate(
                        page=page, per_page=per_page, error_out=False
                    )
                    students = students_pagination.items
                    print(f"🔍 DEBUG: Found {len(students)} students for marks processing")

                    # Pagination info
                    pagination_info = {
                        'page': students_pagination.page,
                        'pages': students_pagination.pages,
                        'per_page': students_pagination.per_page,
                        'total': students_pagination.total,
                        'has_prev': students_pagination.has_prev,
                        'prev_num': students_pagination.prev_num,
                        'has_next': students_pagination.has_next,
                        'next_num': students_pagination.next_num
                    }

                    if students:
                        show_students = True
                        show_download_button = False
                    else:
                        stream_name = stream_obj.name if stream_obj else stream
                        error_message = f"No students found for grade {grade} stream {stream_name}"
                else:
                    if stream.isdigit():
                        error_message = f"Stream ID {stream} not found or does not belong to grade {grade}"
                    else:
                        stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream
                        error_message = f"Stream {stream_letter} not found for grade {grade}"

        # Handle submit marks request (save marks - adapted from classteacher)
        elif "submit_marks" in request.form:
            print(f"🔥 DEBUG: Submit marks request received")
            print(f"🔥 DEBUG: Form data: {dict(request.form)}")
            print(f"🔥 DEBUG: Required fields - education_level: {education_level}, subject: {subject}, grade: {grade}, stream: {stream}, term: {term}, assessment_type: {assessment_type}, total_marks: {total_marks}")

            if not all([education_level, subject, grade, stream, term, assessment_type, total_marks > 0]):
                error_message = "Missing required information"
                print(f"❌ DEBUG: Missing required information - stopping processing")
            else:
                print(f"✅ DEBUG: All required fields present, proceeding with marks processing")

                # Use the same validation logic as upload_marks (handle both IDs and names)
                stream_obj = None

                # Check if stream is a numeric ID (from mobile form)
                if stream.isdigit():
                    stream_id = int(stream)
                    stream_obj = Stream.query.get(stream_id)
                    print(f"🔍 DEBUG: Submit - Looking up stream ID {stream_id}, found: {stream_obj}")

                    # Validate that the stream belongs to the selected grade
                    if stream_obj:
                        # Handle both grade ID (from mobile) and grade name (from desktop)
                        if grade.isdigit():
                            # Mobile form submits grade ID
                            grade_id = int(grade)
                            grade_obj = Grade.query.get(grade_id)
                            print(f"🔍 DEBUG: Submit - Looking up grade ID {grade_id}, found: {grade_obj}")
                        else:
                            # Desktop form submits grade name
                            grade_obj = Grade.query.filter_by(name=grade).first()
                            print(f"🔍 DEBUG: Submit - Looking up grade name '{grade}', found: {grade_obj}")

                        if not grade_obj or stream_obj.grade_id != grade_obj.id:
                            print(f"❌ DEBUG: Submit - Stream validation failed")
                            stream_obj = None  # Invalid stream for this grade
                        else:
                            print(f"✅ DEBUG: Submit - Stream validation passed")
                else:
                    # Desktop format: extract stream letter from "Stream X" format
                    stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream

                    # Handle both grade ID and grade name for desktop compatibility
                    if grade.isdigit():
                        # Grade submitted as ID
                        grade_id = int(grade)
                        stream_obj = Stream.query.filter_by(
                            name=stream_letter, grade_id=grade_id
                        ).first()
                    else:
                        # Grade submitted as name (original desktop logic)
                        stream_obj = Stream.query.join(Grade).filter(
                            Grade.name == grade, Stream.name == stream_letter
                        ).first()
                    print(f"🔍 DEBUG: Submit - Desktop stream lookup, found: {stream_obj}")

                # Get other database objects
                subject_obj = Subject.query.filter_by(name=subject).first()
                term_obj = Term.query.filter_by(name=term).first()
                assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

                print(f"🔍 DEBUG: Submit - Database objects - Subject: {subject_obj}, Term: {term_obj}, Assessment: {assessment_type_obj}")

                # SECURITY: Verify access to selected class/stream before saving marks
                try:
                    if stream_obj and AccessControlProtection:
                        allowed = AccessControlProtection.check_class_access(
                            user_id=session.get('teacher_id'),
                            user_role=session.get('role', 'teacher'),
                            grade_id=stream_obj.grade_id,
                            stream_id=stream_obj.id,
                        )
                        if not allowed:
                            error_message = "You do not have permission to submit marks for this class/stream."
                            stream_obj = None
                except Exception as sec_err:
                    print(f"⚠️ SECURITY: Submit access check failed: {sec_err}")

                if not (stream_obj and subject_obj and term_obj and assessment_type_obj):
                    error_message = "Invalid selection for grade, stream, subject, term, or assessment type"
                    print(f"❌ DEBUG: Submit - Missing database objects, stopping processing")
                else:
                    print(f"✅ DEBUG: Submit - All database objects found, proceeding with student lookup")

                    # Get pagination parameters for marks submission
                    page = request.form.get('page', 1, type=int)
                    per_page = 20  # Students per page

                    # Get students for this stream with pagination
                    students_query = Student.query.filter_by(stream_id=stream_obj.id).order_by(Student.name)
                    students_pagination = students_query.paginate(
                        page=page, per_page=per_page, error_out=False
                    )
                    students = students_pagination.items
                    print(f"🔍 DEBUG: Submit - Found {len(students)} students for marks processing")

                    # Pagination info
                    pagination_info = {
                        'page': students_pagination.page,
                        'pages': students_pagination.pages,
                        'per_page': students_pagination.per_page,
                        'total': students_pagination.total,
                        'has_prev': students_pagination.has_prev,
                        'prev_num': students_pagination.prev_num,
                        'has_next': students_pagination.has_next,
                        'next_num': students_pagination.next_num
                    }

                    if not students:
                        error_message = "No students found for this stream"
                    else:
                        marks_added = 0
                        marks_updated = 0

                        print(f"🔥 DEBUG: Submit - Starting marks processing for {len(students)} students")
                        print(f"🔥 DEBUG: Submit - Subject object: {subject_obj.name}, is_composite: {subject_obj.is_composite}")
                        print(f"🔥 DEBUG: Submit - Form keys containing 'mark': {[k for k in request.form.keys() if 'mark_' in k]}")

                        try:
                            # Check if this is a composite subject (using proven classteacher logic)
                            if subject_obj.is_composite:
                                # Handle composite subject marks (English/Kiswahili)
                                components = subject_obj.get_components()

                                print(f"DEBUG: Processing composite subject marks for {len(students)} students")
                                print(f"DEBUG: Form data keys: {list(request.form.keys())}")

                                for student in students:
                                    student_key = student.name.replace(' ', '_')

                                    # Try multiple field naming patterns for composite subjects
                                    possible_percentage_keys = [
                                        f"hidden_percentage_{student_key}_{subject_obj.id}",
                                        f"percentage_{student_key}",
                                        f"hidden_percentage_{student_key}"
                                    ]

                                    percentage_value = 0.0
                                    used_key = ''
                                    for key in possible_percentage_keys:
                                        value = request.form.get(key, type=float, default=0.0)
                                        if value > 0:
                                            percentage_value = value
                                            used_key = key
                                            break

                                    print(f"DEBUG: Student {student.name} -> used key: {used_key}, value: {percentage_value}")

                                    if percentage_value > 0:  # Only process if percentage was calculated
                                        # Check if mark already exists
                                        existing_mark = Mark.query.filter_by(
                                            student_id=student.id,
                                            subject_id=subject_obj.id,
                                            term_id=term_obj.id,
                                            assessment_type_id=assessment_type_obj.id
                                        ).first()

                                        if existing_mark:
                                            # Update existing mark
                                            existing_mark.percentage = percentage_value
                                            existing_mark.raw_mark = (percentage_value / 100) * total_marks
                                            existing_mark.mark = existing_mark.raw_mark
                                            existing_mark.max_raw_mark = total_marks
                                            existing_mark.total_marks = total_marks
                                            marks_updated += 1
                                        else:
                                            # Create new mark
                                            new_mark = Mark(
                                                student_id=student.id,
                                                subject_id=subject_obj.id,
                                                term_id=term_obj.id,
                                                assessment_type_id=assessment_type_obj.id,
                                                grade_id=stream_obj.grade_id,  # Use grade from stream_obj (from form)
                                                stream_id=stream_obj.id,  # Use stream from stream_obj (from form)
                                                percentage=percentage_value,
                                                raw_mark=(percentage_value / 100) * total_marks,
                                                raw_total_marks=total_marks,  # Use correct field name
                                                mark=(percentage_value / 100) * total_marks,  # For backward compatibility
                                                total_marks=total_marks  # For backward compatibility
                                            )
                                            db.session.add(new_mark)
                                            db.session.flush()  # Get the ID
                                            marks_added += 1

                                        # Save component marks (using proven classteacher logic)
                                        from ..models.academic import ComponentMark
                                        for component in components:
                                            component_key = f"component_{student_key}_{component.id}"
                                            component_value = request.form.get(component_key, '')

                                            if component_value and component_value.isdigit():
                                                component_mark = int(component_value)
                                                component_percentage = (component_mark / component.max_raw_mark) * 100

                                                # Find existing component mark or create new one
                                                component_mark_obj = ComponentMark.query.filter_by(
                                                    mark_id=existing_mark.id if existing_mark else new_mark.id,
                                                    component_id=component.id
                                                ).first()

                                                if component_mark_obj:
                                                    # Update existing component mark
                                                    component_mark_obj.raw_mark = component_mark
                                                    component_mark_obj.max_raw_mark = component.max_raw_mark
                                                    component_mark_obj.percentage = component_percentage
                                                else:
                                                    # Create new component mark
                                                    component_mark_obj = ComponentMark(
                                                        mark_id=existing_mark.id if existing_mark else new_mark.id,
                                                        component_id=component.id,
                                                        raw_mark=component_mark,
                                                        max_raw_mark=component.max_raw_mark,
                                                        percentage=component_percentage
                                                    )
                                                    db.session.add(component_mark_obj)
                            else:
                                # Handle regular subjects (using proven classteacher logic)
                                print(f"DEBUG: Processing regular subject marks for {len(students)} students")
                                print(f"DEBUG: Form data keys: {list(request.form.keys())}")

                                for student in students:
                                    student_key = student.name.replace(' ', '_')

                                    # Try multiple field naming patterns (MOBILE USES mark_{student.id})
                                    possible_keys = [
                                        f"mark_{student.id}",  # MOBILE FORMAT - ADD THIS FIRST!
                                        f"mark_{student_key}_{subject_obj.id}",
                                        f"mark_{student_key}_{subject_obj.name}",  # Add subject name pattern
                                        f"mark_{student_key}_1",
                                        f"mark_{student_key}",
                                        f"mark_{student_key}_{subject_obj.name.replace(' ', '').lower()}"
                                    ]

                                    mark_value = ''
                                    used_key = ''
                                    for key in possible_keys:
                                        value = request.form.get(key, '')
                                        if value:
                                            mark_value = value
                                            used_key = key
                                            break

                                    print(f"DEBUG: Student {student.name} -> used key: {used_key}, value: '{mark_value}'")

                                    if mark_value and mark_value.replace('.', '').replace('-', '').isdigit():
                                        mark = float(mark_value)
                                        if 0 <= mark <= total_marks:
                                            percentage = (mark / total_marks) * 100

                                            # Additional validation: Ensure percentage doesn't exceed 100%
                                            if percentage > 100:
                                                print(f"DEBUG: Skipping {student.name} - percentage {percentage:.1f}% exceeds 100%")
                                                continue

                                            # Check if mark already exists
                                            existing_mark = Mark.query.filter_by(
                                                student_id=student.id,
                                                subject_id=subject_obj.id,
                                                term_id=term_obj.id,
                                                assessment_type_id=assessment_type_obj.id
                                            ).first()

                                            if existing_mark:
                                                # Update existing mark
                                                existing_mark.percentage = percentage
                                                existing_mark.raw_mark = mark
                                                existing_mark.mark = mark
                                                existing_mark.max_raw_mark = total_marks
                                                existing_mark.total_marks = total_marks
                                                marks_updated += 1
                                            else:
                                                # Create new mark
                                                new_mark = Mark(
                                                    student_id=student.id,
                                                    subject_id=subject_obj.id,
                                                    term_id=term_obj.id,
                                                    assessment_type_id=assessment_type_obj.id,
                                                    grade_id=stream_obj.grade_id,  # Use grade from stream_obj (from form)
                                                    stream_id=stream_obj.id,  # Use stream from stream_obj (from form)
                                                    percentage=percentage,
                                                    raw_mark=mark,
                                                    max_raw_mark=total_marks,
                                                    mark=mark,
                                                    total_marks=total_marks
                                                )
                                                db.session.add(new_mark)
                                                marks_added += 1

                            # Commit all changes
                            db.session.commit()

                            # Show success message and enable subject report download
                            print(f"🎉 DEBUG: Submit - Final results - marks_added: {marks_added}, marks_updated: {marks_updated}")

                            if marks_added > 0 or marks_updated > 0:
                                show_download_button = True
                                show_subject_report = True  # Enable subject-specific report
                                flash(f"Successfully saved {marks_added} new marks and updated {marks_updated} existing marks.", "success")

                                # Check if this is a mobile request and redirect to subject report
                                use_mobile = request.args.get('mobile') == 'true' or request.form.get('mobile') == 'true'
                                print(f"📱 DEBUG: Submit - Mobile request detected: {use_mobile}")

                                if use_mobile:
                                    print(f"🚀 DEBUG: Submit - Redirecting to subject report for mobile")
                                    print(f"🚀 DEBUG: Submit - Redirect params: subject={subject}, grade={grade}, stream={stream}, term={term}, assessment_type={assessment_type}")
                                    # For mobile, redirect to subject report after successful submission
                                    return redirect(url_for('teacher.generate_subject_report',
                                                          subject=subject, grade=grade, stream=stream,
                                                          term=term, assessment_type=assessment_type,
                                                          mobile='true'))
                                else:
                                    print(f"🖥️ DEBUG: Submit - Desktop request, staying on current page")
                            else:
                                print("DEBUG: No marks were processed - checking form data...")
                                print(f"DEBUG: Total form fields: {len(request.form)}")
                                print(f"DEBUG: Form keys containing 'mark': {[k for k in request.form.keys() if 'mark' in k.lower()]}")
                                error_message = "No marks were processed. Please ensure you have entered marks for at least one student."

                        except Exception as e:
                            db.session.rollback()
                            error_message = f"Error saving marks: {str(e)}"

    # Get component max marks - prioritize form values over database values
    if request.method == "POST":
        # Use form values if available (from configuration)
        grammar_max_marks = request.form.get("grammar_max", request.form.get("grammar_max_marks", "60"))
        composition_max_marks = request.form.get("composition_max", request.form.get("composition_max_marks", "40"))
        lugha_max_marks = request.form.get("lugha_max", request.form.get("lugha_max_marks", "60"))
        insha_max_marks = request.form.get("insha_max", request.form.get("insha_max_marks", "40"))
    else:
        # Default values from database for initial load
        grammar_max_marks = "60"
        composition_max_marks = "40"
        lugha_max_marks = "60"
        insha_max_marks = "40"

        # Get current component max marks from database for display
        if subject:
            subject_obj = Subject.query.filter_by(name=subject).first()
            if subject_obj and subject_obj.is_composite:
                components = subject_obj.get_components()
                for component in components:
                    if component.name == "Grammar":
                        grammar_max_marks = str(component.max_raw_mark or 60)
                    elif component.name == "Composition":
                        composition_max_marks = str(component.max_raw_mark or 40)
                    elif component.name == "Lugha":
                        lugha_max_marks = str(component.max_raw_mark or 60)
                    elif component.name == "Insha":
                        insha_max_marks = str(component.max_raw_mark or 40)

    # Get school information
    from ..services.school_config_service import SchoolConfigService
    school_info = SchoolConfigService.get_school_info_dict()

    # Check if mobile template should be used (based on user agent, query parameter, or route override)
    use_mobile = (
        request.args.get('mobile', '').lower() == 'true' or
        is_mobile_request(request) or
        hasattr(request, 'mobile_override')
    )

    template_name = "teacher_mobile.html" if use_mobile else "teacher.html"

    # Debug template variables before rendering
    print(f"🎯 DEBUG: Template variables before rendering:")
    print(f"  - show_students: {show_students}")
    print(f"  - students count: {len(students) if students else 0}")
    print(f"  - education_level: {education_level}")
    print(f"  - subject: {subject}")
    print(f"  - grade: {grade}")
    print(f"  - stream: {stream}")
    print(f"  - use_mobile: {use_mobile}")

    # Render the teacher dashboard
    return render_template(
        template_name,
        grades=grades,
        grades_dict=grades_dict,
        subjects_by_education_level=subjects_by_education_level,
        terms=terms,
        school_info=school_info,
        assessment_types=assessment_types,
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
        show_download_button=show_download_button,
        show_subject_report=show_subject_report,
        recent_reports=recent_reports,
        pagination_info=pagination_info,
        grammar_max_marks=grammar_max_marks,
        composition_max_marks=composition_max_marks,
        lugha_max_marks=lugha_max_marks,
        insha_max_marks=insha_max_marks,
        # Role-based assignment data
        assignment_summary=assignment_summary,
        subject_assignments=assignment_summary.get('subject_assignments', []),
        class_teacher_assignments=assignment_summary.get('class_teacher_assignments', []),
        total_subjects_taught=assignment_summary.get('total_subjects_taught', 0),
        can_manage_classes=assignment_summary.get('can_manage_classes', False),
        accessible_subjects=accessible_subjects,
        accessible_grades=accessible_grades,
        accessible_streams=accessible_streams
    )


@teacher_bp.route('/generate_subject_report')
@teacher_required
def generate_subject_report():
    """Generate enhanced subject-specific report with grading analysis."""
    print(f"🔍 GENERATE_SUBJECT_REPORT CALLED")
    subject = request.args.get('subject')
    grade = request.args.get('grade')
    stream = request.args.get('stream')
    term = request.args.get('term')
    assessment_type = request.args.get('assessment_type')
    print(f"Parameters: subject={subject}, grade={grade}, stream={stream}, term={term}, assessment_type={assessment_type}")

    if not all([subject, grade, stream, term, assessment_type]):
        flash("Missing required parameters for report generation", "error")
        return redirect(url_for('teacher.dashboard'))

    # SECURITY: Ensure the requested subject is accessible to the current teacher
    try:
        teacher_id = session.get('teacher_id')
        role = session.get('role', 'teacher')
        accessible_subjects = RoleBasedDataService.get_accessible_subjects(teacher_id, role)
        accessible_subject_names = {s.name for s in accessible_subjects}
        if subject not in accessible_subject_names:
            print(f"🚫 SECURITY: Unauthorized subject access attempt - teacher {teacher_id} subject '{subject}'")
            flash("You do not have permission to generate a report for this subject.", "error")
            return redirect(url_for('teacher.dashboard'))
    except Exception as sec_err:
        # Do not break flow if security helper raises unexpectedly
        print(f"⚠️ SECURITY: Subject access check failed: {sec_err}")

    try:
        # Get database objects with comprehensive error handling

        # 1. Find Grade (handle both ID and name)
        print(f"🔍 Looking for grade: '{grade}'")
        if grade.isdigit():
            # Mobile submits grade ID
            grade_id = int(grade)
            grade_obj = Grade.query.get(grade_id)
            print(f"Grade lookup by ID {grade_id}: {grade_obj}")
        else:
            # Desktop submits grade name
            grade_obj = Grade.query.filter_by(name=grade).first()
            print(f"Grade lookup by name '{grade}': {grade_obj}")

        if not grade_obj:
            print(f"❌ Grade '{grade}' not found")
            flash(f"Grade '{grade}' not found in database", "error")
            return redirect(url_for('teacher.dashboard'))

        # 2. Find Stream (handle both ID and name)
        print(f"🔍 Looking for stream: '{stream}'")
        if stream.isdigit():
            # Mobile submits stream ID
            stream_id = int(stream)
            stream_obj = Stream.query.get(stream_id)
            print(f"Stream lookup by ID {stream_id}: {stream_obj}")

            # Validate that stream belongs to the grade
            if stream_obj and stream_obj.grade_id != grade_obj.id:
                print(f"❌ Stream {stream_id} belongs to grade {stream_obj.grade_id}, not {grade_obj.id}")
                stream_obj = None
        else:
            # Desktop submits stream name
            stream_letter = stream.replace("Stream ", "").strip() if stream.startswith("Stream ") else stream.strip()
            print(f"🔍 Looking for stream name: '{stream_letter}' in grade_id: {grade_obj.id}")
            stream_obj = Stream.query.filter_by(grade_id=grade_obj.id, name=stream_letter).first()
            print(f"Stream lookup by name: {stream_obj}")

        # Fallback strategies for stream (only for name-based lookups)
        if not stream_obj and not stream.isdigit():
            print(f"❌ Stream '{stream}' not found, trying fallback")
            # Try with just the last character
            if len(stream) > 0:
                alt_stream_letter = stream[-1]
                print(f"🔍 Trying alternative stream: '{alt_stream_letter}'")
                stream_obj = Stream.query.filter_by(grade_id=grade_obj.id, name=alt_stream_letter).first()
                print(f"Alternative stream found: {stream_obj}")

        # 3. Find Subject
        print(f"🔍 Looking for subject: '{subject}'")
        subject_obj = Subject.query.filter_by(name=subject).first()
        print(f"Subject found: {subject_obj}")

        # 4. Find Term
        print(f"🔍 Looking for term: '{term}'")
        term_obj = Term.query.filter_by(name=term).first()
        print(f"Term found: {term_obj}")

        # 5. Find Assessment Type with fallback strategies
        print(f"🔍 Looking for assessment type: '{assessment_type}'")
        assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()
        print(f"Assessment type found: {assessment_type_obj}")

        # If not found, try case-insensitive search and common variations
        if not assessment_type_obj:
            print(f"❌ Assessment type '{assessment_type}' not found, trying alternatives")

            # Try case-insensitive search
            assessment_type_obj = AssessmentType.query.filter(AssessmentType.name.ilike(assessment_type)).first()
            print(f"Case-insensitive search result: {assessment_type_obj}")

            # Try common variations
            if not assessment_type_obj:
                variations = [
                    assessment_type.upper(),
                    assessment_type.lower(),
                    assessment_type.title(),
                    f"{assessment_type}s",  # plural
                    assessment_type.replace(" ", "_"),  # underscore
                    assessment_type.replace("_", " "),  # space
                ]

                for variation in variations:
                    assessment_type_obj = AssessmentType.query.filter_by(name=variation).first()
                    if assessment_type_obj:
                        print(f"Found assessment type with variation '{variation}': {assessment_type_obj}")
                        break

            # If still not found, show available assessment types
            if not assessment_type_obj:
                all_assessments = AssessmentType.query.all()
                available_assessments = [a.name for a in all_assessments]
                print(f"❌ No assessment type found. Available: {available_assessments}")

        # Check if all required objects were found
        print(f"🔍 Checking if all objects found...")
        missing_objects = []
        if not stream_obj:
            missing_objects.append(f"Stream '{stream}' in {grade}")
        if not subject_obj:
            missing_objects.append(f"Subject '{subject}'")
        if not term_obj:
            missing_objects.append(f"Term '{term}'")
        if not assessment_type_obj:
            missing_objects.append(f"Assessment '{assessment_type}'")

        if missing_objects:
            print(f"❌ Missing objects: {missing_objects}")
            flash(f"Cannot generate report - missing: {', '.join(missing_objects)}", "error")
            return redirect(url_for('teacher.dashboard'))

        print(f"✅ All database objects found successfully!")
        print(f"Proceeding with report generation...")

        # SECURITY: Verify access to selected class/stream before generating report
        try:
            if AccessControlProtection and grade_obj and stream_obj:
                allowed = AccessControlProtection.check_class_access(
                    user_id=session.get('teacher_id'),
                    user_role=session.get('role', 'teacher'),
                    grade_id=grade_obj.id,
                    stream_id=stream_obj.id,
                )
                if not allowed:
                    print("🚫 SECURITY: Unauthorized class/stream access for report generation")
                    flash("You do not have permission to generate a report for this class/stream.", "error")
                    return redirect(url_for('teacher.dashboard'))
        except Exception as sec_err:
            print(f"⚠️ SECURITY: Class access check failed during report generation: {sec_err}")

        # Get students and their marks for this subject
        print(f"🔍 Looking for students in stream_id: {stream_obj.id}")
        students = Student.query.filter_by(stream_id=stream_obj.id).order_by(Student.name).all()
        print(f"Students found: {len(students)} students")

        if not students:
            print(f"❌ No students found for stream_id: {stream_obj.id}")
            flash("No students found for this class", "error")
            return redirect(url_for('teacher.dashboard'))

        print(f"✅ Found {len(students)} students, proceeding with marks retrieval...")

        # Get marks for all students in this subject
        print(f"🔍 Processing marks for {len(students)} students...")
        marks_data = []
        total_students = len(students)
        students_with_marks = 0

        for i, student in enumerate(students, 1):
            print(f"🔍 Processing student {i}/{len(students)}: {student.name} (ID: {student.id})")
            try:
                mark = Mark.query.filter_by(
                    student_id=student.id,
                    subject_id=subject_obj.id,
                    term_id=term_obj.id,
                    assessment_type_id=assessment_type_obj.id
                ).first()
                print(f"Mark found for {student.name}: {mark}")

                if mark:
                    print(f"✅ Mark found for {student.name}: {mark.raw_mark}/{mark.total_marks} = {mark.percentage}%")
                    students_with_marks += 1
                    # Calculate grade based on percentage using detailed CBC grading
                    percentage = mark.percentage
                    if percentage >= 90:
                        grade_letter = "EE1"
                        grade_description = "Exceeding Expectation 1"
                    elif percentage >= 75:
                        grade_letter = "EE2"
                        grade_description = "Exceeding Expectation 2"
                    elif percentage >= 58:
                        grade_letter = "ME1"
                        grade_description = "Meeting Expectation 1"
                    elif percentage >= 41:
                        grade_letter = "ME2"
                        grade_description = "Meeting Expectation 2"
                    elif percentage >= 31:
                        grade_letter = "AE1"
                        grade_description = "Approaching Expectation 1"
                    elif percentage >= 21:
                        grade_letter = "AE2"
                        grade_description = "Approaching Expectation 2"
                    elif percentage >= 11:
                        grade_letter = "BE1"
                        grade_description = "Below Expectation 1"
                    else:
                        grade_letter = "BE2"
                        grade_description = "Below Expectation 2"

                    marks_data.append({
                        'student': student,
                        'mark': mark,
                        'percentage': percentage,
                        'grade_letter': grade_letter,
                        'grade_description': grade_description
                    })
                    print(f"✅ Added {student.name} to marks_data with grade {grade_letter}")
                else:
                    print(f"❌ No mark found for {student.name}")

            except Exception as e:
                print(f"❌ Error processing student {student.name}: {str(e)}")
                import traceback
                traceback.print_exc()
                flash(f"Error processing marks for {student.name}: {str(e)}", "error")
                return redirect(url_for('teacher.dashboard'))

        # Calculate statistics
        print(f"🔍 Marks processing completed. Found {len(marks_data)} students with marks out of {len(students)} total students")
        if marks_data:
            percentages = [data['percentage'] for data in marks_data]
            average_percentage = sum(percentages) / len(percentages)
            highest_percentage = max(percentages)
            lowest_percentage = min(percentages)

            # Grade distribution using detailed CBC grading
            grade_distribution = {
                'EE1': len([d for d in marks_data if d['grade_letter'] == 'EE1']),
                'EE2': len([d for d in marks_data if d['grade_letter'] == 'EE2']),
                'ME1': len([d for d in marks_data if d['grade_letter'] == 'ME1']),
                'ME2': len([d for d in marks_data if d['grade_letter'] == 'ME2']),
                'AE1': len([d for d in marks_data if d['grade_letter'] == 'AE1']),
                'AE2': len([d for d in marks_data if d['grade_letter'] == 'AE2']),
                'BE1': len([d for d in marks_data if d['grade_letter'] == 'BE1']),
                'BE2': len([d for d in marks_data if d['grade_letter'] == 'BE2'])
            }
        else:
            average_percentage = 0
            highest_percentage = 0
            lowest_percentage = 0
            grade_distribution = {'EE1': 0, 'EE2': 0, 'ME1': 0, 'ME2': 0, 'AE1': 0, 'AE2': 0, 'BE1': 0, 'BE2': 0}

        # Get teacher information
        print(f"🔍 Getting teacher information...")
        teacher_id = session.get('teacher_id')
        teacher = Teacher.query.get(teacher_id) if teacher_id else None
        teacher_name = teacher.full_name if teacher else "Unknown Teacher"
        print(f"Teacher: {teacher_name} (ID: {teacher_id})")

        # Get school information
        print(f"🔍 Getting school information...")
        try:
            from ..services.school_config_service import SchoolConfigService
            school_info = SchoolConfigService.get_school_info_dict()
            # Add logo_url for template compatibility
            if 'logo_path' in school_info:
                school_info['logo_url'] = f"/static/{school_info['logo_path']}"
            print(f"✅ School info retrieved successfully")
        except Exception as e:
            print(f"❌ Error getting school info: {e}")
            school_info = {
                'school_name': 'Hillview School',
                'logo_url': '/static/uploads/logos/optimized_school_logo_1750595986_hvs.jpg'
            }

    # Prepare report data
        print(f"🔍 Preparing report data...")
        report_data = {
            'subject': subject,
            'grade': grade,
            'stream': stream,
            'term': term,
            'assessment_type': assessment_type,
            'total_students': total_students,
            'students_with_marks': students_with_marks,
            'marks_data': marks_data,
            'statistics': {
                'average_percentage': round(average_percentage, 2),
                'highest_percentage': round(highest_percentage, 2),
                'lowest_percentage': round(lowest_percentage, 2),
                'grade_distribution': grade_distribution
            },
            'subject_obj': subject_obj,
            'teacher_name': teacher_name,
            'school_info': school_info
        }
        print(f"✅ Report data prepared successfully")

        print(f"🔍 Attempting to render template 'subject_report.html'...")
        try:
            # Add mobile support to report data
            use_mobile = request.args.get('mobile') == 'true'
            report_data['use_mobile'] = use_mobile

            # Cache the report for recent reports functionality
            from ..services.cache_service import cache_report
            try:
                # Use grade name for caching (consistent with recent reports)
                grade_name = grade_obj.name
                stream_name = stream_obj.name

                cache_report(
                    grade=grade_name,
                    stream=stream_name,
                    term=term,
                    assessment_type=assessment_type,
                    report_data=report_data,
                    expiry=86400  # 24 hours
                )
                print(f"✅ DEBUG: Report cached successfully for recent reports")
            except Exception as cache_error:
                print(f"⚠️ DEBUG: Report caching failed: {cache_error}")

            # Record in report history (file-based, no migration)
            try:
                from ..services.report_history_service import record_subject_report
                avg = report_data['statistics']['average_percentage'] if report_data.get('statistics') else 0
                record_subject_report(
                    teacher_id=teacher_id or 0,
                    subject_id=subject_obj.id,
                    subject_name=subject_obj.name,
                    grade_id=grade_obj.id,
                    grade_name=grade_obj.name,
                    stream_id=stream_obj.id if stream_obj else None,
                    stream_name=stream_obj.name if stream_obj else '',
                    term_id=term_obj.id,
                    term_name=term_obj.name,
                    assessment_type_id=assessment_type_obj.id,
                    assessment_type_name=assessment_type_obj.name,
                    total_students=total_students,
                    students_with_marks=students_with_marks,
                    class_average=avg,
                )
                print("✅ DEBUG: Report history recorded")
            except Exception as history_error:
                print(f"⚠️ DEBUG: Failed to record report history: {history_error}")

            return render_template('subject_report.html', **report_data)
        except Exception as template_error:
            print(f"❌ Template rendering error: {template_error}")
            import traceback
            traceback.print_exc()
            flash(f"Error rendering report template: {str(template_error)}", "error")
            return redirect(url_for('teacher.dashboard'))

    except Exception as e:
        flash(f"Error generating report: {str(e)}", "error")
        return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/api/check-composite/<subject>/<education_level>')
@teacher_required
def check_composite_subject(subject, education_level):
    """Check if a subject is composite for the given education level."""
    try:
        from ..services.flexible_subject_service import FlexibleSubjectService

        # Get subject object to include ID
        subject_obj = Subject.query.filter_by(name=subject).first()
        subject_id = subject_obj.id if subject_obj else None

        # Check if subject is composite
        is_composite = FlexibleSubjectService.is_subject_composite(subject, education_level)

        if is_composite:
            # Get component configuration
            components = FlexibleSubjectService.get_subject_components(subject, education_level)
            config = FlexibleSubjectService.get_subject_configuration(subject, education_level)

            return jsonify({
                'success': True,
                'is_composite': True,
                'subject': {'id': subject_id, 'name': subject},
                'subject_type': FlexibleSubjectService.detect_subject_type(subject),
                'components': components,
                'config': config
            })
        else:
            return jsonify({
                'success': True,
                'is_composite': False,
                'subject': {'id': subject_id, 'name': subject},
                'subject_type': FlexibleSubjectService.detect_subject_type(subject),
                'components': [],
                'config': None
            })

    except Exception as e:
        print(f"Error checking if subject is composite: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@teacher_bp.route('/edit_marks')
@teacher_required
def edit_marks():
    """Edit marks for a specific subject assessment."""
    try:
        # Get parameters from URL
        subject = request.args.get('subject')
        grade = request.args.get('grade')
        stream = request.args.get('stream')
        term = request.args.get('term')
        assessment_type = request.args.get('assessment_type')

        if not all([subject, grade, stream, term, assessment_type]):
            flash("Missing required parameters for editing marks.", "error")
            return redirect(url_for('teacher.dashboard'))

        # Get database objects
        grade_obj = Grade.query.filter_by(name=grade).first()
        if not grade_obj:
            flash(f"Grade '{grade}' not found.", "error")
            return redirect(url_for('teacher.dashboard'))

        stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream
        stream_obj = Stream.query.filter_by(name=stream_letter, grade_id=grade_obj.id).first()
        if not stream_obj:
            flash(f"Stream '{stream}' not found for grade '{grade}'.", "error")
            return redirect(url_for('teacher.dashboard'))

        subject_obj = Subject.query.filter_by(name=subject).first()
        if not subject_obj:
            flash(f"Subject '{subject}' not found.", "error")
            return redirect(url_for('teacher.dashboard'))

        term_obj = Term.query.filter_by(name=term).first()
        if not term_obj:
            flash(f"Term '{term}' not found.", "error")
            return redirect(url_for('teacher.dashboard'))

        assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()
        if not assessment_type_obj:
            flash(f"Assessment type '{assessment_type}' not found.", "error")
            return redirect(url_for('teacher.dashboard'))

        # Get students in this stream
        students = Student.query.filter_by(stream_id=stream_obj.id).order_by(Student.name).all()
        if not students:
            flash(f"No students found in {grade} {stream}.", "error")
            return redirect(url_for('teacher.dashboard'))

        # Get existing marks for these students
        existing_marks = {}
        for student in students:
            mark = Mark.query.filter_by(
                student_id=student.id,
                subject_id=subject_obj.id,
                term_id=term_obj.id,
                assessment_type_id=assessment_type_obj.id
            ).first()
            if mark:
                existing_marks[student.id] = {
                    'raw_mark': mark.raw_mark,
                    'max_raw_mark': mark.max_raw_mark,
                    'percentage': round((mark.raw_mark / mark.max_raw_mark) * 100, 1) if mark.max_raw_mark > 0 else 0
                }

        # Prepare template data
        template_data = {
            'subject': subject,
            'grade': grade,
            'stream': stream,
            'term': term,
            'assessment_type': assessment_type,
            'students': students,
            'existing_marks': existing_marks,
            'total_students': len(students),
            'students_with_marks': len(existing_marks),
            'is_composite': subject_obj.is_composite if subject_obj else False
        }

        return render_template('edit_marks.html', **template_data)

    except Exception as e:
        print(f"❌ Error loading edit marks page: {e}")
        flash(f"Error loading edit marks page: {str(e)}", "error")
        return redirect(url_for('teacher.dashboard'))


@teacher_bp.route('/update_marks', methods=['POST'])
@teacher_required
def update_marks():
    """Update marks with validation to ensure they don't exceed 100%."""
    try:
        # Get form data
        subject = request.form.get('subject')
        grade = request.form.get('grade')
        stream = request.form.get('stream')
        term = request.form.get('term')
        assessment_type = request.form.get('assessment_type')

        if not all([subject, grade, stream, term, assessment_type]):
            flash("Missing required information.", "error")
            return redirect(url_for('teacher.dashboard'))

        # Get database objects
        grade_obj = Grade.query.filter_by(name=grade).first()
        stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream
        stream_obj = Stream.query.filter_by(name=stream_letter, grade_id=grade_obj.id).first()
        subject_obj = Subject.query.filter_by(name=subject).first()
        term_obj = Term.query.filter_by(name=term).first()
        assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

        if not all([grade_obj, stream_obj, subject_obj, term_obj, assessment_type_obj]):
            flash("Invalid selection parameters.", "error")
            return redirect(url_for('teacher.dashboard'))

        # Get students
        students = Student.query.filter_by(stream_id=stream_obj.id).all()

        marks_updated = 0
        validation_errors = []

        for student in students:
            mark_field = f"mark_{student.id}"
            max_mark_field = f"max_mark_{student.id}"

            if mark_field in request.form and max_mark_field in request.form:
                try:
                    raw_mark = float(request.form[mark_field])
                    max_mark = float(request.form[max_mark_field])

                    # Validation: Ensure marks don't exceed max marks
                    if raw_mark > max_mark:
                        validation_errors.append(f"{student.name}: Mark ({raw_mark}) cannot exceed maximum ({max_mark})")
                        continue

                    # Validation: Ensure percentage doesn't exceed 100%
                    percentage = (raw_mark / max_mark) * 100 if max_mark > 0 else 0
                    if percentage > 100:
                        validation_errors.append(f"{student.name}: Percentage ({percentage:.1f}%) cannot exceed 100%")
                        continue

                    # Validation: Ensure marks are not negative
                    if raw_mark < 0 or max_mark <= 0:
                        validation_errors.append(f"{student.name}: Invalid mark values")
                        continue

                    # Find existing mark or create new one
                    mark = Mark.query.filter_by(
                        student_id=student.id,
                        subject_id=subject_obj.id,
                        term_id=term_obj.id,
                        assessment_type_id=assessment_type_obj.id
                    ).first()

                    if mark:
                        # Update existing mark
                        mark.raw_mark = raw_mark
                        mark.max_raw_mark = max_mark
                        mark.percentage = percentage
                    else:
                        # Create new mark
                        mark = Mark(
                            student_id=student.id,
                            subject_id=subject_obj.id,
                            term_id=term_obj.id,
                            assessment_type_id=assessment_type_obj.id,
                            raw_mark=raw_mark,
                            max_raw_mark=max_mark,
                            percentage=percentage
                        )
                        db.session.add(mark)

                    marks_updated += 1

                except ValueError:
                    validation_errors.append(f"{student.name}: Invalid number format")
                    continue

        # Show validation errors if any
        if validation_errors:
            for error in validation_errors:
                flash(error, "error")

            # If there were validation errors, redirect back to edit page
            if marks_updated == 0:
                return redirect(url_for('teacher.edit_marks',
                                      subject=subject, grade=grade, stream=stream,
                                      term=term, assessment_type=assessment_type))

        # Commit changes
        if marks_updated > 0:
            db.session.commit()
            flash(f"Successfully updated {marks_updated} marks.", "success")
        else:
            flash("No marks were updated.", "warning")

        # Redirect back to the subject report
        return redirect(url_for('teacher.generate_subject_report',
                              subject=subject, grade=grade, stream=stream,
                              term=term, assessment_type=assessment_type))

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error updating marks: {e}")
        flash(f"Error updating marks: {str(e)}", "error")
        return redirect(url_for('teacher.dashboard'))


@teacher_bp.route('/api/report-history')
@teacher_required
def api_report_history():
    """Return report history for the logged-in teacher with optional filters."""
    try:
        teacher_id = session.get('teacher_id')
        if not teacher_id:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        # Map filter params (accept both ids and names where possible)
        subject = request.args.get('subject')
        subject_id = None
        if subject:
            subj_obj = Subject.query.filter_by(name=subject).first()
            subject_id = subj_obj.id if subj_obj else None

        grade = request.args.get('grade')
        grade_id = None
        if grade:
            grade_id = int(grade) if grade.isdigit() else (Grade.query.filter_by(name=grade).first().id if Grade.query.filter_by(name=grade).first() else None)

        stream = request.args.get('stream')
        stream_id = None
        if stream:
            if stream.isdigit():
                stream_id = int(stream)
            else:
                # accept formats like 'A' or 'Stream A'
                stream_letter = stream.replace('Stream ', '').strip()
                stream_obj = Stream.query.filter_by(name=stream_letter).first()
                stream_id = stream_obj.id if stream_obj else None

        term = request.args.get('term')
        term_id = None
        if term:
            term_obj = Term.query.filter_by(name=term).first()
            term_id = term_obj.id if term_obj else None

        assessment_type = request.args.get('assessment_type')
        assessment_type_id = None
        if assessment_type:
            at_obj = AssessmentType.query.filter_by(name=assessment_type).first()
            assessment_type_id = at_obj.id if at_obj else None

        from ..services.report_history_service import list_subject_reports, build_view_url

        entries = list_subject_reports(
            teacher_id,
            subject_id=subject_id,
            grade_id=grade_id,
            stream_id=stream_id,
            term_id=term_id,
            assessment_type_id=assessment_type_id,
        )

        # Add view_url for convenience
        for e in entries:
            try:
                e['view_url'] = build_view_url(e)
            except Exception:
                e['view_url'] = None

        return jsonify({'success': True, 'count': len(entries), 'items': entries})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
