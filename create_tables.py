"""
Script to create all necessary tables for the new structure.
"""
import os
import sqlite3
from new_structure import create_app
from new_structure.extensions import db
from new_structure.models.academic import Subject, Grade, Stream, Term, AssessmentType, Student, Mark
from new_structure.models.user import Teacher, teacher_subjects
from new_structure.models.assignment import TeacherSubjectAssignment

def create_tables():
    """Create all necessary tables."""
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        print("All tables created successfully!")

        # Verify tables were created
        db_path = os.path.join('new_structure', 'hillview.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"- {table[0]}")

        # Create specific tables if they don't exist
        create_subject_table = """
        CREATE TABLE IF NOT EXISTS subject (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            education_level VARCHAR(50) NOT NULL
        );
        """
        cursor.execute(create_subject_table)

        create_grade_table = """
        CREATE TABLE IF NOT EXISTS grade (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level VARCHAR(50) NOT NULL UNIQUE
        );
        """
        cursor.execute(create_grade_table)

        create_stream_table = """
        CREATE TABLE IF NOT EXISTS stream (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(10) NOT NULL,
            grade_id INTEGER NOT NULL,
            FOREIGN KEY (grade_id) REFERENCES grade (id)
        );
        """
        cursor.execute(create_stream_table)

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

        conn.commit()
        conn.close()

        print("Tables created successfully using direct SQL!")

if __name__ == "__main__":
    create_tables()
