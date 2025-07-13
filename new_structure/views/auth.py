"""
Authentication views for the Hillview School Management System.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
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

# Simple security decorators for now
def sql_injection_protection(f):
    return f

def auth_rate_limit(f):
    return f

class SQLInjectionProtection:
    @staticmethod
    def validate_input(value, field):
        return True

class RCEProtection:
    @staticmethod
    def detect_code_injection(value):
        return False

# Create a blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """Route for the main index/login page."""
    return render_template('login.html')

@auth_bp.route('/admin_login', methods=['GET', 'POST'])
@auth_rate_limit
@sql_injection_protection
def admin_login():
    """Route for headteacher login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Input validation
        if not username or not password:
            return render_template('admin_login.html', error='Username and password required')

        # Length validation
        if len(username) > 100 or len(password) > 128:
            return render_template('admin_login.html', error='Invalid credentials')

        # SQL injection protection
        if not SQLInjectionProtection.validate_input(username, "username"):
            return render_template('admin_login.html', error='Invalid credentials')

        # Command injection protection
        if (RCEProtection.detect_code_injection(username) or
            RCEProtection.detect_code_injection(password)):
            return render_template('admin_login.html', error='Invalid credentials')

        teacher = authenticate_teacher(username, password, 'headteacher')

        if teacher:
            session['teacher_id'] = teacher.id
            session['role'] = 'headteacher'
            session.permanent = True
            return redirect(url_for('admin.dashboard'))
        return render_template('admin_login.html', error='Invalid credentials')

    return render_template('admin_login.html')

@auth_bp.route('/teacher_login', methods=['GET', 'POST'])
@auth_rate_limit
@sql_injection_protection
def teacher_login():
    """Route for teacher login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Input validation
        if not username or not password:
            return render_template('teacher_login.html', error='Username and password required')

        # Length validation
        if len(username) > 100 or len(password) > 128:
            return render_template('teacher_login.html', error='Invalid credentials')

        # SQL injection protection
        if not SQLInjectionProtection.validate_input(username, "username"):
            return render_template('teacher_login.html', error='Invalid credentials')

        # Command injection protection
        if (RCEProtection.detect_code_injection(username) or
            RCEProtection.detect_code_injection(password)):
            return render_template('teacher_login.html', error='Invalid credentials')

        teacher = authenticate_teacher(username, password, 'teacher')

        if teacher:
            session['teacher_id'] = teacher.id
            session['role'] = 'teacher'
            session.permanent = True
            return redirect(url_for('teacher.dashboard'))

        return render_template('teacher_login.html', error='Invalid credentials')

    return render_template('teacher_login.html')

@auth_bp.route('/classteacher_login', methods=['GET', 'POST'])
@auth_rate_limit
@sql_injection_protection
def classteacher_login():
    """Route for class teacher login. Also allows subject teachers with class assignments."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Input validation
        if not username or not password:
            return render_template('classteacher_login.html', error='Username and password required')

        # Length validation
        if len(username) > 100 or len(password) > 128:
            return render_template('classteacher_login.html', error='Invalid credentials')

        # SQL injection protection
        if not SQLInjectionProtection.validate_input(username, "username"):
            return render_template('classteacher_login.html', error='Invalid credentials')

        # Command injection protection
        if (RCEProtection.detect_code_injection(username) or
            RCEProtection.detect_code_injection(password)):
            return render_template('classteacher_login.html', error='Invalid credentials')

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

@auth_bp.route('/mobile-test')
def mobile_test():
    """Mobile responsive test page."""
    return render_template('mobile_test.html')

@auth_bp.route('/dashboard-mobile-test')
def dashboard_mobile_test():
    """Dashboard mobile responsive test page."""
    # Mock data for testing
    mock_data = {
        'school_info': {
            'school_name': 'Hillview School',
            'logo_url': '/static/images/default_logo.png'
        },
        'current_academic_year': '2025/2026',
        'current_term': 'Term 1',
        'performance_alerts': [],
        'system_alerts': []
    }
    return render_template('headteacher.html', **mock_data)

@auth_bp.route('/dashboard-mobile-demo')
def dashboard_mobile_demo():
    """Comprehensive dashboard mobile responsive demo page."""
    return render_template('dashboard_mobile_test.html')

@auth_bp.route('/classteacher-mobile-test')
def classteacher_mobile_test():
    """Class teacher mobile responsive test page."""
    # Mock data for testing
    mock_data = {
        'school_info': {
            'school_name': 'Hillview School',
            'logo_url': '/static/images/default_logo.png'
        },
        'grade': '8',
        'stream': 'A',
        'subjects': ['Mathematics', 'English', 'Science'],
        'students': []
    }
    return render_template('classteacher.html', **mock_data)

@auth_bp.route('/teacher-mobile-test')
def teacher_mobile_test():
    """Teacher mobile responsive test page."""
    # Mock data for testing
    mock_data = {
        'school_info': {
            'school_name': 'Hillview School',
            'logo_url': '/static/images/default_logo.png'
        },
        'teacher_name': 'John Doe',
        'subjects': ['Mathematics', 'Physics'],
        'classes': []
    }
    return render_template('teacher.html', **mock_data)

@auth_bp.route('/forms-mobile-demo')
def forms_mobile_demo():
    """Forms and file upload mobile responsive demo page."""
    return render_template('forms_mobile_demo.html')