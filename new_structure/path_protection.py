
import os
import re
from flask import request, abort

def validate_file_path(file_path):
    """Validate file paths to prevent path traversal attacks."""
    if not file_path:
        return True
    
    # Normalize the path
    normalized_path = os.path.normpath(file_path)
    
    # Check for path traversal attempts
    if '..' in normalized_path or normalized_path.startswith('/'):
        return False
    
    # Check for null bytes
    if '\x00' in file_path:
        return False
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'\.\./',        # ../
        r'\.\.\\',     # ..\
        r'/etc/',
        r'/proc/',
        r'/sys/',
        r'C:\\',         # Windows drive root
        r'\\\\',       # multiple backslashes
        r'file://',
        r'ftp://',
        r'http://',
        r'https://'
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, file_path, re.IGNORECASE):
            return False
    
    return True

def init_path_protection(app):
    """Register a before_request hook to block path traversal attempts."""
    @app.before_request
    def check_path_traversal():
        # Check URL path
        if not validate_file_path(request.path):
            abort(403, "Access denied: Invalid path")
        
        # Check query parameters
        for _, value in request.args.items():
            if not validate_file_path(value):
                abort(403, "Access denied: Invalid parameter")
        
        # Check form data
        if request.form:
            for _, value in request.form.items():
                if not validate_file_path(value):
                    abort(403, "Access denied: Invalid form data")
def init_path_protection(app):
    """Register a before_request hook to block path traversal attempts."""
    @app.before_request
    def check_path_traversal():
        # Check URL path
        if not validate_file_path(request.path):
            abort(403, "Access denied: Invalid path")
        
        # Check query parameters
        for _, value in request.args.items():
            if not validate_file_path(value):
                abort(403, "Access denied: Invalid parameter")
        
        # Check form data
        if request.form:
            for _, value in request.form.items():
                if not validate_file_path(value):
                    abort(403, "Access denied: Invalid form data")
