"""
Script to create missing tables in the database.
"""
import sqlite3
import os

def create_missing_tables():
    """Create missing tables in the database."""
    db_path = os.path.join(os.path.dirname(__file__), 'hillview.db')
    
    print(f"Using database at: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the Term table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='term';")
    term_table_exists = cursor.fetchone() is not None
    
    if not term_table_exists:
        print("Creating Term table...")
        cursor.execute("""
        CREATE TABLE term (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL UNIQUE,
            academic_year VARCHAR(20),
            is_current BOOLEAN DEFAULT 0,
            start_date DATE,
            end_date DATE
        );
        """)
        
        # Add some default terms
        print("Adding default terms...")
        cursor.execute("INSERT INTO term (name, academic_year, is_current) VALUES (?, ?, ?)", ("Term 1", "2024", 1))
        cursor.execute("INSERT INTO term (name, academic_year) VALUES (?, ?)", ("Term 2", "2024"))
        cursor.execute("INSERT INTO term (name, academic_year) VALUES (?, ?)", ("Term 3", "2024"))
    
    # Check if the AssessmentType table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assessment_type';")
    assessment_type_table_exists = cursor.fetchone() is not None
    
    if not assessment_type_table_exists:
        print("Creating AssessmentType table...")
        cursor.execute("""
        CREATE TABLE assessment_type (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL UNIQUE,
            weight INTEGER,
            "group" VARCHAR(50),
            show_on_reports BOOLEAN DEFAULT 1
        );
        """)
        
        # Add some default assessment types
        print("Adding default assessment types...")
        cursor.execute("INSERT INTO assessment_type (name, weight) VALUES (?, ?)", ("Mid Term", 30))
        cursor.execute("INSERT INTO assessment_type (name, weight) VALUES (?, ?)", ("End Term", 70))
    
    # Check if the Mark table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mark';")
    mark_table_exists = cursor.fetchone() is not None
    
    if not mark_table_exists:
        print("Creating Mark table...")
        cursor.execute("""
        CREATE TABLE mark (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            term_id INTEGER NOT NULL,
            assessment_type_id INTEGER NOT NULL,
            mark FLOAT NOT NULL,
            total_marks FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student (id),
            FOREIGN KEY (subject_id) REFERENCES subject (id),
            FOREIGN KEY (term_id) REFERENCES term (id),
            FOREIGN KEY (assessment_type_id) REFERENCES assessment_type (id)
        );
        """)
    
    # Commit the changes
    conn.commit()
    
    # Close the connection
    conn.close()
    
    print("Missing tables created successfully!")

if __name__ == "__main__":
    create_missing_tables()
