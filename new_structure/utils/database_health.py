"""
Database health check utilities.
"""

import sqlite3
import os
from flask import current_app

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
        # Get database path from config
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
        else:
            results['errors'].append('Unsupported database type')
            results['status'] = 'error'
            return results
        
        if not os.path.exists(db_path):
            results['errors'].append(f'Database file not found: {db_path}')
            results['status'] = 'error'
            return results
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in cursor.fetchall()]
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
        
        # Check table record counts
        table_counts = {}
        for table in existing_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_counts[table] = count
            except Exception as e:
                results['warnings'].append(f'Could not count records in {table}: {e}')
        
        results['table_counts'] = table_counts
        
        # Check for essential data
        if 'teacher' in existing_tables:
            cursor.execute("SELECT COUNT(*) FROM teacher WHERE role = 'headteacher'")
            headteacher_count = cursor.fetchone()[0]
            if headteacher_count == 0:
                results['warnings'].append('No headteacher account found')
        
        conn.close()
        
    except Exception as e:
        results['errors'].append(f'Database health check failed: {e}')
        results['status'] = 'error'
    
    return results

def create_missing_tables():
    """
    Create any missing required tables.
    
    Returns:
        dict: Creation results
    """
    results = {
        'success': False,
        'tables_created': [],
        'errors': []
    }
    
    try:
        # Get database path from config
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
        else:
            results['errors'].append('Unsupported database type')
            return results
        
        if not os.path.exists(db_path):
            results['errors'].append(f'Database file not found: {db_path}')
            return results
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        # Create missing permission tables
        if 'class_teacher_permissions' not in existing_tables:
            cursor.execute("""
                CREATE TABLE class_teacher_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    grade_id INTEGER NOT NULL,
                    stream_id INTEGER,
                    granted_by INTEGER NOT NULL,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    revoked_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    expires_at TIMESTAMP,
                    is_permanent BOOLEAN DEFAULT 0,
                    auto_granted BOOLEAN DEFAULT 0,
                    permission_scope TEXT DEFAULT 'full_class_admin',
                    notes TEXT,
                    FOREIGN KEY (teacher_id) REFERENCES teacher (id) ON DELETE CASCADE,
                    FOREIGN KEY (grade_id) REFERENCES grade (id) ON DELETE CASCADE,
                    FOREIGN KEY (stream_id) REFERENCES stream (id) ON DELETE CASCADE,
                    FOREIGN KEY (granted_by) REFERENCES teacher (id)
                )
            """)
            results['tables_created'].append('class_teacher_permissions')
        
        if 'function_permissions' not in existing_tables:
            cursor.execute("""
                CREATE TABLE function_permissions (
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
            """)
            results['tables_created'].append('function_permissions')
        
        if 'permission_requests' not in existing_tables:
            cursor.execute("""
                CREATE TABLE permission_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    grade_id INTEGER NOT NULL,
                    stream_id INTEGER,
                    request_type TEXT DEFAULT 'class_access',
                    justification TEXT,
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    reviewed_by INTEGER,
                    status TEXT DEFAULT 'pending',
                    response_notes TEXT,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (teacher_id) REFERENCES teacher (id) ON DELETE CASCADE,
                    FOREIGN KEY (grade_id) REFERENCES grade (id) ON DELETE CASCADE,
                    FOREIGN KEY (stream_id) REFERENCES stream (id) ON DELETE CASCADE,
                    FOREIGN KEY (reviewed_by) REFERENCES teacher (id)
                )
            """)
            results['tables_created'].append('permission_requests')
        
        # Create teacher_subjects table (many-to-many relationship)
        if 'teacher_subjects' not in existing_tables:
            cursor.execute("""
                CREATE TABLE teacher_subjects (
                    teacher_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    PRIMARY KEY (teacher_id, subject_id),
                    FOREIGN KEY (teacher_id) REFERENCES teacher (id) ON DELETE CASCADE,
                    FOREIGN KEY (subject_id) REFERENCES subject (id) ON DELETE CASCADE
                )
            """)
            results['tables_created'].append('teacher_subjects')

        # Create subject_component table
        if 'subject_component' not in existing_tables:
            cursor.execute("""
                CREATE TABLE subject_component (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    max_raw_mark INTEGER DEFAULT 100,
                    FOREIGN KEY (subject_id) REFERENCES subject (id) ON DELETE CASCADE
                )
            """)
            results['tables_created'].append('subject_component')

        # Create component_mark table
        if 'component_mark' not in existing_tables:
            cursor.execute("""
                CREATE TABLE component_mark (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mark_id INTEGER NOT NULL,
                    component_id INTEGER NOT NULL,
                    raw_mark REAL NOT NULL,
                    max_raw_mark INTEGER DEFAULT 100,
                    percentage REAL NOT NULL,
                    FOREIGN KEY (mark_id) REFERENCES mark (id) ON DELETE CASCADE,
                    FOREIGN KEY (component_id) REFERENCES subject_component (id) ON DELETE CASCADE
                )
            """)
            results['tables_created'].append('component_mark')

        if 'school_configuration' not in existing_tables:
            cursor.execute("""
                CREATE TABLE school_configuration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_name TEXT NOT NULL DEFAULT 'Hillview School',
                    school_motto TEXT DEFAULT 'Excellence in Education',
                    school_address TEXT,
                    school_phone TEXT,
                    school_email TEXT,
                    school_website TEXT,
                    current_academic_year TEXT DEFAULT '2024',
                    current_term TEXT DEFAULT 'Term 1',
                    use_streams BOOLEAN DEFAULT 1,
                    grading_system TEXT DEFAULT 'percentage',
                    show_position BOOLEAN DEFAULT 1,
                    show_class_average BOOLEAN DEFAULT 1,
                    show_subject_teacher BOOLEAN DEFAULT 1,
                    logo_filename TEXT,
                    primary_color TEXT DEFAULT '#1f7d53',
                    secondary_color TEXT DEFAULT '#18230f',
                    headteacher_name TEXT DEFAULT 'Head Teacher',
                    deputy_headteacher_name TEXT DEFAULT 'Deputy Head Teacher',
                    max_raw_marks_default INTEGER DEFAULT 100,
                    pass_mark_percentage INTEGER DEFAULT 50,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    headteacher_id INTEGER,
                    deputy_headteacher_id INTEGER,
                    FOREIGN KEY (headteacher_id) REFERENCES teacher (id),
                    FOREIGN KEY (deputy_headteacher_id) REFERENCES teacher (id)
                )
            """)
            
            # Insert default configuration
            cursor.execute("""
                INSERT INTO school_configuration (
                    school_name, school_motto, current_academic_year, current_term,
                    headteacher_name, deputy_headteacher_name
                ) VALUES (
                    'Hillview School', 'Excellence in Education', '2024', 'Term 1',
                    'Head Teacher', 'Deputy Head Teacher'
                )
            """)
            results['tables_created'].append('school_configuration')
        
        conn.commit()
        conn.close()
        
        results['success'] = True
        
    except Exception as e:
        results['errors'].append(f'Failed to create missing tables: {e}')
    
    return results

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
