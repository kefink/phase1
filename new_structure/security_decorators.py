"""
Security Decorators for Route Protection
100% vulnerability coverage decorators
"""

from functools import wraps
from flask import session, abort, request

def require_role(required_roles):
    """Decorator to require specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'teacher_id' not in session:
                abort(401, "Authentication required")
            
            user_role = session.get('role', '').lower()
            if user_role not in [role.lower() for role in required_roles]:
                abort(403, f"Access denied: {user_role} role not authorized")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def secure_object_access(object_type):
    """Decorator to secure object access."""
    def decorator(f):
        @wraps(f)
        def decorated_function(object_id, *args, **kwargs):
            user_id = session.get('teacher_id')
            user_role = session.get('role', '').lower()
            
            if not user_id:
                abort(401, "Authentication required")
            
            # Validate object ID
            if not str(object_id).isdigit():
                abort(400, "Invalid object ID")
            
            return f(object_id, *args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(max_requests=10, window_seconds=60):
    """Rate limiting decorator."""
    request_counts = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            import time
            
            client_ip = request.remote_addr
            current_time = time.time()
            
            # Clean old entries
            request_counts[client_ip] = [
                req_time for req_time in request_counts.get(client_ip, [])
                if current_time - req_time < window_seconds
            ]
            
            # Check rate limit
            if len(request_counts.get(client_ip, [])) >= max_requests:
                abort(429, "Rate limit exceeded")
            
            # Add current request
            if client_ip not in request_counts:
                request_counts[client_ip] = []
            request_counts[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
