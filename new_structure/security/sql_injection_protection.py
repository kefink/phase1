"""
SQL Injection Protection Module
Comprehensive protection against SQL injection attacks.
"""

import re
import logging
from functools import wraps
from flask import request, abort, current_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

class SQLInjectionProtection:
    """Comprehensive SQL injection protection."""
    
    # SQL injection patterns to detect
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(UNION\s+SELECT)",
        r"(INFORMATION_SCHEMA|SYSOBJECTS|SYSCOLUMNS)",
        r"(\bEXEC\s*\(|\bEXECUTE\s*\()",
        r"(\bSP_|XP_)",
        r"(WAITFOR\s+DELAY)",
        r"(BENCHMARK\s*\(|SLEEP\s*\()",
        r"(\bLOAD_FILE\s*\(|\bINTO\s+OUTFILE)",
        r"(@@VERSION|@@SERVERNAME|@@IDENTITY)",
        r"(\bCAST\s*\(.*\bAS\b|\bCONVERT\s*\()",
        r"(\bCHAR\s*\(|\bASCII\s*\(|\bORD\s*\()",
        r"(0x[0-9A-Fa-f]+)",
        r"(\bHEX\s*\(|\bUNHEX\s*\()",
        r"(\bCONCAT\s*\(|\bCONCAT_WS\s*\()",
        r"(\bSUBSTRING\s*\(|\bSUBSTR\s*\(|\bMID\s*\()",
        r"(\bIF\s*\(|\bIFNULL\s*\(|\bNULLIF\s*\()",
        r"(\bCOUNT\s*\(|\bSUM\s*\(|\bAVG\s*\(|\bMIN\s*\(|\bMAX\s*\()",
        r"(\bGROUP\s+BY|\bORDER\s+BY|\bHAVING\b)",
        r"(\bLIMIT\s+\d+\s*,|\bOFFSET\s+\d+)",
        r"(\bEXISTS\s*\(|\bNOT\s+EXISTS\s*\()",
        r"(\bIN\s*\(.*\)|\bNOT\s+IN\s*\(.*\))",
        r"(\bLIKE\s+['\"].*[%_].*['\"])",
        r"(\bREGEXP\s+|\bRLIKE\s+)",
        r"(\bIS\s+NULL|\bIS\s+NOT\s+NULL)",
        r"(\bBETWEEN\s+.*\bAND\b)",
        r"(\bCASE\s+WHEN|\bWHEN\s+.*\bTHEN|\bELSE\b|\bEND\b)"
    ]
    
    @classmethod
    def validate_input(cls, input_value, field_name="input"):
        """
        Validate input for SQL injection patterns.
        
        Args:
            input_value: The input to validate
            field_name: Name of the field for logging
            
        Returns:
            bool: True if safe, False if potentially malicious
        """
        if not input_value:
            return True
            
        input_str = str(input_value).upper()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                logging.warning(f"SQL injection attempt detected in {field_name}: {input_value}")
                return False
                
        return True
    
    @classmethod
    def sanitize_input(cls, input_value):
        """
        Sanitize input by removing potentially dangerous characters.
        
        Args:
            input_value: The input to sanitize
            
        Returns:
            str: Sanitized input
        """
        if not input_value:
            return input_value
            
        # Remove SQL comment markers
        sanitized = re.sub(r'(--|#|/\*|\*/)', '', str(input_value))
        
        # Remove multiple spaces
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Remove leading/trailing whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    @classmethod
    def validate_form_data(cls, form_data):
        """
        Validate all form data for SQL injection.
        
        Args:
            form_data: Flask request.form or similar
            
        Returns:
            bool: True if all inputs are safe
        """
        for field_name, value in form_data.items():
            if not cls.validate_input(value, field_name):
                return False
        return True
    
    @classmethod
    def validate_query_params(cls, args):
        """
        Validate URL query parameters for SQL injection.
        
        Args:
            args: Flask request.args or similar
            
        Returns:
            bool: True if all parameters are safe
        """
        for param_name, value in args.items():
            if not cls.validate_input(value, f"query_param_{param_name}"):
                return False
        return True
    
    @classmethod
    def safe_execute_query(cls, db_session, query, params=None):
        """
        Safely execute a database query with parameterized inputs.
        
        Args:
            db_session: Database session
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result or None if error
        """
        try:
            if params:
                # Validate all parameters
                for key, value in params.items():
                    if not cls.validate_input(value, f"query_param_{key}"):
                        logging.error(f"SQL injection attempt in query parameter: {key}={value}")
                        return None
                
                result = db_session.execute(text(query), params)
            else:
                result = db_session.execute(text(query))
                
            return result
            
        except SQLAlchemyError as e:
            logging.error(f"Database error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in safe_execute_query: {e}")
            return None

