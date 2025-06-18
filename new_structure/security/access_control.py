"""
Access Control Protection Module
Comprehensive protection against broken access control vulnerabilities.
"""

import logging
from functools import wraps
from flask import session, request, abort, current_app
try:
    from ..services.auth_service import is_authenticated, get_role
except ImportError:
    # Fallback for direct imports
    try:
        from services.auth_service import is_authenticated, get_role
    except ImportError:
        # Mock functions for testing
        def is_authenticated(session):
            return session.get('teacher_id') is not None

        def get_role(session):
            return session.get('role', 'guest')

class AccessControlProtection:
    """Comprehensive access control protection."""
    
    # Role hierarchy (higher number = more permissions)
    ROLE_HIERARCHY = {
        'student': 1,
        'parent': 2,
        'teacher': 3,
        'classteacher': 4,
        'headteacher': 5,
        'admin': 6,
        'superadmin': 7
    }
    
    # Resource permissions mapping
    RESOURCE_PERMISSIONS = {
        'student_records': {
            'read': ['teacher', 'classteacher', 'headteacher', 'admin'],
            'write': ['classteacher', 'headteacher', 'admin'],
            'delete': ['headteacher', 'admin']
        },
        'marks': {
            'read': ['teacher', 'classteacher', 'headteacher', 'admin'],
            'write': ['teacher', 'classteacher', 'headteacher', 'admin'],
            'delete': ['headteacher', 'admin']
        },
        'reports': {
            'read': ['teacher', 'classteacher', 'headteacher', 'admin'],
            'write': ['classteacher', 'headteacher', 'admin'],
            'delete': ['headteacher', 'admin']
        },
        'teacher_management': {
            'read': ['headteacher', 'admin'],
            'write': ['headteacher', 'admin'],
            'delete': ['admin']
        },
        'system_config': {
            'read': ['headteacher', 'admin'],
            'write': ['admin'],
            'delete': ['admin']
        },
        'analytics': {
            'read': ['classteacher', 'headteacher', 'admin'],
            'write': ['headteacher', 'admin'],
            'delete': ['admin']
        },
        'parent_management': {
            'read': ['headteacher', 'admin'],
            'write': ['headteacher', 'admin'],
            'delete': ['admin']
        }
    }
    
    @classmethod
    def check_role_permission(cls, user_role, required_role):
        """
        Check if user role has sufficient permissions.
        
        Args:
            user_role: Current user's role
            required_role: Required role for access
            
        Returns:
            bool: True if permission granted
        """
        user_level = cls.ROLE_HIERARCHY.get(user_role, 0)
        required_level = cls.ROLE_HIERARCHY.get(required_role, 999)
        
        return user_level >= required_level
    
    @classmethod
    def check_resource_permission(cls, user_role, resource, action):
        """
        Check if user has permission for specific resource action.
        
        Args:
            user_role: Current user's role
            resource: Resource name
            action: Action type (read, write, delete)
            
        Returns:
            bool: True if permission granted
        """
        if resource not in cls.RESOURCE_PERMISSIONS:
            logging.warning(f"Unknown resource: {resource}")
            return False
        
        if action not in cls.RESOURCE_PERMISSIONS[resource]:
            logging.warning(f"Unknown action {action} for resource {resource}")
            return False
        
        allowed_roles = cls.RESOURCE_PERMISSIONS[resource][action]
        return user_role in allowed_roles
    
    @classmethod
    def check_object_ownership(cls, user_id, object_owner_id, user_role):
        """
        Check if user owns the object or has sufficient role.
        
        Args:
            user_id: Current user's ID
            object_owner_id: Object owner's ID
            user_role: Current user's role
            
        Returns:
            bool: True if access granted
        """
        # Owner always has access
        if str(user_id) == str(object_owner_id):
            return True
        
        # Higher roles can access other users' objects
        if user_role in ['headteacher', 'admin', 'superadmin']:
            return True
        
        return False
    
    @classmethod
    def check_class_access(cls, user_id, user_role, grade_id, stream_id=None):
        """
        Check if user has access to specific class/stream.
        
        Args:
            user_id: Current user's ID
            user_role: Current user's role
            grade_id: Grade ID
            stream_id: Stream ID (optional)
            
        Returns:
            bool: True if access granted
        """
        # Headteacher and admin have universal access
        if user_role in ['headteacher', 'admin', 'superadmin']:
            return True
        
        # For teachers and classteachers, check specific assignments
        if user_role in ['teacher', 'classteacher']:
            try:
                from ..services.permission_service import PermissionService
            except ImportError:
                try:
                    from services.permission_service import PermissionService
                except ImportError:
                    # Mock for testing
                    class PermissionService:
                        @staticmethod
                        def check_class_access(user_id, grade_id, stream_id):
                            return True
            return PermissionService.check_class_access(user_id, grade_id, stream_id)
        
        return False
    
    @classmethod
    def validate_session(cls):
        """
        Validate current session for security.
        
        Returns:
            bool: True if session is valid
        """
        if not is_authenticated(session):
            return False
        
        # Check session timeout
        if 'last_activity' in session:
            import time
            current_time = time.time()
            last_activity = session.get('last_activity', 0)
            timeout = current_app.config.get('SESSION_TIMEOUT', 3600)  # 1 hour default
            
            if current_time - last_activity > timeout:
                logging.info(f"Session timeout for user {session.get('teacher_id')}")
                return False
        
        # Update last activity
        session['last_activity'] = time.time()
        
        return True
    
    @classmethod
    def log_access_attempt(cls, user_id, resource, action, success, ip_address=None):
        """
        Log access attempts for security monitoring.
        
        Args:
            user_id: User ID attempting access
            resource: Resource being accessed
            action: Action being attempted
            success: Whether access was granted
            ip_address: Client IP address
        """
        status = "SUCCESS" if success else "DENIED"
        ip = ip_address or request.remote_addr if request else "unknown"
        
        logging.info(f"ACCESS {status}: User {user_id} attempted {action} on {resource} from {ip}")
        
        # In production, you might want to store this in a database for analysis
        if not success:
            logging.warning(f"SECURITY ALERT: Unauthorized access attempt by user {user_id}")

