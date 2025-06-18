"""
Database utility functions for the Hillview School Management System.
Enhanced with connection pooling and scalability features.
"""
import sqlite3
import os
from typing import Optional, Dict, Any, List
from sqlalchemy import text
from ..extensions import db
from .db_pool import initialize_pool, get_db_connection, get_pool_stats, close_pool

def check_table_exists(table_name):
    """
    Check if a table exists in the database.
    
    Args:
        table_name (str): Name of the table to check
        
    Returns:
        bool: True if table exists, False otherwise
    """
    try:
        # Use SQLAlchemy to check if table exists
        result = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
            {"table_name": table_name}
        )
        return result.fetchone() is not None
    except Exception as e:
        print(f"Error checking table existence: {e}")
        return False

def ensure_teacher_assignment_table():
    """
    Ensure the teacher_subject_assignment table exists.
    Creates it if it doesn't exist.
    
    Returns:
        bool: True if table exists or was created successfully, False otherwise
    """
    try:
        # First check if table exists
        if check_table_exists('teacher_subject_assignment'):
            return True
        
        print("Creating teacher_subject_assignment table...")
        
        # Create the table
        create_table_sql = text("""
            CREATE TABLE IF NOT EXISTS teacher_subject_assignment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                grade_id INTEGER NOT NULL,
                stream_id INTEGER,
                is_class_teacher BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teacher (id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subject (id) ON DELETE CASCADE,
                FOREIGN KEY (grade_id) REFERENCES grade (id) ON DELETE CASCADE,
                FOREIGN KEY (stream_id) REFERENCES stream (id) ON DELETE CASCADE
            )
        """)
        
        db.session.execute(create_table_sql)
        db.session.commit()
        
        print("✅ Teacher assignment table created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating teacher assignment table: {e}")
        return False

def get_teacher_assignments_safely():
    """
    Safely get all teacher assignments with proper error handling.
    
    Returns:
        list: List of teacher assignments, empty list if error occurs
    """
    try:
        # Ensure table exists first
        if not ensure_teacher_assignment_table():
            return []
        
        # Import here to avoid circular imports
        from ..models.assignment import TeacherSubjectAssignment
        
        # Get all assignments
        assignments = TeacherSubjectAssignment.query.all()
        return assignments
        
    except Exception as e:
        print(f"Error getting teacher assignments: {e}")
        return []

def test_database_connection():
    """
    Test the database connection and basic functionality.
    
    Returns:
        dict: Status information about the database
    """
    status = {
        'connected': False,
        'tables_exist': False,
        'teacher_assignment_table': False,
        'error': None
    }
    
    try:
        # Test basic connection
        result = db.session.execute(text("SELECT 1"))
        if result.fetchone():
            status['connected'] = True
        
        # Check for essential tables
        essential_tables = ['teacher', 'subject', 'grade', 'stream']
        tables_exist = all(check_table_exists(table) for table in essential_tables)
        status['tables_exist'] = tables_exist
        
        # Check teacher assignment table specifically
        status['teacher_assignment_table'] = check_table_exists('teacher_subject_assignment')
        
    except Exception as e:
        status['error'] = str(e)
    
    return status

