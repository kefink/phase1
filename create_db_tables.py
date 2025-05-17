"""
Script to create database tables directly using SQLite.
"""
import os
import sqlite3

def create_tables():
    """Create all necessary tables directly using SQLite."""
    # Path to the database
    db_path = os.path.join('new_structure', 'hillview.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database before creation:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Create subject table
    create_subject_table = """
    CREATE TABLE IF NOT EXISTS subject (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        education_level VARCHAR(50) NOT NULL
    );
    """
    cursor.execute(create_subject_table)
    
    # Create grade table
    create_grade_table = """
    CREATE TABLE IF NOT EXISTS grade (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level VARCHAR(50) NOT NULL UNIQUE
    );
    """
    cursor.execute(create_grade_table)
    
    # Create stream table
    create_stream_table = """
    CREATE TABLE IF NOT EXISTS stream (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(10) NOT NULL,
        grade_id INTEGER NOT NULL,
        FOREIGN KEY (grade_id) REFERENCES grade (id)
    );
    """
    cursor.execute(create_stream_table)
    
    # Create teacher table
    create_teacher_table = """
    CREATE TABLE IF NOT EXISTS teacher (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(100) NOT NULL,
        role VARCHAR(50) NOT NULL,
        stream_id INTEGER,
        FOREIGN KEY (stream_id) REFERENCES stream (id)
    );
    """
    cursor.execute(create_teacher_table)
    
    # Create teacher_subjects table
    create_teacher_subjects_table = """
    CREATE TABLE IF NOT EXISTS teacher_subjects (
        teacher_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        PRIMARY KEY (teacher_id, subject_id),
        FOREIGN KEY (teacher_id) REFERENCES teacher (id),
        FOREIGN KEY (subject_id) REFERENCES subject (id)
    );
    """
    cursor.execute(create_teacher_subjects_table)
    
    # Create teacher_subject_assignment table
    create_teacher_subject_assignment_table = """
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
    """
    cursor.execute(create_teacher_subject_assignment_table)
    
    # Commit changes
    conn.commit()
    
    # Get all tables after creation
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("\nTables in database after creation:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Close connection
    conn.close()
    
    print("\nTables created successfully!")

if __name__ == "__main__":
    create_tables()
