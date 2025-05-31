#!/usr/bin/env python3
"""
Initialize complete database with all required tables.
This script creates all missing tables and populates them with default data.
"""

import os
import sys
import sqlite3
from datetime import datetime

def create_complete_database():
    """Create complete database with all required tables."""
    print("🔧 Creating complete database schema...")
    
    db_path = '../kirima_primary.db'
    
    # Create backup
    if os.path.exists(db_path):
        backup_path = f'../kirima_primary.db.backup_complete_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        print(f"📋 Existing tables: {existing_tables}")
        
        # Create teacher table (enhanced)
        if 'teacher' not in existing_tables:
            cursor.execute("""
                CREATE TABLE teacher (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(100) NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    stream_id INTEGER,
                    full_name TEXT,
                    employee_id TEXT,
                    phone_number TEXT,
                    email TEXT,
                    qualification TEXT,
                    specialization TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    date_joined DATE,
                    FOREIGN KEY (stream_id) REFERENCES stream (id)
                )
            """)
            print("✅ Created teacher table")
        
        # Create school_configuration table (enhanced)
        if 'school_configuration' not in existing_tables:
            cursor.execute("""
                CREATE TABLE school_configuration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_name TEXT NOT NULL,
                    school_motto TEXT,
                    school_address TEXT,
                    school_phone TEXT,
                    school_email TEXT,
                    school_website TEXT,
                    current_academic_year TEXT,
                    current_term TEXT,
                    use_streams BOOLEAN DEFAULT 1,
                    grading_system TEXT DEFAULT 'percentage',
                    show_position BOOLEAN DEFAULT 1,
                    show_class_average BOOLEAN DEFAULT 1,
                    show_subject_teacher BOOLEAN DEFAULT 1,
                    logo_filename TEXT,
                    primary_color TEXT DEFAULT '#1f7d53',
                    secondary_color TEXT DEFAULT '#18230f',
                    headteacher_name TEXT,
                    deputy_headteacher_name TEXT,
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
            print("✅ Created school_configuration table")
        
        # Create subject table
        if 'subject' not in existing_tables:
            cursor.execute("""
                CREATE TABLE subject (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    education_level TEXT NOT NULL,
                    is_standard BOOLEAN DEFAULT 1,
                    is_composite BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Created subject table")
        
        # Create grade table
        if 'grade' not in existing_tables:
            cursor.execute("""
                CREATE TABLE grade (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    education_level TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Created grade table")
        
        # Create stream table
        if 'stream' not in existing_tables:
            cursor.execute("""
                CREATE TABLE stream (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    grade_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (grade_id) REFERENCES grade (id)
                )
            """)
            print("✅ Created stream table")
        
        # Create student table
        if 'student' not in existing_tables:
            cursor.execute("""
                CREATE TABLE student (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    admission_number TEXT UNIQUE,
                    grade_id INTEGER NOT NULL,
                    stream_id INTEGER NOT NULL,
                    date_of_birth DATE,
                    gender TEXT,
                    parent_contact TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (grade_id) REFERENCES grade (id),
                    FOREIGN KEY (stream_id) REFERENCES stream (id)
                )
            """)
            print("✅ Created student table")
        
        # Create term table
        if 'term' not in existing_tables:
            cursor.execute("""
                CREATE TABLE term (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    academic_year TEXT,
                    start_date DATE,
                    end_date DATE,
                    is_current BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Created term table")
        
        # Create assessment_type table
        if 'assessment_type' not in existing_tables:
            cursor.execute("""
                CREATE TABLE assessment_type (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    weight REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Created assessment_type table")
        
        # Create marks table
        if 'marks' not in existing_tables:
            cursor.execute("""
                CREATE TABLE marks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    term_id INTEGER NOT NULL,
                    assessment_type_id INTEGER NOT NULL,
                    raw_mark REAL,
                    percentage REAL,
                    grade TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES student (id),
                    FOREIGN KEY (subject_id) REFERENCES subject (id),
                    FOREIGN KEY (term_id) REFERENCES term (id),
                    FOREIGN KEY (assessment_type_id) REFERENCES assessment_type (id)
                )
            """)
            print("✅ Created marks table")
        
        # Create teacher_subjects table (many-to-many relationship)
        if 'teacher_subjects' not in existing_tables:
            cursor.execute("""
                CREATE TABLE teacher_subjects (
                    teacher_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    PRIMARY KEY (teacher_id, subject_id),
                    FOREIGN KEY (teacher_id) REFERENCES teacher (id),
                    FOREIGN KEY (subject_id) REFERENCES subject (id)
                )
            """)
            print("✅ Created teacher_subjects table")
        
        conn.commit()
        print("✅ Database schema created successfully!")
        
        # Now populate with default data
        populate_default_data(cursor, conn)
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False

def populate_default_data(cursor, conn):
    """Populate database with default data."""
    print("📝 Populating default data...")
    
    try:
        # Insert default admin teacher if not exists
        cursor.execute("SELECT COUNT(*) FROM teacher WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO teacher (username, password, role, full_name, employee_id, is_active)
                VALUES ('admin', 'admin', 'admin', 'Administrator', 'EMP001', 1)
            """)
            print("✅ Created admin teacher")
        
        # Insert school configuration if not exists
        cursor.execute("SELECT COUNT(*) FROM school_configuration")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO school_configuration (
                    school_name, school_motto, current_academic_year, current_term,
                    headteacher_name, deputy_headteacher_name
                ) VALUES (
                    'Hillview School', 'Excellence in Education', '2024', 'Term 1',
                    'Head Teacher', 'Deputy Head Teacher'
                )
            """)
            print("✅ Created school configuration")
        
        # Insert default grades
        grades_data = [
            ('Grade 1', 'lower_primary'),
            ('Grade 2', 'lower_primary'),
            ('Grade 3', 'lower_primary'),
            ('Grade 4', 'upper_primary'),
            ('Grade 5', 'upper_primary'),
            ('Grade 6', 'upper_primary'),
            ('Grade 7', 'junior_secondary'),
            ('Grade 8', 'junior_secondary'),
            ('Grade 9', 'junior_secondary')
        ]
        
        for grade_name, education_level in grades_data:
            cursor.execute("SELECT COUNT(*) FROM grade WHERE name = ?", (grade_name,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO grade (name, education_level) VALUES (?, ?)", 
                             (grade_name, education_level))
        print("✅ Created default grades")
        
        # Insert default streams for each grade
        cursor.execute("SELECT id, name FROM grade")
        grades = cursor.fetchall()
        
        for grade_id, grade_name in grades:
            # Check if streams exist for this grade
            cursor.execute("SELECT COUNT(*) FROM stream WHERE grade_id = ?", (grade_id,))
            if cursor.fetchone()[0] == 0:
                # Create default streams
                streams = ['A', 'B'] if 'Grade' in grade_name else ['Stream A', 'Stream B']
                for stream_name in streams:
                    cursor.execute("INSERT INTO stream (name, grade_id) VALUES (?, ?)", 
                                 (stream_name, grade_id))
        print("✅ Created default streams")
        
        # Insert default subjects
        subjects_data = [
            # Lower Primary
            ('English', 'lower_primary', True, False),
            ('Kiswahili', 'lower_primary', True, False),
            ('Mathematics', 'lower_primary', True, False),
            ('Environmental Activities', 'lower_primary', True, False),
            ('Creative Arts', 'lower_primary', True, False),
            ('Physical Education', 'lower_primary', True, False),
            
            # Upper Primary
            ('English', 'upper_primary', True, False),
            ('Kiswahili', 'upper_primary', True, False),
            ('Mathematics', 'upper_primary', True, False),
            ('Science', 'upper_primary', True, False),
            ('Social Studies', 'upper_primary', True, False),
            ('Creative Arts', 'upper_primary', True, False),
            ('Physical Education', 'upper_primary', True, False),
            
            # Junior Secondary
            ('English', 'junior_secondary', True, False),
            ('Kiswahili', 'junior_secondary', True, False),
            ('Mathematics', 'junior_secondary', True, False),
            ('Biology', 'junior_secondary', True, False),
            ('Chemistry', 'junior_secondary', True, False),
            ('Physics', 'junior_secondary', True, False),
            ('Geography', 'junior_secondary', True, False),
            ('History', 'junior_secondary', True, False),
            ('Religious Education', 'junior_secondary', True, False),
            ('Physical Education', 'junior_secondary', True, False)
        ]
        
        for subject_name, education_level, is_standard, is_composite in subjects_data:
            cursor.execute("""
                SELECT COUNT(*) FROM subject 
                WHERE name = ? AND education_level = ?
            """, (subject_name, education_level))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO subject (name, education_level, is_standard, is_composite)
                    VALUES (?, ?, ?, ?)
                """, (subject_name, education_level, is_standard, is_composite))
        print("✅ Created default subjects")
        
        # Insert default terms
        terms_data = [
            ('Term 1', '2024', '2024-01-15', '2024-04-12', True),
            ('Term 2', '2024', '2024-05-06', '2024-08-02', False),
            ('Term 3', '2024', '2024-08-26', '2024-11-22', False)
        ]
        
        for term_name, academic_year, start_date, end_date, is_current in terms_data:
            cursor.execute("SELECT COUNT(*) FROM term WHERE name = ? AND academic_year = ?", 
                         (term_name, academic_year))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO term (name, academic_year, start_date, end_date, is_current)
                    VALUES (?, ?, ?, ?, ?)
                """, (term_name, academic_year, start_date, end_date, is_current))
        print("✅ Created default terms")
        
        # Insert default assessment types
        assessment_types = [
            ('End of Term Exam', 'Final examination for the term', 1.0),
            ('Mid Term Test', 'Mid-term assessment', 0.5),
            ('Continuous Assessment', 'Ongoing classroom assessment', 0.3)
        ]
        
        for name, description, weight in assessment_types:
            cursor.execute("SELECT COUNT(*) FROM assessment_type WHERE name = ?", (name,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO assessment_type (name, description, weight)
                    VALUES (?, ?, ?)
                """, (name, description, weight))
        print("✅ Created default assessment types")
        
        conn.commit()
        print("✅ Default data populated successfully!")
        
    except Exception as e:
        print(f"❌ Data population failed: {e}")

def verify_database():
    """Verify the database is complete."""
    print("🔍 Verifying database...")
    
    try:
        conn = sqlite3.connect('../kirima_primary.db')
        cursor = conn.cursor()
        
        # Check all required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        required_tables = [
            'teacher', 'school_configuration', 'subject', 'grade', 'stream',
            'student', 'term', 'assessment_type', 'marks', 'teacher_subjects'
        ]
        
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        print(f"✅ All required tables present: {len(tables)} total")
        
        # Check data counts
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} records")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def main():
    """Run the complete database initialization."""
    print("🚀 Complete Database Initialization")
    print("=" * 60)
    
    if not create_complete_database():
        print("❌ Database creation failed")
        return False
    
    if not verify_database():
        print("❌ Database verification failed")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Complete database initialization successful!")
    print("\n🚀 Your Flask application should now work properly.")
    print("All tables and default data have been created.")
    
    return True

if __name__ == "__main__":
    main()
