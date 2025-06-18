"""
Security Manager - Central security management for the application
Integrates all security modules and provides centralized security controls.
"""

import logging
from flask import Flask
from .sql_injection_protection import SQLInjectionProtection, sql_injection_protection
from .xss_protection import XSSProtection, xss_protection
from .access_control import AccessControlProtection, require_role, require_resource_permission
from .csrf_protection import CSRFProtection, init_csrf_protection
from .security_config import SecurityConfiguration, init_security_config
from .idor_protection import IDORProtection, protect_object_access
from .rce_protection import RCEProtection, rce_protection
from .file_upload_security import FileUploadSecurity, secure_file_upload
from .file_inclusion_protection import FileInclusionProtection, file_inclusion_protection
from .ssrf_protection import SSRFProtection, ssrf_protection

class SecurityManager:
    """Central security manager for the application."""
    
    def __init__(self, app=None):
        """
        Initialize security manager.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        self.security_enabled = True
        self.security_modules = {}
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize security for Flask application.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Configure logging
        self._configure_security_logging()
        
        # Initialize all security modules
        self._init_security_modules(app)
        
        # Register security middleware
        self._register_security_middleware(app)
        
        # Add security context processors
        self._add_security_context_processors(app)
        
        logging.info("🔒 Security Manager initialized with comprehensive protection")
    
    def _configure_security_logging(self):
        """Configure security-specific logging."""
        # Create security logger
        security_logger = logging.getLogger('security')
        security_logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Create formatter
        formatter = logging.Formatter(
            '🔒 SECURITY - %(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        security_logger.addHandler(console_handler)
    
    def _init_security_modules(self, app: Flask):
        """
        Initialize all security modules.
        
        Args:
            app: Flask application instance
        """
        # Initialize security configuration
        init_security_config(app)
        self.security_modules['config'] = SecurityConfiguration
        
        # Initialize CSRF protection
        init_csrf_protection(app)
        self.security_modules['csrf'] = CSRFProtection
        
        # Initialize other security modules
        self.security_modules['sql_injection'] = SQLInjectionProtection
        self.security_modules['xss'] = XSSProtection
        self.security_modules['access_control'] = AccessControlProtection
        self.security_modules['idor'] = IDORProtection
        self.security_modules['rce'] = RCEProtection
        self.security_modules['file_upload'] = FileUploadSecurity
        self.security_modules['file_inclusion'] = FileInclusionProtection
        self.security_modules['ssrf'] = SSRFProtection
        
        logging.info("✅ All security modules initialized")
    
    def _register_security_middleware(self, app: Flask):
        """
        Register security middleware.
        
        Args:
            app: Flask application instance
        """
        @app.before_request
        def security_middleware():
            """Global security middleware."""
            if not self.security_enabled:
                return
            
            # Log security events
            security_logger = logging.getLogger('security')
            
            # Update session activity
            AccessControlProtection.validate_session()
            
            # Additional security checks can be added here
            
        @app.after_request
        def security_headers(response):
            """Add security headers to all responses."""
            if not self.security_enabled:
                return response
            
            # Add security headers
            headers = app.config.get('SECURITY_HEADERS', {})
            for header, value in headers.items():
                response.headers[header] = value
            
            return response
    
    def _add_security_context_processors(self, app: Flask):
        """
        Add security-related context processors.
        
        Args:
            app: Flask application instance
        """
        @app.context_processor
        def security_context():
            """Add security context to templates."""
            return {
                'csrf_token': CSRFProtection.get_session_token(),
                'security_enabled': self.security_enabled
            }
    
    def get_security_status(self):
        """
        Get comprehensive security status.
        
        Returns:
            dict: Security status information
        """
        return {
            'enabled': self.security_enabled,
            'modules': list(self.security_modules.keys()),
            'csrf_protection': 'csrf' in self.security_modules,
            'sql_injection_protection': 'sql_injection' in self.security_modules,
            'xss_protection': 'xss' in self.security_modules,
            'access_control': 'access_control' in self.security_modules,
            'idor_protection': 'idor' in self.security_modules,
            'rce_protection': 'rce' in self.security_modules,
            'file_upload_security': 'file_upload' in self.security_modules,
            'file_inclusion_protection': 'file_inclusion' in self.security_modules,
            'ssrf_protection': 'ssrf' in self.security_modules,
            'security_config': 'config' in self.security_modules
        }
    
    def enable_security(self):
        """Enable security features."""
        self.security_enabled = True
        logging.info("🔒 Security features enabled")
    
    def disable_security(self):
        """Disable security features (for testing only)."""
        self.security_enabled = False
        logging.warning("⚠️ Security features disabled - USE ONLY FOR TESTING!")
    
    def validate_input(self, input_value, field_name="input"):
        """
        Comprehensive input validation.
        
        Args:
            input_value: Input to validate
            field_name: Field name for logging
            
        Returns:
            bool: True if input is safe
        """
        if not self.security_enabled:
            return True
        
        # SQL injection check
        if not SQLInjectionProtection.validate_input(input_value, field_name):
            return False
        
        # XSS check
        if not XSSProtection.validate_input(input_value, field_name):
            return False
        
        # RCE check
        if not RCEProtection.validate_input_for_rce(input_value, field_name):
            return False
        
        # File inclusion check
        if FileInclusionProtection.detect_lfi_attempt(input_value) or \
           FileInclusionProtection.detect_rfi_attempt(input_value):
            logging.warning(f"File inclusion attempt in {field_name}: {input_value}")
            return False
        
        return True
    
    def sanitize_input(self, input_value, allow_html=False):
        """
        Comprehensive input sanitization.
        
        Args:
            input_value: Input to sanitize
            allow_html: Whether to allow safe HTML tags
            
        Returns:
            str: Sanitized input
        """
        if not self.security_enabled:
            return input_value
        
        # SQL injection sanitization
        sanitized = SQLInjectionProtection.sanitize_input(input_value)
        
        # XSS sanitization
        sanitized = XSSProtection.sanitize_html(sanitized, allow_html)
        
        return sanitized
    
    def check_access(self, user_id, user_role, resource, action='read', object_id=None):
        """
        Comprehensive access control check.
        
        Args:
            user_id: User ID
            user_role: User role
            resource: Resource being accessed
            action: Action being performed
            object_id: Object ID (for IDOR protection)
            
        Returns:
            bool: True if access granted
        """
        if not self.security_enabled:
            return True
        
        # Role-based access control
        if not AccessControlProtection.check_resource_permission(user_role, resource, action):
            return False
        
        # IDOR protection
        if object_id:
            if not IDORProtection.check_object_access(user_id, user_role, resource, object_id, action):
                return False
        
        return True

# Global security manager instance
security_manager = SecurityManager()

# Convenience decorators that use the global security manager
def comprehensive_security(strict_csp=True):
    """
    Comprehensive security decorator that applies all protections.
    
    Args:
        strict_csp: Whether to use strict Content Security Policy
    """
    def decorator(f):
        # Apply all security decorators
        f = sql_injection_protection(f)
        f = xss_protection(strict_csp)(f)
        f = rce_protection(f)
        f = file_inclusion_protection(f)
        f = ssrf_protection(f)
        return f
    return decorator

def secure_admin_route(f):
    """Security decorator for admin routes."""
    f = comprehensive_security()(f)
    f = require_role('admin')(f)
    return f

def secure_headteacher_route(f):
    """Security decorator for headteacher routes."""
    f = comprehensive_security()(f)
    f = require_role('headteacher')(f)
    return f

def secure_teacher_route(f):
    """Security decorator for teacher routes."""
    f = comprehensive_security()(f)
    f = require_role('teacher')(f)
    return f

def secure_file_upload_route(allowed_extensions=None, max_size=None):
    """Security decorator for file upload routes."""
    def decorator(f):
        f = comprehensive_security()(f)
        f = secure_file_upload(allowed_extensions, max_size)(f)
        return f
    return decorator

def secure_object_access_route(object_type, action='read', id_param='id'):
    """Security decorator for object access routes."""
    def decorator(f):
        f = comprehensive_security()(f)
        f = protect_object_access(object_type, action, id_param)(f)
        return f
    return decorator

# Export all security components
__all__ = [
    'SecurityManager',
    'security_manager',
    'comprehensive_security',
    'secure_admin_route',
    'secure_headteacher_route', 
    'secure_teacher_route',
    'secure_file_upload_route',
    'secure_object_access_route',
    'SQLInjectionProtection',
    'XSSProtection',
    'AccessControlProtection',
    'CSRFProtection',
    'SecurityConfiguration',
    'IDORProtection',
    'RCEProtection',
    'FileUploadSecurity',
    'FileInclusionProtection',
    'SSRFProtection'
]