def initialize_missing_tables():
    """
    Initialize any missing tables in the database.
    
    Returns:
        dict: Results of the initialization process
    """
    results = {
        'success': False,
        'tables_created': [],
        'errors': []
    }
    
    try:
        # List of tables to ensure exist
        tables_to_create = {
            'teacher_subject_assignment': """
                CREATE TABLE IF NOT EXISTS teacher_subject_assignment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    grade_id INTEGER NOT NULL,
                    stream_id INTEGER,
                    is_class_teacher BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (teacher_id) REFERENCES teacher (id) ON DELETE CASCADE,
                    FOREIGN KEY (subject_id) REFERENCES subject (id) ON DELETE CASCADE,
                    FOREIGN KEY (grade_id) REFERENCES grade (id) ON DELETE CASCADE,
                    FOREIGN KEY (stream_id) REFERENCES stream (id) ON DELETE CASCADE
                )
            """,
            'class_teacher_permissions': """
                CREATE TABLE IF NOT EXISTS class_teacher_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    grade_id INTEGER NOT NULL,
                    stream_id INTEGER,
                    granted_by INTEGER NOT NULL,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    permission_scope TEXT DEFAULT 'full_class_admin',
                    notes TEXT,
                    FOREIGN KEY (teacher_id) REFERENCES teacher (id) ON DELETE CASCADE,
                    FOREIGN KEY (grade_id) REFERENCES grade (id) ON DELETE CASCADE,
                    FOREIGN KEY (stream_id) REFERENCES stream (id) ON DELETE CASCADE,
                    FOREIGN KEY (granted_by) REFERENCES teacher (id)
                )
            """,
            'function_permissions': """
                CREATE TABLE IF NOT EXISTS function_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    function_name TEXT NOT NULL,
                    function_category TEXT NOT NULL,
                    scope_type TEXT DEFAULT 'global',
                    grade_id INTEGER,
                    stream_id INTEGER,
                    granted_by INTEGER NOT NULL,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    revoked_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    notes TEXT,
                    auto_granted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (teacher_id) REFERENCES teacher (id) ON DELETE CASCADE,
                    FOREIGN KEY (grade_id) REFERENCES grade (id) ON DELETE CASCADE,
                    FOREIGN KEY (stream_id) REFERENCES stream (id) ON DELETE CASCADE,
                    FOREIGN KEY (granted_by) REFERENCES teacher (id)
                )
            """
        }
        
        for table_name, create_sql in tables_to_create.items():
            if not check_table_exists(table_name):
                try:
                    db.session.execute(text(create_sql))
                    results['tables_created'].append(table_name)
                    print(f"✅ Created table: {table_name}")
                except Exception as e:
                    error_msg = f"Failed to create {table_name}: {str(e)}"
                    results['errors'].append(error_msg)
                    print(f"❌ {error_msg}")
        
        # Commit all changes
        if results['tables_created']:
            db.session.commit()
            results['success'] = True
        
    except Exception as e:
        results['errors'].append(f"General error: {str(e)}")
        print(f"❌ Error during table initialization: {e}")
    
    return results

