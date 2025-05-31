import sqlite3
import os

# Database path
db_path = '../kirima_primary.db'

print("🔧 Creating missing database tables...")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create subject table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject (
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grade (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            education_level TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Created grade table")
    
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
    print("✅ Created stream table")
    
    # Create student table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student (
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
    print("✅ Created term table")
    
    # Create assessment_type table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_type (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            weight REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Created assessment_type table")
    
    # Create marks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marks (
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
    
    # Create teacher_subjects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_subjects (
            teacher_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            PRIMARY KEY (teacher_id, subject_id),
            FOREIGN KEY (teacher_id) REFERENCES teacher (id),
            FOREIGN KEY (subject_id) REFERENCES subject (id)
        )
    """)
    print("✅ Created teacher_subjects table")
    
    # Create teacher_subject_assignment table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_subject_assignment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            grade_id INTEGER NOT NULL,
            stream_id INTEGER NOT NULL,
            is_class_teacher BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES teacher (id),
            FOREIGN KEY (subject_id) REFERENCES subject (id),
            FOREIGN KEY (grade_id) REFERENCES grade (id),
            FOREIGN KEY (stream_id) REFERENCES stream (id)
        )
    """)
    print("✅ Created teacher_subject_assignment table")
    
    # Insert default data
    print("📝 Inserting default data...")
    
    # Insert grades
    grades = [
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
    
    for grade_name, education_level in grades:
        cursor.execute("INSERT OR IGNORE INTO grade (name, education_level) VALUES (?, ?)", 
                      (grade_name, education_level))
    
    # Insert streams
    cursor.execute("SELECT id, name FROM grade")
    grade_records = cursor.fetchall()
    
    for grade_id, grade_name in grade_records:
        cursor.execute("INSERT OR IGNORE INTO stream (name, grade_id) VALUES (?, ?)", ('A', grade_id))
        cursor.execute("INSERT OR IGNORE INTO stream (name, grade_id) VALUES (?, ?)", ('B', grade_id))
    
    # Insert subjects
    subjects = [
        ('English', 'lower_primary'),
        ('Kiswahili', 'lower_primary'),
        ('Mathematics', 'lower_primary'),
        ('Environmental Activities', 'lower_primary'),
        ('Creative Arts', 'lower_primary'),
        ('Physical Education', 'lower_primary'),
        ('English', 'upper_primary'),
        ('Kiswahili', 'upper_primary'),
        ('Mathematics', 'upper_primary'),
        ('Science', 'upper_primary'),
        ('Social Studies', 'upper_primary'),
        ('Creative Arts', 'upper_primary'),
        ('Physical Education', 'upper_primary'),
        ('English', 'junior_secondary'),
        ('Kiswahili', 'junior_secondary'),
        ('Mathematics', 'junior_secondary'),
        ('Biology', 'junior_secondary'),
        ('Chemistry', 'junior_secondary'),
        ('Physics', 'junior_secondary'),
        ('Geography', 'junior_secondary'),
        ('History', 'junior_secondary'),
        ('Religious Education', 'junior_secondary'),
        ('Physical Education', 'junior_secondary')
    ]
    
    for subject_name, education_level in subjects:
        cursor.execute("""
            INSERT OR IGNORE INTO subject (name, education_level, is_standard, is_composite)
            VALUES (?, ?, 1, 0)
        """, (subject_name, education_level))
    
    # Insert terms
    cursor.execute("INSERT OR IGNORE INTO term (name, academic_year, is_current) VALUES (?, ?, ?)", 
                  ('Term 1', '2024', 1))
    cursor.execute("INSERT OR IGNORE INTO term (name, academic_year, is_current) VALUES (?, ?, ?)", 
                  ('Term 2', '2024', 0))
    cursor.execute("INSERT OR IGNORE INTO term (name, academic_year, is_current) VALUES (?, ?, ?)", 
                  ('Term 3', '2024', 0))
    
    # Insert assessment types
    cursor.execute("INSERT OR IGNORE INTO assessment_type (name, description) VALUES (?, ?)", 
                  ('End of Term Exam', 'Final examination for the term'))
    cursor.execute("INSERT OR IGNORE INTO assessment_type (name, description) VALUES (?, ?)", 
                  ('Mid Term Test', 'Mid-term assessment'))
    cursor.execute("INSERT OR IGNORE INTO assessment_type (name, description) VALUES (?, ?)", 
                  ('Continuous Assessment', 'Ongoing classroom assessment'))
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]
    print(f"📋 Tables in database: {tables}")
    
    # Check counts
    for table in ['subject', 'grade', 'stream', 'term', 'assessment_type']:
        if table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} records")
    
    conn.close()
    print("🎉 Database setup completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
