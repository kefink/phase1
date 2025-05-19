"""
Script to add composite subject functionality to the database.
This adds tables for subject components and component marks.
"""
import os
import sys
import sqlite3
from datetime import datetime

# Log file setup
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"composite_subjects_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

def log_message(message):
    """Log a message to both console and log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    try:
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")

def execute_query(conn, query, params=None):
    """Execute a query and log it."""
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return True
    except sqlite3.Error as e:
        log_message(f"Error executing query: {e}")
        log_message(f"Query: {query}")
        if params:
            log_message(f"Params: {params}")
        conn.rollback()
        return False

def create_subject_components_table(conn):
    """Create the subject_components table."""
    query = """
    CREATE TABLE IF NOT EXISTS subject_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        name VARCHAR(100) NOT NULL,
        weight FLOAT DEFAULT 1.0,
        max_raw_mark INTEGER DEFAULT 100,
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    );
    """
    return execute_query(conn, query)

def create_component_marks_table(conn):
    """Create the component_marks table."""
    query = """
    CREATE TABLE IF NOT EXISTS component_marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mark_id INTEGER NOT NULL,
        component_id INTEGER NOT NULL,
        raw_mark FLOAT NOT NULL,
        max_raw_mark INTEGER DEFAULT 100,
        percentage FLOAT,
        FOREIGN KEY (mark_id) REFERENCES marks(id),
        FOREIGN KEY (component_id) REFERENCES subject_components(id)
    );
    """
    return execute_query(conn, query)

def add_is_standard_column(conn):
    """Add is_standard column to subjects table."""
    # Check if the column already exists
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(subjects)")
    columns = [column[1] for column in cursor.fetchall()]

    if "is_standard" not in columns:
        query = "ALTER TABLE subjects ADD COLUMN is_standard BOOLEAN DEFAULT 1;"
        return execute_query(conn, query)
    else:
        log_message("Column 'is_standard' already exists in subjects table")
        return True

def add_is_composite_column(conn):
    """Add is_composite column to subjects table."""
    # Check if the column already exists
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(subjects)")
    columns = [column[1] for column in cursor.fetchall()]

    if "is_composite" not in columns:
        query = "ALTER TABLE subjects ADD COLUMN is_composite BOOLEAN DEFAULT 0;"
        return execute_query(conn, query)
    else:
        log_message("Column 'is_composite' already exists in subjects table")
        return True

def setup_english_components(conn):
    """Set up English subject as composite with Grammar and Composition components."""
    # First, find the English subject
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM subjects WHERE name = 'ENGLISH'")
    result = cursor.fetchone()

    if not result:
        log_message("English subject not found")
        return False

    english_id = result[0]

    # Mark English as composite
    execute_query(conn, "UPDATE subjects SET is_composite = 1 WHERE id = ?", (english_id,))

    # Check if components already exist
    cursor.execute("SELECT id FROM subject_components WHERE subject_id = ?", (english_id,))
    if cursor.fetchone():
        log_message("English components already exist")
        return True

    # Add Grammar component (60%)
    execute_query(conn,
                 "INSERT INTO subject_components (subject_id, name, weight, max_raw_mark) VALUES (?, ?, ?, ?)",
                 (english_id, "Grammar", 0.6, 60))

    # Add Composition component (40%)
    execute_query(conn,
                 "INSERT INTO subject_components (subject_id, name, weight, max_raw_mark) VALUES (?, ?, ?, ?)",
                 (english_id, "Composition", 0.4, 40))

    log_message("English components added successfully")
    return True

def setup_kiswahili_components(conn):
    """Set up Kiswahili subject as composite with Lugha and Insha components."""
    # First, find the Kiswahili subject
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM subjects WHERE name = 'KISWAHILI'")
    result = cursor.fetchone()

    if not result:
        log_message("Kiswahili subject not found")
        return False

    kiswahili_id = result[0]

    # Mark Kiswahili as composite
    execute_query(conn, "UPDATE subjects SET is_composite = 1 WHERE id = ?", (kiswahili_id,))

    # Check if components already exist
    cursor.execute("SELECT id FROM subject_components WHERE subject_id = ?", (kiswahili_id,))
    if cursor.fetchone():
        log_message("Kiswahili components already exist")
        return True

    # Add Lugha component (60%)
    execute_query(conn,
                 "INSERT INTO subject_components (subject_id, name, weight, max_raw_mark) VALUES (?, ?, ?, ?)",
                 (kiswahili_id, "Lugha", 0.6, 60))

    # Add Insha component (40%)
    execute_query(conn,
                 "INSERT INTO subject_components (subject_id, name, weight, max_raw_mark) VALUES (?, ?, ?, ?)",
                 (kiswahili_id, "Insha", 0.4, 40))

    log_message("Kiswahili components added successfully")
    return True

def add_additional_subjects(conn):
    """Add additional subjects like Computer, French, Chinese, Mandarin, and German."""
    additional_subjects = [
        ("COMPUTER STUDIES", "junior_secondary", 0),
        ("FRENCH", "junior_secondary", 0),
        ("CHINESE", "junior_secondary", 0),
        ("MANDARIN", "junior_secondary", 0),
        ("GERMAN", "junior_secondary", 0)
    ]

    for subject_name, education_level, is_standard in additional_subjects:
        # Check if subject already exists
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
        if cursor.fetchone():
            log_message(f"Subject {subject_name} already exists")
            # Update is_standard flag
            execute_query(conn, "UPDATE subjects SET is_standard = ? WHERE name = ?", (is_standard, subject_name))
        else:
            # Add new subject
            execute_query(conn,
                         "INSERT INTO subjects (name, education_level, is_standard) VALUES (?, ?, ?)",
                         (subject_name, education_level, is_standard))
            log_message(f"Added subject: {subject_name}")

    return True

def main():
    """Main function to run the script."""
    print("Starting composite subjects database update")

    # Connect to the database
    try:
        print("Attempting to connect to database...")
        conn = sqlite3.connect("kirima_primary.db")
        print("Connected to database")
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return

    try:
        # Check if tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subject_components';")
        if cursor.fetchone():
            print("subject_components table already exists")
        else:
            # Create new tables
            if create_subject_components_table(conn):
                print("Created subject_components table")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='component_marks';")
        if cursor.fetchone():
            print("component_marks table already exists")
        else:
            if create_component_marks_table(conn):
                print("Created component_marks table")

        # Check if the table is called 'subject' (singular)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subject';")
        if cursor.fetchone():
            print("Found table 'subject' instead of 'subjects'")

            # Add columns to existing tables
            cursor.execute("PRAGMA table_info(subject)")
            columns = [column[1] for column in cursor.fetchall()]

            if "is_standard" not in columns:
                print("Adding is_standard column to subject table")
                cursor.execute("ALTER TABLE subject ADD COLUMN is_standard BOOLEAN DEFAULT 1;")
                conn.commit()
                print("Added is_standard column to subject table")
            else:
                print("Column 'is_standard' already exists in subject table")

            if "is_composite" not in columns:
                print("Adding is_composite column to subject table")
                cursor.execute("ALTER TABLE subject ADD COLUMN is_composite BOOLEAN DEFAULT 0;")
                conn.commit()
                print("Added is_composite column to subject table")
            else:
                print("Column 'is_composite' already exists in subject table")

            # Set up composite subjects
            cursor.execute("SELECT id FROM subject WHERE name = 'ENGLISH'")
            result = cursor.fetchone()

            if result:
                english_id = result[0]
                print(f"Found English subject with ID: {english_id}")

                # Mark English as composite
                cursor.execute("UPDATE subject SET is_composite = 1 WHERE id = ?", (english_id,))
                conn.commit()

                # Check if components already exist
                cursor.execute("SELECT id FROM subject_components WHERE subject_id = ?", (english_id,))
                if cursor.fetchone():
                    print("English components already exist")
                else:
                    # Add Grammar component (60%)
                    cursor.execute(
                        "INSERT INTO subject_components (subject_id, name, weight, max_raw_mark) VALUES (?, ?, ?, ?)",
                        (english_id, "Grammar", 0.6, 60))

                    # Add Composition component (40%)
                    cursor.execute(
                        "INSERT INTO subject_components (subject_id, name, weight, max_raw_mark) VALUES (?, ?, ?, ?)",
                        (english_id, "Composition", 0.4, 40))

                    conn.commit()
                    print("English components added successfully")
            else:
                print("English subject not found")

            # Set up Kiswahili components
            cursor.execute("SELECT id FROM subject WHERE name = 'KISWAHILI'")
            result = cursor.fetchone()

            if result:
                kiswahili_id = result[0]
                print(f"Found Kiswahili subject with ID: {kiswahili_id}")

                # Mark Kiswahili as composite
                cursor.execute("UPDATE subject SET is_composite = 1 WHERE id = ?", (kiswahili_id,))
                conn.commit()

                # Check if components already exist
                cursor.execute("SELECT id FROM subject_components WHERE subject_id = ?", (kiswahili_id,))
                if cursor.fetchone():
                    print("Kiswahili components already exist")
                else:
                    # Add Lugha component (60%)
                    cursor.execute(
                        "INSERT INTO subject_components (subject_id, name, weight, max_raw_mark) VALUES (?, ?, ?, ?)",
                        (kiswahili_id, "Lugha", 0.6, 60))

                    # Add Insha component (40%)
                    cursor.execute(
                        "INSERT INTO subject_components (subject_id, name, weight, max_raw_mark) VALUES (?, ?, ?, ?)",
                        (kiswahili_id, "Insha", 0.4, 40))

                    conn.commit()
                    print("Kiswahili components added successfully")
            else:
                print("Kiswahili subject not found")

            # Add additional subjects
            additional_subjects = [
                ("COMPUTER STUDIES", "junior_secondary", 0),
                ("FRENCH", "junior_secondary", 0),
                ("CHINESE", "junior_secondary", 0),
                ("MANDARIN", "junior_secondary", 0),
                ("GERMAN", "junior_secondary", 0)
            ]

            for subject_name, education_level, is_standard in additional_subjects:
                # Check if subject already exists
                cursor.execute("SELECT id FROM subject WHERE name = ?", (subject_name,))
                if cursor.fetchone():
                    print(f"Subject {subject_name} already exists")
                    # Update is_standard flag
                    cursor.execute("UPDATE subject SET is_standard = ? WHERE name = ?", (is_standard, subject_name))
                    conn.commit()
                else:
                    # Add new subject
                    cursor.execute(
                        "INSERT INTO subject (name, education_level, is_standard) VALUES (?, ?, ?)",
                        (subject_name, education_level, is_standard))
                    conn.commit()
                    print(f"Added subject: {subject_name}")

        print("Database update completed successfully")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("Database connection closed")

if __name__ == "__main__":
    main()
