"""
SQL Injection Protection Module for Hillview School Management System
Provides comprehensive protection against SQL injection attacks.
"""

import re
import logging
from functools import wraps
from flask import request, abort

logger = logging.getLogger(__name__)

class SQLInjectionProtection:
    """SQL injection protection utilities."""

    # Common SQL injection patterns (simplified for performance)
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bDROP\s+TABLE\b)",
        r"(\bUNION\s+SELECT\b)",
        r"(\bSCRIPT\b.*\bSRC\b)",
        r"(\bjavascript\s*:)",
        r"(\bon\w+\s*=)",
        r"(\beval\s*\()"
    ]

    @staticmethod
    def validate_input(value, field_name="input"):
        """
        Validate input for SQL injection patterns.

        Args:
            value: Input value to validate
            field_name: Name of the field being validated

        Returns:
            bool: True if input is safe, False if potentially malicious
        """
        if not value:
            return True

        # Convert to string for pattern matching
        str_value = str(value).upper()

        # Check against SQL injection patterns
        for pattern in SQLInjectionProtection.SQL_INJECTION_PATTERNS:
            if re.search(pattern, str_value, re.IGNORECASE):
                logger.warning(f"SQL injection attempt detected in {field_name}: {pattern}")
                return False

        # Additional checks for common injection techniques
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', '\\', '\x00', '\n', '\r', '\x1a']
        for char in dangerous_chars:
            if char in str(value):
                logger.warning(f"Dangerous character detected in {field_name}: {char}")
                return False

        return True
def sql_injection_protection(f):
    """
    Decorator to protect routes from SQL injection attacks.

    Args:
        f: Function to protect

    Returns:
        Decorated function with SQL injection protection
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check form data
        if request.method in ['POST', 'PUT', 'PATCH']:
            for key, value in request.form.items():
                if not SQLInjectionProtection.validate_input(value, key):
                    logger.warning(f"SQL injection attempt blocked in form field {key}")
                    abort(400, "Invalid input detected")

        # Check query parameters
        for key, value in request.args.items():
            if not SQLInjectionProtection.validate_input(value, key):
                logger.warning(f"SQL injection attempt blocked in query parameter {key}")
                abort(400, "Invalid input detected")

        # Check JSON data
        if request.is_json and request.json:
            def check_json_recursive(data, path=""):
                if isinstance(data, dict):
                    for key, value in data.items():
                        check_json_recursive(value, f"{path}.{key}")
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        check_json_recursive(item, f"{path}[{i}]")
                elif isinstance(data, str):
                    if not SQLInjectionProtection.validate_input(data, path):
                        logger.warning(f"SQL injection attempt blocked in JSON field {path}")
                        abort(400, "Invalid input detected")

            check_json_recursive(request.json)

        return f(*args, **kwargs)

    return decorated_function