def sql_injection_protection(f):
    """
    Decorator to protect routes from SQL injection attacks.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Validate form data
        if request.form and not SQLInjectionProtection.validate_form_data(request.form):
            logging.warning(f"SQL injection attempt blocked on route: {request.endpoint}")
            abort(400, "Invalid input detected")
        
        # Validate query parameters
        if request.args and not SQLInjectionProtection.validate_query_params(request.args):
            logging.warning(f"SQL injection attempt blocked on route: {request.endpoint}")
            abort(400, "Invalid query parameters detected")
        
        # Validate JSON data
        if request.is_json and request.json:
            for key, value in request.json.items():
                if not SQLInjectionProtection.validate_input(value, f"json_{key}"):
                    logging.warning(f"SQL injection attempt blocked on route: {request.endpoint}")
                    abort(400, "Invalid JSON data detected")
        
        return f(*args, **kwargs)
    
    return decorated_function

class SecureQueryBuilder:
    """
    Helper class for building secure database queries.
    """
    
    @staticmethod
    def build_where_clause(conditions):
        """
        Build a secure WHERE clause with parameterized conditions.
        
        Args:
            conditions: Dict of field->value conditions
            
        Returns:
            tuple: (where_clause, params)
        """
        if not conditions:
            return "", {}
        
        where_parts = []
        params = {}
        
        for field, value in conditions.items():
            # Validate field name (should only contain alphanumeric and underscore)
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field):
                raise ValueError(f"Invalid field name: {field}")
            
            # Validate value
            if not SQLInjectionProtection.validate_input(value, field):
                raise ValueError(f"Invalid value for field {field}")
            
            param_name = f"param_{field}"
            where_parts.append(f"{field} = :{param_name}")
            params[param_name] = value
        
        where_clause = " AND ".join(where_parts)
        return where_clause, params
    
    @staticmethod
    def build_order_clause(order_by, allowed_fields):
        """
        Build a secure ORDER BY clause.
        
        Args:
            order_by: Field to order by
            allowed_fields: List of allowed field names
            
        Returns:
            str: Safe ORDER BY clause
        """
        if not order_by:
            return ""
        
        # Extract field and direction
        parts = order_by.split()
        field = parts[0]
        direction = parts[1] if len(parts) > 1 else "ASC"
        
        # Validate field name
        if field not in allowed_fields:
            raise ValueError(f"Invalid order field: {field}")
        
        # Validate direction
        if direction.upper() not in ["ASC", "DESC"]:
            raise ValueError(f"Invalid order direction: {direction}")
        
        return f"ORDER BY {field} {direction.upper()}"
    
    @staticmethod
    def build_limit_clause(limit, offset=None):
        """
        Build a secure LIMIT clause.
        
        Args:
            limit: Number of records to limit
            offset: Number of records to skip
            
        Returns:
            str: Safe LIMIT clause
        """
        try:
            limit = int(limit)
            if limit < 0 or limit > 10000:  # Reasonable upper limit
                raise ValueError("Invalid limit value")
            
            clause = f"LIMIT {limit}"
            
            if offset is not None:
                offset = int(offset)
                if offset < 0:
                    raise ValueError("Invalid offset value")
                clause += f" OFFSET {offset}"
            
            return clause
            
        except (ValueError, TypeError):
            raise ValueError("Invalid limit or offset value")
