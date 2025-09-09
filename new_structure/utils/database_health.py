"""Database health check utilities (MySQL/SQLAlchemy version).

Legacy SQLite direct file inspection removed. All checks now use SQLAlchemy
introspection so the same logic works for MySQL. Functions retain the same
signatures to avoid breaking existing imports.
"""

from flask import current_app
from ..extensions import db
from sqlalchemy import inspect, text

def check_database_health():
    """
    Check the health of the database and ensure all required tables exist.
    
    Returns:
        dict: Health check results
    """
    results = {
        'status': 'healthy',
        'missing_tables': [],
        'existing_tables': [],
        'errors': [],
        'warnings': []
    }
    
    try:
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        results['existing_tables'] = existing_tables
        
        # Define required tables
        required_tables = [
            'teacher',
            'grade',
            'stream',
            'subject',
            'term',
            'assessment_type',
            'student',
            'mark',
            'teacher_subjects',
            'teacher_subject_assignment',
            'subject_component',
            'component_mark',
            'class_teacher_permissions',
            'function_permissions',
            'permission_requests',
            'school_configuration'
        ]
        
        # Check for missing tables
        missing_tables = [table for table in required_tables if table not in existing_tables]
        results['missing_tables'] = missing_tables
        
        if missing_tables:
            results['status'] = 'warning'
            results['warnings'].append(f'Missing tables: {", ".join(missing_tables)}')
        
        # Check table record counts (lightweight; skip if too many tables)
        table_counts = {}
        for table in existing_tables:
            try:
                count = db.session.execute(text(f"SELECT COUNT(*) FROM `{table}`"))  # backticks for MySQL
                table_counts[table] = count.scalar()
            except Exception:
                # Ignore counting errors (permissions/large tables)
                continue
        results['table_counts'] = table_counts

        # Essential data presence
        if 'teacher' in existing_tables:
            try:
                headteacher_count = db.session.execute(text("SELECT COUNT(*) FROM teacher WHERE role='headteacher'"))
                if headteacher_count.scalar() == 0:
                    results['warnings'].append('No headteacher account found')
            except Exception:
                results['warnings'].append('Could not verify headteacher presence')
        
    except Exception as e:
        results['errors'].append(f'Database health check failed: {e}')
        results['status'] = 'error'
    
    return results

def create_missing_tables():  # Backwards compatible stub
    """Deprecated: Table creation now managed via Alembic migrations.

    Returns a neutral response so callers don't break.
    """
    return {
        'success': False,
        'tables_created': [],
        'errors': ['create_missing_tables deprecated - use Alembic migrations']
    }

def safe_table_operation(operation_func, table_name, *args, **kwargs):
    """
    Safely perform a table operation with error handling.
    
    Args:
        operation_func: Function to execute
        table_name: Name of the table being operated on
        *args, **kwargs: Arguments to pass to the operation function
    
    Returns:
        tuple: (success: bool, result: any, error: str)
    """
    try:
        result = operation_func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        error_msg = f"Error in {table_name} operation: {e}"
        print(error_msg)
        return False, None, error_msg
