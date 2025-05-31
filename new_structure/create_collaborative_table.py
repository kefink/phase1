#!/usr/bin/env python3
"""
Simple script to create the SubjectMarksStatus table.
"""
import sqlite3
import os

def create_table():
    """Create the SubjectMarksStatus table directly in SQLite."""

    # Database path
    db_path = '../hillview.db'

    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS subject_marks_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade_id INTEGER NOT NULL,
            stream_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            term_id INTEGER NOT NULL,
            assessment_type_id INTEGER NOT NULL,
            is_uploaded BOOLEAN DEFAULT 0,
            uploaded_by_teacher_id INTEGER,
            upload_date DATETIME,
            last_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_students INTEGER DEFAULT 0,
            students_with_marks INTEGER DEFAULT 0,
            completion_percentage REAL DEFAULT 0.0,
            FOREIGN KEY (grade_id) REFERENCES grade (id),
            FOREIGN KEY (stream_id) REFERENCES stream (id),
            FOREIGN KEY (subject_id) REFERENCES subject (id),
            FOREIGN KEY (term_id) REFERENCES term (id),
            FOREIGN KEY (assessment_type_id) REFERENCES assessment_type (id),
            FOREIGN KEY (uploaded_by_teacher_id) REFERENCES teacher (id)
        );
        """

        cursor.execute(create_table_sql)

        # Create index for better performance
        index_sql = """
        CREATE INDEX IF NOT EXISTS idx_subject_marks_status_lookup
        ON subject_marks_status (grade_id, stream_id, subject_id, term_id, assessment_type_id);
        """

        cursor.execute(index_sql)

        # Commit changes
        conn.commit()

        # Verify table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subject_marks_status';")
        result = cursor.fetchone()

        if result:
            print("✅ SubjectMarksStatus table created successfully!")

            # Show table structure
            cursor.execute("PRAGMA table_info(subject_marks_status);")
            columns = cursor.fetchall()
            print("\n📋 Table structure:")
            for column in columns:
                print(f"  - {column[1]}: {column[2]}")
        else:
            print("❌ Failed to create SubjectMarksStatus table")

        # Close connection
        conn.close()

    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")

if __name__ == "__main__":
    print("🚀 Creating SubjectMarksStatus table...")
    create_table()
    print("✅ Done!")
