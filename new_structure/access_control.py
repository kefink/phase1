
from functools import wraps
from flask import session, abort, request

def require_role(required_roles):
    """Decorator to enforce role-based access control."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in
            if 'teacher_id' not in session:
                abort(401, "Authentication required")
            
            # Check user role
            user_role = session.get('role')
            if user_role not in required_roles:
                abort(403, f"Access denied: {user_role} role not authorized")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_object_access(object_type, object_id, user_role):
    """Validate if user can access specific object."""
    
    # Validate object ID format
    if not str(object_id).isdigit():
        return False
    
    # Role-based access rules
    access_rules = {
        'headteacher': ['student', 'teacher', 'report', 'mark'],
        'classteacher': ['student', 'report', 'mark'],
        'teacher': ['mark']
    }
    
    allowed_objects = access_rules.get(user_role, [])
    return object_type in allowed_objects

def secure_object_access(object_type):
    """Decorator to secure object access endpoints."""
    def decorator(f):
        @wraps(f)
        def decorated_function(object_id, *args, **kwargs):
            user_role = session.get('role')
            
            if not user_role:
                abort(401, "Authentication required")
            
            if not validate_object_access(object_type, object_id, user_role):
                abort(403, f"Access denied: Cannot access {object_type} {object_id}")
            
            return f(object_id, *args, **kwargs)
        return decorated_function
    return decorator
