"""
Parent Management views for the Hillview School Management System.
This module handles parent account management for headteachers.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from ..services.auth_service import is_authenticated, get_role
from ..models import db
try:
    from ..models.parent import Parent, ParentStudent, ParentEmailLog, EmailTemplate
except ImportError:
    from ..models.parent import Parent, ParentStudent, EmailTemplate
    ParentEmailLog = None  # Optional when email logs are not enabled
from ..models.academic import Student, Grade, Stream
from ..models.user import Teacher
from datetime import datetime
import secrets
import string

# Create blueprint for parent management
parent_management_bp = Blueprint('parent_management', __name__, url_prefix='/parent_management')

def headteacher_required(f):
    """Decorator to require headteacher authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session) or get_role(session) != 'headteacher':
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@parent_management_bp.route('/debug_session')
def debug_session():
    """Debug route to check session status."""
    return jsonify({
        'session_data': dict(session),
        'is_authenticated': is_authenticated(session),
        'role': get_role(session),
        'teacher_id': session.get('teacher_id')
    })

@parent_management_bp.route('/debug_auth')
def debug_auth():
    """Debug route to check authentication and create test headteacher."""
    from ..models.user import Teacher
    from werkzeug.security import generate_password_hash

    try:
        # Check existing headteachers
        headteachers = Teacher.query.filter_by(role='headteacher').all()

        result = {
            'session_data': dict(session),
            'is_authenticated': is_authenticated(session),
            'role': get_role(session),
            'headteachers_found': len(headteachers),
            'headteacher_accounts': []
        }

        for ht in headteachers:
            result['headteacher_accounts'].append({
                'id': ht.id,
                'username': ht.username,
                'name': ht.name,
                'role': ht.role
            })

        # Create default headteacher if none exists
        if not headteachers:
            default_ht = Teacher(
                username='admin',
                name='System Administrator',
                role='headteacher',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(default_ht)
            db.session.commit()

            result['created_default'] = True
            result['default_credentials'] = {'username': 'admin', 'password': 'admin123'}

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)})

@parent_management_bp.route('/test_dashboard')
def test_dashboard():
    """Test dashboard without authentication (for debugging)."""
    try:
        # Get statistics
        total_parents = Parent.query.count()
        active_parents = Parent.query.filter_by(is_active=True).count()
        verified_parents = Parent.query.filter_by(is_verified=True).count()

        # Get parent-student links
        total_links = ParentStudent.query.count()

        # Get recent parents (last 10)
        recent_parents = Parent.query.order_by(Parent.created_at.desc()).limit(10).all()

        # Get parents without children linked
        parents_without_children = db.session.query(Parent).outerjoin(ParentStudent).filter(ParentStudent.parent_id.is_(None)).all()

        # Get students without parents linked
        students_without_parents = db.session.query(Student).outerjoin(ParentStudent).filter(ParentStudent.student_id.is_(None)).all()

        return render_template('parent_management_dashboard.html',
                             total_parents=total_parents,
                             active_parents=active_parents,
                             verified_parents=verified_parents,
                             total_links=total_links,
                             recent_parents=recent_parents,
                             parents_without_children=parents_without_children,
                             students_without_parents=students_without_parents)

    except Exception as e:
        flash(f'Error loading parent management dashboard: {str(e)}', 'error')
        return f"Error: {str(e)}"