def safe_delete_teacher(teacher_id):
    """
    Safely delete a teacher and all related records.

    Args:
        teacher_id (int): ID of the teacher to delete

    Returns:
        dict: Result of the deletion operation
    """
    result = {
        'success': False,
        'message': '',
        'teacher_name': ''
    }

    try:
        from sqlalchemy import text

        # First get teacher name without loading relationships
        teacher_name_result = db.session.execute(
            text("SELECT username FROM teacher WHERE id = :teacher_id"),
            {"teacher_id": teacher_id}
        ).fetchone()

        if not teacher_name_result:
            result['message'] = 'Teacher not found'
            return result

        teacher_name = teacher_name_result[0]
        result['teacher_name'] = teacher_name

        # Delete all related records using raw SQL to avoid relationship loading
        print(f"Deleting teacher {teacher_name} (ID: {teacher_id}) and related records...")

        # Delete from teacher_subjects table
        try:
            deleted_subjects = db.session.execute(
                text("DELETE FROM teacher_subjects WHERE teacher_id = :teacher_id"),
                {"teacher_id": teacher_id}
            ).rowcount
            print(f"Deleted {deleted_subjects} subject relationships")
        except Exception as e:
            print(f"Note: teacher_subjects table cleanup: {e}")

        # Delete from teacher_subject_assignment table
        try:
            deleted_assignments = db.session.execute(
                text("DELETE FROM teacher_subject_assignment WHERE teacher_id = :teacher_id"),
                {"teacher_id": teacher_id}
            ).rowcount
            print(f"Deleted {deleted_assignments} subject assignments")
        except Exception as e:
            print(f"Note: teacher_subject_assignment table cleanup: {e}")

        # Delete from class_teacher_permissions table
        try:
            deleted_class_perms = db.session.execute(
                text("DELETE FROM class_teacher_permissions WHERE teacher_id = :teacher_id"),
                {"teacher_id": teacher_id}
            ).rowcount
            print(f"Deleted {deleted_class_perms} class permissions")
        except Exception as e:
            print(f"Note: class_teacher_permissions table cleanup: {e}")

        # Delete from function_permissions table
        try:
            deleted_func_perms = db.session.execute(
                text("DELETE FROM function_permissions WHERE teacher_id = :teacher_id"),
                {"teacher_id": teacher_id}
            ).rowcount
            print(f"Deleted {deleted_func_perms} function permissions")
        except Exception as e:
            print(f"Note: function_permissions table cleanup: {e}")

        # Delete from permission_requests table
        try:
            deleted_requests = db.session.execute(
                text("DELETE FROM permission_requests WHERE teacher_id = :teacher_id"),
                {"teacher_id": teacher_id}
            ).rowcount
            print(f"Deleted {deleted_requests} permission requests")
        except Exception as e:
            print(f"Note: permission_requests table cleanup: {e}")

        # Finally delete the teacher record itself using raw SQL
        try:
            deleted_teacher = db.session.execute(
                text("DELETE FROM teacher WHERE id = :teacher_id"),
                {"teacher_id": teacher_id}
            ).rowcount

            if deleted_teacher == 0:
                result['message'] = 'Teacher not found or already deleted'
                return result

            print(f"Deleted teacher record")
        except Exception as e:
            raise Exception(f"Failed to delete teacher record: {e}")

        # Commit all changes
        db.session.commit()

        result['success'] = True
        result['message'] = f"Teacher '{teacher_name}' deleted successfully"
        print(f"✅ Successfully deleted teacher {teacher_name}")

    except Exception as e:
        db.session.rollback()
        result['message'] = f"Error deleting teacher: {str(e)}"
        print(f"❌ Error in safe_delete_teacher: {e}")

    return result

def get_database_health():
    """
    Get comprehensive database health information.

    Returns:
        dict: Complete database health status
    """
    health = {
        'status': 'unknown',
        'connection': test_database_connection(),
        'missing_tables': [],
        'recommendations': []
    }

    # Check for missing tables
    essential_tables = [
        'teacher', 'subject', 'grade', 'stream', 'student', 'term', 'assessment_type',
        'teacher_subject_assignment', 'teacher_subjects', 'class_teacher_permissions', 'function_permissions'
    ]

    for table in essential_tables:
        if not check_table_exists(table):
            health['missing_tables'].append(table)

    # Determine overall status
    if health['connection']['connected'] and not health['missing_tables']:
        health['status'] = 'healthy'
    elif health['connection']['connected'] and health['missing_tables']:
        health['status'] = 'needs_migration'
        health['recommendations'].append('Run database migration to create missing tables')
    else:
        health['status'] = 'critical'
        health['recommendations'].append('Database connection failed - check database file and permissions')

    return health

# Connection Pool Management Functions
def initialize_database_pool(database_path: str = None, min_connections: int = 5,
                            max_connections: int = 20, max_idle_time: int = 300):
    """
    Initialize database connection pool for improved scalability

    Args:
        database_path: Path to database file
        min_connections: Minimum connections to maintain
        max_connections: Maximum connections allowed
        max_idle_time: Maximum idle time before closing connection
    """
    if database_path is None:
        # Use default database path
        database_path = os.path.join(os.path.dirname(__file__), '..', 'kirima_primary.db')

    try:
        initialize_pool(database_path, min_connections, max_connections, max_idle_time)
        print(f"✅ Database connection pool initialized: {database_path}")
        print(f"   Pool size: {min_connections}-{max_connections} connections")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize connection pool: {e}")
        return False

def get_pooled_connection(timeout: int = 30):
    """
    Get a connection from the pool

    Args:
        timeout: Connection timeout in seconds

    Returns:
        Pooled database connection or None
    """
    try:
        return get_db_connection(timeout)
    except Exception as e:
        print(f"❌ Failed to get pooled connection: {e}")
        return None

