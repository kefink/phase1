"""
Authentication views for the Hillview School Management System.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..services import authenticate_teacher, logout

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
        username = request.form.get('username')
        password = request.form.get('password')
        
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
    """Route for class teacher login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Debug: Print received credentials
        print(f"DEBUG: Login attempt - Username: '{username}', Password: '{password}'")

        teacher = authenticate_teacher(username, password, 'classteacher')

        # Debug: Print authentication result
        print(f"DEBUG: Authentication result - Teacher: {teacher}")

        if teacher:
            print(f"DEBUG: Setting session - Teacher ID: {teacher.id}, Role: classteacher")
            session['teacher_id'] = teacher.id
            session['role'] = 'classteacher'
            session.permanent = True
            print(f"DEBUG: Redirecting to classteacher dashboard")
            return redirect(url_for('classteacher.dashboard'))

        print(f"DEBUG: Authentication failed - returning error")
        return render_template('classteacher_login.html', error='Invalid credentials')

    return render_template('classteacher_login.html')

@auth_bp.route('/logout')
def logout_route():
    """Route for logging out."""
    logout(session)
    return redirect(url_for('auth.index'))