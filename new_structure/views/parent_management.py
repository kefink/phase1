"""
Parent Management views for the Hillview School Management System.
This module handles parent account management for headteachers.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from ..services.auth_service import is_authenticated, get_role
from ..models import db
from ..models.parent import Parent, ParentStudent, ParentEmailLog, EmailTemplate
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
    students = db.session.query(Student, Grade, Stream).join(Grade).join(Stream).order_by(Grade.name, Stream.name, Student.name).all()
    
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
        ).join(Student).join(Grade).join(Stream).filter(
            ParentStudent.parent_id == parent_id
        ).order_by(Grade.name, Stream.name, Student.name)
        
        children = children_query.all()
        
        # Get email logs for this parent
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
        ).join(Grade).join(Stream).filter(
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