def get_database_pool_stats() -> Dict[str, Any]:
    """
    Get database connection pool statistics

    Returns:
        Dictionary with pool statistics
    """
    try:
        stats = get_pool_stats()
        return {
            'pool_enabled': True,
            'stats': stats,
            'health': 'healthy' if stats.get('failed_requests', 0) == 0 else 'degraded'
        }
    except Exception as e:
        return {
            'pool_enabled': False,
            'error': str(e),
            'health': 'unavailable'
        }

def close_database_pool():
    """Close the database connection pool"""
    try:
        close_pool()
        print("✅ Database connection pool closed")
        return True
    except Exception as e:
        print(f"❌ Error closing connection pool: {e}")
        return False

def execute_with_pool(query: str, params: tuple = (), fetch_one: bool = False,
                     fetch_all: bool = False, commit: bool = False):
    """
    Execute query using connection pool

    Args:
        query: SQL query to execute
        params: Query parameters
        fetch_one: Whether to fetch one result
        fetch_all: Whether to fetch all results
        commit: Whether to commit the transaction

    Returns:
        Query result or None
    """
    conn = get_pooled_connection()
    if not conn:
        return None

    try:
        cursor = conn.execute(query, params)

        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = cursor.rowcount

        if commit:
            conn.commit()

        return result

    except Exception as e:
        conn.rollback()
        print(f"❌ Query execution error: {e}")
        return None
    finally:
        conn.close()

def batch_execute_with_pool(queries: List[Dict[str, Any]], commit: bool = True):
    """
    Execute multiple queries in a batch using connection pool

    Args:
        queries: List of query dictionaries with 'query' and 'params' keys
        commit: Whether to commit all queries as a transaction

    Returns:
        Dictionary with execution results
    """
    conn = get_pooled_connection()
    if not conn:
        return {'success': False, 'error': 'Could not get database connection'}

    results = {
        'success': False,
        'executed_queries': 0,
        'failed_queries': 0,
        'errors': []
    }

    try:
        for i, query_info in enumerate(queries):
            try:
                query = query_info.get('query', '')
                params = query_info.get('params', ())

                conn.execute(query, params)
                results['executed_queries'] += 1

            except Exception as e:
                results['failed_queries'] += 1
                results['errors'].append(f"Query {i+1}: {str(e)}")

        if commit and results['failed_queries'] == 0:
            conn.commit()
            results['success'] = True
        elif results['failed_queries'] > 0:
            conn.rollback()

    except Exception as e:
        conn.rollback()
        results['errors'].append(f"Batch execution error: {str(e)}")
    finally:
        conn.close()

    return results

def optimize_database_performance():
    """
    Apply database performance optimizations

    Returns:
        Dictionary with optimization results
    """
    optimizations = {
        'applied': [],
        'failed': [],
        'success': False
    }

    # SQLite performance optimizations
    optimization_queries = [
        {'query': 'PRAGMA journal_mode=WAL', 'description': 'Enable WAL mode'},
        {'query': 'PRAGMA synchronous=NORMAL', 'description': 'Set synchronous mode'},
        {'query': 'PRAGMA cache_size=10000', 'description': 'Increase cache size'},
        {'query': 'PRAGMA temp_store=MEMORY', 'description': 'Store temp data in memory'},
        {'query': 'PRAGMA mmap_size=268435456', 'description': 'Enable memory mapping'},
        {'query': 'ANALYZE', 'description': 'Update query planner statistics'}
    ]

    conn = get_pooled_connection()
    if not conn:
        optimizations['failed'].append('Could not get database connection')
        return optimizations

    try:
        for opt in optimization_queries:
            try:
                conn.execute(opt['query'])
                optimizations['applied'].append(opt['description'])
            except Exception as e:
                optimizations['failed'].append(f"{opt['description']}: {str(e)}")

        conn.commit()
        optimizations['success'] = len(optimizations['failed']) == 0

    except Exception as e:
        optimizations['failed'].append(f"General optimization error: {str(e)}")
    finally:
        conn.close()

    return optimizations
