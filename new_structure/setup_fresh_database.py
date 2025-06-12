#!/usr/bin/env python3
"""
Fresh database setup script to create a clean database structure
without any test data, ready for real data entry.
"""

import sqlite3
import os
from datetime import datetime

def setup_fresh_database():
    """Set up a fresh database with structure only, no test data."""
    db_path = 'kirima_primary.db'
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        backup_name = f'kirima_primary_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        os.rename(db_path, backup_name)
        print(f"📦 Existing database backed up as: {backup_name}")
    
    print(f"🔧 Creating fresh database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        print("📋 Creating table structure...")
        
        # Create all tables with proper structure
        create_all_tables(cursor)
        
        print("👤 Creating minimal admin account...")
        
        # Create only the headteacher account
        cursor.execute("""
            INSERT INTO teacher (username, password, role, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        """, ('headteacher', 'admin123', 'headteacher', 'System', 'Administrator'))
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        print("✅ Fresh database created successfully!")
        print("\n🎯 Database is ready for your data!")
        print("\n📝 Next steps:")
        print("1. Start the application: python run.py")
        print("2. Login as headteacher (username: headteacher, password: admin123)")
        print("3. Use the admin interface to create:")
        print("   - Grades and streams")
        print("   - Subjects")
        print("   - Terms and assessments")
        print("   - Teachers")
        print("   - Students")
        print("4. Login as classteacher to upload marks")
        print("5. View analytics with your real data!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating fresh database: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_all_tables(cursor):
    """Create all necessary tables with proper structure."""
    
    # Grade table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grade (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            education_level TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Stream table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stream (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grade_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (grade_id) REFERENCES grade (id)
        )
    """)
    
    # Subject table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            education_level TEXT NOT NULL,
            is_composite INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Term table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS term (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            academic_year TEXT NOT NULL,
            is_current INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            start_date DATE,
            end_date DATE
        )
    """)
    
    # Assessment type table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_type (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            weight REAL,
            category TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            group_name TEXT,
            show_on_reports INTEGER DEFAULT 1
        )
    """)
    
    # Teacher table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            stream_id INTEGER,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stream_id) REFERENCES stream (id)
        )
    """)
    
    # Student table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            admission_number TEXT UNIQUE,
            stream_id INTEGER,
            grade_id INTEGER,
            gender TEXT DEFAULT 'Unknown',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stream_id) REFERENCES stream (id),
            FOREIGN KEY (grade_id) REFERENCES grade (id)
        )
    """)
    
    # Mark table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mark (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            term_id INTEGER NOT NULL,
            assessment_type_id INTEGER NOT NULL,
            mark REAL NOT NULL,
            total_marks REAL NOT NULL,
            raw_mark REAL NOT NULL,
            raw_total_marks REAL NOT NULL,
            percentage REAL NOT NULL,
            grade_letter TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student (id),
            FOREIGN KEY (subject_id) REFERENCES subject (id),
            FOREIGN KEY (term_id) REFERENCES term (id),
            FOREIGN KEY (assessment_type_id) REFERENCES assessment_type (id)
        )
    """)
    
    # Teacher-subjects many-to-many table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_subjects (
            teacher_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            PRIMARY KEY (teacher_id, subject_id),
            FOREIGN KEY (teacher_id) REFERENCES teacher (id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subject (id) ON DELETE CASCADE
        )
    """)
    
    # Teacher subject assignment table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_subject_assignment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            grade_id INTEGER NOT NULL,
            stream_id INTEGER,
            is_class_teacher INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES teacher (id),
            FOREIGN KEY (subject_id) REFERENCES subject (id),
            FOREIGN KEY (grade_id) REFERENCES grade (id),
            FOREIGN KEY (stream_id) REFERENCES stream (id)
        )
    """)
    
    # Class teacher permissions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS class_teacher_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            grade_id INTEGER NOT NULL,
            stream_id INTEGER,
            granted_by INTEGER NOT NULL,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            revoked_at TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            expires_at TIMESTAMP,
            is_permanent INTEGER DEFAULT 0,
            auto_granted INTEGER DEFAULT 0,
            permission_scope TEXT DEFAULT 'full_class_admin',
            notes TEXT,
            FOREIGN KEY (teacher_id) REFERENCES teacher (id),
            FOREIGN KEY (grade_id) REFERENCES grade (id),
            FOREIGN KEY (stream_id) REFERENCES stream (id),
            FOREIGN KEY (granted_by) REFERENCES teacher (id)
        )
    """)
    
    # Function permissions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS function_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            function_name TEXT NOT NULL,
            function_category TEXT NOT NULL,
            granted_by INTEGER NOT NULL,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            scope_type TEXT DEFAULT 'global',
            scope_grade_id INTEGER,
            scope_stream_id INTEGER,
            notes TEXT,
            auto_granted INTEGER DEFAULT 0,
            FOREIGN KEY (teacher_id) REFERENCES teacher (id),
            FOREIGN KEY (granted_by) REFERENCES teacher (id),
            FOREIGN KEY (scope_grade_id) REFERENCES grade (id),
            FOREIGN KEY (scope_stream_id) REFERENCES stream (id)
        )
    """)
    
    # Permission requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permission_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            grade_id INTEGER NOT NULL,
            stream_id INTEGER,
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            reviewed_by INTEGER,
            reviewed_at TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (teacher_id) REFERENCES teacher (id),
            FOREIGN KEY (grade_id) REFERENCES grade (id),
            FOREIGN KEY (stream_id) REFERENCES stream (id),
            FOREIGN KEY (reviewed_by) REFERENCES teacher (id)
        )
    """)
    
    # Subject component table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject_component (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            weight REAL DEFAULT 100.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subject (id)
        )
    """)
    
    # School configuration table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS school_configuration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("✅ All tables created successfully")

if __name__ == '__main__':
    print("🚀 FRESH DATABASE SETUP")
    print("=" * 50)
    print("This will create a clean database with structure only.")
    print("No test data will be included.")
    print("=" * 50)
    
    success = setup_fresh_database()
    
    if success:
        print("\n🎉 Fresh database setup completed successfully!")
        print("You can now add your own data through the application interface.")
    else:
        print("\n❌ Fresh database setup failed!")
