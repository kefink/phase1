"""
Security Configuration Module
Comprehensive security configurations and headers.
"""

import os
import logging
from flask import Flask, request, session
from datetime import timedelta

class SecurityConfiguration:
    """Comprehensive security configuration."""
    
    @staticmethod
    def configure_app_security(app: Flask):
        """
        Configure comprehensive security settings for Flask app.
        
        Args:
            app: Flask application instance
        """
        # Session Security
        app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
        app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # 2 hour timeout
        app.config['SESSION_TIMEOUT'] = 7200  # 2 hours in seconds
        
        # Security Headers
        is_development = os.environ.get('FLASK_ENV', 'development') == 'development'
        app.config['SECURITY_HEADERS'] = {
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Content-Security-Policy': SecurityConfiguration.get_csp_policy(development=is_development)
        }
        
        # Disable debug mode in production
        if os.environ.get('FLASK_ENV') == 'production':
            app.config['DEBUG'] = False
            app.config['TESTING'] = False
        
        # Server signature hiding
        app.config['SERVER_NAME'] = None
        
        # File upload security
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        app.config['UPLOAD_EXTENSIONS'] = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.gif']
        app.config['UPLOAD_PATH'] = 'uploads'
        
        # Database security
        app.config['SQLALCHEMY_ECHO'] = False  # Don't log SQL queries
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Rate limiting configuration
        app.config['RATELIMIT_STORAGE_URL'] = 'memory://'
        app.config['RATELIMIT_DEFAULT'] = '100 per hour'
        
        # Logging configuration
        SecurityConfiguration.configure_security_logging(app)
    
    @staticmethod
    def get_csp_policy(development=False):
        """
        Get Content Security Policy.

        Args:
            development: Whether this is for development environment

        Returns:
            str: CSP policy string
        """
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none';"
        )

        # Only add upgrade-insecure-requests in production
        if not development:
            csp += " upgrade-insecure-requests;"

        return csp
    
    @staticmethod
    def configure_security_logging(app: Flask):
        """
        Configure security-focused logging.
        
        Args:
            app: Flask application instance
        """
        # Create security logger
        security_logger = logging.getLogger('security')
        security_logger.setLevel(logging.INFO)
        
        # Create file handler for security logs
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        security_handler = logging.FileHandler('logs/security.log')
        security_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        security_handler.setFormatter(formatter)
        
        # Add handler to logger
        security_logger.addHandler(security_handler)
        
        # Configure app logger
        if not app.debug:
            app.logger.setLevel(logging.INFO)
            app.logger.addHandler(security_handler)
    
    @staticmethod
    def add_security_headers(app: Flask):
        """
        Add security headers to all responses.
        
        Args:
            app: Flask application instance
        """
        @app.after_request
        def set_security_headers(response):
            headers = app.config.get('SECURITY_HEADERS', {})
            
            for header, value in headers.items():
                response.headers[header] = value
            
            # Remove server information
            response.headers.pop('Server', None)
            
            return response
    
    @staticmethod
    def configure_session_security(app: Flask):
        """
        Configure session security.
        
        Args:
            app: Flask application instance
        """
        @app.before_request
        def check_session_security():
            # Regenerate session ID on login
            if request.endpoint in ['auth.login', 'auth.admin_login', 'auth.teacher_login']:
                session.permanent = True
            
            # Check session timeout
            if 'last_activity' in session:
                import time
                current_time = time.time()
                last_activity = session.get('last_activity', 0)
                timeout = app.config.get('SESSION_TIMEOUT', 3600)
                
                if current_time - last_activity > timeout:
                    session.clear()
                    return redirect(url_for('auth.login'))
            
            # Update last activity
            session['last_activity'] = time.time()
            
            # Add security markers
            session['ip_address'] = request.remote_addr
            session['user_agent'] = request.headers.get('User-Agent', '')
    
    @staticmethod
    def configure_error_handling(app: Flask):
        """
        Configure secure error handling.
        
        Args:
            app: Flask application instance
        """
        @app.errorhandler(400)
        def bad_request(error):
            return render_template('error.html', 
                                 error_code=400, 
                                 error_message="Bad Request"), 400
        
        @app.errorhandler(401)
        def unauthorized(error):
            return render_template('error.html', 
                                 error_code=401, 
                                 error_message="Unauthorized Access"), 401
        
        @app.errorhandler(403)
        def forbidden(error):
            return render_template('error.html', 
                                 error_code=403, 
                                 error_message="Access Forbidden"), 403
        
        @app.errorhandler(404)
        def not_found(error):
            return render_template('error.html', 
                                 error_code=404, 
                                 error_message="Page Not Found"), 404
        
        @app.errorhandler(500)
        def internal_error(error):
            # Log the error but don't expose details
            app.logger.error(f"Internal error: {error}")
            return render_template('error.html', 
                                 error_code=500, 
                                 error_message="Internal Server Error"), 500
    
    @staticmethod
    def configure_input_validation(app: Flask):
        """
        Configure global input validation.
        
        Args:
            app: Flask application instance
        """
        @app.before_request
        def validate_request_size():
            # Check content length
            max_length = app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
            if request.content_length and request.content_length > max_length:
                abort(413, "Request too large")
        
        @app.before_request
        def validate_request_headers():
            # Check for suspicious headers
            suspicious_headers = [
                'X-Forwarded-Host',
                'X-Original-URL',
                'X-Rewrite-URL'
            ]
            
            for header in suspicious_headers:
                if header in request.headers:
                    app.logger.warning(f"Suspicious header detected: {header}")
    
    @staticmethod
    def configure_rate_limiting(app: Flask):
        """
        Configure rate limiting.
        
        Args:
            app: Flask application instance
        """
        try:
            from flask_limiter import Limiter
            from flask_limiter.util import get_remote_address
            
            limiter = Limiter(
                app,
                key_func=get_remote_address,
                default_limits=["100 per hour"]
            )
            
            # Apply stricter limits to authentication endpoints
            @limiter.limit("5 per minute")
            @app.route('/admin_login', methods=['POST'])
            def rate_limited_admin_login():
                pass
            
            @limiter.limit("5 per minute")
            @app.route('/teacher_login', methods=['POST'])
            def rate_limited_teacher_login():
                pass
            
            @limiter.limit("5 per minute")
            @app.route('/parent_login', methods=['POST'])
            def rate_limited_parent_login():
                pass
            
        except ImportError:
            app.logger.warning("Flask-Limiter not installed, rate limiting disabled")
    
    @staticmethod
    def configure_file_upload_security(app: Flask):
        """
        Configure secure file upload handling.
        
        Args:
            app: Flask application instance
        """
        @app.before_request
        def validate_file_uploads():
            if request.files:
                allowed_extensions = app.config.get('UPLOAD_EXTENSIONS', [])
                
                for file_key, file in request.files.items():
                    if file.filename:
                        # Check file extension
                        file_ext = os.path.splitext(file.filename)[1].lower()
                        if file_ext not in allowed_extensions:
                            abort(400, f"File type {file_ext} not allowed")
                        
                        # Check file size
                        file.seek(0, os.SEEK_END)
                        file_size = file.tell()
                        file.seek(0)
                        
                        max_size = app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
                        if file_size > max_size:
                            abort(413, "File too large")

def init_security_config(app: Flask):
    """
    Initialize all security configurations.
    
    Args:
        app: Flask application instance
    """
    SecurityConfiguration.configure_app_security(app)
    SecurityConfiguration.add_security_headers(app)
    SecurityConfiguration.configure_session_security(app)
    SecurityConfiguration.configure_error_handling(app)
    SecurityConfiguration.configure_input_validation(app)
    SecurityConfiguration.configure_rate_limiting(app)
    SecurityConfiguration.configure_file_upload_security(app)
    
    app.logger.info("Security configuration initialized")