@parent_management_bp.route('/dashboard')
@headteacher_required
def dashboard():
    """Parent management dashboard for headteachers."""
    try:
        # Get filter parameters
        grade_filter = request.args.get('grade_filter', '')
        stream_filter = request.args.get('stream_filter', '')
        education_level_filter = request.args.get('education_level_filter', '')
        search_query = request.args.get('search', '')
        
        # Pagination parameters
        students_page = request.args.get('students_page', 1, type=int)
        parents_page = request.args.get('parents_page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get statistics
        total_parents = Parent.query.count()
        active_parents = Parent.query.filter_by(is_active=True).count()
        verified_parents = Parent.query.filter_by(is_verified=True).count()
        
        # Get parent-student links
        total_links = ParentStudent.query.count()
        
        # Get recent parents (last 10)
        recent_parents = Parent.query.order_by(Parent.created_at.desc()).limit(10).all()
        
        # Get parents without children linked with pagination
        parents_without_children_query = db.session.query(Parent).outerjoin(ParentStudent).filter(ParentStudent.parent_id.is_(None))
        
        # Apply search filter for parents if provided
        if search_query:
            parents_without_children_query = parents_without_children_query.filter(
                db.or_(
                    Parent.first_name.ilike(f'%{search_query}%'),
                    Parent.last_name.ilike(f'%{search_query}%'),
                    Parent.email.ilike(f'%{search_query}%')
                )
            )
        
        parents_without_children_paginated = parents_without_children_query.paginate(
            page=parents_page, per_page=per_page, error_out=False
        )
        
        # Get students without parents linked with filtering and pagination
        students_without_parents_query = db.session.query(Student, Grade, Stream)\
            .join(Grade, Student.grade_id == Grade.id)\
            .join(Stream, Student.stream_id == Stream.id)\
            .outerjoin(ParentStudent, Student.id == ParentStudent.student_id)\
            .filter(ParentStudent.student_id.is_(None))
        
        # Apply filters
        if grade_filter:
            students_without_parents_query = students_without_parents_query.filter(Grade.id == grade_filter)
        
        if stream_filter:
            students_without_parents_query = students_without_parents_query.filter(Stream.id == stream_filter)
        
        if education_level_filter:
            students_without_parents_query = students_without_parents_query.filter(Grade.education_level == education_level_filter)
        
        if search_query:
            students_without_parents_query = students_without_parents_query.filter(
                db.or_(
                    Student.name.ilike(f'%{search_query}%'),
                    Student.admission_number.ilike(f'%{search_query}%')
                )
            )
        
        students_without_parents_query = students_without_parents_query.order_by(Grade.name, Stream.name, Student.name)
        
        students_without_parents_paginated = students_without_parents_query.paginate(
            page=students_page, per_page=per_page, error_out=False
        )
        
        # Get filter options
        all_grades = Grade.query.order_by(Grade.name).all()
        all_streams = Stream.query.order_by(Stream.name).all()
        education_levels = db.session.query(Grade.education_level).distinct().filter(Grade.education_level.isnot(None)).all()
        education_levels = [level[0] for level in education_levels if level[0]]
        
        # Get summary counts for filtered data
        total_students_without_parents = students_without_parents_query.count()
        total_parents_without_children = parents_without_children_query.count()
        
        return render_template('parent_management_dashboard.html',
                             total_parents=total_parents,
                             active_parents=active_parents,
                             verified_parents=verified_parents,
                             total_links=total_links,
                             recent_parents=recent_parents,
                             parents_without_children=parents_without_children_paginated.items,
                             parents_pagination=parents_without_children_paginated,
                             students_without_parents=students_without_parents_paginated.items,
                             students_pagination=students_without_parents_paginated,
                             all_grades=all_grades,
                             all_streams=all_streams,
                             education_levels=education_levels,
                             current_filters={
                                 'grade_filter': grade_filter,
                                 'stream_filter': stream_filter,
                                 'education_level_filter': education_level_filter,
                                 'search_query': search_query,
                                 'per_page': per_page
                             },
                             total_students_without_parents=total_students_without_parents,
                             total_parents_without_children=total_parents_without_children)
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error loading parent management dashboard: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@parent_management_bp.route('/add_parent', methods=['GET', 'POST'])
@headteacher_required
def add_parent():
    """Add a new parent account."""
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            
            # Validation
            if not all([first_name, last_name, email]):
                flash('First name, last name, and email are required.', 'error')
                return render_template('add_parent.html')
            
            # Check if email already exists
            existing_parent = Parent.query.filter_by(email=email).first()
            if existing_parent:
                flash('A parent with this email already exists.', 'error')
                return render_template('add_parent.html')
            
            # Generate temporary password
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            
            # Create parent account
            parent = Parent(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                is_verified=False,  # Will need to verify email
                is_active=True
            )
            parent.set_password(temp_password)
            
            db.session.add(parent)
            db.session.commit()
            
            flash(f'Parent account created successfully! Temporary password: {temp_password}', 'success')
            flash('Please share the temporary password with the parent and ask them to change it after first login.', 'info')
            
            return redirect(url_for('parent_management.dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating parent account: {str(e)}', 'error')
    
    return render_template('add_parent.html')

@parent_management_bp.route('/link_parent_student', methods=['GET', 'POST'])
@headteacher_required
def link_parent_student():
    """Link a parent to a student."""
    if request.method == 'POST':
        try:
            parent_id = request.form.get('parent_id', type=int)
            student_id = request.form.get('student_id', type=int)
            relationship_type = request.form.get('relationship_type', 'parent')
            is_primary_contact = request.form.get('is_primary_contact') == 'on'
            
            # Validation
            if not parent_id or not student_id:
                flash('Please select both parent and student.', 'error')
                return redirect(url_for('parent_management.link_parent_student'))
            
            # Check if link already exists
            existing_link = ParentStudent.query.filter_by(parent_id=parent_id, student_id=student_id).first()
            if existing_link:
                flash('This parent is already linked to this student.', 'error')
                return redirect(url_for('parent_management.link_parent_student'))
            
            # Create the link
            link = ParentStudent(
                parent_id=parent_id,
                student_id=student_id,
                relationship_type=relationship_type,
                is_primary_contact=is_primary_contact,
                created_by=session.get('teacher_id')
            )
            
            db.session.add(link)
            db.session.commit()
            
            flash('Parent and student linked successfully!', 'success')
            return redirect(url_for('parent_management.dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error linking parent and student: {str(e)}', 'error')
    
    # Get all parents and students for the form
    parents = Parent.query.filter_by(is_active=True).order_by(Parent.first_name, Parent.last_name).all()
    students = db.session.query(Student, Grade, Stream)\
        .join(Grade, Student.grade_id == Grade.id)\
        .join(Stream, Student.stream_id == Stream.id)\
        .order_by(Grade.name, Stream.name, Student.name).all()
    
    return render_template('link_parent_student.html', parents=parents, students=students)

@parent_management_bp.route('/view_parent/<int:parent_id>')
@headteacher_required
def view_parent(parent_id):
    """View parent details and linked children."""
    try:
        parent = Parent.query.get_or_404(parent_id)
        
        # Get linked children with their class information
        children_query = db.session.query(
            ParentStudent, Student, Grade, Stream
        ).join(Student, ParentStudent.student_id == Student.id)\
         .join(Grade, Student.grade_id == Grade.id)\
         .join(Stream, Student.stream_id == Stream.id)\
         .filter(ParentStudent.parent_id == parent_id)\
         .order_by(Grade.name, Stream.name, Student.name)
        
        children = children_query.all()
        
        # Get email logs for this parent
        email_logs = []
        if ParentEmailLog:
            email_logs = ParentEmailLog.query.filter_by(parent_id=parent_id).order_by(ParentEmailLog.created_at.desc()).limit(10).all()
        
        return render_template('view_parent.html', 
                             parent=parent, 
                             children=children,
                             email_logs=email_logs)
    
    except Exception as e:
        flash(f'Error viewing parent: {str(e)}', 'error')
        return redirect(url_for('parent_management.dashboard'))

@parent_management_bp.route('/unlink_parent_student/<int:link_id>')
@headteacher_required
def unlink_parent_student(link_id):
    """Remove a parent-student link."""
    try:
        link = ParentStudent.query.get_or_404(link_id)
        parent_name = link.parent.get_full_name()
        student_name = link.student.name
        
        db.session.delete(link)
        db.session.commit()
        
        flash(f'Successfully unlinked {parent_name} from {student_name}.', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error unlinking parent and student: {str(e)}', 'error')
    
    return redirect(url_for('parent_management.dashboard'))

@parent_management_bp.route('/toggle_parent_status/<int:parent_id>')
@headteacher_required
def toggle_parent_status(parent_id):
    """Toggle parent active/inactive status."""
    try:
        parent = Parent.query.get_or_404(parent_id)
        parent.is_active = not parent.is_active
        
        db.session.commit()
        
        status = "activated" if parent.is_active else "deactivated"
        flash(f'Parent account {status} successfully.', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating parent status: {str(e)}', 'error')
    
    return redirect(url_for('parent_management.dashboard'))

@parent_management_bp.route('/search_parents')
@headteacher_required
def search_parents():
    """Search parents by name or email."""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'parents': []})
    
    try:
        parents = Parent.query.filter(
            db.or_(
                Parent.first_name.ilike(f'%{query}%'),
                Parent.last_name.ilike(f'%{query}%'),
                Parent.email.ilike(f'%{query}%')
            )
        ).limit(10).all()
        
        parent_list = []
        for parent in parents:
            parent_list.append({
                'id': parent.id,
                'name': parent.get_full_name(),
                'email': parent.email,
                'phone': parent.phone,
                'is_active': parent.is_active,
                'is_verified': parent.is_verified
            })
        
        return jsonify({'parents': parent_list})
    
    except Exception as e:
        return jsonify({'error': str(e)})

@parent_management_bp.route('/search_students')
@headteacher_required
def search_students():
    """Search students by name or admission number."""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'students': []})
    
    try:
        students_query = db.session.query(
            Student, Grade, Stream
        ).join(Grade, Student.grade_id == Grade.id)\
         .join(Stream, Student.stream_id == Stream.id)\
         .filter(
            db.or_(
                Student.name.ilike(f'%{query}%'),
                Student.admission_number.ilike(f'%{query}%')
            )
        ).limit(10)
        
        student_list = []
        for student, grade, stream in students_query:
            student_list.append({
                'id': student.id,
                'name': student.name,
                'admission_number': student.admission_number,
                'class': f'{grade.name} {stream.name}',
                'grade_id': grade.id,
                'stream_id': stream.id
            })
        
        return jsonify({'students': student_list})
    
    except Exception as e:
        return jsonify({'error': str(e)})

@parent_management_bp.route('/bulk_link_students', methods=['POST'])
@headteacher_required
def bulk_link_students():
    """Bulk link multiple students to a parent."""
    try:
        parent_id = request.form.get('parent_id', type=int)
        student_ids = request.form.getlist('student_ids[]')
        relationship_type = request.form.get('relationship_type', 'parent')
        
        if not parent_id or not student_ids:
            return jsonify({'success': False, 'message': 'Please select a parent and at least one student.'})
        
        # Verify parent exists
        parent = Parent.query.get(parent_id)
        if not parent:
            return jsonify({'success': False, 'message': 'Parent not found.'})
        
        linked_count = 0
        errors = []
        
        for student_id in student_ids:
            try:
                # Check if link already exists
                existing_link = ParentStudent.query.filter_by(parent_id=parent_id, student_id=student_id).first()
                if existing_link:
                    student = Student.query.get(student_id)
                    errors.append(f'{student.name if student else f"Student {student_id}"} is already linked to this parent.')
                    continue
                
                # Create the link
                link = ParentStudent(
                    parent_id=parent_id,
                    student_id=student_id,
                    relationship_type=relationship_type,
                    is_primary_contact=False,
                    created_by=session.get('teacher_id')
                )
                
                db.session.add(link)
                linked_count += 1
                
            except Exception as e:
                errors.append(f'Error linking student {student_id}: {str(e)}')
        
        db.session.commit()
        
        message = f'Successfully linked {linked_count} student(s) to {parent.get_full_name()}.'
        if errors:
            message += f' {len(errors)} error(s): ' + '; '.join(errors[:3])
            if len(errors) > 3:
                message += f' and {len(errors) - 3} more...'
        
        return jsonify({'success': True, 'message': message})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@parent_management_bp.route('/export_unlinked_data')
@headteacher_required
def export_unlinked_data():
    """Export unlinked students and parents data as CSV."""
    try:
        import csv
        from io import StringIO
        from flask import make_response
        
        # Get unlinked students with class information
        students_query = db.session.query(Student, Grade, Stream)\
            .join(Grade, Student.grade_id == Grade.id)\
            .join(Stream, Student.stream_id == Stream.id)\
            .outerjoin(ParentStudent, Student.id == ParentStudent.student_id)\
            .filter(ParentStudent.student_id.is_(None))\
            .order_by(Grade.name, Stream.name, Student.name)
        
        students_data = students_query.all()
        
        # Get unlinked parents
        parents_data = db.session.query(Parent)\
            .outerjoin(ParentStudent)\
            .filter(ParentStudent.parent_id.is_(None))\
            .order_by(Parent.first_name, Parent.last_name).all()
        
        # Create CSV content
        output = StringIO()
        
        # Write students data
        output.write("=== STUDENTS WITHOUT PARENTS ===\n")
        output.write("Name,Admission Number,Grade,Stream,Education Level\n")
        
        for student, grade, stream in students_data:
            output.write(f'"{student.name}","{student.admission_number}","{grade.name}","{stream.name}","{grade.education_level or ""}"\n')
        
        output.write("\n=== PARENTS WITHOUT CHILDREN ===\n")
        output.write("First Name,Last Name,Email,Phone,Status,Verified\n")
        
        for parent in parents_data:
            status = "Active" if parent.is_active else "Inactive"
            verified = "Yes" if parent.is_verified else "No"
            phone = parent.phone or ""
            output.write(f'"{parent.first_name}","{parent.last_name}","{parent.email}","{phone}","{status}","{verified}"\n')
        
        # Create response
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=unlinked_data.csv"
        response.headers["Content-type"] = "text/csv"
        
        return response
    
    except Exception as e:
        flash(f'Error exporting data: {str(e)}', 'error')
        return redirect(url_for('parent_management.dashboard'))
