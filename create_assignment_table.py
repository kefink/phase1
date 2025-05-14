"""
Migration script to create the teacher_subject_assignment table.
This script creates the table directly using SQL commands.
"""
import sqlite3
import os

# Get the database path
db_path = os.path.join('new_structure', 'hillview.db')

# SQL to create the teacher_subject_assignment table
create_table_sql = '''
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
'''

def create_table():
    """Create the teacher_subject_assignment table."""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create the table
        cursor.execute(create_table_sql)
        
        # Commit the changes
        conn.commit()
        
        print("TeacherSubjectAssignment table created successfully!")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    create_table()
