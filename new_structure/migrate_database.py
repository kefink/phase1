#!/usr/bin/env python3
"""
Database migration script to add missing tables to existing databases.
This script will safely add missing tables without affecting existing data.
"""
import sqlite3
import os

def migrate_database():
    """Migrate existing database to add missing tables."""
    db_path = 'kirima_primary.db'
    
    print(f"🔧 Migrating database at: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("💡 Run init_db.py to create a new database")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Found existing tables: {', '.join(existing_tables)}")
        
        migrations_applied = 0

        # Migration 0: Add missing columns to existing tables
        # Add start_date and end_date to term table
        if 'term' in existing_tables:
            cursor.execute("PRAGMA table_info(term)")
            term_columns = [column[1] for column in cursor.fetchall()]
            if 'start_date' not in term_columns:
                print("🔄 Adding start_date column to term table...")
                cursor.execute("ALTER TABLE term ADD COLUMN start_date DATE")
                migrations_applied += 1
            if 'end_date' not in term_columns:
                print("🔄 Adding end_date column to term table...")
                cursor.execute("ALTER TABLE term ADD COLUMN end_date DATE")
                migrations_applied += 1

        # Add group_name and show_on_reports to assessment_type table
        if 'assessment_type' in existing_tables:
            cursor.execute("PRAGMA table_info(assessment_type)")
            assessment_columns = [column[1] for column in cursor.fetchall()]
            if 'group_name' not in assessment_columns:
                print("🔄 Adding group_name column to assessment_type table...")
                cursor.execute("ALTER TABLE assessment_type ADD COLUMN group_name TEXT")
                migrations_applied += 1
            if 'show_on_reports' not in assessment_columns:
                print("🔄 Adding show_on_reports column to assessment_type table...")
                cursor.execute("ALTER TABLE assessment_type ADD COLUMN show_on_reports BOOLEAN DEFAULT 1")
                migrations_applied += 1

        # Migration 1: Add grade_id to student table if missing
        if 'student' in existing_tables:
            cursor.execute("PRAGMA table_info(student)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'grade_id' not in columns:
                print("🔄 Adding grade_id column to student table...")
                cursor.execute("ALTER TABLE student ADD COLUMN grade_id INTEGER")
                cursor.execute("UPDATE student SET grade_id = (SELECT grade_id FROM stream WHERE stream.id = student.stream_id)")
                migrations_applied += 1
        
        # Migration 2: Create teacher_subjects table
        if 'teacher_subjects' not in existing_tables:
            print("🔄 Creating teacher_subjects table...")
            cursor.execute("""
                CREATE TABLE teacher_subjects (
                    teacher_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    PRIMARY KEY (teacher_id, subject_id),
                    FOREIGN KEY (teacher_id) REFERENCES teacher (id) ON DELETE CASCADE,
                    FOREIGN KEY (subject_id) REFERENCES subject (id) ON DELETE CASCADE
                )
            """)
            migrations_applied += 1
        
        # Migration 3: Create teacher_subject_assignment table
        if 'teacher_subject_assignment' not in existing_tables:
            print("🔄 Creating teacher_subject_assignment table...")
            cursor.execute("""
                CREATE TABLE teacher_subject_assignment (
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
            migrations_applied += 1
        
        # Migration 4: Create mark table
        if 'mark' not in existing_tables:
            print("🔄 Creating mark table...")
            cursor.execute("""
                CREATE TABLE mark (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    term_id INTEGER NOT NULL,
                    assessment_type_id INTEGER NOT NULL,
                    raw_mark REAL,
                    total_marks REAL,
                    percentage REAL,
                    grade_letter TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES student (id) ON DELETE CASCADE,
                    FOREIGN KEY (subject_id) REFERENCES subject (id) ON DELETE CASCADE,
                    FOREIGN KEY (term_id) REFERENCES term (id) ON DELETE CASCADE,
                    FOREIGN KEY (assessment_type_id) REFERENCES assessment_type (id) ON DELETE CASCADE
                )
            """)
            migrations_applied += 1
        
        # Migration 5: Create class_teacher_permissions table
        if 'class_teacher_permissions' not in existing_tables:
            print("🔄 Creating class_teacher_permissions table...")
            cursor.execute("""
                CREATE TABLE class_teacher_permissions (
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
            """)
            migrations_applied += 1
        
        # Migration 6: Create function_permissions table
        if 'function_permissions' not in existing_tables:
            print("🔄 Creating function_permissions table...")
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
            migrations_applied += 1
        
        # Migration 7: Create permission_requests table
        if 'permission_requests' not in existing_tables:
            print("🔄 Creating permission_requests table...")
            cursor.execute("""
                CREATE TABLE permission_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    grade_id INTEGER,
                    stream_id INTEGER,
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    processed_at TIMESTAMP,
                    processed_by INTEGER,
                    reason TEXT,
                    admin_notes TEXT,
                    FOREIGN KEY (teacher_id) REFERENCES teacher (id) ON DELETE CASCADE,
                    FOREIGN KEY (grade_id) REFERENCES grade (id) ON DELETE CASCADE,
                    FOREIGN KEY (stream_id) REFERENCES stream (id) ON DELETE CASCADE,
                    FOREIGN KEY (processed_by) REFERENCES teacher (id)
                )
            """)
            migrations_applied += 1
        
        # Migration 8: Create subject_component table
        if 'subject_component' not in existing_tables:
            print("🔄 Creating subject_component table...")
            cursor.execute("""
                CREATE TABLE subject_component (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subject_id) REFERENCES subject (id) ON DELETE CASCADE
                )
            """)
            migrations_applied += 1
        
        # Migration 9: Create school_configuration table
        if 'school_configuration' not in existing_tables:
            print("🔄 Creating school_configuration table...")
            cursor.execute("""
                CREATE TABLE school_configuration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            migrations_applied += 1
        
        # Create sample teacher-subject assignments if table was just created
        if 'teacher_subject_assignment' not in existing_tables and migrations_applied > 0:
            print("📚 Creating sample teacher-subject assignments...")
            
            # Get teacher IDs
            cursor.execute("SELECT id FROM teacher WHERE username = 'classteacher1'")
            classteacher_id = cursor.fetchone()
            
            cursor.execute("SELECT id FROM teacher WHERE username = 'teacher1'")
            teacher1_id = cursor.fetchone()
            
            if classteacher_id and teacher1_id:
                classteacher_id = classteacher_id[0]
                teacher1_id = teacher1_id[0]
                
                # Get subject and grade IDs
                cursor.execute("SELECT id FROM subject WHERE name = 'Mathematics' LIMIT 1")
                math_subject = cursor.fetchone()
                
                cursor.execute("SELECT id FROM subject WHERE name = 'English' LIMIT 1")
                english_subject = cursor.fetchone()
                
                cursor.execute("SELECT id FROM grade WHERE name = 'Grade 1'")
                grade1 = cursor.fetchone()
                
                if grade1:
                    cursor.execute("SELECT id FROM stream WHERE name = 'A' AND grade_id = ?", (grade1[0],))
                    stream_a = cursor.fetchone()
                    
                    if math_subject and grade1 and stream_a:
                        cursor.execute("""
                            INSERT OR IGNORE INTO teacher_subject_assignment 
                            (teacher_id, subject_id, grade_id, stream_id, is_class_teacher)
                            VALUES (?, ?, ?, ?, ?)
                        """, (classteacher_id, math_subject[0], grade1[0], stream_a[0], 1))
                    
                    if english_subject and grade1 and stream_a:
                        cursor.execute("""
                            INSERT OR IGNORE INTO teacher_subject_assignment 
                            (teacher_id, subject_id, grade_id, stream_id, is_class_teacher)
                            VALUES (?, ?, ?, ?, ?)
                        """, (teacher1_id, english_subject[0], grade1[0], stream_a[0], 0))
                
                print("✅ Sample teacher-subject assignments created")
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        print(f"✅ Database migration completed successfully!")
        print(f"📊 Applied {migrations_applied} migrations")
        
        return True
        
    except Exception as e:
        print(f"❌ Error migrating database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = migrate_database()
    if success:
        print("\n🚀 Migration completed successfully!")
        print("🎯 You can now use all features including analytics with teacher information")
    else:
        print("\n❌ Migration failed!")