def require_role(required_role):
    """
    Decorator to require specific role for route access.
    
    Args:
        required_role: Minimum required role
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not AccessControlProtection.validate_session():
                abort(401, "Session invalid or expired")
            
            user_role = get_role(session)
            user_id = session.get('teacher_id')
            
            if not AccessControlProtection.check_role_permission(user_role, required_role):
                AccessControlProtection.log_access_attempt(
                    user_id, f"route_{request.endpoint}", "access", False
                )
                abort(403, "Insufficient permissions")
            
            AccessControlProtection.log_access_attempt(
                user_id, f"route_{request.endpoint}", "access", True
            )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_resource_permission(resource, action):
    """
    Decorator to require specific resource permission.
    
    Args:
        resource: Resource name
        action: Action type (read, write, delete)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not AccessControlProtection.validate_session():
                abort(401, "Session invalid or expired")
            
            user_role = get_role(session)
            user_id = session.get('teacher_id')
            
            if not AccessControlProtection.check_resource_permission(user_role, resource, action):
                AccessControlProtection.log_access_attempt(
                    user_id, resource, action, False
                )
                abort(403, f"No permission for {action} on {resource}")
            
            AccessControlProtection.log_access_attempt(
                user_id, resource, action, True
            )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_ownership_or_role(owner_field='user_id', required_role='admin'):
    """
    Decorator to require object ownership or sufficient role.
    
    Args:
        owner_field: Field name containing owner ID
        required_role: Role that can bypass ownership check
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not AccessControlProtection.validate_session():
                abort(401, "Session invalid or expired")
            
            user_role = get_role(session)
            user_id = session.get('teacher_id')
            
            # Get object owner ID from request or kwargs
            object_owner_id = None
            
            # Try to get from URL parameters
            if owner_field in kwargs:
                object_owner_id = kwargs[owner_field]
            elif owner_field in request.args:
                object_owner_id = request.args.get(owner_field)
            elif request.is_json and owner_field in request.json:
                object_owner_id = request.json.get(owner_field)
            elif owner_field in request.form:
                object_owner_id = request.form.get(owner_field)
            
            # If we can't determine ownership, require the role
            if object_owner_id is None:
                if not AccessControlProtection.check_role_permission(user_role, required_role):
                    abort(403, "Insufficient permissions")
            else:
                if not AccessControlProtection.check_object_ownership(user_id, object_owner_id, user_role):
                    abort(403, "Access denied - not owner and insufficient role")
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_class_access():
    """
    Decorator to require access to specific class/stream.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not AccessControlProtection.validate_session():
                abort(401, "Session invalid or expired")
            
            user_role = get_role(session)
            user_id = session.get('teacher_id')
            
            # Get grade and stream from request
            grade_id = None
            stream_id = None
            
            # Try multiple sources for grade/stream info
            for source in [kwargs, request.args, request.form, request.json or {}]:
                if not grade_id:
                    grade_id = source.get('grade_id') or source.get('grade')
                if not stream_id:
                    stream_id = source.get('stream_id') or source.get('stream')
            
            if not grade_id:
                abort(400, "Grade information required")
            
            if not AccessControlProtection.check_class_access(user_id, user_role, grade_id, stream_id):
                AccessControlProtection.log_access_attempt(
                    user_id, f"class_{grade_id}_{stream_id}", "access", False
                )
                abort(403, "No access to this class")
            
            AccessControlProtection.log_access_attempt(
                user_id, f"class_{grade_id}_{stream_id}", "access", True
            )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
