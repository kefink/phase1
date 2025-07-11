"""
Authentication views for the Hillview School Management System.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
try:
    from ..services import authenticate_teacher, logout
except ImportError:
    try:
        from services import authenticate_teacher, logout
    except ImportError:
        # Mock functions for testing
        def authenticate_teacher(username, password, role):
            return None
        def logout(session):
            session.clear()

# Create a blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """Route for the main index/login page."""
    return render_template('login.html')

@auth_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """Route for headteacher login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        teacher = authenticate_teacher(username, password, 'headteacher')

        if teacher:
            session['teacher_id'] = teacher.id
            session['role'] = 'headteacher'
            session.permanent = True
            return redirect(url_for('admin.dashboard'))
        return render_template('admin_login.html', error='Invalid credentials')

    return render_template('admin_login.html')

@auth_bp.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    """Route for teacher login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        teacher = authenticate_teacher(username, password, 'teacher')
        
        if teacher:
            session['teacher_id'] = teacher.id
            session['role'] = 'teacher'
            session.permanent = True
            return redirect(url_for('teacher.dashboard'))
        
        return render_template('teacher_login.html', error='Invalid credentials')
    
    return render_template('teacher_login.html')

@auth_bp.route('/classteacher_login', methods=['GET', 'POST'])
def classteacher_login():
    """Route for class teacher login. Also allows subject teachers with class assignments."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # First try to authenticate as classteacher
        teacher = authenticate_teacher(username, password, 'classteacher')

        if teacher:
            session['teacher_id'] = teacher.id
            session['role'] = 'classteacher'
            session.permanent = True
            return redirect(url_for('classteacher.dashboard'))

        # If classteacher auth failed, try as subject teacher with class assignments
        teacher = authenticate_teacher(username, password, 'teacher')

        if teacher:
            # Check if this subject teacher has class assignments
            from ..services.flexible_marks_service import FlexibleMarksService
            can_access = FlexibleMarksService.can_teacher_access_classteacher_portal(teacher.id)

            if can_access:
                session['teacher_id'] = teacher.id
                session['role'] = 'teacher'  # Keep original role but allow access
                session.permanent = True
                return redirect(url_for('classteacher.dashboard'))
            else:
                return render_template('classteacher_login.html',
                                     error='You don\'t have any class assignments. Please use the subject teacher portal.')

        return render_template('classteacher_login.html', error='Invalid credentials')

    return render_template('classteacher_login.html')

@auth_bp.route('/logout')
def logout_route():
    """Route for logging out."""
    logout(session)
    return redirect(url_for('auth.index'))