"""Database health check utilities (MySQL/SQLAlchemy).

All inspection uses SQLAlchemy; no direct filesystem access.
"""

from sqlalchemy import inspect, text
from ..extensions import db

REQUIRED_TABLES = [
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

def check_database_health(sample_counts: bool = True, count_limit: int = 50_000):
    """Check schema presence and light data signals.

    Args:
        sample_counts: Whether to include row counts.
        count_limit: If a table's count exceeds this, store as a threshold string.
    Returns:
        dict: health snapshot
    """
    results = {
        'status': 'healthy',
        'missing_tables': [],
        'existing_tables': [],
        'errors': [],
        'warnings': [],
        'table_counts': {}
    }

    try:
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        results['existing_tables'] = existing_tables

        # Missing tables
        missing = [t for t in REQUIRED_TABLES if t not in existing_tables]
        results['missing_tables'] = missing
        if missing:
            results['status'] = 'warning'
            results['warnings'].append(f"Missing tables: {', '.join(missing)}")

        # Headteacher presence
        if 'teacher' in existing_tables:
            try:
                head_count = db.session.execute(
                    text("SELECT COUNT(*) FROM teacher WHERE role='headteacher'")
                ).scalar()
                if head_count == 0:
                    results['warnings'].append('No headteacher account found')
            except Exception as e:  # pragma: no cover - defensive
                results['warnings'].append(f'Headteacher check failed: {e}')

        # Optional row counts
        if sample_counts:
            for table in existing_tables:
                try:
                    cnt = db.session.execute(text(f"SELECT COUNT(*) FROM `{table}`")).scalar()
                    if cnt is not None:
                        results['table_counts'][table] = cnt if cnt <= count_limit else f">{count_limit}"
                except Exception:  # pragma: no cover - ignore counting failures
                    continue

    except Exception as e:
        results['errors'].append(f'Database health check failed: {e}')
        results['status'] = 'error'

    return results

def check_password_hash_integrity():
    """Inspect teacher.password for non-modern or null hashes.

    Returns:
        dict
    """
    out = {
        'column_used': 'password',
        'non_modern_hash': None,
        'null_hashes': None,
        'healthy': False,
        'skipped': False
    }

    try:
        inspector = inspect(db.engine)
        if 'teacher' not in inspector.get_table_names():
            out['skipped'] = True
            out['healthy'] = True
            return out

        plain_like = db.session.execute(text(
            "SELECT COUNT(*) FROM teacher "
            "WHERE (password NOT LIKE 'scrypt:%' AND password NOT LIKE 'pbkdf2:%')"
        )).scalar()
        null_hashes = db.session.execute(text(
            "SELECT COUNT(*) FROM teacher WHERE password IS NULL"
        )).scalar()
        out['non_modern_hash'] = plain_like
        out['null_hashes'] = null_hashes
        out['healthy'] = (plain_like == 0 and null_hashes == 0)
    except Exception as e:  # pragma: no cover
        out['error'] = f'Password hash integrity check failed: {e}'
    return out

def create_missing_tables():  # Backwards compatibility
    """Deprecated: use Alembic migrations instead."""
    return {
        'success': False,
        'tables_created': [],
        'errors': ['create_missing_tables deprecated - use Alembic migrations']
    }

def safe_table_operation(operation_func, table_name, *args, **kwargs):
    """Wrap a table operation with error handling.

    Returns:
        (success: bool, result, error: str|None)
    """
    try:
        result = operation_func(*args, **kwargs)
        return True, result, None
    except Exception as e:  # pragma: no cover
        msg = f"Error in {table_name} operation: {e}"
        print(msg)
        return False, None, msg

def full_health_report():
    """Aggregate database core checks + password hash integrity."""
    core = check_database_health()
    pwd = check_password_hash_integrity()

    if core['status'] == 'error':
        overall = 'error'
    elif core['status'] == 'warning' or not pwd.get('healthy', True):
        overall = 'warning'
    else:
        overall = 'healthy'

    return {
        'database': core,
        'password_hash_integrity': pwd,
        'overall_status': overall
    }

__all__ = [
    'check_database_health',
    'check_password_hash_integrity',
    'create_missing_tables',
    'safe_table_operation',
    'full_health_report'
]
