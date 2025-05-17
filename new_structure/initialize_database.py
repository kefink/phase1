"""
Script to initialize the database with all necessary tables for the new structure.
"""
import os
import sqlite3
import sys

def initialize_database():
    """Initialize the database with all necessary tables."""
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'kirima_primary.db')

    print(f"Using database at: {db_path}")

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create Teacher table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teacher (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        stream_id INTEGER,
        FOREIGN KEY (stream_id) REFERENCES stream (id)
    );
    """)

    # Create Subject table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subject (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        education_level TEXT NOT NULL
    );
    """)

    # Create Grade table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grade (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT NOT NULL UNIQUE
    );
    """)

    # Create Stream table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stream (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        grade_id INTEGER NOT NULL,
        FOREIGN KEY (grade_id) REFERENCES grade (id)
    );
    """)

    # Create Term table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS term (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        academic_year TEXT,
        is_current BOOLEAN DEFAULT 0,
        start_date DATE,
        end_date DATE
    );
    """)

    # Create AssessmentType table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assessment_type (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        weight INTEGER,
        group_name TEXT,
        show_on_reports BOOLEAN DEFAULT 1
    );
    """)

    # Create Student table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        admission_number TEXT NOT NULL UNIQUE,
        stream_id INTEGER,
        gender TEXT NOT NULL DEFAULT 'Unknown',
        FOREIGN KEY (stream_id) REFERENCES stream (id)
    );
    """)

    # Create Mark table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mark (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        term_id INTEGER NOT NULL,
        assessment_type_id INTEGER NOT NULL,
        mark FLOAT NOT NULL,
        total_marks FLOAT NOT NULL,
        percentage FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES student (id),
        FOREIGN KEY (subject_id) REFERENCES subject (id),
        FOREIGN KEY (term_id) REFERENCES term (id),
        FOREIGN KEY (assessment_type_id) REFERENCES assessment_type (id)
    );
    """)

    # Create teacher_subjects association table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teacher_subjects (
        teacher_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        PRIMARY KEY (teacher_id, subject_id),
        FOREIGN KEY (teacher_id) REFERENCES teacher (id),
        FOREIGN KEY (subject_id) REFERENCES subject (id)
    );
    """)

    # Create TeacherSubjectAssignment table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teacher_subject_assignment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        grade_id INTEGER NOT NULL,
        stream_id INTEGER,
        is_class_teacher BOOLEAN DEFAULT 0,
        FOREIGN KEY (teacher_id) REFERENCES teacher (id),
        FOREIGN KEY (subject_id) REFERENCES subject (id),
        FOREIGN KEY (grade_id) REFERENCES grade (id),
        FOREIGN KEY (stream_id) REFERENCES stream (id)
    );
    """)

    # Commit the changes
    conn.commit()

    # Check if we need to add sample data
    if len(sys.argv) > 1 and sys.argv[1] == '--with-sample-data':
        add_sample_data(cursor, conn)

    # Close the connection
    conn.close()

    print("Database initialized successfully.")

def add_sample_data(cursor, conn):
    """Add sample data to the database."""
    print("Adding sample data...")

    # Add sample teacher (Kevin)
    cursor.execute("SELECT id FROM teacher WHERE username = 'kevin'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO teacher (username, password, role) VALUES ('kevin', 'kev123', 'classteacher')
        """)

    # Add sample grades
    grades = ['Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5', 'Grade 6', 'Grade 7', 'Grade 8']
    for grade in grades:
        cursor.execute("SELECT id FROM grade WHERE level = ?", (grade,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO grade (level) VALUES (?)", (grade,))

    # Add sample streams
    streams = [('A', 1), ('B', 1), ('A', 2), ('B', 2), ('A', 3), ('B', 3)]
    for name, grade_id in streams:
        cursor.execute("SELECT id FROM stream WHERE name = ? AND grade_id = ?", (name, grade_id))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO stream (name, grade_id) VALUES (?, ?)", (name, grade_id))

    # Add sample terms
    terms = ['Term 1', 'Term 2', 'Term 3']
    for term in terms:
        cursor.execute("SELECT id FROM term WHERE name = ?", (term,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO term (name, academic_year, is_current) VALUES (?, '2023', ?)",
                          (term, 1 if term == 'Term 1' else 0))

    # Add sample assessment types
    assessment_types = ['Mid Term', 'End Term']
    for assessment_type in assessment_types:
        cursor.execute("SELECT id FROM assessment_type WHERE name = ?", (assessment_type,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO assessment_type (name, weight, show_on_reports) VALUES (?, 50, 1)",
                          (assessment_type,))

    # Add sample subjects
    subjects = [
        ('Mathematics', 'upper_primary'),
        ('English', 'upper_primary'),
        ('Kiswahili', 'upper_primary'),
        ('Science', 'upper_primary'),
        ('Social Studies', 'upper_primary'),
        ('Mathematics', 'junior_secondary'),
        ('English', 'junior_secondary'),
        ('Kiswahili', 'junior_secondary'),
        ('Science', 'junior_secondary'),
        ('Social Studies', 'junior_secondary')
    ]
    for name, education_level in subjects:
        cursor.execute("SELECT id FROM subject WHERE name = ? AND education_level = ?", (name, education_level))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO subject (name, education_level) VALUES (?, ?)", (name, education_level))

    # Add sample students
    # First, get the stream IDs
    cursor.execute("SELECT id FROM stream WHERE name = 'A' AND grade_id = 1")
    result = cursor.fetchone()
    stream_id_1a = result[0] if result else None

    cursor.execute("SELECT id FROM stream WHERE name = 'B' AND grade_id = 1")
    result = cursor.fetchone()
    stream_id_1b = result[0] if result else None

    # If we have valid stream IDs, add students
    if stream_id_1a:
        students = [
            ('John Doe', 'JD001', stream_id_1a, 'Male'),
            ('Jane Smith', 'JS002', stream_id_1a, 'Female'),
            ('Bob Johnson', 'BJ003', stream_id_1a, 'Male'),
            ('Alice Brown', 'AB004', stream_id_1a, 'Female'),
            ('Charlie Davis', 'CD005', stream_id_1a, 'Male')
        ]
        for name, admission_number, stream_id, gender in students:
            cursor.execute("SELECT id FROM student WHERE admission_number = ?", (admission_number,))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO student (name, admission_number, stream_id, gender)
                VALUES (?, ?, ?, ?)
                """, (name, admission_number, stream_id, gender))

    if stream_id_1b:
        students = [
            ('David Wilson', 'DW006', stream_id_1b, 'Male'),
            ('Emma Taylor', 'ET007', stream_id_1b, 'Female'),
            ('Frank Miller', 'FM008', stream_id_1b, 'Male'),
            ('Grace Lee', 'GL009', stream_id_1b, 'Female'),
            ('Henry Clark', 'HC010', stream_id_1b, 'Male')
        ]
        for name, admission_number, stream_id, gender in students:
            cursor.execute("SELECT id FROM student WHERE admission_number = ?", (admission_number,))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO student (name, admission_number, stream_id, gender)
                VALUES (?, ?, ?, ?)
                """, (name, admission_number, stream_id, gender))

    # Commit the changes
    conn.commit()
    print("Sample data added successfully.")

if __name__ == "__main__":
    initialize_database()
