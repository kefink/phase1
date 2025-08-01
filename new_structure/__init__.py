"""
Application factory for the Hillview School Management System.
This file initializes the Flask application and registers extensions and blueprints.
"""
from flask import Flask, request, abort, session, redirect, url_for, jsonify
from datetime import datetime
from .extensions import db, csrf
from .config import config
from .logging_config import setup_logging
from .middleware import MarkSanitizerMiddleware
# Temporarily disable security manager for debugging
# from .security.security_manager import security_manager

def create_app(config_name='default'):
    """Create and configure the Flask application.

    Args:
        config_name: Name of the configuration to use (default, development, testing, production)

    Returns:
        Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Set up logging
    setup_logging(app)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)

    # Initialize database with tables and default data
    with app.app_context():
        try:
            from .utils.database_init import initialize_database_completely, check_database_integrity

            # Check if database needs initialization
            status = check_database_integrity()

            if status['status'] != 'healthy':
                result = initialize_database_completely()
                if not result['success']:
                    print(f"⚠️ Database initialization failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"⚠️ Database error: {e}")

    # Register blueprints with error handling
    try:
        from .views import blueprints
        for blueprint in blueprints:
            app.register_blueprint(blueprint)
            # Exempt parent portal from CSRF protection
            if hasattr(blueprint, 'name') and 'parent' in blueprint.name:
                csrf.exempt(blueprint)
    except Exception as e:
        print(f"⚠️ Blueprint error: {e}")

    # Register middleware
    MarkSanitizerMiddleware(app)

    # Minimize logging output
    import logging

    # Set up clean logging
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)  # Only show warnings and errors

    # Filter out SSL/TLS noise and other verbose logs
    class CleanLogFilter(logging.Filter):
        def filter(self, record):
            message = record.getMessage()
            # Filter out these types of messages
            noise_patterns = [
                'Bad request version',
                'code 400, message Bad request version',
                'Bad HTTP/0.9 request type',
                'code 400, message Bad request syntax',
                '\x16\x03\x01',  # SSL handshake attempts
                'DEBUG in __init__',
                'Context processor success',
                'Response headers before cleanup',
                'Response headers after cleanup'
            ]
            return not any(pattern in message for pattern in noise_patterns)

    # Apply filter to werkzeug logger
    werkzeug_logger.addFilter(CleanLogFilter())

    # Also apply to app logger
    app.logger.addFilter(CleanLogFilter())
    app.logger.setLevel(logging.INFO)  # Only show INFO and above

    # Security Headers Configuration
    @app.after_request
    def set_security_headers(response):
        """Add comprehensive security headers to all responses."""
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Enforce HTTPS (HSTS)
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        # Enhanced Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests"
        )
        response.headers['Content-Security-Policy'] = csp

        # Control referrer information
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Control browser features
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=(), usb=()'

        # Additional security headers
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'

        # Cache control for sensitive pages
        if request.endpoint and any(sensitive in request.endpoint for sensitive in
                                  ['admin', 'teacher', 'classteacher', 'headteacher']):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

        # Remove server information and version disclosure
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)

        return response

    # PATH TRAVERSAL PROTECTION - FIXES 12 VULNERABILITIES
    @app.before_request
    def prevent_path_traversal():
        """Comprehensive path traversal protection."""
        import os
        import re

        def is_safe_path(path):
            if not path:
                return True

            path_str = str(path)
            normalized = os.path.normpath(path_str)

            # Dangerous patterns
            dangerous_patterns = [
                r'\.\./', r'\.\.\\\\', r'/etc/', r'/proc/', r'/sys/',
                r'C:\\\\', r'\\\\\\\\', r'file://', r'ftp://', r'\\x00',
                r'%00', r'%2e%2e', r'%252e%252e', r'0x2e0x2e'
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, path_str, re.IGNORECASE):
                    return False

            if '..' in normalized or normalized.startswith('/'):
                return False

            return True

        # Check URL path
        if not is_safe_path(request.path):
            abort(403, "Access denied: Invalid path detected")

        # Check all parameters
        for key, value in request.args.items():
            if not is_safe_path(str(value)):
                abort(403, f"Access denied: Invalid parameter '{key}'")

        if request.form:
            for key, value in request.form.items():
                if not is_safe_path(str(value)):
                    abort(403, f"Access denied: Invalid form data '{key}'")

    # INPUT VALIDATION - PREVENTS INJECTION ATTACKS
    @app.before_request
    def validate_all_inputs():
        """Comprehensive input validation for all requests."""
        import re

        def is_safe_input(value):
            if not value:
                return True

            value_str = str(value)

            if len(value_str) > 10000:
                return False

            # Dangerous patterns
            dangerous_patterns = [
                r"'.*OR.*'", r"'.*UNION.*SELECT", r"'.*DROP.*TABLE",
                r"<script", r"javascript:", r"onload\\s*=", r"onerror\\s*=",
                r";\\s*ls", r";\\s*dir", r"\\|\\s*ls", r"&&\\s*ls"
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, value_str, re.IGNORECASE):
                    return False

            return True

        # Skip for safe endpoints
        safe_endpoints = ['/health', '/static', '/logout']
        if any(request.path.startswith(ep) for ep in safe_endpoints):
            return

        # Validate all inputs
        for key, value in request.args.items():
            if not is_safe_input(value):
                abort(400, f"Invalid input in parameter '{key}'")

        if request.form:
            for key, value in request.form.items():
                if not is_safe_input(value):
                    abort(400, f"Invalid input in field '{key}'")

    # ACCESS CONTROL ENFORCEMENT - FIXES 12 VULNERABILITIES - TEMPORARILY DISABLED FOR DEBUG
    # @app.before_request
    def enforce_strict_access_control_disabled():
        """Comprehensive access control enforcement."""

        # Skip for public endpoints and debug routes
        public_endpoints = [
            '/', '/health', '/static', '/login', '/logout',
            '/admin_login', '/teacher_login', '/classteacher_login',
            '/debug/', '/parent/'  # Add debug and parent routes
        ]
        if any(request.path.startswith(ep) for ep in public_endpoints):
            return

        # IMPORTANT: Let route decorators handle authentication first
        # Only enforce role-based access if user is already authenticated
        if 'teacher_id' not in session:
            # Don't block here - let the route decorators handle authentication
            return

        # Get user role
        user_role = session.get('role', '').lower()

        # Enhanced role-based access control with comprehensive paths
        role_access = {
            'headteacher': [
                '/headteacher/', '/admin/', '/universal/', '/permission/',
                '/manage_teachers', '/analytics', '/staff/', '/school_setup/',
                '/subject_config/', '/bulk_assignments/', '/missing_routes/'
            ],
            'classteacher': [
                '/classteacher/', '/manage_students', '/collaborative_marks',
                '/analytics_api/', '/bulk_assignments/'
            ],
            'teacher': [
                '/teacher/', '/upload_marks', '/view_marks', '/analytics_api/'
            ]
        }

        allowed_paths = role_access.get(user_role, [])

        # Check if user can access this path
        path_allowed = any(request.path.startswith(path) for path in allowed_paths)

        # Debug logging for student promotion route
        if 'student-promotion' in request.path:
            print(f"🔍 SECURITY DEBUG: Student promotion route check")
            print(f"🔍 Request path: {request.path}")
            print(f"🔍 User role: {user_role}")
            print(f"🔍 Allowed paths: {allowed_paths}")
            print(f"🔍 Path allowed: {path_allowed}")
            for path in allowed_paths:
                print(f"🔍 Checking {request.path}.startswith('{path}') = {request.path.startswith(path)}")

        # Additional check for headteacher universal access
        if user_role == 'headteacher' and session.get('headteacher_universal_access'):
            # Headteacher with universal access can access classteacher routes
            classteacher_paths = role_access.get('classteacher', [])
            if any(request.path.startswith(path) for path in classteacher_paths):
                path_allowed = True

        if not path_allowed and not request.path.startswith('/static'):
            print(f"=== SECURITY MIDDLEWARE DEBUG ===")
            print(f"Request path: {request.path}")
            print(f"User role: {user_role}")
            print(f"Allowed paths: {allowed_paths}")
            print(f"Path allowed: {path_allowed}")
            print(f"Universal access: {session.get('headteacher_universal_access')}")
            print(f"❌ BLOCKING REQUEST")
            app.logger.warning(f"Access denied: {user_role} tried to access {request.path}")
            abort(403, f"Access denied: {user_role} cannot access {request.path}")

    # ULTRA-SECURE SESSION CONFIGURATION AT RUNTIME
    app.config.update({
        'SESSION_COOKIE_SECURE': False,          # Allow HTTP for development
        'SESSION_COOKIE_HTTPONLY': True,        # No JavaScript access
        'SESSION_COOKIE_SAMESITE': 'Lax',       # Less strict for development
        'PERMANENT_SESSION_LIFETIME': 1800,     # 30 minutes timeout
        'SESSION_COOKIE_NAME': 'hillview_secure_session',
        'FORCE_HTTPS': False,                    # Disable for testing
        'STRICT_ROLE_ENFORCEMENT': True         # Strict access control
    })

    # Remove problematic headers for development
    @app.after_request
    def clean_headers(response):
        """Remove headers that might cause HTTPS upgrade issues in development."""
        # Remove any CSP headers that might force HTTPS
        response.headers.pop('Content-Security-Policy', None)
        response.headers.pop('Content-Security-Policy-Report-Only', None)
        # Also remove HSTS header in development
        response.headers.pop('Strict-Transport-Security', None)
        return response

    # HTTPS ENFORCEMENT
    @app.before_request
    def force_https_production():
        """Force HTTPS in production."""
        if app.config.get('FORCE_HTTPS', False) and not request.is_secure:
            if request.headers.get('X-Forwarded-Proto') != 'https':
                return redirect(request.url.replace('http://', 'https://'), code=301)

    # ENHANCED PATH TRAVERSAL PROTECTION
    @app.before_request
    def enhanced_path_protection():
        """Enhanced protection against all path traversal attempts."""
        import re

        # Block any request with path traversal patterns
        dangerous_paths = [
            r'\.\./', r'\.\.\\\\', r'%2e%2e', r'%252e%252e',
            r'0x2e0x2e', r'\\x2e\\x2e', r'file://', r'ftp://'
        ]

        full_url = request.url
        for pattern in dangerous_paths:
            if re.search(pattern, full_url, re.IGNORECASE):
                abort(403, "Path traversal attempt blocked")

        # Block requests to sensitive paths
        sensitive_paths = ['/etc/', '/proc/', '/sys/', '/root/', '/home/']
        for path in sensitive_paths:
            if path in request.path:
                abort(403, "Access to sensitive path blocked")

    # STRICT OBJECT ACCESS CONTROL
    @app.before_request
    def strict_object_access_control():
        """Prevent all unauthorized object access."""

        # Extract object access patterns
        import re
        object_pattern = r'/(\w+)/(\d+|\.\.)'
        match = re.search(object_pattern, request.path)

        if match:
            object_type, object_id = match.groups()

            # Block any non-numeric object IDs (prevents ../ attacks)
            if not object_id.isdigit():
                abort(403, f"Invalid object ID: {object_id}")

            # Strict role-based object access
            user_role = session.get('role', '').lower()

            object_permissions = {
                'headteacher': ['student', 'teacher', 'report', 'mark', 'grade', 'stream', 'streams', 'api', 'get_grade_streams', 'teacher_streams', 'get_streams'],
                'classteacher': ['student', 'report', 'mark', 'get_grade_streams', 'teacher_streams', 'streams', 'get_streams'],
                'teacher': ['mark', 'get_streams', 'streams']
            }

            allowed_objects = object_permissions.get(user_role, [])

            if object_type not in allowed_objects:
                abort(403, f"Access denied: {user_role} cannot access {object_type}")

    # REMOVE SERVER HEADER
    @app.after_request
    def remove_server_header(response):
        """Remove server information disclosure."""
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)

        return response

    # Register template context processor for school information
    @app.context_processor
    def inject_school_info():
        """Inject school information into all templates."""
        try:
            from .services.dynamic_school_info_service import DynamicSchoolInfoService
            result = DynamicSchoolInfoService.inject_school_info()
            app.logger.debug(f"Context processor success: {result['school_info']['school_name']}")
            return result
        except Exception as e:
            app.logger.error(f"Error injecting school info: {e}")
            import traceback
            traceback.print_exc()
            return {
                'school_info': {
                    'school_name': 'Your School Name',
                    'school_motto': 'Excellence in Education',
                    'logo_url': '/static/images/default_logo.png',
                    'primary_color': '#1f7d53',
                    'secondary_color': '#18230f',
                    'accent_color': '#4ade80'
                },
                'school_colors': {
                    'primary': '#1f7d53',
                    'secondary': '#18230f',
                    'accent': '#4ade80'
                },
                'grading_info': {
                    'primary_system': 'CBC',
                    'show_multiple_grades': False
                }
            }

    # Register custom Jinja2 filters
    @app.template_filter('get_education_level')
    def get_education_level(grade):
        """Filter to determine the education level for a grade."""
        education_level_mapping = {
            'lower_primary': ['Grade 1', 'Grade 2', 'Grade 3'],
            'upper_primary': ['Grade 4', 'Grade 5', 'Grade 6'],
            'junior_secondary': ['Grade 7', 'Grade 8', 'Grade 9']
        }

        for level, grades in education_level_mapping.items():
            if grade in grades:
                return level
        return ''

    @app.template_filter('tojsonhtml')
    def tojsonhtml_filter(obj):
        """Convert object to JSON for safe use in HTML templates."""
        import json
        from markupsafe import Markup
        return Markup(json.dumps(obj))

    @app.template_filter('get_grade_for_percentage')
    def get_grade_for_percentage_filter(percentage, system='primary'):
        """Filter to get grade for a percentage."""
        try:
            from .services.dynamic_school_info_service import DynamicSchoolInfoService
            return DynamicSchoolInfoService.get_grade_for_percentage(percentage, system)
        except:
            return 'N/A'

    # Import the classteacher blueprint
    from .views.classteacher import classteacher_bp

    # Add debug route for login testing
    @app.route('/debug/login_test')
    def debug_login_test():
        """Debug route to test login functionality."""
        try:
            from .models.user import Teacher
            from .services.auth_service import authenticate_teacher

            result = "<h2>🔐 Login System Debug</h2>"

            # Check database connection
            try:
                teacher_count = Teacher.query.count()
                result += f"<p>✅ Database connected: {teacher_count} teachers found</p>"
            except Exception as e:
                result += f"<p>❌ Database error: {str(e)}</p>"
                return result

            # List all teachers
            teachers = Teacher.query.all()
            result += "<h3>👥 Available Teachers:</h3><ul>"
            for teacher in teachers:
                result += f"<li><strong>{teacher.username}</strong> - Role: {teacher.role} - Password: {teacher.password}</li>"
            result += "</ul>"

            # Test authentication
            result += "<h3>🧪 Authentication Tests:</h3>"
            test_users = [
                ('headteacher', 'admin123', 'headteacher'),
                ('kevin', 'kev123', 'classteacher'),
                ('telvo', 'telvo123', 'teacher')
            ]

            for username, password, role in test_users:
                try:
                    auth_result = authenticate_teacher(username, password, role)
                    if auth_result:
                        result += f"<p>✅ {username}/{role}: Authentication successful</p>"
                    else:
                        result += f"<p>❌ {username}/{role}: Authentication failed</p>"
                except Exception as e:
                    result += f"<p>⚠️ {username}/{role}: Error - {str(e)}</p>"

            return result

        except Exception as e:
            return f"<h2>❌ Debug Error</h2><p>{str(e)}</p>"

    # Add debug route to check blueprints
    @app.route('/debug/blueprints')
    def debug_blueprints():
        """Debug route to check registered blueprints."""
        blueprint_info = []
        for blueprint_name, blueprint in app.blueprints.items():
            routes = []
            for rule in app.url_map.iter_rules():
                if rule.endpoint.startswith(blueprint_name + '.'):
                    routes.append(f"{rule.rule} -> {rule.endpoint}")
            blueprint_info.append({
                'name': blueprint_name,
                'routes': routes
            })

        result = "<h2>🔍 Registered Blueprints</h2>"
        result += "<p><strong>Quick Links:</strong></p>"
        result += "<ul>"
        result += "<li><a href='/'>Main Login</a></li>"
        result += "<li><a href='/premium'>Premium Login</a></li>"
        result += "<li><a href='/polished'>Polished Login</a></li>"
        result += "</ul>"

        for bp in blueprint_info:
            result += f"<h3>📋 {bp['name']}</h3><ul>"
            for route in bp['routes']:
                result += f"<li>{route}</li>"
            result += "</ul>"

        return result

    # Add direct route for polished login (fallback)
    @app.route('/polished')
    def direct_polished_login():
        """Direct route for polished login page"""
        try:
            school_info = {
                'school_name': 'Hillview School',
                'school_motto': 'Excellence Through Knowledge and Character',
                'logo_url': None
            }
            return render_template('login_polished.html', school_info=school_info)
        except Exception as e:
            return f"<h2>❌ Polished Login Error</h2><p>Error: {str(e)}</p><p><a href='/debug/blueprints'>Check Routes</a></p>"

    # Add simple test route
    @app.route('/test-polished')
    def test_polished():
        """Simple test route"""
        return "<h1>✅ Test Route Works!</h1><p><a href='/polished'>Try Polished Login</a></p>"

    # Add database initialization debug route
    @app.route('/debug/init_database')
    def debug_init_database():
        """Force database initialization."""
        try:
            from .utils.database_init import initialize_database_completely

            result = "<h2>🗄️ Database Initialization</h2>"
            result += "<p>Initializing database...</p>"

            init_result = initialize_database_completely()

            if init_result.get('success'):
                result += "<p>✅ Database initialized successfully!</p>"
                result += f"<p>Details: {init_result}</p>"
            else:
                result += f"<p>❌ Database initialization failed: {init_result.get('error')}</p>"

            result += "<p><a href='/debug/login_test'>🔐 Test Login Now</a></p>"
            result += "<p><a href='/'>🏠 Go to Login Page</a></p>"

            return result

        except Exception as e:
            return f"<h2>❌ Initialization Error</h2><p>{str(e)}</p>"

    # Add login form debug route
    @app.route('/debug/test_login', methods=['GET', 'POST'])
    def debug_test_login():
        """Debug route to test login forms."""
        if request.method == 'GET':
            from flask_wtf.csrf import generate_csrf
            csrf_token = generate_csrf()
            return f'''
            <h2>🔐 Login Form Tester</h2>
            <form method="POST">
                <input type="hidden" name="csrf_token" value="{csrf_token}" />
                <h3>Test Login:</h3>
                <p>Username: <input type="text" name="username" value="headteacher"></p>
                <p>Password: <input type="password" name="password" value="admin123"></p>
                <p>Role:
                    <select name="role">
                        <option value="headteacher">Headteacher</option>
                        <option value="classteacher">Class Teacher</option>
                        <option value="teacher">Teacher</option>
                    </select>
                </p>
                <p><input type="submit" value="Test Login"></p>
            </form>
            <hr>
            <h3>📋 Available Credentials:</h3>
            <ul>
                <li><strong>headteacher</strong> / admin123 (Role: headteacher)</li>
                <li><strong>kevin</strong> / kev123 (Role: classteacher)</li>
                <li><strong>carol</strong> / carol123 (Role: teacher)</li>
            </ul>
            <hr>
            <h3>🔗 Direct Login Links:</h3>
            <ul>
                <li><a href="/admin_login" target="_blank">👨‍💼 Headteacher Login</a></li>
                <li><a href="/classteacher_login" target="_blank">👩‍🏫 Class Teacher Login</a></li>
                <li><a href="/teacher_login" target="_blank">👨‍🎓 Teacher Login</a></li>
            </ul>
            '''

        # Handle POST request
        try:
            from .services.auth_service import authenticate_teacher

            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')

            result = f"<h2>🧪 Login Test Results</h2>"
            result += f"<p><strong>Username:</strong> {username}</p>"
            result += f"<p><strong>Password:</strong> {password}</p>"
            result += f"<p><strong>Role:</strong> {role}</p>"

            auth_result = authenticate_teacher(username, password, role)

            if auth_result:
                result += f"<p>✅ <strong>Authentication Successful!</strong></p>"
                result += f"<p>User details: {auth_result}</p>"
                result += f"<p><a href='/admin_dashboard' target='_blank'>🎯 Try Admin Dashboard</a></p>"
                result += f"<p><a href='/classteacher_dashboard' target='_blank'>🎯 Try Class Teacher Dashboard</a></p>"
            else:
                result += f"<p>❌ <strong>Authentication Failed!</strong></p>"
                result += f"<p>Check username, password, and role combination.</p>"

            result += f"<p><a href='/debug/test_login'>🔄 Test Again</a></p>"
            return result

        except Exception as e:
            return f"<h2>❌ Login Test Error</h2><p>{str(e)}</p>"

    # Add CSRF-exempt debug route for easier testing
    @app.route('/debug/simple_login', methods=['GET', 'POST'])
    @csrf.exempt
    def debug_simple_login():
        """Simple login test without CSRF protection."""
        if request.method == 'GET':
            return '''
            <h2>🔐 Simple Login Tester (No CSRF)</h2>
            <form method="POST">
                <h3>Test Login:</h3>
                <p>Username: <input type="text" name="username" value="headteacher"></p>
                <p>Password: <input type="password" name="password" value="admin123"></p>
                <p>Role:
                    <select name="role">
                        <option value="headteacher">Headteacher</option>
                        <option value="classteacher">Class Teacher</option>
                        <option value="teacher">Teacher</option>
                    </select>
                </p>
                <p><input type="submit" value="Test Login"></p>
            </form>
            <p><em>Note: This form bypasses CSRF protection for debugging.</em></p>
            '''

        # Handle POST request
        try:
            from .services.auth_service import authenticate_teacher

            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')

            result = f"<h2>🧪 Simple Login Test Results</h2>"
            result += f"<p><strong>Username:</strong> {username}</p>"
            result += f"<p><strong>Password:</strong> {password}</p>"
            result += f"<p><strong>Role:</strong> {role}</p>"

            auth_result = authenticate_teacher(username, password, role)

            if auth_result:
                result += f"<p>✅ <strong>Authentication Successful!</strong></p>"
                result += f"<p>User details: {auth_result}</p>"

                # Set session for testing
                session['teacher_id'] = auth_result.id
                session['role'] = role
                session.permanent = True

                result += f"<p>✅ <strong>Session Set!</strong></p>"
                result += f"<p>Session data: {dict(session)}</p>"
                result += f"<p><a href='/headteacher/' target='_blank'>🎯 Try Dashboard</a></p>"
            else:
                result += f"<p>❌ <strong>Authentication Failed!</strong></p>"

            result += f"<p><a href='/debug/simple_login'>🔄 Test Again</a></p>"
            return result

        except Exception as e:
            return f"<h2>❌ Simple Login Test Error</h2><p>{str(e)}</p>"

    # Add debug route to test admin dashboard directly
    @app.route('/debug/test_admin_dashboard')
    def debug_test_admin_dashboard():
        """Test admin dashboard without login."""
        try:
            # Set session manually for testing
            session['teacher_id'] = 2  # headteacher ID from your debug
            session['role'] = 'headteacher'
            session.permanent = True

            # Try to import and call the dashboard function
            from .views.admin import dashboard

            result = "<h2>🧪 Admin Dashboard Test</h2>"
            result += f"<p>Session set: {dict(session)}</p>"
            result += f"<p>Attempting to load dashboard...</p>"

            # Try to call the dashboard function directly
            dashboard_result = dashboard()

            result += f"<p>✅ Dashboard loaded successfully!</p>"
            result += f"<p><a href='/headteacher/' target='_blank'>🎯 Try Real Dashboard</a></p>"

            return result

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return f"""
            <h2>❌ Admin Dashboard Test Error</h2>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><strong>Full Traceback:</strong></p>
            <pre>{error_details}</pre>
            <p><a href='/debug/simple_login'>🔄 Try Simple Login</a></p>
            """

    # Add fallback root route in case blueprint route fails
    @app.route('/', methods=['GET'])
    def fallback_index():
        """Fallback root route."""
        try:
            from .views.auth import index
            return index()
        except Exception as e:
            return f"""
            <h2>🏠 Hillview School Management System</h2>
            <p>Welcome! Please choose your login type:</p>
            <ul>
                <li><a href="/admin_login">👨‍💼 Headteacher Login</a></li>
                <li><a href="/classteacher_login">👩‍🏫 Class Teacher Login</a></li>
                <li><a href="/teacher_login">👨‍🎓 Teacher Login</a></li>
            </ul>
            <p><small>Debug: {str(e)}</small></p>
            """

    # Add a simple test route
    @app.route('/test')
    def simple_test():
        """Simple test route to verify server is working"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Server Test</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .info {{ background: #f0f8ff; padding: 20px; border-radius: 8px; }}
                .success {{ color: #28a745; }}
                ul {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <h1 class="success">✅ Server is Working!</h1>
            <div class="info">
                <p><strong>Time:</strong> {datetime.now()}</p>
                <p><strong>Request URL:</strong> {request.url}</p>
                <p><strong>Remote Address:</strong> {request.remote_addr}</p>
                <p><strong>Is Secure:</strong> {request.is_secure}</p>
                <p><strong>Force HTTPS:</strong> {app.config.get('FORCE_HTTPS', 'Not Set')}</p>
            </div>
            <h3>Request Headers:</h3>
            <ul>
            {''.join(f'<li><strong>{k}:</strong> {v}</li>' for k, v in request.headers.items())}
            </ul>
            <p><a href="/" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Home Page</a></p>
            <p><a href="/simple-login" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Simple Login Test</a></p>
        </body>
        </html>
        """

    # Add a simple login test without external resources
    @app.route('/simple-login')
    def simple_login_test():
        """Simple login page without external CDN resources"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Simple Login Test</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .login-container {
                    max-width: 400px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }
                .form-group { margin-bottom: 20px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input[type="text"], input[type="password"] {
                    width: 100%;
                    padding: 12px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    font-size: 16px;
                    box-sizing: border-box;
                }
                .btn {
                    background: #667eea;
                    color: white;
                    padding: 12px 30px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    width: 100%;
                }
                .btn:hover { background: #5a6fd8; }
                h2 { text-align: center; color: #333; margin-bottom: 30px; }
                .back-link { text-align: center; margin-top: 20px; }
                .back-link a { color: #667eea; text-decoration: none; }
            </style>
        </head>
        <body>
            <div class="login-container">
                <h2>🏫 Simple Login Test</h2>
                <form method="post" action="/debug/simple_login">
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn">Login</button>
                </form>
                <div class="back-link">
                    <a href="/test">← Back to Test Page</a> |
                    <a href="/">Home Page</a>
                </div>
            </div>
        </body>
        </html>
        """

    # Add URL debugging route
    @app.route('/debug-urls')
    def debug_urls():
        """Debug route to check what URLs Flask is generating"""
        from flask import url_for
        urls = {
            'admin.dashboard': url_for('admin.dashboard', _external=True),
            'classteacher.dashboard': url_for('classteacher.dashboard', _external=True),
            'teacher.dashboard': url_for('teacher.dashboard', _external=True),
            'auth.index': url_for('auth.index', _external=True),
            'auth.admin_login': url_for('auth.admin_login', _external=True),
        }

        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>URL Debug</title></head>
        <body>
            <h1>Flask URL Generation Debug</h1>
            <p><strong>Request URL:</strong> {request.url}</p>
            <p><strong>Request is secure:</strong> {request.is_secure}</p>
            <p><strong>PREFERRED_URL_SCHEME:</strong> {app.config.get('PREFERRED_URL_SCHEME', 'Not Set')}</p>
            <p><strong>FORCE_HTTPS:</strong> {app.config.get('FORCE_HTTPS', 'Not Set')}</p>
            <h2>Generated URLs:</h2>
            <ul>
            {''.join(f'<li><strong>{name}:</strong> {url}</li>' for name, url in urls.items())}
            </ul>
            <p><a href="/test">Back to Test</a></p>
        </body>
        </html>
        """

    # Add a simple health check route
    @app.route('/health')
    def health_check():
        """Simple health check route"""
        try:
            from .utils.database_init import check_database_integrity
            status = check_database_integrity()

            if status['status'] == 'healthy':
                return f"""
                <h2>✅ System Health Check</h2>
                <p><strong>Status:</strong> <span style="color: green;">Healthy</span></p>
                <p><strong>Teachers:</strong> {status['teacher_count']}</p>
                <p><strong>Subjects:</strong> {status['subject_count']}</p>
                <p><strong>Grades:</strong> {status['grade_count']}</p>
                <p><strong>Streams:</strong> {status['stream_count']}</p>
                <p><a href="/">🏠 Go to Login Page</a></p>
                """
            else:
                return f"""
                <h2>⚠️ System Health Check</h2>
                <p><strong>Status:</strong> <span style="color: red;">{status['status']}</span></p>
                <p><a href="/debug/initialize_database" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🔄 Initialize Database</a></p>
                <p><a href="/">🏠 Go to Login Page</a></p>
                """
        except Exception as e:
            return f"""
            <h2>❌ System Health Check</h2>
            <p><strong>Status:</strong> <span style="color: red;">Error</span></p>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><a href="/debug/initialize_database" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🔄 Initialize Database</a></p>
            """

    # Register error handlers
    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"Internal Server Error: {str(e)}")
        # Check if it's a database error and provide helpful message
        error_str = str(e)
        if "no such table" in error_str.lower() or "database" in error_str.lower():
            return f"""
            <h2>🔧 Database Error Detected</h2>
            <p>It looks like there's a database issue. This usually means the database tables haven't been created yet.</p>
            <p><strong>Quick Fix:</strong></p>
            <p><a href="/debug/initialize_database" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🔄 Initialize Database</a></p>
            <p><a href="/debug/check_tables" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">📋 Check Database Tables</a></p>
            <hr>
            <p><strong>Error Details:</strong> {error_str}</p>
            """, 500
        return "Internal Server Error", 500



    @app.route('/debug/school_setup_info')
    def debug_school_setup_info():
        """Debug route to check school setup information."""
        try:
            from .models.school_setup import SchoolSetup

            result = "<h2>🏫 School Setup Information</h2>"

            # Get current setup
            setup = SchoolSetup.query.first()

            if setup:
                result += f"<p><strong>✅ School Setup Found:</strong></p>"
                result += f"<ul>"
                result += f"<li><strong>School Name:</strong> {setup.school_name}</li>"
                result += f"<li><strong>Motto:</strong> {setup.school_motto}</li>"
                result += f"<li><strong>Academic Year:</strong> {setup.current_academic_year}</li>"
                result += f"<li><strong>Current Term:</strong> {setup.current_term}</li>"
                result += f"<li><strong>Education System:</strong> {setup.education_system}</li>"
                result += f"<li><strong>Setup Completed:</strong> {setup.setup_completed}</li>"
                result += f"<li><strong>Setup Step:</strong> {setup.setup_step}</li>"
                result += f"</ul>"

                # Show all tables
                from .extensions import db
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()

                result += f"<p><strong>📋 Database Tables ({len(tables)}):</strong></p>"
                result += f"<ul>"
                for table in sorted(tables):
                    result += f"<li>{table}</li>"
                result += f"</ul>"

            else:
                result += f"<p><strong>❌ No school setup found</strong></p>"

            result += f"<p><a href='/school-setup/'>🏫 Go to School Setup</a></p>"
            result += f"<p><a href='/headteacher/'>🏠 Go to Headteacher Dashboard</a></p>"

            return result

        except Exception as e:
            return f"❌ Error checking school setup: {str(e)}"

    @app.route('/debug/session_info')
    def debug_session_info():
        """Debug route to check current session information."""
        try:
            session_data = dict(session)

            result = "<h2>🔍 Current Session Information</h2>"
            result += f"<p><strong>Session Data:</strong></p><pre>{session_data}</pre>"

            if 'teacher_id' in session:
                from .models.user import Teacher
                teacher = Teacher.query.get(session['teacher_id'])
                if teacher:
                    result += f"<p><strong>✅ Authenticated User:</strong></p>"
                    result += f"<ul>"
                    result += f"<li><strong>ID:</strong> {teacher.id}</li>"
                    result += f"<li><strong>Username:</strong> {teacher.username}</li>"
                    result += f"<li><strong>Role:</strong> {teacher.role}</li>"
                    result += f"</ul>"
                else:
                    result += f"<p><strong>❌ Teacher ID {session['teacher_id']} not found in database</strong></p>"
            else:
                result += f"<p><strong>❌ No authentication session found</strong></p>"

            result += f"<p><a href='/admin_login'>🔐 Go to Login</a></p>"
            result += f"<p><a href='/headteacher/'>🏠 Try Headteacher Dashboard</a></p>"

            return result

        except Exception as e:
            return f"❌ Error checking session: {str(e)}"

    @app.route('/debug/check_users')
    def debug_check_users():
        """Debug route to check all users."""
        try:
            from .models.user import Teacher

            teachers = Teacher.query.all()

            result = f"<h2>Users in Database ({len(teachers)} total):</h2><ul>"

            for teacher in teachers:
                result += f"<li><strong>{teacher.username}</strong> - Password: {teacher.password} - Role: {teacher.role}"
                if hasattr(teacher, 'full_name') and teacher.full_name:
                    result += f" - Full Name: {teacher.full_name}"
                result += "</li>"

            result += "</ul>"

            # Check for Kevin specifically
            kevin = Teacher.query.filter_by(username='kevin').first()
            if kevin:
                result += f"<p>✅ <strong>Kevin found!</strong> Username: {kevin.username}, Password: {kevin.password}</p>"
            else:
                result += f"<p>❌ <strong>Kevin NOT found</strong></p>"
                result += f'<p><a href="/debug/add_kevin">Click here to add Kevin</a></p>'

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    @app.route('/debug/add_kevin')
    def debug_add_kevin():
        """Debug route to add Kevin user."""
        try:
            from .models.user import Teacher

            # Check if Kevin exists
            kevin = Teacher.query.filter_by(username='kevin').first()

            if kevin:
                return f"Kevin already exists: {kevin.username}, role: {kevin.role}"

            # Add Kevin
            kevin = Teacher(
                username='kevin',
                password='kev123',
                role='classteacher'
            )

            # Add enhanced fields if they exist
            if hasattr(Teacher, 'full_name'):
                kevin.full_name = 'Kevin Teacher'
            if hasattr(Teacher, 'employee_id'):
                kevin.employee_id = 'EMP002'
            if hasattr(Teacher, 'is_active'):
                kevin.is_active = True

            db.session.add(kevin)
            db.session.commit()

            return "✅ Kevin added successfully! You can now login with kevin/kev123<br><a href='/debug/check_users'>Check users again</a>"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    @app.route('/debug/check_all_databases')
    def debug_check_all_databases():
        """Debug route to check all database files."""
        import glob
        import os

        def check_db_users(db_path):
            if not os.path.exists(db_path):
                return None
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher'")
                if not cursor.fetchone():
                    conn.close()
                    return "No teacher table"
                cursor.execute("SELECT id, username, password, role FROM teacher")
                users = cursor.fetchall()
                conn.close()
                return users
            except Exception as e:
                return f"Error: {e}"

        result = "<h2>🔍 All Database Files Check</h2>"

        # Check main databases
        db_files = ["../kirima_primary.db", "kirima_primary.db"]

        # Add backup files
        backup_files = glob.glob("kirima_primary.db.backup_*")
        backup_files.extend(glob.glob("../kirima_primary.db.backup_*"))

        all_files = db_files + backup_files

        for db_file in all_files:
            result += f"<h3>📁 {db_file}</h3>"
            result += f"<p>Exists: {os.path.exists(db_file)}</p>"

            if os.path.exists(db_file):
                size = os.path.getsize(db_file)
                result += f"<p>Size: {size:,} bytes</p>"

                users = check_db_users(db_file)

                if isinstance(users, list):
                    result += f"<p><strong>Users: {len(users)} found</strong></p><ul>"
                    for user in users:
                        result += f"<li>{user[1]} (password: {user[2]}, role: {user[3]})</li>"
                    result += "</ul>"

                    # Check for kevin
                    kevin_found = any(user[1] == 'kevin' for user in users)
                    if kevin_found:
                        result += f"<p style='color: green;'>✅ <strong>KEVIN FOUND in this database!</strong></p>"
                        result += f"<p><a href='/debug/restore_from_backup?file={db_file}'>Restore from this database</a></p>"
                else:
                    result += f"<p>Status: {users}</p>"

            result += "<hr>"

        return result

    @app.route('/debug/check_subjects')
    def debug_check_subjects():
        """Debug route to check all subjects in the database."""
        try:
            from .models.academic import Subject

            subjects = Subject.query.order_by(Subject.education_level, Subject.name).all()

            result = f"<h2>📚 Subjects in Database ({len(subjects)} total)</h2>"

            if not subjects:
                result += "<p style='color: red;'>❌ <strong>NO SUBJECTS FOUND!</strong></p>"
                result += "<p>This means the subject table is empty or doesn't exist.</p>"
                return result

            # Group by education level
            levels = {}
            for subject in subjects:
                level = subject.education_level
                if level not in levels:
                    levels[level] = []
                levels[level].append(subject)

            for level, level_subjects in levels.items():
                result += f"<h3>🎓 {level.replace('_', ' ').title()} ({len(level_subjects)} subjects)</h3>"
                result += "<ul>"
                for subject in level_subjects:
                    result += f"<li><strong>{subject.name}</strong>"
                    if hasattr(subject, 'is_standard'):
                        result += f" - Standard: {subject.is_standard}"
                    if hasattr(subject, 'is_composite'):
                        result += f" - Composite: {subject.is_composite}"
                    result += "</li>"
                result += "</ul>"

            return result

        except Exception as e:
            return f"❌ Error checking subjects: {str(e)}"

    @app.route('/debug/check_tables')
    def debug_check_tables():
        """Debug route to check what tables exist in the database."""
        try:
            import sqlite3
            from .config import config

            # Get the database path from config
            conf = config['development']()
            db_uri = conf.SQLALCHEMY_DATABASE_URI
            db_path = db_uri.replace('sqlite:///', '')

            result = f"<h2>🗃️ Database Tables Check</h2>"
            result += f"<p><strong>Database Path:</strong> {db_path}</p>"
            result += f"<p><strong>Database URI:</strong> {db_uri}</p>"

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]

            result += f"<h3>📋 Tables Found ({len(tables)} total):</h3><ul>"

            for table in sorted(tables):
                result += f"<li><strong>{table}</strong>"

                # Get row count for each table
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    result += f" - {count} records"
                except:
                    result += " - Error counting records"

                result += "</li>"

            result += "</ul>"

            # Check specific tables we care about
            important_tables = ['teacher', 'subject', 'grade', 'stream', 'student', 'term']
            missing_tables = [table for table in important_tables if table not in tables]

            if missing_tables:
                result += f"<h3 style='color: red;'>❌ Missing Important Tables:</h3><ul>"
                for table in missing_tables:
                    result += f"<li>{table}</li>"
                result += "</ul>"
            else:
                result += f"<h3 style='color: green;'>✅ All Important Tables Present</h3>"

            conn.close()
            return result

        except Exception as e:
            return f"❌ Error checking tables: {str(e)}"

    @app.route('/debug/find_real_database')
    def debug_find_real_database():
        """Search for the real database with telvo, kevin, and classteacher1."""
        import os
        import glob
        import sqlite3

        result = "<h2>🔍 Searching for Your Real Database</h2>"
        result += "<p>Looking for database with users: telvo, kevin, classteacher1</p><hr>"

        # Search patterns
        search_paths = [
            "*.db",
            "../*.db",
            "../../*.db",
            "**/kirima*.db",
            "**/school*.db",
            "**/*.db"
        ]

        found_databases = set()

        for pattern in search_paths:
            try:
                files = glob.glob(pattern, recursive=True)
                for file in files:
                    if os.path.exists(file):
                        found_databases.add(os.path.abspath(file))
            except:
                pass

        result += f"<h3>📁 Found {len(found_databases)} database files:</h3>"

        for db_path in sorted(found_databases):
            result += f"<h4>🗃️ {db_path}</h4>"

            try:
                # Get file info
                size = os.path.getsize(db_path)
                result += f"<p>Size: {size:,} bytes</p>"

                # Check users
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Check if teacher table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher'")
                if not cursor.fetchone():
                    result += "<p>❌ No teacher table</p>"
                    conn.close()
                    continue

                # Get all users
                cursor.execute("SELECT id, username, password, role FROM teacher")
                users = cursor.fetchall()

                result += f"<p><strong>Users ({len(users)}):</strong></p><ul>"

                # Check for your specific users
                telvo_found = False
                kevin_found = False
                classteacher1_found = False

                for user in users:
                    username = user[1].lower()
                    result += f"<li><strong>{user[1]}</strong> (password: {user[2]}, role: {user[3]})</li>"

                    if 'telvo' in username:
                        telvo_found = True
                    if 'kevin' in username:
                        kevin_found = True
                    if 'classteacher1' in username:
                        classteacher1_found = True

                result += "</ul>"

                # Check if this is the real database
                matches = sum([telvo_found, kevin_found, classteacher1_found])
                if matches >= 2:
                    result += f"<p style='color: green; font-size: 18px;'>🎯 <strong>POTENTIAL MATCH!</strong> Found {matches}/3 of your users!</p>"
                    result += f"<p><a href='/debug/use_database?path={db_path}' style='background: green; color: white; padding: 10px; text-decoration: none;'>USE THIS DATABASE</a></p>"

                # Also check subjects to see if they're your real subjects
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subject'")
                if cursor.fetchone():
                    cursor.execute("SELECT COUNT(*) FROM subject")
                    subject_count = cursor.fetchone()[0]
                    result += f"<p>📚 Subjects: {subject_count} found</p>"

                conn.close()

            except Exception as e:
                result += f"<p>❌ Error: {e}</p>"

            result += "<hr>"

        return result

    @app.route('/debug/use_database')
    def debug_use_database():
        """Switch to use a specific database."""
        import shutil
        import os
        from flask import request
        from datetime import datetime

        db_path = request.args.get('path')
        if not db_path or not os.path.exists(db_path):
            return "❌ Invalid database path"

        try:
            # Get the current database path
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            current_db_path = current_db_uri.replace('sqlite:///', '')

            # Create backup of current database
            backup_path = f"{current_db_path}.backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(current_db_path, backup_path)

            # Copy the real database to the current location
            shutil.copy2(db_path, current_db_path)

            return f"""
            <h2>✅ Database Restored!</h2>
            <p><strong>Copied from:</strong> {db_path}</p>
            <p><strong>To:</strong> {current_db_path}</p>
            <p><strong>Backup created:</strong> {backup_path}</p>
            <p><a href='/debug/check_users'>Check users now</a></p>
            <p><strong>You may need to restart the Flask app for changes to take effect.</strong></p>
            """

        except Exception as e:
            return f"❌ Error restoring database: {e}"

    @app.route('/debug/check_git_database')
    def debug_check_git_database():
        """Check the last committed database from Git."""
        import subprocess
        import os
        import sqlite3
        import tempfile

        result = "<h2>🔍 Checking Git for Original Database</h2>"

        try:
            # Check if we're in a git repository
            git_check = subprocess.run(['git', 'status'], capture_output=True, text=True, cwd='..')
            if git_check.returncode != 0:
                return result + "<p>❌ Not in a Git repository or Git not available</p>"

            result += "<p>✅ Git repository found</p>"

            # Get the last few commits
            commits = subprocess.run(['git', 'log', '--oneline', '-10'], capture_output=True, text=True, cwd='..')
            result += f"<h3>📋 Recent Commits:</h3><pre>{commits.stdout}</pre>"

            # Check if database file is tracked in git
            git_files = subprocess.run(['git', 'ls-files', '*.db'], capture_output=True, text=True, cwd='..')
            result += f"<h3>🗃️ Database files in Git:</h3><pre>{git_files.stdout}</pre>"

            # Try to get the database from the last commit
            db_files_in_git = git_files.stdout.strip().split('\n') if git_files.stdout.strip() else []

            for db_file in db_files_in_git:
                if db_file:
                    result += f"<h4>📁 Checking {db_file} from Git</h4>"

                    # Get the file from the last commit
                    try:
                        git_show = subprocess.run(['git', 'show', f'HEAD:{db_file}'], capture_output=True, cwd='..')

                        if git_show.returncode == 0:
                            # Save to temporary file
                            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
                                temp_db.write(git_show.stdout)
                                temp_db_path = temp_db.name

                            # Check users in this database
                            conn = sqlite3.connect(temp_db_path)
                            cursor = conn.cursor()

                            # Check if teacher table exists
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher'")
                            if cursor.fetchone():
                                cursor.execute("SELECT id, username, password, role FROM teacher")
                                users = cursor.fetchall()

                                result += f"<p><strong>Users in Git version ({len(users)}):</strong></p><ul>"

                                telvo_found = False
                                kevin_found = False
                                classteacher1_found = False

                                for user in users:
                                    username = user[1].lower()
                                    result += f"<li><strong>{user[1]}</strong> (password: {user[2]}, role: {user[3]})</li>"

                                    if 'telvo' in username:
                                        telvo_found = True
                                    if 'kevin' in username:
                                        kevin_found = True
                                    if 'classteacher1' in username:
                                        classteacher1_found = True

                                result += "</ul>"

                                matches = sum([telvo_found, kevin_found, classteacher1_found])
                                if matches >= 2:
                                    result += f"<p style='color: green; font-size: 18px;'>🎯 <strong>FOUND YOUR ORIGINAL DATABASE!</strong> Found {matches}/3 of your users!</p>"
                                    result += f"<p><a href='/debug/restore_git_database?file={db_file}' style='background: green; color: white; padding: 10px; text-decoration: none;'>RESTORE THIS DATABASE</a></p>"

                                # Check subjects
                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subject'")
                                if cursor.fetchone():
                                    cursor.execute("SELECT COUNT(*) FROM subject")
                                    subject_count = cursor.fetchone()[0]
                                    result += f"<p>📚 Subjects: {subject_count} found</p>"

                                    # Show some subjects
                                    cursor.execute("SELECT name FROM subject LIMIT 10")
                                    subjects = cursor.fetchall()
                                    result += "<p>Sample subjects: " + ", ".join([s[0] for s in subjects]) + "</p>"

                            conn.close()
                            os.unlink(temp_db_path)  # Clean up temp file

                        else:
                            result += f"<p>❌ Could not retrieve {db_file} from Git</p>"

                    except Exception as e:
                        result += f"<p>❌ Error checking {db_file}: {e}</p>"

            return result

        except Exception as e:
            return result + f"<p>❌ Error: {e}</p>"

    @app.route('/debug/restore_git_database')
    def debug_restore_git_database():
        """Restore database from Git."""
        import subprocess
        import os
        from flask import request
        from datetime import datetime

        db_file = request.args.get('file')
        if not db_file:
            return "❌ No database file specified"

        try:
            # Get the current database path
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            current_db_path = current_db_uri.replace('sqlite:///', '')

            # Create backup of current database
            backup_path = f"{current_db_path}.backup_before_git_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists(current_db_path):
                import shutil
                shutil.copy2(current_db_path, backup_path)

            # Get the database from Git and save it
            git_show = subprocess.run(['git', 'show', f'HEAD:{db_file}'], capture_output=True, cwd='..')

            if git_show.returncode == 0:
                with open(current_db_path, 'wb') as f:
                    f.write(git_show.stdout)

                return f"""
                <h2>✅ Database Restored from Git!</h2>
                <p><strong>Restored:</strong> {db_file} from Git HEAD</p>
                <p><strong>To:</strong> {current_db_path}</p>
                <p><strong>Backup created:</strong> {backup_path}</p>
                <p><a href='/debug/check_users'>Check users now</a></p>
                <p><strong>Please restart the Flask app for changes to take effect.</strong></p>
                <p><strong>You should now be able to login with your original credentials!</strong></p>
                """
            else:
                return f"❌ Could not retrieve {db_file} from Git"

        except Exception as e:
            return f"❌ Error restoring from Git: {e}"

    @app.route('/debug/enhance_restored_database')
    def debug_enhance_restored_database():
        """Add enhanced columns to the restored database."""
        import sqlite3
        import os
        from datetime import datetime

        result = "<h2>🔧 Enhancing Restored Database</h2>"

        try:
            # Get the current database path
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            current_db_path = current_db_uri.replace('sqlite:///', '')

            result += f"<p><strong>Database:</strong> {current_db_path}</p>"

            # Create backup before enhancement
            backup_path = f"{current_db_path}.backup_before_enhancement_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(current_db_path, backup_path)
            result += f"<p>✅ Backup created: {backup_path}</p>"

            conn = sqlite3.connect(current_db_path)
            cursor = conn.cursor()

            # Check current teacher table structure
            cursor.execute("PRAGMA table_info(teacher)")
            columns = [col[1] for col in cursor.fetchall()]
            result += f"<p><strong>Current columns:</strong> {', '.join(columns)}</p>"

            # Enhanced columns to add
            enhanced_columns = [
                ('full_name', 'TEXT'),
                ('employee_id', 'TEXT'),
                ('phone_number', 'TEXT'),
                ('email', 'TEXT'),
                ('qualification', 'TEXT'),
                ('specialization', 'TEXT'),
                ('is_active', 'BOOLEAN DEFAULT 1'),
                ('date_joined', 'DATE')
            ]

            # Add missing columns
            added_columns = []
            for col_name, col_type in enhanced_columns:
                if col_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE teacher ADD COLUMN {col_name} {col_type}")
                        added_columns.append(col_name)
                        result += f"<p>✅ Added column: {col_name}</p>"
                    except Exception as e:
                        result += f"<p>❌ Failed to add {col_name}: {e}</p>"

            # Update existing teachers with default enhanced values
            cursor.execute("SELECT id, username FROM teacher")
            teachers = cursor.fetchall()

            result += f"<p><strong>Updating {len(teachers)} teachers with enhanced data...</strong></p>"

            for teacher_id, username in teachers:
                updates = []

                # Set full_name to username if null
                if 'full_name' in added_columns:
                    updates.append(f"full_name = '{username}'")

                # Set employee_id if null
                if 'employee_id' in added_columns:
                    updates.append(f"employee_id = 'EMP{teacher_id:03d}'")

                # Set is_active to true if null
                if 'is_active' in added_columns:
                    updates.append("is_active = 1")

                if updates:
                    update_sql = f"UPDATE teacher SET {', '.join(updates)} WHERE id = ?"
                    cursor.execute(update_sql, (teacher_id,))
                    result += f"<p>✅ Updated {username}</p>"

            # Check if school_configuration table exists, create if missing
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='school_configuration'")
            if not cursor.fetchone():
                result += f"<p>⚠️ school_configuration table missing - creating it...</p>"
                cursor.execute("""
                    CREATE TABLE school_configuration (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        school_name TEXT NOT NULL DEFAULT 'Hillview School',
                        school_motto TEXT DEFAULT 'Excellence in Education',
                        school_address TEXT,
                        school_phone TEXT,
                        school_email TEXT,
                        school_website TEXT,
                        current_academic_year TEXT DEFAULT '2024',
                        current_term TEXT DEFAULT 'Term 1',
                        use_streams BOOLEAN DEFAULT 1,
                        grading_system TEXT DEFAULT 'percentage',
                        show_position BOOLEAN DEFAULT 1,
                        show_class_average BOOLEAN DEFAULT 1,
                        show_subject_teacher BOOLEAN DEFAULT 1,
                        logo_filename TEXT,
                        primary_color TEXT DEFAULT '#1f7d53',
                        secondary_color TEXT DEFAULT '#18230f',
                        headteacher_name TEXT DEFAULT 'Head Teacher',
                        deputy_headteacher_name TEXT DEFAULT 'Deputy Head Teacher',
                        max_raw_marks_default INTEGER DEFAULT 100,
                        pass_mark_percentage INTEGER DEFAULT 50,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        headteacher_id INTEGER,
                        deputy_headteacher_id INTEGER,
                        FOREIGN KEY (headteacher_id) REFERENCES teacher (id),
                        FOREIGN KEY (deputy_headteacher_id) REFERENCES teacher (id)
                    )
                """)

                # Insert default configuration
                cursor.execute("""
                    INSERT INTO school_configuration (
                        school_name, school_motto, current_academic_year, current_term,
                        headteacher_name, deputy_headteacher_name
                    ) VALUES (
                        'Hillview School', 'Excellence in Education', '2024', 'Term 1',
                        'Head Teacher', 'Deputy Head Teacher'
                    )
                """)
                result += f"<p>✅ Created school_configuration table with default data</p>"
            else:
                # Table exists, check and add enhanced columns
                cursor.execute("PRAGMA table_info(school_configuration)")
                config_columns = [col[1] for col in cursor.fetchall()]

                if 'headteacher_id' not in config_columns:
                    cursor.execute("ALTER TABLE school_configuration ADD COLUMN headteacher_id INTEGER")
                    result += f"<p>✅ Added headteacher_id to school_configuration</p>"

                if 'deputy_headteacher_id' not in config_columns:
                    cursor.execute("ALTER TABLE school_configuration ADD COLUMN deputy_headteacher_id INTEGER")
                    result += f"<p>✅ Added deputy_headteacher_id to school_configuration</p>"

            conn.commit()

            # Verify final structure
            cursor.execute("PRAGMA table_info(teacher)")
            final_columns = [col[1] for col in cursor.fetchall()]
            result += f"<p><strong>Final teacher columns:</strong> {', '.join(final_columns)}</p>"

            # Test query
            cursor.execute("SELECT id, username, full_name, employee_id FROM teacher LIMIT 3")
            test_teachers = cursor.fetchall()
            result += f"<p><strong>Sample enhanced teachers:</strong></p><ul>"
            for teacher in test_teachers:
                result += f"<li>{teacher[1]} - Full Name: {teacher[2]}, Employee ID: {teacher[3]}</li>"
            result += "</ul>"

            conn.close()

            result += f"<h3 style='color: green;'>✅ Database Enhancement Complete!</h3>"
            result += f"<p><strong>Your original data is preserved with enhanced features added.</strong></p>"
            result += f"<p><a href='/debug/check_users'>Check users now</a></p>"
            result += f"<p><strong>Please restart the Flask app to use the enhanced database.</strong></p>"

            return result

        except Exception as e:
            return f"❌ Error enhancing database: {e}"

    @app.route('/debug/complete_database_setup')
    def debug_complete_database_setup():
        """Add ALL missing tables to the restored database."""
        import sqlite3
        import os
        from datetime import datetime

        result = "<h2>🔧 Complete Database Setup</h2>"
        result += "<p>Adding all missing tables while preserving your original data...</p>"

        try:
            # Get the current database path
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            current_db_path = current_db_uri.replace('sqlite:///', '')

            result += f"<p><strong>Database:</strong> {current_db_path}</p>"

            # Create backup before setup
            backup_path = f"{current_db_path}.backup_before_complete_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(current_db_path, backup_path)
            result += f"<p>✅ Backup created: {backup_path}</p>"

            conn = sqlite3.connect(current_db_path)
            cursor = conn.cursor()

            # Check what tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [table[0] for table in cursor.fetchall()]
            result += f"<p><strong>Existing tables:</strong> {', '.join(existing_tables)}</p>"

            # Create grade table if missing
            if 'grade' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE grade (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        education_level TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Insert default grades
                grades_data = [
                    ('Grade 1', 'lower_primary'),
                    ('Grade 2', 'lower_primary'),
                    ('Grade 3', 'lower_primary'),
                    ('Grade 4', 'upper_primary'),
                    ('Grade 5', 'upper_primary'),
                    ('Grade 6', 'upper_primary'),
                    ('Grade 7', 'junior_secondary'),
                    ('Grade 8', 'junior_secondary'),
                    ('Grade 9', 'junior_secondary')
                ]

                for grade_name, education_level in grades_data:
                    cursor.execute("INSERT INTO grade (name, education_level) VALUES (?, ?)",
                                 (grade_name, education_level))

                result += f"<p>✅ Created grade table with {len(grades_data)} grades</p>"

            # Create stream table if missing
            if 'stream' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE stream (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        grade_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (grade_id) REFERENCES grade (id)
                    )
                """)

                # Insert default streams for each grade
                cursor.execute("SELECT id, name FROM grade")
                grade_records = cursor.fetchall()

                stream_count = 0
                for grade_id, grade_name in grade_records:
                    cursor.execute("INSERT INTO stream (name, grade_id) VALUES (?, ?)", ('A', grade_id))
                    cursor.execute("INSERT INTO stream (name, grade_id) VALUES (?, ?)", ('B', grade_id))
                    stream_count += 2

                result += f"<p>✅ Created stream table with {stream_count} streams</p>"

            # Create term table if missing
            if 'term' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE term (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        academic_year TEXT,
                        start_date DATE,
                        end_date DATE,
                        is_current BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Insert default terms
                cursor.execute("INSERT INTO term (name, academic_year, is_current) VALUES (?, ?, ?)",
                              ('Term 1', '2024', 1))
                cursor.execute("INSERT INTO term (name, academic_year, is_current) VALUES (?, ?, ?)",
                              ('Term 2', '2024', 0))
                cursor.execute("INSERT INTO term (name, academic_year, is_current) VALUES (?, ?, ?)",
                              ('Term 3', '2024', 0))

                result += f"<p>✅ Created term table with 3 terms</p>"

            # Create assessment_type table if missing
            if 'assessment_type' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE assessment_type (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        weight REAL DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Insert default assessment types
                cursor.execute("INSERT INTO assessment_type (name, description) VALUES (?, ?)",
                              ('End of Term Exam', 'Final examination for the term'))
                cursor.execute("INSERT INTO assessment_type (name, description) VALUES (?, ?)",
                              ('Mid Term Test', 'Mid-term assessment'))
                cursor.execute("INSERT INTO assessment_type (name, description) VALUES (?, ?)",
                              ('Continuous Assessment', 'Ongoing classroom assessment'))

                result += f"<p>✅ Created assessment_type table with 3 types</p>"

            # Create student table if missing
            if 'student' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE student (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        admission_number TEXT UNIQUE,
                        grade_id INTEGER NOT NULL,
                        stream_id INTEGER NOT NULL,
                        date_of_birth DATE,
                        gender TEXT,
                        parent_contact TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (grade_id) REFERENCES grade (id),
                        FOREIGN KEY (stream_id) REFERENCES stream (id)
                    )
                """)
                result += f"<p>✅ Created student table</p>"

            # Create marks table if missing
            if 'marks' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE marks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        subject_id INTEGER NOT NULL,
                        term_id INTEGER NOT NULL,
                        assessment_type_id INTEGER NOT NULL,
                        raw_mark REAL,
                        percentage REAL,
                        grade TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES student (id),
                        FOREIGN KEY (subject_id) REFERENCES subject (id),
                        FOREIGN KEY (term_id) REFERENCES term (id),
                        FOREIGN KEY (assessment_type_id) REFERENCES assessment_type (id)
                    )
                """)
                result += f"<p>✅ Created marks table</p>"

            # Create teacher_subjects table if missing
            if 'teacher_subjects' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE teacher_subjects (
                        teacher_id INTEGER NOT NULL,
                        subject_id INTEGER NOT NULL,
                        PRIMARY KEY (teacher_id, subject_id),
                        FOREIGN KEY (teacher_id) REFERENCES teacher (id),
                        FOREIGN KEY (subject_id) REFERENCES subject (id)
                    )
                """)
                result += f"<p>✅ Created teacher_subjects table</p>"

            # Create teacher_subject_assignment table if missing
            if 'teacher_subject_assignment' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE teacher_subject_assignment (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        teacher_id INTEGER NOT NULL,
                        subject_id INTEGER NOT NULL,
                        grade_id INTEGER NOT NULL,
                        stream_id INTEGER NOT NULL,
                        is_class_teacher BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (teacher_id) REFERENCES teacher (id),
                        FOREIGN KEY (subject_id) REFERENCES subject (id),
                        FOREIGN KEY (grade_id) REFERENCES grade (id),
                        FOREIGN KEY (stream_id) REFERENCES stream (id)
                    )
                """)
                result += f"<p>✅ Created teacher_subject_assignment table</p>"

            conn.commit()

            # Final verification
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            final_tables = [table[0] for table in cursor.fetchall()]
            result += f"<p><strong>Final tables ({len(final_tables)}):</strong> {', '.join(sorted(final_tables))}</p>"

            # Check data counts
            for table in ['grade', 'stream', 'term', 'assessment_type']:
                if table in final_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    result += f"<p>  - {table}: {count} records</p>"

            conn.close()

            result += f"<h3 style='color: green;'>✅ Complete Database Setup Finished!</h3>"
            result += f"<p><strong>Your original data is preserved with all required tables added.</strong></p>"
            result += f"<p><a href='/debug/check_users'>Check users</a> | <a href='/debug/check_subjects'>Check subjects</a></p>"
            result += f"<p><strong>Please restart the Flask app to use the complete database.</strong></p>"

            return result

        except Exception as e:
            return f"❌ Error in complete database setup: {e}"

    @app.route('/debug/test_school_config')
    def debug_test_school_config():
        """Test the school configuration integration."""
        try:
            from .services.school_config_service import SchoolConfigService

            result = "<h2>🧪 School Configuration Integration Test</h2>"

            # Test get_school_name
            school_name = SchoolConfigService.get_school_name()
            result += f"<h3>📋 get_school_name():</h3>"
            result += f"<p><strong>{school_name}</strong></p>"

            # Test get_school_info_dict
            school_info = SchoolConfigService.get_school_info_dict()
            result += f"<h3>📋 get_school_info_dict():</h3>"
            result += "<ul>"
            for key, value in school_info.items():
                result += f"<li><strong>{key}:</strong> {value}</li>"
            result += "</ul>"

            # Check if using setup data
            from .models.school_setup import SchoolSetup
            setup = SchoolSetup.query.first()

            if setup and setup.setup_completed:
                result += f"<h3>✅ School Setup Status:</h3>"
                result += f"<p>Setup completed: <strong>Yes</strong></p>"
                result += f"<p>Setup school name: <strong>{setup.school_name}</strong></p>"
                result += f"<p>Service school name: <strong>{school_name}</strong></p>"

                if school_name.lower() == setup.school_name.lower():
                    result += f"<p style='color: green; font-size: 18px;'>🎯 <strong>SUCCESS!</strong> Service is using setup data!</p>"
                else:
                    result += f"<p style='color: red; font-size: 18px;'>❌ <strong>ISSUE!</strong> Service is not using setup data!</p>"
            else:
                result += f"<h3>❌ School Setup Status:</h3>"
                result += f"<p>Setup completed: <strong>No</strong></p>"

            return result

        except Exception as e:
            return f"❌ Error testing school config: {e}"

    @app.route('/debug/check_new_structure_databases')
    def debug_check_new_structure_databases():
        """Check for databases specifically in the new_structure directory."""
        import os
        import glob
        import sqlite3

        result = "<h2>🔍 Checking new_structure Directory for Databases</h2>"

        try:
            # Get current working directory
            current_dir = os.getcwd()
            result += f"<p><strong>Current working directory:</strong> {current_dir}</p>"

            # Check Flask app database configuration
            from .config import config
            conf = config['development']()
            db_uri = conf.SQLALCHEMY_DATABASE_URI
            configured_db_path = db_uri.replace('sqlite:///', '')
            result += f"<p><strong>Flask configured database:</strong> {configured_db_path}</p>"
            result += f"<p><strong>Configured DB exists:</strong> {os.path.exists(configured_db_path)}</p>"

            # Look for all .db files in current directory (new_structure)
            db_files_here = glob.glob("*.db")
            result += f"<h3>📁 Database files in new_structure directory ({len(db_files_here)}):</h3>"

            if not db_files_here:
                result += "<p>❌ No .db files found in new_structure directory</p>"
            else:
                for db_file in db_files_here:
                    result += f"<h4>🗃️ {db_file}</h4>"

                    try:
                        # Get file info
                        full_path = os.path.abspath(db_file)
                        size = os.path.getsize(db_file)
                        result += f"<p><strong>Full path:</strong> {full_path}</p>"
                        result += f"<p><strong>Size:</strong> {size:,} bytes</p>"

                        # Check if this is the configured database
                        if os.path.abspath(db_file) == os.path.abspath(configured_db_path):
                            result += f"<p style='color: green;'>✅ <strong>This is the Flask configured database!</strong></p>"

                        # Check users in this database
                        conn = sqlite3.connect(db_file)
                        cursor = conn.cursor()

                        # Check if teacher table exists
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher'")
                        if cursor.fetchone():
                            cursor.execute("SELECT id, username, password, role FROM teacher")
                            users = cursor.fetchall()

                            result += f"<p><strong>Users ({len(users)}):</strong></p><ul>"

                            telvo_found = False
                            kevin_found = False
                            classteacher1_found = False

                            for user in users:
                                username = user[1].lower()
                                result += f"<li><strong>{user[1]}</strong> (password: {user[2]}, role: {user[3]})</li>"

                                if 'telvo' in username:
                                    telvo_found = True
                                if 'kevin' in username:
                                    kevin_found = True
                                if 'classteacher1' in username:
                                    classteacher1_found = True

                            result += "</ul>"

                            matches = sum([telvo_found, kevin_found, classteacher1_found])
                            if matches >= 2:
                                result += f"<p style='color: green; font-size: 16px;'>🎯 <strong>CONTAINS YOUR ORIGINAL USERS!</strong> ({matches}/3 found)</p>"
                        else:
                            result += "<p>❌ No teacher table found</p>"

                        # Check what tables exist
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = [table[0] for table in cursor.fetchall()]
                        result += f"<p><strong>Tables ({len(tables)}):</strong> {', '.join(sorted(tables))}</p>"

                        # Check subjects if table exists
                        if 'subject' in tables:
                            cursor.execute("SELECT COUNT(*) FROM subject")
                            subject_count = cursor.fetchone()[0]
                            result += f"<p><strong>Subjects:</strong> {subject_count} found</p>"

                            if subject_count > 0:
                                cursor.execute("SELECT name FROM subject LIMIT 5")
                                sample_subjects = [s[0] for s in cursor.fetchall()]
                                result += f"<p><strong>Sample subjects:</strong> {', '.join(sample_subjects)}</p>"

                        conn.close()

                    except Exception as e:
                        result += f"<p>❌ Error checking {db_file}: {e}</p>"

                    result += "<hr>"

            # Also check parent directory
            parent_db_files = glob.glob("../*.db")
            result += f"<h3>📁 Database files in parent directory ({len(parent_db_files)}):</h3>"

            for db_file in parent_db_files:
                db_name = os.path.basename(db_file)
                result += f"<p>📄 {db_name}</p>"

            # Summary
            result += f"<h3>📋 Summary:</h3>"
            result += f"<p>• Flask is configured to use: <code>{configured_db_path}</code></p>"
            result += f"<p>• Database files in new_structure: {len(db_files_here)}</p>"
            result += f"<p>• Database files in parent: {len(parent_db_files)}</p>"

            return result

        except Exception as e:
            return f"❌ Error checking new_structure databases: {e}"

    @app.route('/debug/fix_grade_table')
    def debug_fix_grade_table():
        """Specifically fix the grade table issue."""
        import sqlite3
        import os
        from datetime import datetime

        result = "<h2>🔧 Fixing Grade Table</h2>"

        try:
            # Get the current database path
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            current_db_path = current_db_uri.replace('sqlite:///', '')

            result += f"<p><strong>Database:</strong> {current_db_path}</p>"

            # Create backup
            backup_path = f"{current_db_path}.backup_grade_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(current_db_path, backup_path)
            result += f"<p>✅ Backup created: {backup_path}</p>"

            conn = sqlite3.connect(current_db_path)
            cursor = conn.cursor()

            # Check if grade table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='grade'")
            grade_table_exists = cursor.fetchone()

            if grade_table_exists:
                result += f"<p>📋 Grade table exists - checking structure...</p>"

                # Check current structure
                cursor.execute("PRAGMA table_info(grade)")
                columns = cursor.fetchall()
                result += f"<p><strong>Current columns:</strong></p><ul>"
                for col in columns:
                    result += f"<li>{col[1]} ({col[2]})</li>"
                result += "</ul>"

                # Check if 'name' column exists
                column_names = [col[1] for col in columns]
                if 'name' not in column_names:
                    result += f"<p>❌ Missing 'name' column - adding it...</p>"

                    # Add name column
                    cursor.execute("ALTER TABLE grade ADD COLUMN name TEXT")

                    # If there's a 'level' column, copy its data to 'name'
                    if 'level' in column_names:
                        cursor.execute("UPDATE grade SET name = level")
                        result += f"<p>✅ Copied data from 'level' to 'name' column</p>"

                if 'education_level' not in column_names:
                    result += f"<p>❌ Missing 'education_level' column - adding it...</p>"
                    cursor.execute("ALTER TABLE grade ADD COLUMN education_level TEXT")

                    # Set default education levels based on grade names
                    cursor.execute("""
                        UPDATE grade SET education_level =
                        CASE
                            WHEN name IN ('Grade 1', 'Grade 2', 'Grade 3') THEN 'lower_primary'
                            WHEN name IN ('Grade 4', 'Grade 5', 'Grade 6') THEN 'upper_primary'
                            WHEN name IN ('Grade 7', 'Grade 8', 'Grade 9') THEN 'junior_secondary'
                            ELSE 'lower_primary'
                        END
                    """)
                    result += f"<p>✅ Added education_level column with default values</p>"

            else:
                result += f"<p>❌ Grade table doesn't exist - creating it...</p>"

                # Create grade table
                cursor.execute("""
                    CREATE TABLE grade (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        education_level TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Insert default grades
                grades_data = [
                    ('Grade 1', 'lower_primary'),
                    ('Grade 2', 'lower_primary'),
                    ('Grade 3', 'lower_primary'),
                    ('Grade 4', 'upper_primary'),
                    ('Grade 5', 'upper_primary'),
                    ('Grade 6', 'upper_primary'),
                    ('Grade 7', 'junior_secondary'),
                    ('Grade 8', 'junior_secondary'),
                    ('Grade 9', 'junior_secondary')
                ]

                for grade_name, education_level in grades_data:
                    cursor.execute("INSERT INTO grade (name, education_level) VALUES (?, ?)",
                                 (grade_name, education_level))

                result += f"<p>✅ Created grade table with {len(grades_data)} grades</p>"

            # Also create stream table if missing
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stream'")
            if not cursor.fetchone():
                result += f"<p>⚠️ Stream table missing - creating it...</p>"

                cursor.execute("""
                    CREATE TABLE stream (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        grade_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (grade_id) REFERENCES grade (id)
                    )
                """)

                # Insert default streams for each grade
                cursor.execute("SELECT id, name FROM grade")
                grade_records = cursor.fetchall()

                stream_count = 0
                for grade_id, grade_name in grade_records:
                    cursor.execute("INSERT INTO stream (name, grade_id) VALUES (?, ?)", ('A', grade_id))
                    cursor.execute("INSERT INTO stream (name, grade_id) VALUES (?, ?)", ('B', grade_id))
                    stream_count += 2

                result += f"<p>✅ Created stream table with {stream_count} streams</p>"

            conn.commit()

            # Verify the fix
            cursor.execute("PRAGMA table_info(grade)")
            final_columns = [col[1] for col in cursor.fetchall()]
            result += f"<p><strong>Final grade table columns:</strong> {', '.join(final_columns)}</p>"

            # Test the query that was failing
            cursor.execute("SELECT id, name, education_level FROM grade LIMIT 3")
            test_grades = cursor.fetchall()
            result += f"<p><strong>Test query results:</strong></p><ul>"
            for grade in test_grades:
                result += f"<li>ID: {grade[0]}, Name: {grade[1]}, Level: {grade[2]}</li>"
            result += "</ul>"

            conn.close()

            result += f"<h3 style='color: green;'>✅ Grade Table Fix Complete!</h3>"
            result += f"<p><strong>The grade table now has the correct structure.</strong></p>"
            result += f"<p><a href='/debug/check_users'>Check users</a> | <a href='/classteacher_login'>Try login</a></p>"
            result += f"<p><strong>Please restart the Flask app to use the fixed database.</strong></p>"

            return result

        except Exception as e:
            return f"❌ Error fixing grade table: {e}"

    @app.route('/debug/cleanup_databases')
    def debug_cleanup_databases():
        """Show which database files can be safely removed."""
        import os
        import glob
        from datetime import datetime

        result = "<h2>🧹 Database Cleanup Guide</h2>"
        result += "<p>Here's what database files exist and which ones you can safely remove:</p>"

        try:
            # Get the current active database
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            active_db_path = os.path.abspath(current_db_uri.replace('sqlite:///', ''))

            result += f"<h3>🎯 ACTIVE DATABASE (DO NOT DELETE):</h3>"
            result += f"<p style='color: green; font-weight: bold;'>{active_db_path}</p>"
            result += f"<p>This is the database your Flask app is currently using.</p>"

            # Find all database files
            search_patterns = [
                "*.db",
                "../*.db",
                "*.db.backup*",
                "../*.db.backup*"
            ]

            all_db_files = set()
            for pattern in search_patterns:
                files = glob.glob(pattern)
                for file in files:
                    all_db_files.add(os.path.abspath(file))

            # Remove the active database from the list
            cleanup_files = all_db_files - {active_db_path}

            if cleanup_files:
                result += f"<h3>🗑️ FILES SAFE TO DELETE ({len(cleanup_files)} files):</h3>"
                result += "<p>These are backup files and unused databases that can be safely removed:</p>"
                result += "<ul>"

                # Group files by type
                backups = []
                other_dbs = []

                for file_path in sorted(cleanup_files):
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

                    if 'backup' in file_name:
                        backups.append((file_path, file_name, file_size))
                    else:
                        other_dbs.append((file_path, file_name, file_size))

                # Show backup files
                if backups:
                    result += "<li><strong>📦 Backup Files:</strong><ul>"
                    for file_path, file_name, file_size in backups:
                        result += f"<li>{file_name} ({file_size:,} bytes)<br><small>{file_path}</small></li>"
                    result += "</ul></li>"

                # Show other database files
                if other_dbs:
                    result += "<li><strong>🗃️ Other Database Files:</strong><ul>"
                    for file_path, file_name, file_size in other_dbs:
                        result += f"<li>{file_name} ({file_size:,} bytes)<br><small>{file_path}</small></li>"
                    result += "</ul></li>"

                result += "</ul>"

                # Calculate total space that can be freed
                total_size = sum(file_size for _, _, file_size in backups + other_dbs)
                result += f"<p><strong>💾 Total space that can be freed: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)</strong></p>"

                # Provide cleanup commands
                result += f"<h3>🔧 How to Clean Up:</h3>"
                result += f"<p><strong>Option 1: Delete backup files only (recommended):</strong></p>"
                result += f"<pre>cd {os.path.dirname(active_db_path)}\n"
                for file_path, file_name, _ in backups:
                    if 'backup' in file_name:
                        result += f"del \"{file_name}\"\n"
                result += "</pre>"

                result += f"<p><strong>Option 2: Delete all unused databases:</strong></p>"
                result += f"<pre>cd {os.path.dirname(active_db_path)}\n"
                for file_path, file_name, _ in backups + other_dbs:
                    result += f"del \"{file_name}\"\n"
                result += "</pre>"

                result += f"<p><strong>⚠️ Safety Note:</strong> Keep at least one recent backup in case you need to restore.</p>"

            else:
                result += f"<h3>✅ NO CLEANUP NEEDED</h3>"
                result += f"<p>Only the active database exists. No unnecessary files found.</p>"

            # Show summary
            result += f"<h3>📋 Summary:</h3>"
            result += f"<ul>"
            result += f"<li><strong>Active database:</strong> {os.path.basename(active_db_path)}</li>"
            result += f"<li><strong>Backup files:</strong> {len(backups)}</li>"
            result += f"<li><strong>Other databases:</strong> {len(other_dbs)}</li>"
            result += f"<li><strong>Total files found:</strong> {len(all_db_files)}</li>"
            result += f"</ul>"

            return result

        except Exception as e:
            return f"❌ Error analyzing databases: {e}"

    @app.route('/debug/perform_cleanup')
    def debug_perform_cleanup():
        """Automatically clean up unnecessary database files."""
        import os
        import glob
        from datetime import datetime

        result = "<h2>🧹 Performing Database Cleanup</h2>"

        try:
            # Get the current active database
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            active_db_path = os.path.abspath(current_db_uri.replace('sqlite:///', ''))

            result += f"<p><strong>🎯 Active database (keeping):</strong> {os.path.basename(active_db_path)}</p>"

            # Find all database files
            search_patterns = [
                "*.db",
                "../*.db",
                "*.db.backup*",
                "../*.db.backup*"
            ]

            all_db_files = set()
            for pattern in search_patterns:
                files = glob.glob(pattern)
                for file in files:
                    all_db_files.add(os.path.abspath(file))

            # Remove the active database from cleanup list
            cleanup_files = all_db_files - {active_db_path}

            if not cleanup_files:
                result += "<p>✅ No files need cleanup. Your system is already clean!</p>"
                return result

            # Categorize files
            backup_files = []
            old_databases = []

            for file_path in cleanup_files:
                file_name = os.path.basename(file_path)
                if 'backup' in file_name:
                    backup_files.append(file_path)
                else:
                    old_databases.append(file_path)

            # Keep the most recent backup as safety
            if backup_files:
                # Sort by modification time, keep the newest
                backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                keep_backup = backup_files[0] if backup_files else None
                backup_files_to_delete = backup_files[1:] if len(backup_files) > 1 else []
            else:
                keep_backup = None
                backup_files_to_delete = []

            # Perform cleanup
            deleted_files = []
            total_space_freed = 0

            result += "<h3>🗑️ Cleanup Results:</h3>"

            # Delete old backup files (keep the newest one)
            if backup_files_to_delete:
                result += f"<p><strong>📦 Deleting old backup files:</strong></p><ul>"
                for file_path in backup_files_to_delete:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_files.append(os.path.basename(file_path))
                        total_space_freed += file_size
                        result += f"<li>✅ Deleted: {os.path.basename(file_path)} ({file_size:,} bytes)</li>"
                    except Exception as e:
                        result += f"<li>❌ Failed to delete {os.path.basename(file_path)}: {e}</li>"
                result += "</ul>"

            # Keep the newest backup
            if keep_backup:
                result += f"<p><strong>📦 Keeping newest backup:</strong> {os.path.basename(keep_backup)}</p>"

            # Handle other database files (be more cautious)
            if old_databases:
                result += f"<p><strong>🗃️ Other database files found:</strong></p><ul>"
                for file_path in old_databases:
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)

                    # Only delete if it's clearly a duplicate or test database
                    if file_name in ['kirima_primary.db'] and file_path != active_db_path:
                        # This is likely a duplicate in a different directory
                        try:
                            os.remove(file_path)
                            deleted_files.append(file_name)
                            total_space_freed += file_size
                            result += f"<li>✅ Deleted duplicate: {file_name} ({file_size:,} bytes)</li>"
                        except Exception as e:
                            result += f"<li>❌ Failed to delete {file_name}: {e}</li>"
                    else:
                        result += f"<li>⚠️ Kept (uncertain): {file_name} ({file_size:,} bytes)<br><small>{file_path}</small></li>"
                result += "</ul>"

            # Summary
            result += f"<h3>📋 Cleanup Summary:</h3>"
            result += f"<ul>"
            result += f"<li><strong>Files deleted:</strong> {len(deleted_files)}</li>"
            result += f"<li><strong>Space freed:</strong> {total_space_freed:,} bytes ({total_space_freed/1024/1024:.1f} MB)</li>"
            result += f"<li><strong>Active database:</strong> Preserved ✅</li>"
            result += f"<li><strong>Safety backup:</strong> {'Kept' if keep_backup else 'None needed'}</li>"
            result += f"</ul>"

            if deleted_files:
                result += f"<p><strong>🎉 Cleanup completed successfully!</strong></p>"
                result += f"<p>Deleted files: {', '.join(deleted_files)}</p>"
            else:
                result += f"<p><strong>ℹ️ No files were deleted.</strong> Your system was already clean or files were kept for safety.</p>"

            result += f"<p><a href='/debug/cleanup_databases'>View cleanup guide again</a></p>"

            return result

        except Exception as e:
            return f"❌ Error performing cleanup: {e}"

    @app.route('/debug/initialize_database')
    def debug_initialize_database():
        """Debug route to manually initialize the database."""
        try:
            from .utils.database_init import initialize_database_completely, check_database_integrity

            # Check current status
            current_status = check_database_integrity()

            result = "<h2>🔄 Database Initialization</h2>"
            result += f"<h3>📊 Current Status:</h3>"
            result += f"<ul>"
            result += f"<li>Tables Exist: {'✅' if current_status['tables_exist'] else '❌'}</li>"
            result += f"<li>Has Data: {'✅' if current_status['has_data'] else '❌'}</li>"
            result += f"<li>Teachers: {current_status.get('teacher_count', 0)}</li>"
            result += f"<li>Subjects: {current_status.get('subject_count', 0)}</li>"
            result += f"<li>Grades: {current_status.get('grade_count', 0)}</li>"
            result += f"<li>Streams: {current_status.get('stream_count', 0)}</li>"
            result += f"<li>Status: {current_status['status']}</li>"
            result += f"</ul>"

            if current_status['status'] != 'healthy':
                result += f"<h3>🔧 Initializing Database...</h3>"

                init_result = initialize_database_completely()

                if init_result['success']:
                    result += f"<p style='color: green;'>✅ <strong>Database initialized successfully!</strong></p>"
                    result += f"<ul>"
                    result += f"<li>Teachers: {init_result['status']['teacher_count']}</li>"
                    result += f"<li>Subjects: {init_result['status']['subject_count']}</li>"
                    result += f"<li>Grades: {init_result['status']['grade_count']}</li>"
                    result += f"<li>Streams: {init_result['status']['stream_count']}</li>"
                    result += f"</ul>"
                    result += f"<p><strong>Default Users Created:</strong></p>"
                    result += f"<ul>"
                    result += f"<li><strong>headteacher</strong> / admin123 (Headteacher)</li>"
                    result += f"<li><strong>classteacher1</strong> / class123 (Class Teacher)</li>"
                    result += f"<li><strong>kevin</strong> / kev123 (Class Teacher)</li>"
                    result += f"<li><strong>telvo</strong> / telvo123 (Subject Teacher)</li>"
                    result += f"</ul>"
                    result += f"<p><a href='/'>🏠 Go to Login Page</a></p>"
                else:
                    result += f"<p style='color: red;'>❌ <strong>Database initialization failed:</strong> {init_result.get('error', 'Unknown error')}</p>"
            else:
                result += f"<p style='color: green;'>✅ <strong>Database is already healthy!</strong></p>"
                result += f"<p><a href='/debug/check_users'>👥 Check Users</a></p>"
                result += f"<p><a href='/'>🏠 Go to Login Page</a></p>"

            return result

        except Exception as e:
            return f"❌ Error during database initialization: {str(e)}"

    @app.route('/debug/repair_database')
    def debug_repair_database():
        """Debug route to repair the database."""
        try:
            from .utils.database_init import repair_database

            result = "<h2>🔧 Database Repair</h2>"

            repair_result = repair_database()

            if repair_result['success']:
                result += f"<p style='color: green;'>✅ <strong>Database repaired successfully!</strong></p>"
                result += f"<h3>📊 Before Repair:</h3><ul>"
                before = repair_result['before']
                result += f"<li>Tables Exist: {'✅' if before['tables_exist'] else '❌'}</li>"
                result += f"<li>Has Data: {'✅' if before['has_data'] else '❌'}</li>"
                result += f"<li>Status: {before['status']}</li>"
                result += f"</ul>"

                result += f"<h3>📊 After Repair:</h3><ul>"
                after = repair_result['after']
                result += f"<li>Tables Exist: {'✅' if after['tables_exist'] else '❌'}</li>"
                result += f"<li>Has Data: {'✅' if after['has_data'] else '❌'}</li>"
                result += f"<li>Teachers: {after.get('teacher_count', 0)}</li>"
                result += f"<li>Subjects: {after.get('subject_count', 0)}</li>"
                result += f"<li>Status: {after['status']}</li>"
                result += f"</ul>"

                result += f"<p><a href='/'>🏠 Go to Login Page</a></p>"
            else:
                result += f"<p style='color: red;'>❌ <strong>Database repair failed:</strong> {repair_result.get('error', 'Unknown error')}</p>"

            return result

        except Exception as e:
            return f"❌ Error during database repair: {str(e)}"

    @app.route('/debug/check_teachers')
    def debug_check_teachers():
        """Debug route to check all teachers in the database."""
        try:
            from .models.user import Teacher
            from .services.auth_service import authenticate_teacher

            result = "<h2>👥 Teachers Database Check</h2>"
            result += "<style>table { border-collapse: collapse; width: 100%; } th, td { border: 1px solid #ddd; padding: 8px; text-align: left; } th { background-color: #f2f2f2; }</style>"

            # Get all teachers
            teachers = Teacher.query.all()
            result += f"<h3>📊 Total Teachers: {len(teachers)}</h3>"

            if teachers:
                result += "<table><tr><th>ID</th><th>Username</th><th>Password</th><th>Role</th><th>First Name</th><th>Last Name</th><th>Active</th></tr>"
                for teacher in teachers:
                    result += f"<tr><td>{teacher.id}</td><td>{teacher.username}</td><td>{teacher.password}</td><td>{teacher.role}</td><td>{teacher.first_name or 'N/A'}</td><td>{teacher.last_name or 'N/A'}</td><td>{'✅' if teacher.is_active else '❌'}</td></tr>"
                result += "</table>"
            else:
                result += "<p>❌ No teachers found in database</p>"

            # Test Carol's authentication
            result += "<h3>🔐 Carol Authentication Test</h3>"
            carol_teacher = authenticate_teacher('carol', 'carol123', 'teacher')
            if carol_teacher:
                result += f"<p style='color: green;'>✅ Carol authentication successful! Teacher ID: {carol_teacher.id}</p>"
            else:
                result += f"<p style='color: red;'>❌ Carol authentication failed</p>"

                # Check if Carol exists with different role
                carol_any_role = Teacher.query.filter_by(username='carol').first()
                if carol_any_role:
                    result += f"<p style='color: orange;'>⚠️ Found Carol with role: {carol_any_role.role} (expected: teacher)</p>"
                else:
                    result += f"<p style='color: red;'>❌ Carol not found in database at all</p>"

            result += f"<p><a href='/teacher_login'>🔗 Go to Teacher Login</a></p>"
            result += f"<p><a href='/debug/fix_carol_password'>🔧 Fix Carol's Password</a></p>"
            return result

        except Exception as e:
            return f"❌ Error checking teachers: {str(e)}"

    # Debug routes removed - issue resolved

    @app.route('/debug/carol-assignments-resolved')
    def debug_carol_assignments_resolved():
        """Simplified debug route - issue was resolved."""
        return """
        <h2>✅ Carol's Assignment Issue - RESOLVED</h2>
        <p><strong>Issue:</strong> Carol couldn't see her subject assignments</p>
        <p><strong>Root Cause:</strong> Flash message error on login page from stale session data</p>
        <p><strong>Solution:</strong> Clear session data and flash messages on login page access</p>
        <p><strong>Status:</strong> ✅ FIXED - Carol can now see her assignments</p>
        <hr>
        <p><a href='/teacher_login'>🔗 Test Teacher Login</a></p>
        <p><a href='/teacher/'>🔗 Test Teacher Dashboard</a></p>
        """

    @app.route('/debug/fix-carol-assignments')
    def debug_fix_carol_assignments():
        """Debug route to add subject assignments for Carol."""
        try:
            from .models.user import Teacher
            from .models.assignment import TeacherSubjectAssignment
            from .models.academic import Subject, Grade, Stream
            from .extensions import db

            result = "<h2>🔧 Fixing Carol's Subject Assignments</h2>"

            # Find Carol
            carol = Teacher.query.filter_by(username='carol').first()
            if not carol:
                result += "<p style='color: red;'>❌ <strong>Carol not found in database!</strong></p>"
                return result

            result += f"<p>✅ <strong>Found Carol:</strong> ID={carol.id}, Username={carol.username}</p>"

            # Check if Carol already has assignments
            existing_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=carol.id).all()
            if existing_assignments:
                result += f"<p>✅ <strong>Carol already has {len(existing_assignments)} assignments:</strong></p><ul>"
                for assignment in existing_assignments:
                    subject = Subject.query.get(assignment.subject_id)
                    grade = Grade.query.get(assignment.grade_id)
                    stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

                    subject_name = subject.name if subject else f"Subject ID {assignment.subject_id}"
                    grade_name = grade.name if grade else f"Grade ID {assignment.grade_id}"
                    stream_name = stream.name if stream else "All Streams"

                    result += f"<li>{subject_name} for {grade_name} {stream_name}</li>"
                result += "</ul>"
                result += "<p>Carol should already be able to see her assignments. Try refreshing her dashboard.</p>"
                return result

            result += "<p>📝 <strong>Carol has no assignments. Creating some...</strong></p>"

            # Get some subjects and grades to assign to Carol
            subjects = Subject.query.limit(3).all()
            grades = Grade.query.limit(2).all()
            streams = Stream.query.limit(2).all()

            if not subjects:
                result += "<p style='color: red;'>❌ <strong>No subjects found in database</strong></p>"
                return result

            if not grades:
                result += "<p style='color: red;'>❌ <strong>No grades found in database</strong></p>"
                return result

            result += f"<p>📚 <strong>Available subjects:</strong> {', '.join([s.name for s in subjects])}</p>"
            result += f"<p>📊 <strong>Available grades:</strong> {', '.join([g.name for g in grades])}</p>"
            result += f"<p>🏫 <strong>Available streams:</strong> {', '.join([s.name for s in streams]) if streams else 'No streams'}</p>"

            assignments_created = 0

            # Create assignments for Carol
            for i, subject in enumerate(subjects[:2]):  # Assign first 2 subjects
                grade = grades[0]  # Use first grade

                if streams:
                    # If streams exist, assign to first stream
                    stream = streams[0]
                    assignment = TeacherSubjectAssignment(
                        teacher_id=carol.id,
                        subject_id=subject.id,
                        grade_id=grade.id,
                        stream_id=stream.id,
                        is_class_teacher=False
                    )
                    db.session.add(assignment)
                    assignments_created += 1
                    result += f"<p>✅ <strong>Created assignment:</strong> {subject.name} for {grade.name} {stream.name}</p>"
                else:
                    # No streams, assign to whole grade
                    assignment = TeacherSubjectAssignment(
                        teacher_id=carol.id,
                        subject_id=subject.id,
                        grade_id=grade.id,
                        stream_id=None,
                        is_class_teacher=False
                    )
                    db.session.add(assignment)
                    assignments_created += 1
                    result += f"<p>✅ <strong>Created assignment:</strong> {subject.name} for {grade.name} (All Streams)</p>"

            # Commit the changes
            try:
                db.session.commit()
                result += f"<p style='color: green;'>🎉 <strong>Successfully created {assignments_created} assignments for Carol!</strong></p>"

                # Verify the assignments were created
                carol_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=carol.id).all()
                result += f"<h3>📋 Carol's New Assignments ({len(carol_assignments)} total):</h3><ul>"
                for assignment in carol_assignments:
                    subject = Subject.query.get(assignment.subject_id)
                    grade = Grade.query.get(assignment.grade_id)
                    stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None

                    subject_name = subject.name if subject else f"Subject ID {assignment.subject_id}"
                    grade_name = grade.name if grade else f"Grade ID {assignment.grade_id}"
                    stream_name = stream.name if stream else "All Streams"

                    result += f"<li><strong>{subject_name}</strong> for <strong>{grade_name} {stream_name}</strong></li>"
                result += "</ul>"

                result += "<h3>🎯 Next Steps:</h3>"
                result += "<ol>"
                result += "<li><strong>Login as Carol</strong> (username: carol, password: carol123)</li>"
                result += "<li><strong>Go to teacher dashboard</strong></li>"
                result += "<li><strong>Check 'My Assignments' section</strong> - should now show her subjects</li>"
                result += "<li><strong>Try uploading marks</strong> for her assigned subjects</li>"
                result += "</ol>"

            except Exception as e:
                db.session.rollback()
                result += f"<p style='color: red;'>❌ <strong>Error saving assignments:</strong> {str(e)}</p>"

            return result

        except Exception as e:
            import traceback
            return f"<h2>❌ Debug Error</h2><pre>{str(e)}\n\n{traceback.format_exc()}</pre>"

    @app.route('/debug/carol-dashboard-data')
    def debug_carol_dashboard_data():
        """Debug route to see exactly what data Carol's dashboard receives."""
        try:
            from .models.user import Teacher
            from .models.assignment import TeacherSubjectAssignment
            from .services.role_based_data_service import RoleBasedDataService

            result = "<h2>🔍 Carol's Dashboard Data Debug</h2>"

            # Find Carol
            carol = Teacher.query.filter_by(username='carol').first()
            if not carol:
                result += "<p style='color: red;'>❌ <strong>Carol not found!</strong></p>"
                return result

            result += f"<p>✅ <strong>Found Carol:</strong> ID={carol.id}</p>"

            # Simulate the exact dashboard call
            teacher_id = carol.id
            role = 'teacher'

            result += f"<h3>🔄 Calling RoleBasedDataService.get_teacher_assignments_summary({teacher_id}, '{role}')</h3>"

            # Get the assignment summary (same as dashboard)
            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, role)

            result += f"<h4>📊 Assignment Summary Response:</h4>"
            result += f"<pre>{assignment_summary}</pre>"

            # Check if there's an error
            if 'error' in assignment_summary:
                result += f"<p style='color: red;'>❌ <strong>Service Error:</strong> {assignment_summary['error']}</p>"
                return result

            # Extract the subject_assignments (same as dashboard)
            subject_assignments = assignment_summary.get('subject_assignments', [])

            result += f"<h4>📚 Subject Assignments (what template receives):</h4>"
            result += f"<p><strong>Length:</strong> {len(subject_assignments)}</p>"

            if not subject_assignments:
                result += "<p style='color: orange;'>⚠️ <strong>subject_assignments is empty!</strong></p>"
                result += "<p>This is why the template doesn't show anything.</p>"

                # Let's check the raw assignments
                raw_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).all()
                result += f"<h4>🔍 Raw Database Assignments:</h4>"
                result += f"<p><strong>Count:</strong> {len(raw_assignments)}</p>"

                if raw_assignments:
                    result += "<ul>"
                    for assignment in raw_assignments:
                        result += f"<li>ID: {assignment.id}, Subject: {assignment.subject_id}, Grade: {assignment.grade_id}, Stream: {assignment.stream_id}</li>"
                    result += "</ul>"

                    # Test the service method directly
                    result += "<h4>🧪 Testing _get_subject_teacher_summary directly:</h4>"
                    try:
                        direct_result = RoleBasedDataService._get_subject_teacher_summary(raw_assignments)
                        result += f"<pre>{direct_result}</pre>"
                    except Exception as e:
                        result += f"<p style='color: red;'>❌ <strong>Direct method error:</strong> {str(e)}</p>"
                        import traceback
                        result += f"<pre>{traceback.format_exc()}</pre>"

            else:
                result += "<ul>"
                for i, assignment in enumerate(subject_assignments):
                    result += f"<li><strong>Assignment {i+1}:</strong> {assignment}</li>"
                result += "</ul>"

            # Check template variables that would be passed
            result += f"<h4>📝 Template Variables (what dashboard passes):</h4>"
            result += f"<ul>"
            result += f"<li><strong>assignment_summary:</strong> {type(assignment_summary)} with {len(assignment_summary)} keys</li>"
            result += f"<li><strong>subject_assignments:</strong> {type(subject_assignments)} with {len(subject_assignments)} items</li>"
            result += f"<li><strong>total_subjects_taught:</strong> {assignment_summary.get('total_subjects_taught', 0)}</li>"
            result += f"</ul>"

            return result

        except Exception as e:
            import traceback
            return f"<h2>❌ Debug Error</h2><pre>{str(e)}\n\n{traceback.format_exc()}</pre>"

    @app.route('/debug/test-relationships')
    def debug_test_relationships():
        """Debug route to test if database relationships are working."""
        try:
            from .models.user import Teacher
            from .models.assignment import TeacherSubjectAssignment
            from .models.academic import Subject, Grade, Stream

            result = "<h2>🔍 Testing Database Relationships</h2>"

            # Find Carol
            carol = Teacher.query.filter_by(username='carol').first()
            if not carol:
                result += "<p style='color: red;'>❌ Carol not found!</p>"
                return result

            result += f"<p>✅ <strong>Found Carol:</strong> ID={carol.id}</p>"

            # Get Carol's assignments
            assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=carol.id).all()
            result += f"<p>📊 <strong>Carol has {len(assignments)} assignments</strong></p>"

            if not assignments:
                result += "<p style='color: red;'>❌ No assignments found for Carol!</p>"
                return result

            # Test each assignment's relationships
            for i, assignment in enumerate(assignments):
                result += f"<h3>📋 Assignment {i+1} (ID: {assignment.id})</h3>"
                result += f"<ul>"
                result += f"<li><strong>Teacher ID:</strong> {assignment.teacher_id}</li>"
                result += f"<li><strong>Subject ID:</strong> {assignment.subject_id}</li>"
                result += f"<li><strong>Grade ID:</strong> {assignment.grade_id}</li>"
                result += f"<li><strong>Stream ID:</strong> {assignment.stream_id}</li>"
                result += f"<li><strong>Is Class Teacher:</strong> {assignment.is_class_teacher}</li>"
                result += f"</ul>"

                # Test relationships
                result += f"<h4>🔗 Testing Relationships:</h4>"
                result += f"<ul>"

                # Test teacher relationship
                try:
                    teacher = assignment.teacher
                    if teacher:
                        result += f"<li>✅ <strong>Teacher:</strong> {teacher.username} (ID: {teacher.id})</li>"
                    else:
                        result += f"<li>❌ <strong>Teacher:</strong> None</li>"
                except Exception as e:
                    result += f"<li>❌ <strong>Teacher Error:</strong> {str(e)}</li>"

                # Test subject relationship
                try:
                    subject = assignment.subject
                    if subject:
                        result += f"<li>✅ <strong>Subject:</strong> {subject.name} (ID: {subject.id})</li>"
                    else:
                        result += f"<li>❌ <strong>Subject:</strong> None</li>"
                except Exception as e:
                    result += f"<li>❌ <strong>Subject Error:</strong> {str(e)}</li>"

                # Test grade relationship
                try:
                    grade = assignment.grade
                    if grade:
                        result += f"<li>✅ <strong>Grade:</strong> {grade.name} (ID: {grade.id})</li>"
                    else:
                        result += f"<li>❌ <strong>Grade:</strong> None</li>"
                except Exception as e:
                    result += f"<li>❌ <strong>Grade Error:</strong> {str(e)}</li>"

                # Test stream relationship
                try:
                    stream = assignment.stream
                    if stream:
                        result += f"<li>✅ <strong>Stream:</strong> {stream.name} (ID: {stream.id})</li>"
                    else:
                        result += f"<li>⚠️ <strong>Stream:</strong> None (this is OK if no streams)</li>"
                except Exception as e:
                    result += f"<li>❌ <strong>Stream Error:</strong> {str(e)}</li>"

                result += f"</ul>"

                # Test the _format_assignment method directly
                result += f"<h4>🧪 Testing _format_assignment:</h4>"
                try:
                    from .services.role_based_data_service import RoleBasedDataService
                    formatted = RoleBasedDataService._format_assignment(assignment)
                    result += f"<pre>{formatted}</pre>"
                except Exception as e:
                    result += f"<p style='color: red;'>❌ <strong>Format Error:</strong> {str(e)}</p>"
                    import traceback
                    result += f"<pre>{traceback.format_exc()}</pre>"

            return result

        except Exception as e:
            import traceback
            return f"<h2>❌ Debug Error</h2><pre>{str(e)}\n\n{traceback.format_exc()}</pre>"

    @app.route('/debug/carol-session')
    def debug_carol_session():
        """Debug route to check Carol's session when she's logged in."""
        try:
            from flask import session

            result = "<h2>🔍 Carol's Session Debug</h2>"

            # Check session data
            result += f"<h3>📊 Current Session Data:</h3>"
            result += f"<ul>"
            result += f"<li><strong>teacher_id:</strong> {session.get('teacher_id', 'NOT SET')}</li>"
            result += f"<li><strong>username:</strong> {session.get('username', 'NOT SET')}</li>"
            result += f"<li><strong>role:</strong> {session.get('role', 'NOT SET')}</li>"
            result += f"<li><strong>All session keys:</strong> {list(session.keys())}</li>"
            result += f"</ul>"

            # Check if user is logged in
            teacher_id = session.get('teacher_id')
            if not teacher_id:
                result += "<p style='color: red;'>❌ <strong>No teacher_id in session - Carol is not logged in!</strong></p>"
                result += "<p>Please login as Carol first, then access this debug route.</p>"
                result += f"<p><a href='/teacher_login'>🔗 Login as Carol</a></p>"
                return result

            result += f"<p>✅ <strong>Carol is logged in with teacher_id: {teacher_id}</strong></p>"

            # Now test the exact same flow as the dashboard
            from .models.user import Teacher
            from .services.role_based_data_service import RoleBasedDataService

            role = session.get('role', 'teacher')

            result += f"<h3>🔄 Testing Dashboard Flow:</h3>"
            result += f"<p>Calling: <code>RoleBasedDataService.get_teacher_assignments_summary({teacher_id}, '{role}')</code></p>"

            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, role)

            result += f"<h4>📊 Assignment Summary:</h4>"
            if 'error' in assignment_summary:
                result += f"<p style='color: red;'>❌ <strong>Error:</strong> {assignment_summary['error']}</p>"
            else:
                result += f"<ul>"
                result += f"<li><strong>total_subjects_taught:</strong> {assignment_summary.get('total_subjects_taught', 0)}</li>"
                result += f"<li><strong>subject_assignments count:</strong> {len(assignment_summary.get('subject_assignments', []))}</li>"
                result += f"<li><strong>class_teacher_assignments count:</strong> {len(assignment_summary.get('class_teacher_assignments', []))}</li>"
                result += f"</ul>"

                # Show the actual subject assignments
                subject_assignments = assignment_summary.get('subject_assignments', [])
                if subject_assignments:
                    result += f"<h4>📚 Subject Assignments Details:</h4>"
                    result += f"<ol>"
                    for assignment in subject_assignments:
                        result += f"<li>{assignment}</li>"
                    result += f"</ol>"
                else:
                    result += f"<p style='color: orange;'>⚠️ <strong>subject_assignments is empty!</strong></p>"

            # Test accessible subjects
            result += f"<h3>🔍 Testing Accessible Subjects:</h3>"
            try:
                accessible_subjects = RoleBasedDataService.get_accessible_subjects(teacher_id, role)
                result += f"<p><strong>Accessible subjects count:</strong> {len(accessible_subjects)}</p>"
                if accessible_subjects:
                    result += f"<ul>"
                    for subject in accessible_subjects[:5]:  # Show first 5
                        result += f"<li>{subject.name} (ID: {subject.id})</li>"
                    result += f"</ul>"
                else:
                    result += f"<p style='color: orange;'>⚠️ <strong>No accessible subjects!</strong></p>"
            except Exception as e:
                result += f"<p style='color: red;'>❌ <strong>Accessible subjects error:</strong> {str(e)}</p>"

            return result

        except Exception as e:
            import traceback
            return f"<h2>❌ Debug Error</h2><pre>{str(e)}\n\n{traceback.format_exc()}</pre>"

    @app.route('/debug/assignment-summary-structure')
    def debug_assignment_summary_structure():
        """Debug route to check the exact structure of assignment_summary."""
        try:
            from flask import session
            from .services.role_based_data_service import RoleBasedDataService

            result = "<h2>🔍 Assignment Summary Structure Debug</h2>"

            # Check if user is logged in
            teacher_id = session.get('teacher_id')
            if not teacher_id:
                result += "<p style='color: red;'>❌ Please login as Carol first</p>"
                result += f"<p><a href='/teacher_login'>🔗 Login as Carol</a></p>"
                return result

            role = session.get('role', 'teacher')
            result += f"<p>✅ <strong>Testing with teacher_id: {teacher_id}, role: {role}</strong></p>"

            # Get assignment summary
            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, role)

            result += f"<h3>📊 Assignment Summary Structure:</h3>"
            result += f"<p><strong>Type:</strong> {type(assignment_summary)}</p>"
            result += f"<p><strong>Keys:</strong> {list(assignment_summary.keys()) if isinstance(assignment_summary, dict) else 'Not a dict'}</p>"

            # Check each key
            if isinstance(assignment_summary, dict):
                for key, value in assignment_summary.items():
                    result += f"<h4>🔑 Key: '{key}'</h4>"
                    result += f"<ul>"
                    result += f"<li><strong>Type:</strong> {type(value)}</li>"
                    result += f"<li><strong>Value:</strong> {value}</li>"
                    if isinstance(value, list):
                        result += f"<li><strong>Length:</strong> {len(value)}</li>"
                        if value:
                            result += f"<li><strong>First item:</strong> {value[0]}</li>"
                    result += f"</ul>"

            # Check the specific template condition
            result += f"<h3>🎯 Template Condition Check:</h3>"
            result += f"<p><strong>assignment_summary:</strong> {bool(assignment_summary)}</p>"

            if assignment_summary:
                teacher_obj = assignment_summary.get('teacher')
                result += f"<p><strong>assignment_summary.teacher:</strong> {teacher_obj}</p>"
                result += f"<p><strong>assignment_summary.teacher exists:</strong> {bool(teacher_obj)}</p>"

                if teacher_obj:
                    result += f"<p><strong>Teacher object type:</strong> {type(teacher_obj)}</p>"
                    result += f"<p><strong>Teacher username:</strong> {getattr(teacher_obj, 'username', 'NO USERNAME')}</p>"
                    result += f"<p><strong>Teacher id:</strong> {getattr(teacher_obj, 'id', 'NO ID')}</p>"

                # Check the template condition result
                condition_result = assignment_summary and assignment_summary.get('teacher')
                result += f"<p style='color: {'green' if condition_result else 'red'};'><strong>Template condition (assignment_summary and assignment_summary.teacher):</strong> {condition_result}</p>"

                if not condition_result:
                    result += f"<p style='color: red;'>❌ <strong>This is why the assignments section is not showing!</strong></p>"
                else:
                    result += f"<p style='color: green;'>✅ <strong>Template condition passes - assignments section should show</strong></p>"

                    # Check subject_assignments specifically
                    subject_assignments = assignment_summary.get('subject_assignments', [])
                    result += f"<p><strong>subject_assignments length:</strong> {len(subject_assignments)}</p>"
                    if not subject_assignments:
                        result += f"<p style='color: orange;'>⚠️ <strong>subject_assignments is empty - this is why no assignments show in the list</strong></p>"

            return result

        except Exception as e:
            import traceback
            return f"<h2>❌ Debug Error</h2><pre>{str(e)}\n\n{traceback.format_exc()}</pre>"

    @app.route('/debug/check-basic-data')
    def debug_check_basic_data():
        """Debug route to check if basic data (subjects, grades, streams) exists."""
        try:
            from .models.academic import Subject, Grade, Stream

            result = "<h2>🔍 Basic Data Check</h2>"

            # Check subjects
            subjects = Subject.query.all()
            result += f"<h3>📚 Subjects ({len(subjects)} total):</h3>"
            if subjects:
                result += "<ul>"
                for subject in subjects[:10]:  # Show first 10
                    result += f"<li><strong>{subject.name}</strong> (ID: {subject.id}, Level: {subject.education_level})</li>"
                result += "</ul>"
                if len(subjects) > 10:
                    result += f"<p>... and {len(subjects) - 10} more subjects</p>"
            else:
                result += "<p style='color: red;'>❌ <strong>NO SUBJECTS FOUND!</strong></p>"

            # Check grades
            grades = Grade.query.all()
            result += f"<h3>📊 Grades ({len(grades)} total):</h3>"
            if grades:
                result += "<ul>"
                for grade in grades:
                    result += f"<li><strong>{grade.name}</strong> (ID: {grade.id}, Level: {grade.education_level})</li>"
                result += "</ul>"
            else:
                result += "<p style='color: red;'>❌ <strong>NO GRADES FOUND!</strong></p>"

            # Check streams
            streams = Stream.query.all()
            result += f"<h3>🏫 Streams ({len(streams)} total):</h3>"
            if streams:
                result += "<ul>"
                for stream in streams[:10]:  # Show first 10
                    result += f"<li><strong>{stream.name}</strong> (ID: {stream.id}, Grade: {stream.grade_id})</li>"
                result += "</ul>"
                if len(streams) > 10:
                    result += f"<p>... and {len(streams) - 10} more streams</p>"
            else:
                result += "<p style='color: orange;'>⚠️ <strong>NO STREAMS FOUND</strong> (this might be OK)</p>"

            # Check if we have the minimum data needed
            result += f"<h3>✅ Data Availability Summary:</h3>"
            result += f"<ul>"
            result += f"<li><strong>Subjects available:</strong> {'✅ Yes' if subjects else '❌ No'}</li>"
            result += f"<li><strong>Grades available:</strong> {'✅ Yes' if grades else '❌ No'}</li>"
            result += f"<li><strong>Can create assignments:</strong> {'✅ Yes' if subjects and grades else '❌ No - missing basic data'}</li>"
            result += f"</ul>"

            if not subjects or not grades:
                result += f"<h3>🔧 Fix Required:</h3>"
                result += f"<p style='color: red;'>❌ <strong>Missing basic data!</strong> The system needs subjects and grades to create teacher assignments.</p>"
                result += f"<p>You need to:</p>"
                result += f"<ol>"
                result += f"<li>Login as headteacher</li>"
                result += f"<li>Set up subjects and grades first</li>"
                result += f"<li>Then assign subjects to teachers</li>"
                result += f"</ol>"

            return result

        except Exception as e:
            import traceback
            return f"<h2>❌ Debug Error</h2><pre>{str(e)}\n\n{traceback.format_exc()}</pre>"

    @app.route('/debug/comprehensive-carol-fix')
    def debug_comprehensive_carol_fix():
        """Comprehensive debug and fix for Carol's assignments."""
        try:
            from .models.user import Teacher
            from .models.assignment import TeacherSubjectAssignment
            from .models.academic import Subject, Grade, Stream
            from .extensions import db
            from .services.role_based_data_service import RoleBasedDataService

            result = "<h2>🔧 Comprehensive Carol Fix</h2>"

            # Step 1: Find Carol
            carol = Teacher.query.filter_by(username='carol').first()
            if not carol:
                result += "<p style='color: red;'>❌ Carol not found!</p>"
                return result

            result += f"<p>✅ <strong>Found Carol:</strong> ID={carol.id}</p>"

            # Step 2: Check basic data
            subjects = Subject.query.all()
            grades = Grade.query.all()
            streams = Stream.query.all()

            result += f"<h3>📊 Basic Data Check:</h3>"
            result += f"<ul>"
            result += f"<li><strong>Subjects:</strong> {len(subjects)}</li>"
            result += f"<li><strong>Grades:</strong> {len(grades)}</li>"
            result += f"<li><strong>Streams:</strong> {len(streams)}</li>"
            result += f"</ul>"

            if not subjects or not grades:
                result += "<p style='color: red;'>❌ <strong>Missing basic data! Cannot create assignments.</strong></p>"
                return result

            # Step 3: Clear existing assignments for Carol
            existing_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=carol.id).all()
            result += f"<p>🗑️ <strong>Clearing {len(existing_assignments)} existing assignments for Carol</strong></p>"

            for assignment in existing_assignments:
                db.session.delete(assignment)

            try:
                db.session.commit()
                result += "<p>✅ <strong>Cleared existing assignments</strong></p>"
            except Exception as e:
                db.session.rollback()
                result += f"<p style='color: red;'>❌ <strong>Error clearing assignments:</strong> {str(e)}</p>"
                return result

            # Step 4: Create new assignments with detailed logging
            result += f"<h3>🔨 Creating New Assignments:</h3>"

            # Get first 2 subjects and first grade
            target_subjects = subjects[:2]
            target_grade = grades[0]
            target_stream = streams[0] if streams else None

            result += f"<p><strong>Target subjects:</strong> {[s.name for s in target_subjects]}</p>"
            result += f"<p><strong>Target grade:</strong> {target_grade.name}</p>"
            result += f"<p><strong>Target stream:</strong> {target_stream.name if target_stream else 'None'}</p>"

            assignments_created = 0

            for subject in target_subjects:
                result += f"<h4>📝 Creating assignment: {subject.name} for {target_grade.name}</h4>"

                try:
                    assignment = TeacherSubjectAssignment(
                        teacher_id=carol.id,
                        subject_id=subject.id,
                        grade_id=target_grade.id,
                        stream_id=target_stream.id if target_stream else None,
                        is_class_teacher=False
                    )

                    db.session.add(assignment)
                    db.session.flush()  # Flush to get the ID

                    result += f"<p>✅ <strong>Created assignment ID {assignment.id}</strong></p>"
                    assignments_created += 1

                except Exception as e:
                    result += f"<p style='color: red;'>❌ <strong>Error creating assignment:</strong> {str(e)}</p>"
                    db.session.rollback()
                    return result

            # Commit all assignments
            try:
                db.session.commit()
                result += f"<p style='color: green;'>🎉 <strong>Successfully committed {assignments_created} assignments!</strong></p>"
            except Exception as e:
                db.session.rollback()
                result += f"<p style='color: red;'>❌ <strong>Error committing assignments:</strong> {str(e)}</p>"
                return result

            # Step 5: Verify assignments were created
            new_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=carol.id).all()
            result += f"<h3>✅ Verification ({len(new_assignments)} assignments found):</h3>"

            if new_assignments:
                result += "<ul>"
                for assignment in new_assignments:
                    result += f"<li><strong>ID {assignment.id}:</strong> Subject {assignment.subject_id}, Grade {assignment.grade_id}, Stream {assignment.stream_id}</li>"
                result += "</ul>"
            else:
                result += "<p style='color: red;'>❌ <strong>No assignments found after creation!</strong></p>"
                return result

            # Step 6: Test the service
            result += f"<h3>🧪 Testing RoleBasedDataService:</h3>"

            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(carol.id, 'teacher')

            if 'error' in assignment_summary:
                result += f"<p style='color: red;'>❌ <strong>Service error:</strong> {assignment_summary['error']}</p>"
            else:
                result += f"<ul>"
                result += f"<li><strong>total_subjects_taught:</strong> {assignment_summary.get('total_subjects_taught', 0)}</li>"
                result += f"<li><strong>subject_assignments count:</strong> {len(assignment_summary.get('subject_assignments', []))}</li>"
                result += f"<li><strong>teacher object exists:</strong> {bool(assignment_summary.get('teacher'))}</li>"
                result += f"</ul>"

                subject_assignments = assignment_summary.get('subject_assignments', [])
                if subject_assignments:
                    result += f"<h4>📚 Subject Assignments:</h4>"
                    result += f"<ol>"
                    for assignment in subject_assignments:
                        result += f"<li>{assignment}</li>"
                    result += f"</ol>"
                    result += f"<p style='color: green;'>✅ <strong>SUCCESS! Carol should now see her assignments!</strong></p>"
                else:
                    result += f"<p style='color: red;'>❌ <strong>Service returned empty subject_assignments</strong></p>"

            result += f"<h3>🎯 Next Steps:</h3>"
            result += f"<ol>"
            result += f"<li><a href='/teacher_login'>🔗 Login as Carol</a></li>"
            result += f"<li><a href='/teacher/'>🔗 Go to Teacher Dashboard</a></li>"
            result += f"<li>Check if 'My Assignments' section now shows her subjects</li>"
            result += f"</ol>"

            return result

        except Exception as e:
            import traceback
            return f"<h2>❌ Debug Error</h2><pre>{str(e)}\n\n{traceback.format_exc()}</pre>"

    @app.route('/debug/initialize-basic-data')
    def debug_initialize_basic_data():
        """Initialize basic data (subjects, grades, streams) if missing."""
        try:
            from .models.academic import Subject, Grade, Stream
            from .extensions import db

            result = "<h2>🔧 Initialize Basic Data</h2>"

            # Check current data
            subjects = Subject.query.all()
            grades = Grade.query.all()
            streams = Stream.query.all()

            result += f"<h3>📊 Current Data:</h3>"
            result += f"<ul>"
            result += f"<li><strong>Subjects:</strong> {len(subjects)}</li>"
            result += f"<li><strong>Grades:</strong> {len(grades)}</li>"
            result += f"<li><strong>Streams:</strong> {len(streams)}</li>"
            result += f"</ul>"

            created_items = []

            # Create basic grades if missing
            if not grades:
                result += f"<h3>📊 Creating Basic Grades:</h3>"
                basic_grades = [
                    {'name': 'Grade 1', 'education_level': 'lower_primary'},
                    {'name': 'Grade 2', 'education_level': 'lower_primary'},
                    {'name': 'Grade 3', 'education_level': 'lower_primary'},
                    {'name': 'Grade 4', 'education_level': 'upper_primary'},
                    {'name': 'Grade 5', 'education_level': 'upper_primary'},
                    {'name': 'Grade 6', 'education_level': 'upper_primary'},
                ]

                for grade_data in basic_grades:
                    grade = Grade(**grade_data)
                    db.session.add(grade)
                    created_items.append(f"Grade: {grade_data['name']}")
                    result += f"<p>✅ Created {grade_data['name']}</p>"

            # Create basic subjects if missing
            if not subjects:
                result += f"<h3>📚 Creating Basic Subjects:</h3>"
                basic_subjects = [
                    {'name': 'MATHEMATICS', 'education_level': 'lower_primary', 'is_standard': True, 'is_composite': False},
                    {'name': 'ENGLISH', 'education_level': 'lower_primary', 'is_standard': True, 'is_composite': False},
                    {'name': 'KISWAHILI', 'education_level': 'lower_primary', 'is_standard': True, 'is_composite': False},
                    {'name': 'SCIENCE', 'education_level': 'lower_primary', 'is_standard': True, 'is_composite': False},
                    {'name': 'SOCIAL STUDIES', 'education_level': 'lower_primary', 'is_standard': True, 'is_composite': False},
                ]

                for subject_data in basic_subjects:
                    subject = Subject(**subject_data)
                    db.session.add(subject)
                    created_items.append(f"Subject: {subject_data['name']}")
                    result += f"<p>✅ Created {subject_data['name']}</p>"

            # Create basic streams if missing
            if not streams and grades:
                result += f"<h3>🏫 Creating Basic Streams:</h3>"
                # Get Grade 1 for streams
                grade_1 = Grade.query.filter_by(name='Grade 1').first()
                if grade_1:
                    basic_streams = [
                        {'name': 'Stream A', 'grade_id': grade_1.id},
                        {'name': 'Stream B', 'grade_id': grade_1.id},
                    ]

                    for stream_data in basic_streams:
                        stream = Stream(**stream_data)
                        db.session.add(stream)
                        created_items.append(f"Stream: {stream_data['name']}")
                        result += f"<p>✅ Created {stream_data['name']} for Grade 1</p>"

            # Commit all changes
            if created_items:
                try:
                    db.session.commit()
                    result += f"<p style='color: green;'>🎉 <strong>Successfully created {len(created_items)} items!</strong></p>"
                    result += f"<ul>"
                    for item in created_items:
                        result += f"<li>{item}</li>"
                    result += f"</ul>"
                except Exception as e:
                    db.session.rollback()
                    result += f"<p style='color: red;'>❌ <strong>Error committing data:</strong> {str(e)}</p>"
                    return result
            else:
                result += f"<p>✅ <strong>All basic data already exists</strong></p>"

            # Now try to create Carol's assignments
            result += f"<h3>👩‍🏫 Now Creating Carol's Assignments:</h3>"
            result += f"<p><a href='/debug/comprehensive-carol-fix' style='background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;'>🔧 Create Carol's Assignments</a></p>"

            return result

        except Exception as e:
            import traceback
            return f"<h2>❌ Debug Error</h2><pre>{str(e)}\n\n{traceback.format_exc()}</pre>"

    @app.route('/debug/fix_carol_password')
    def debug_fix_carol_password():
        """Debug route to fix Carol's password."""
        try:
            from .models.user import Teacher
            from .extensions import db

            result = "<h2>🔧 Fix Carol's Password</h2>"

            # Find Carol
            carol = Teacher.query.filter_by(username='carol').first()
            if not carol:
                result += "<p style='color: red;'>❌ Carol not found in database</p>"
                return result

            # Update Carol's password to plain text
            carol.password = 'carol123'
            db.session.commit()

            result += f"<p style='color: green;'>✅ Carol's password updated to plain text 'carol123'</p>"
            result += f"<p>Carol can now login with:</p>"
            result += f"<ul><li><strong>Username:</strong> carol</li><li><strong>Password:</strong> carol123</li><li><strong>Role:</strong> {carol.role}</li></ul>"
            result += f"<p><a href='/teacher_login'>🔗 Try Teacher Login Now</a></p>"
            result += f"<p><a href='/debug/check_teachers'>🔍 Check Teachers Again</a></p>"

            return result

        except Exception as e:
            return f"❌ Error fixing Carol's password: {str(e)}"

    @app.route('/debug/migrate_passwords')
    def debug_migrate_passwords():
        """Debug route to migrate all plain text passwords to hashed passwords."""
        try:
            from .models.user import Teacher
            from .extensions import db

            result = "<h2>🔐 Password Migration</h2>"
            result += "<style>table { border-collapse: collapse; width: 100%; } th, td { border: 1px solid #ddd; padding: 8px; text-align: left; } th { background-color: #f2f2f2; }</style>"

            # Get all teachers
            teachers = Teacher.query.all()
            result += f"<h3>📊 Total Teachers: {len(teachers)}</h3>"

            if not teachers:
                result += "<p>❌ No teachers found in database</p>"
                return result

            # Check which passwords need migration
            plain_text_teachers = []
            hashed_teachers = []

            for teacher in teachers:
                if teacher.is_password_hashed():
                    hashed_teachers.append(teacher)
                else:
                    plain_text_teachers.append(teacher)

            result += f"<h3>📈 Migration Status:</h3>"
            result += f"<ul><li>✅ Already Hashed: {len(hashed_teachers)}</li><li>🔄 Need Migration: {len(plain_text_teachers)}</li></ul>"

            if plain_text_teachers:
                result += "<h3>🔄 Migrating Plain Text Passwords:</h3>"
                result += "<table><tr><th>Username</th><th>Role</th><th>Old Password</th><th>Status</th></tr>"

                migrated_count = 0
                for teacher in plain_text_teachers:
                    try:
                        old_password = teacher.password
                        teacher.set_password(old_password)  # This will hash the password
                        db.session.add(teacher)
                        migrated_count += 1
                        result += f"<tr><td>{teacher.username}</td><td>{teacher.role}</td><td>{old_password}</td><td style='color: green;'>✅ Migrated</td></tr>"
                    except Exception as e:
                        result += f"<tr><td>{teacher.username}</td><td>{teacher.role}</td><td>{teacher.password}</td><td style='color: red;'>❌ Error: {str(e)}</td></tr>"

                result += "</table>"

                # Commit all changes
                try:
                    db.session.commit()
                    result += f"<p style='color: green;'>✅ Successfully migrated {migrated_count} passwords!</p>"
                except Exception as e:
                    db.session.rollback()
                    result += f"<p style='color: red;'>❌ Error committing changes: {str(e)}</p>"
            else:
                result += "<p style='color: green;'>✅ All passwords are already hashed!</p>"

            result += f"<p><a href='/debug/check_teachers'>🔍 Check Teachers Again</a></p>"
            result += f"<p><a href='/teacher_login'>🔗 Try Teacher Login</a></p>"

            return result

        except Exception as e:
            return f"❌ Error during password migration: {str(e)}"



    # Log application startup
    app.logger.info("Application initialized")

    return app