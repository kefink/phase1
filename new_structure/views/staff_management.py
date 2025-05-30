"""
Staff Management Views for enhanced teacher and staff administration.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from ..models.user import Teacher
from ..models.academic import SchoolConfiguration
from ..services.staff_assignment_service import StaffAssignmentService
from ..extensions import db

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

@staff_bp.route('/management')
def management():
    """Staff management dashboard."""
    try:
        # Get all teachers
        teachers = Teacher.query.all()

        # Get current leadership
        current_headteacher = StaffAssignmentService.get_headteacher()
        current_deputy = StaffAssignmentService.get_deputy_headteacher()

        # Calculate statistics
        active_teachers = len([t for t in teachers if getattr(t, 'is_active', True)])
        qualified_teachers = len([t for t in teachers if getattr(t, 'qualification', None)])

        # Count class teachers (teachers with role 'classteacher' or assigned to streams)
        class_teachers = len([t for t in teachers if t.role == 'classteacher' or t.stream_id])

        # Get school configuration
        config = SchoolConfiguration.get_config()

        return render_template('staff_management.html',
                             teachers=teachers,
                             current_headteacher=current_headteacher,
                             current_deputy=current_deputy,
                             active_teachers=active_teachers,
                             qualified_teachers=qualified_teachers,
                             class_teachers=class_teachers,
                             config=config)

    except Exception as e:
        flash(f'Error loading staff management: {str(e)}', 'error')
        return redirect(url_for('classteacher.dashboard'))

@staff_bp.route('/assign_headteacher', methods=['POST'])
def assign_headteacher():
    """Assign a teacher as headteacher."""
    try:
        teacher_id = request.json.get('teacher_id')

        if not teacher_id:
            return jsonify({'success': False, 'message': 'Teacher ID required'})

        success = StaffAssignmentService.set_headteacher(teacher_id)

        if success:
            return jsonify({'success': True, 'message': 'Headteacher assigned successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to assign headteacher'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@staff_bp.route('/assign_deputy', methods=['POST'])
def assign_deputy():
    """Assign a teacher as deputy headteacher."""
    try:
        teacher_id = request.json.get('teacher_id')

        if not teacher_id:
            return jsonify({'success': False, 'message': 'Teacher ID required'})

        success = StaffAssignmentService.set_deputy_headteacher(teacher_id)

        if success:
            return jsonify({'success': True, 'message': 'Deputy headteacher assigned successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to assign deputy headteacher'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@staff_bp.route('/teacher/<int:teacher_id>/update', methods=['POST'])
def update_teacher(teacher_id):
    """Update teacher information."""
    try:
        teacher = Teacher.query.get_or_404(teacher_id)

        # Update teacher fields
        teacher.full_name = request.json.get('full_name', teacher.full_name)
        teacher.email = request.json.get('email', teacher.email)
        teacher.phone_number = request.json.get('phone_number', teacher.phone_number)
        teacher.qualification = request.json.get('qualification', teacher.qualification)
        teacher.specialization = request.json.get('specialization', teacher.specialization)

        # Handle is_active field safely
        is_active = request.json.get('is_active')
        if is_active is not None:
            if hasattr(teacher, 'is_active'):
                teacher.is_active = is_active

        db.session.commit()

        return jsonify({'success': True, 'message': 'Teacher updated successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@staff_bp.route('/teacher/<int:teacher_id>/info')
def teacher_info(teacher_id):
    """Get teacher information for editing."""
    try:
        teacher = Teacher.query.get_or_404(teacher_id)

        teacher_data = {
            'id': teacher.id,
            'username': teacher.username,
            'full_name': getattr(teacher, 'full_name', None),
            'email': getattr(teacher, 'email', None),
            'phone_number': getattr(teacher, 'phone_number', None),
            'qualification': getattr(teacher, 'qualification', None),
            'specialization': getattr(teacher, 'specialization', None),
            'employee_id': getattr(teacher, 'employee_id', None),
            'is_active': getattr(teacher, 'is_active', True),
            'role': teacher.role
        }

        return jsonify({'success': True, 'teacher': teacher_data})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@staff_bp.route('/assign_class_teacher', methods=['POST'])
def assign_class_teacher():
    """Assign a teacher as class teacher for a specific grade and stream."""
    try:
        teacher_id = request.json.get('teacher_id')
        grade = request.json.get('grade')
        stream = request.json.get('stream')

        if not all([teacher_id, grade, stream]):
            return jsonify({'success': False, 'message': 'Teacher ID, grade, and stream required'})

        success = StaffAssignmentService.assign_class_teacher(teacher_id, grade, stream)

        if success:
            return jsonify({'success': True, 'message': 'Class teacher assigned successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to assign class teacher'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@staff_bp.route('/staff_report/<grade>/<stream>')
def staff_report(grade, stream):
    """Get staff report for a specific grade and stream."""
    try:
        staff_info = StaffAssignmentService.get_report_staff_info(grade, stream)
        return jsonify({'success': True, 'staff_info': staff_info})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@staff_bp.route('/teachers/list')
def teachers_list():
    """Get list of all teachers for dropdowns."""
    try:
        teachers = Teacher.query.filter_by(is_active=True).all() if hasattr(Teacher, 'is_active') else Teacher.query.all()

        teachers_data = []
        for teacher in teachers:
            teachers_data.append({
                'id': teacher.id,
                'name': getattr(teacher, 'full_name', None) or teacher.username,
                'employee_id': getattr(teacher, 'employee_id', None),
                'role': teacher.role,
                'qualification': getattr(teacher, 'qualification', None)
            })

        return jsonify({'success': True, 'teachers': teachers_data})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@staff_bp.route('/create_teacher', methods=['POST'])
def create_teacher():
    """Create a new teacher."""
    try:
        username = request.json.get('username')
        password = request.json.get('password', 'password123')  # Default password
        role = request.json.get('role', 'teacher')
        full_name = request.json.get('full_name')
        email = request.json.get('email')
        phone_number = request.json.get('phone_number')
        qualification = request.json.get('qualification')
        specialization = request.json.get('specialization')

        if not username:
            return jsonify({'success': False, 'message': 'Username is required'})

        # Check if username already exists
        existing_teacher = Teacher.query.filter_by(username=username).first()
        if existing_teacher:
            return jsonify({'success': False, 'message': 'Username already exists'})

        # Create new teacher
        teacher_data = {
            'username': username,
            'password': password,
            'role': role
        }

        # Add enhanced fields if they exist in the model
        if hasattr(Teacher, 'full_name'):
            teacher_data['full_name'] = full_name
        if hasattr(Teacher, 'email'):
            teacher_data['email'] = email
        if hasattr(Teacher, 'phone_number'):
            teacher_data['phone_number'] = phone_number
        if hasattr(Teacher, 'qualification'):
            teacher_data['qualification'] = qualification
        if hasattr(Teacher, 'specialization'):
            teacher_data['specialization'] = specialization
        if hasattr(Teacher, 'is_active'):
            teacher_data['is_active'] = True

        teacher = Teacher(**teacher_data)

        # Generate employee ID if the field exists
        if hasattr(Teacher, 'employee_id'):
            db.session.add(teacher)
            db.session.flush()  # Get the ID
            teacher.employee_id = f"EMP{teacher.id:03d}"

        db.session.commit()

        return jsonify({'success': True, 'message': 'Teacher created successfully', 'teacher_id': teacher.id})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@staff_bp.route('/subjects/list')
def subjects_list():
    """Get list of all subjects for assignment."""
    try:
        from ..models.academic import Subject

        subjects = Subject.query.all()

        subjects_data = []
        for subject in subjects:
            subjects_data.append({
                'id': subject.id,
                'name': subject.name,
                'education_level': subject.education_level
            })

        return jsonify({'success': True, 'subjects': subjects_data})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@staff_bp.route('/grades/list')
def grades_list():
    """Get list of all grades for assignment."""
    try:
        from ..models.academic import Grade

        grades = Grade.query.all()

        grades_data = []
        for grade in grades:
            grades_data.append({
                'id': grade.id,
                'name': grade.name,
                'education_level': grade.education_level
            })

        return jsonify({'success': True, 'grades': grades_data})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@staff_bp.route('/assign_subjects', methods=['POST'])
def assign_subjects():
    """Assign subjects to a teacher."""
    try:
        from ..models.assignment import TeacherSubjectAssignment
        from ..models.academic import Subject, Grade, Stream

        teacher_id = request.json.get('teacher_id')
        subject_ids = request.json.get('subject_ids', [])

        if not teacher_id:
            return jsonify({'success': False, 'message': 'Teacher ID required'})

        # Get teacher
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            return jsonify({'success': False, 'message': 'Teacher not found'})

        # Clear existing assignments for this teacher
        TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).delete()

        # Create new assignments
        for subject_id in subject_ids:
            subject = Subject.query.get(subject_id)
            if subject:
                # For now, assign to all grades and streams that match the subject's education level
                grades = Grade.query.filter_by(education_level=subject.education_level).all()

                for grade in grades:
                    streams = Stream.query.filter_by(grade_id=grade.id).all()

                    for stream in streams:
                        assignment = TeacherSubjectAssignment(
                            teacher_id=teacher_id,
                            subject_id=subject_id,
                            grade_id=grade.id,
                            stream_id=stream.id,
                            is_class_teacher=False
                        )
                        db.session.add(assignment)

        db.session.commit()

        return jsonify({'success': True, 'message': 'Subject assignments saved successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})