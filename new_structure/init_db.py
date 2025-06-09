#!/usr/bin/env python3
"""
Database initialization script to create all necessary tables and data.
"""
import sqlite3
import os

def init_database():
    """Initialize the database with all required tables and data."""
    db_path = 'kirima_primary.db'
    
    print(f"🔧 Initializing database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        print("📋 Creating tables...")
        
        # Create grade table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grade (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                education_level TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create stream table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stream (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                grade_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (grade_id) REFERENCES grade (id)
            )
        """)
        
        # Create term table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS term (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                academic_year TEXT,
                start_date DATE,
                end_date DATE,
                is_current BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create assessment_type table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessment_type (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                weight INTEGER,
                group_name TEXT,
                show_on_reports BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create subject table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subject (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                education_level TEXT NOT NULL,
                is_composite BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create teacher table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
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
        
        # Create student table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                admission_number TEXT UNIQUE,
                stream_id INTEGER,
                gender TEXT DEFAULT 'Unknown',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stream_id) REFERENCES stream (id)
            )
        """)
        
        print("✅ Tables created successfully")
        
        # Insert default grades
        print("📚 Inserting default grades...")
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
            cursor.execute("""
                INSERT OR IGNORE INTO grade (name, education_level) 
                VALUES (?, ?)
            """, (grade_name, education_level))
        
        # Insert default streams for each grade
        print("🏫 Inserting default streams...")
        cursor.execute("SELECT id, name FROM grade")
        grade_records = cursor.fetchall()
        
        stream_count = 0
        for grade_id, grade_name in grade_records:
            cursor.execute("""
                INSERT OR IGNORE INTO stream (name, grade_id) 
                VALUES (?, ?)
            """, ('A', grade_id))
            cursor.execute("""
                INSERT OR IGNORE INTO stream (name, grade_id) 
                VALUES (?, ?)
            """, ('B', grade_id))
            stream_count += 2
        
        print(f"✅ Created {stream_count} streams")
        
        # Insert default terms
        print("📅 Inserting default terms...")
        terms_data = [
            ('Term 1', '2024', 1),
            ('Term 2', '2024', 0),
            ('Term 3', '2024', 0)
        ]
        
        for term_name, academic_year, is_current in terms_data:
            cursor.execute("""
                INSERT OR IGNORE INTO term (name, academic_year, is_current) 
                VALUES (?, ?, ?)
            """, (term_name, academic_year, is_current))
        
        # Insert default assessment types
        print("📝 Inserting default assessment types...")
        assessment_types_data = [
            ('Mid Term', 30, 'Exams', 1),
            ('End Term', 70, 'Exams', 1),
            ('Assignment', 0, 'Continuous Assessment', 1)
        ]
        
        for name, weight, group_name, show_on_reports in assessment_types_data:
            cursor.execute("""
                INSERT OR IGNORE INTO assessment_type (name, weight, group_name, show_on_reports) 
                VALUES (?, ?, ?, ?)
            """, (name, weight, group_name, show_on_reports))
        
        # Insert default subjects
        print("📖 Inserting default subjects...")
        subjects_data = [
            # Lower Primary
            ('Mathematics', 'lower_primary'),
            ('English', 'lower_primary'),
            ('Kiswahili', 'lower_primary'),
            ('Environmental Activities', 'lower_primary'),
            ('Creative Activities', 'lower_primary'),
            ('Movement and Creative Activities', 'lower_primary'),
            
            # Upper Primary
            ('Mathematics', 'upper_primary'),
            ('English', 'upper_primary'),
            ('Kiswahili', 'upper_primary'),
            ('Science and Technology', 'upper_primary'),
            ('Social Studies', 'upper_primary'),
            ('Creative Arts', 'upper_primary'),
            ('Physical and Health Education', 'upper_primary'),
            
            # Junior Secondary
            ('Mathematics', 'junior_secondary'),
            ('English', 'junior_secondary'),
            ('Kiswahili', 'junior_secondary'),
            ('Integrated Science', 'junior_secondary'),
            ('Social Studies', 'junior_secondary'),
            ('Creative Arts', 'junior_secondary'),
            ('Physical and Health Education', 'junior_secondary'),
            ('Pre-Technical Studies', 'junior_secondary'),
            ('Religious Education', 'junior_secondary')
        ]
        
        for subject_name, education_level in subjects_data:
            cursor.execute("""
                INSERT OR IGNORE INTO subject (name, education_level)
                VALUES (?, ?)
            """, (subject_name, education_level))

        # Insert default teachers
        print("👨‍🏫 Inserting default teachers...")
        teachers_data = [
            ('classteacher1', 'password123', 'classteacher', 1),  # Assigned to Grade 1 Stream A
            ('headteacher', 'admin123', 'headteacher', None),
            ('teacher1', 'teacher123', 'teacher', None)
        ]

        for username, password, role, stream_id in teachers_data:
            cursor.execute("""
                INSERT OR IGNORE INTO teacher (username, password, role, stream_id)
                VALUES (?, ?, ?, ?)
            """, (username, password, role, stream_id))

        # Commit all changes
        conn.commit()
        conn.close()
        
        print("✅ Database initialization completed successfully!")
        print("🎯 You can now use the upload marks functionality.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = init_database()
    if success:
        print("\n🚀 Next steps:")
        print("1. Start the Flask application")
        print("2. Login as classteacher")
        print("3. Try the upload marks functionality")
    else:
        print("\n❌ Database initialization failed!")
