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

# Create a blueprint for teacher routes
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

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
        streams = Stream.query.filter_by(grade_id=grade_id).all()
        stream_data = [{'id': stream.id, 'name': stream.name} for stream in streams]
        return jsonify({'success': True, 'streams': stream_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

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

    if 'error' in assignment_summary:
        flash(f"Error loading assignments: {assignment_summary['error']}", "error")
        assignment_summary = {
            'teacher': None,
            'role': role,
            'subject_assignments': [],
            'class_teacher_assignments': [],
            'total_subjects_taught': 0,
            'subjects_involved': []
        }

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
    grades = [grade.name for grade in accessible_grades]
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

    # Get recent reports
    recent_reports = []
    pagination_info = None  # Placeholder

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

                # Extract stream letter from "Stream X" format
                stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream

                # Get the stream object
                stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream_letter).first()

                if stream_obj:
                    # Get pagination parameters
                    page = request.form.get('page', 1, type=int)
                    per_page = 20  # Students per page

                    # Get students for this stream with pagination
                    students_query = Student.query.filter_by(stream_id=stream_obj.id).order_by(Student.name)
                    students_pagination = students_query.paginate(
                        page=page, per_page=per_page, error_out=False
                    )
                    students = students_pagination.items

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
                        error_message = f"No students found for grade {grade} stream {stream_letter}"
                else:
                    error_message = f"Stream {stream_letter} not found for grade {grade}"

        # Handle submit marks request (save marks - adapted from classteacher)
        elif "submit_marks" in request.form:
            if not all([education_level, subject, grade, stream, term, assessment_type, total_marks > 0]):
                error_message = "Missing required information"
            else:
                # Extract stream letter and get objects
                stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream
                stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream_letter).first()
                subject_obj = Subject.query.filter_by(name=subject).first()
                term_obj = Term.query.filter_by(name=term).first()
                assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

                if not (stream_obj and subject_obj and term_obj and assessment_type_obj):
                    error_message = "Invalid selection for grade, stream, subject, term, or assessment type"
                else:
                    # Get pagination parameters for marks submission
                    page = request.form.get('page', 1, type=int)
                    per_page = 20  # Students per page

                    # Get students for this stream with pagination
                    students_query = Student.query.filter_by(stream_id=stream_obj.id).order_by(Student.name)
                    students_pagination = students_query.paginate(
                        page=page, per_page=per_page, error_out=False
                    )
                    students = students_pagination.items

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

                                    # Try multiple field naming patterns
                                    possible_keys = [
                                        f"mark_{student_key}_{subject_obj.id}",
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
                            print(f"DEBUG: Final results - marks_added: {marks_added}, marks_updated: {marks_updated}")

                            if marks_added > 0 or marks_updated > 0:
                                show_download_button = True
                                show_subject_report = True  # Enable subject-specific report
                                flash(f"Successfully saved {marks_added} new marks and updated {marks_updated} existing marks.", "success")
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

    # Render the teacher dashboard
    return render_template(
        "teacher.html",
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
    subject = request.args.get('subject')
    grade = request.args.get('grade')
    stream = request.args.get('stream')
    term = request.args.get('term')
    assessment_type = request.args.get('assessment_type')

    if not all([subject, grade, stream, term, assessment_type]):
        flash("Missing required parameters for report generation", "error")
        return redirect(url_for('teacher.dashboard'))

    try:
        # Get database objects
        stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream
        stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream_letter).first()
        subject_obj = Subject.query.filter_by(name=subject).first()
        term_obj = Term.query.filter_by(name=term).first()
        assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

        if not all([stream_obj, subject_obj, term_obj, assessment_type_obj]):
            flash("Invalid parameters for report generation", "error")
            return redirect(url_for('teacher.dashboard'))

        # Get students and their marks for this subject
        students = Student.query.filter_by(stream_id=stream_obj.id).order_by(Student.name).all()

        if not students:
            flash("No students found for this class", "error")
            return redirect(url_for('teacher.dashboard'))

        # Get marks for all students in this subject
        marks_data = []
        total_students = len(students)
        students_with_marks = 0

        for student in students:
            mark = Mark.query.filter_by(
                student_id=student.id,
                subject_id=subject_obj.id,
                term_id=term_obj.id,
                assessment_type_id=assessment_type_obj.id
            ).first()

            if mark:
                students_with_marks += 1
                # Calculate grade based on percentage
                percentage = mark.percentage
                if percentage >= 75:
                    grade_letter = "E.E"
                    grade_description = "Exceeds Expectations"
                elif percentage >= 50:
                    grade_letter = "M.E"
                    grade_description = "Meets Expectations"
                elif percentage >= 30:
                    grade_letter = "A.E"
                    grade_description = "Approaches Expectations"
                else:
                    grade_letter = "B.E"
                    grade_description = "Below Expectations"

                marks_data.append({
                    'student': student,
                    'mark': mark,
                    'percentage': percentage,
                    'grade_letter': grade_letter,
                    'grade_description': grade_description
                })

        # Calculate statistics
        if marks_data:
            percentages = [data['percentage'] for data in marks_data]
            average_percentage = sum(percentages) / len(percentages)
            highest_percentage = max(percentages)
            lowest_percentage = min(percentages)

            # Grade distribution
            grade_distribution = {
                'E.E': len([d for d in marks_data if d['grade_letter'] == 'E.E']),
                'M.E': len([d for d in marks_data if d['grade_letter'] == 'M.E']),
                'A.E': len([d for d in marks_data if d['grade_letter'] == 'A.E']),
                'B.E': len([d for d in marks_data if d['grade_letter'] == 'B.E'])
            }
        else:
            average_percentage = 0
            highest_percentage = 0
            lowest_percentage = 0
            grade_distribution = {'E.E': 0, 'M.E': 0, 'A.E': 0, 'B.E': 0}

        # Prepare report data
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
            'subject_obj': subject_obj
        }

        return render_template('subject_report.html', **report_data)

    except Exception as e:
        flash(f"Error generating report: {str(e)}", "error")
        return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/api/check-composite/<subject>/<education_level>')
@teacher_required
def check_composite_subject(subject, education_level):
    """Check if a subject is composite for the given education level."""
    try:
        from ..services.flexible_subject_service import FlexibleSubjectService

        # Check if subject is composite
        is_composite = FlexibleSubjectService.is_subject_composite(subject, education_level)

        if is_composite:
            # Get component configuration
            components = FlexibleSubjectService.get_subject_components(subject, education_level)
            config = FlexibleSubjectService.get_subject_configuration(subject, education_level)

            return jsonify({
                'success': True,
                'is_composite': True,
                'subject_type': FlexibleSubjectService.detect_subject_type(subject),
                'components': components,
                'config': config
            })
        else:
            return jsonify({
                'success': True,
                'is_composite': False,
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
