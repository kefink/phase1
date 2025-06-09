#!/usr/bin/env python3
"""
Enhanced database initialization script with comprehensive sample data
for showcasing the analytics features.
"""
import sqlite3
import os
import random
from datetime import datetime

def create_comprehensive_database():
    """Create a comprehensive database with realistic sample data."""
    db_path = 'kirima_primary.db'
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Removed existing database: {db_path}")
    
    print(f"🔧 Creating comprehensive database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        print("📋 Creating tables...")
        
        # Create all tables
        create_tables(cursor)
        
        print("📚 Inserting comprehensive sample data...")
        
        # Insert sample data
        insert_grades_and_streams(cursor)
        insert_subjects(cursor)
        insert_terms_and_assessments(cursor)
        insert_teachers(cursor)
        insert_students(cursor)
        insert_marks(cursor)
        
        # Commit all changes
        conn.commit()
        
        # Print summary
        print_database_summary(cursor)
        
        conn.close()
        
        print("✅ Comprehensive database created successfully!")
        print("🎯 Analytics features are now ready to showcase!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_tables(cursor):
    """Create all necessary tables."""
    
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
            name TEXT NOT NULL UNIQUE,
            education_level TEXT NOT NULL,
            is_composite BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Term table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS term (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            academic_year TEXT NOT NULL,
            is_current BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Assessment type table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_type (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            weight REAL NOT NULL,
            category TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Teacher table
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

def insert_grades_and_streams(cursor):
    """Insert grades and streams."""
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
            INSERT INTO grade (name, education_level) 
            VALUES (?, ?)
        """, (grade_name, education_level))
    
    # Insert streams for each grade
    cursor.execute("SELECT id, name FROM grade")
    grade_records = cursor.fetchall()
    
    for grade_id, grade_name in grade_records:
        # Create streams A and B for each grade
        cursor.execute("""
            INSERT INTO stream (name, grade_id) 
            VALUES (?, ?)
        """, ('A', grade_id))
        cursor.execute("""
            INSERT INTO stream (name, grade_id) 
            VALUES (?, ?)
        """, ('B', grade_id))

def insert_subjects(cursor):
    """Insert comprehensive subject list."""
    subjects_data = [
        ('MATHEMATICS', 'all'),
        ('ENGLISH', 'all'),
        ('KISWAHILI', 'all'),
        ('INTEGRATED SCIENCE', 'all'),
        ('SOCIAL STUDIES', 'all'),
        ('RELIGIOUS EDUCATION', 'all'),
        ('CREATIVE ARTS', 'all'),
        ('PHYSICAL EDUCATION', 'all'),
        ('LIFE SKILLS', 'all'),
        ('AGRICULTURE', 'upper_primary'),
        ('HOME SCIENCE', 'upper_primary'),
        ('BUSINESS STUDIES', 'junior_secondary'),
        ('COMPUTER SCIENCE', 'junior_secondary')
    ]
    
    for subject_name, education_level in subjects_data:
        cursor.execute("""
            INSERT INTO subject (name, education_level) 
            VALUES (?, ?)
        """, (subject_name, education_level))

def insert_terms_and_assessments(cursor):
    """Insert terms and assessment types."""
    # Terms
    terms_data = [
        ('Term 1', '2024', 1),
        ('Term 2', '2024', 0),
        ('Term 3', '2024', 0)
    ]
    
    for term_name, academic_year, is_current in terms_data:
        cursor.execute("""
            INSERT INTO term (name, academic_year, is_current) 
            VALUES (?, ?, ?)
        """, (term_name, academic_year, is_current))
    
    # Assessment types
    assessment_types_data = [
        ('Mid Term', 30, 'Exams', 1),
        ('End Term', 70, 'Exams', 1),
        ('Assignment', 0, 'Continuous Assessment', 1)
    ]
    
    for name, weight, category, is_active in assessment_types_data:
        cursor.execute("""
            INSERT INTO assessment_type (name, weight, category, is_active) 
            VALUES (?, ?, ?, ?)
        """, (name, weight, category, is_active))

def insert_teachers(cursor):
    """Insert sample teachers."""
    # Get stream IDs for class teacher assignments
    cursor.execute("SELECT id FROM stream LIMIT 5")
    stream_ids = [row[0] for row in cursor.fetchall()]
    
    teachers_data = [
        ('headteacher', 'admin123', 'headteacher', None, 'Dr. Sarah', 'Mwangi'),
        ('classteacher1', 'password123', 'classteacher', stream_ids[0] if stream_ids else None, 'John', 'Kamau'),
        ('classteacher2', 'password123', 'classteacher', stream_ids[1] if len(stream_ids) > 1 else None, 'Mary', 'Wanjiku'),
        ('classteacher3', 'password123', 'classteacher', stream_ids[2] if len(stream_ids) > 2 else None, 'Peter', 'Ochieng'),
        ('teacher1', 'teacher123', 'teacher', None, 'Grace', 'Nyong'),
        ('teacher2', 'teacher123', 'teacher', None, 'David', 'Kiprop')
    ]

    for username, password, role, stream_id, first_name, last_name in teachers_data:
        cursor.execute("""
            INSERT INTO teacher (username, password, role, stream_id, first_name, last_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, password, role, stream_id, first_name, last_name))

def insert_students(cursor):
    """Insert diverse student population."""
    # Get all streams with their grade info
    cursor.execute("""
        SELECT s.id, s.name as stream_name, g.id as grade_id, g.name as grade_name
        FROM stream s
        JOIN grade g ON s.grade_id = g.id
    """)
    streams = cursor.fetchall()

    # Kenyan student names for realism
    first_names = [
        'Adrian', 'Abby', 'Alvin', 'Beatrice', 'Brian', 'Catherine', 'David', 'Diana',
        'Emmanuel', 'Faith', 'Grace', 'Henry', 'Irene', 'James', 'Joyce', 'Kevin',
        'Linda', 'Mark', 'Nancy', 'Oscar', 'Patricia', 'Robert', 'Sarah', 'Timothy',
        'Violet', 'William', 'Zipporah', 'Collins', 'Mercy', 'Joseph', 'Ruth', 'Daniel',
        'Esther', 'Francis', 'Hannah', 'Isaac', 'Jane', 'Kennedy', 'Lucy', 'Michael',
        'Naomi', 'Paul', 'Rachel', 'Samuel', 'Tabitha', 'Victor', 'Winnie', 'Xavier'
    ]

    last_names = [
        'Mwangi', 'Kamau', 'Wanjiku', 'Ochieng', 'Nyong', 'Kiprop', 'Mbau', 'Tatyana',
        'Mukabi', 'Ndoro', 'Kiprotich', 'Wambui', 'Macharia', 'Otieno', 'Maina',
        'Njoroge', 'Kariuki', 'Mutua', 'Kimani', 'Wairimu', 'Githui', 'Muthoni',
        'Karanja', 'Waweru', 'Kibet', 'Cheruiyot', 'Rotich', 'Langat', 'Koech'
    ]

    genders = ['Male', 'Female']
    student_id = 1

    # Create 6-8 students per stream for realistic class sizes
    for stream_id, stream_name, grade_id, grade_name in streams:
        num_students = random.randint(6, 8)

        for i in range(num_students):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            full_name = f"{first_name} {last_name}"

            # Create realistic admission numbers
            grade_num = grade_name.split()[-1]  # Extract number from "Grade X"
            admission_number = f"HSK{grade_num}{stream_name}{student_id:03d}"

            gender = random.choice(genders)

            cursor.execute("""
                INSERT INTO student (name, admission_number, stream_id, grade_id, gender)
                VALUES (?, ?, ?, ?, ?)
            """, (full_name, admission_number, stream_id, grade_id, gender))

            student_id += 1

def insert_marks(cursor):
    """Insert realistic marks data with varied performance levels."""
    # Get all students
    cursor.execute("SELECT id, grade_id FROM student")
    students = cursor.fetchall()

    # Get subjects appropriate for each education level
    cursor.execute("SELECT id, name, education_level FROM subject")
    all_subjects = cursor.fetchall()

    # Get terms and assessment types
    cursor.execute("SELECT id FROM term WHERE is_current = 1")
    current_term_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM assessment_type WHERE name = 'End Term'")
    assessment_type_id = cursor.fetchone()[0]

    # Grade level mapping
    grade_levels = {
        1: 'lower_primary', 2: 'lower_primary', 3: 'lower_primary',
        4: 'upper_primary', 5: 'upper_primary', 6: 'upper_primary',
        7: 'junior_secondary', 8: 'junior_secondary', 9: 'junior_secondary'
    }

    print(f"📊 Generating marks for {len(students)} students...")

    for student_id, grade_id in students:
        grade_level = grade_levels.get(grade_id, 'all')

        # Get subjects for this grade level
        applicable_subjects = [
            (subj_id, subj_name) for subj_id, subj_name, edu_level in all_subjects
            if edu_level == 'all' or edu_level == grade_level
        ]

        # Create performance profile for student (some excel, some struggle)
        performance_type = random.choices(
            ['excellent', 'good', 'average', 'struggling'],
            weights=[15, 25, 40, 20]  # Realistic distribution
        )[0]

        for subject_id, subject_name in applicable_subjects:
            # Generate marks based on performance type
            raw_marks, total_marks = generate_realistic_marks(performance_type, subject_name)
            percentage = round((raw_marks / total_marks) * 100, 2)
            grade_letter = get_cbc_grade(percentage)

            cursor.execute("""
                INSERT INTO mark (
                    student_id, subject_id, term_id, assessment_type_id,
                    mark, total_marks, raw_mark, raw_total_marks, percentage, grade_letter
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student_id, subject_id, current_term_id, assessment_type_id,
                percentage, 100, raw_marks, total_marks, percentage, grade_letter
            ))

def generate_realistic_marks(performance_type, subject_name):
    """Generate realistic marks based on student performance type and subject."""
    total_marks = 100

    # Subject difficulty factors
    subject_factors = {
        'MATHEMATICS': 0.85,  # Generally challenging
        'ENGLISH': 0.90,
        'INTEGRATED SCIENCE': 0.85,
        'KISWAHILI': 0.92,
        'SOCIAL STUDIES': 0.95,
        'RELIGIOUS EDUCATION': 0.98,
        'CREATIVE ARTS': 0.95,
        'PHYSICAL EDUCATION': 0.98,
        'LIFE SKILLS': 0.96
    }

    base_factor = subject_factors.get(subject_name, 0.90)

    # Performance type base ranges
    if performance_type == 'excellent':
        base_range = (85, 98)
    elif performance_type == 'good':
        base_range = (70, 85)
    elif performance_type == 'average':
        base_range = (50, 70)
    else:  # struggling
        base_range = (25, 50)

    # Apply subject difficulty and add randomness
    min_mark = max(10, int(base_range[0] * base_factor))
    max_mark = min(100, int(base_range[1] * base_factor))

    raw_marks = random.randint(min_mark, max_mark)
    return raw_marks, total_marks

def get_cbc_grade(percentage):
    """Get CBC grade letter based on percentage."""
    if percentage >= 90:
        return 'EE1'
    elif percentage >= 75:
        return 'EE2'
    elif percentage >= 58:
        return 'ME1'
    elif percentage >= 41:
        return 'ME2'
    elif percentage >= 31:
        return 'AE1'
    elif percentage >= 21:
        return 'AE2'
    elif percentage >= 11:
        return 'BE1'
    else:
        return 'BE2'

def print_database_summary(cursor):
    """Print a summary of the created database."""
    print("\n" + "="*50)
    print("📊 DATABASE SUMMARY")
    print("="*50)

    tables = [
        ('Students', 'student'),
        ('Marks', 'mark'),
        ('Grades', 'grade'),
        ('Streams', 'stream'),
        ('Subjects', 'subject'),
        ('Teachers', 'teacher'),
        ('Terms', 'term'),
        ('Assessment Types', 'assessment_type')
    ]

    for name, table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{name:15}: {count:4d}")

    # Show sample performance distribution
    print("\n📈 PERFORMANCE DISTRIBUTION:")
    cursor.execute("""
        SELECT grade_letter, COUNT(*) as count
        FROM mark
        GROUP BY grade_letter
        ORDER BY grade_letter
    """)

    for grade, count in cursor.fetchall():
        print(f"{grade:3}: {count:3d} marks")

    print("\n🎯 Ready for analytics showcase!")

if __name__ == '__main__':
    success = create_comprehensive_database()
    if success:
        print("\n🚀 Next steps:")
        print("1. Start the Flask application")
        print("2. Login as headteacher (username: headteacher, password: admin123)")
        print("3. Navigate to Analytics Dashboard")
        print("4. Explore the enhanced analytics features!")
    else:
        print("\n❌ Database creation failed!")
