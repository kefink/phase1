"""
Test script to check if composite subjects are working correctly.
"""
import sqlite3
import sys
import os

def test_composite_subjects():
    """Test if composite subjects are set up correctly in the database."""
    conn = sqlite3.connect('kirima_primary.db')
    cursor = conn.cursor()

    # Check if subject table has is_composite column
    cursor.execute("PRAGMA table_info(subject)")
    columns = cursor.fetchall()
    has_is_composite = any(col[1] == 'is_composite' for col in columns)
    
    print(f"Subject table has is_composite column: {has_is_composite}")
    
    if not has_is_composite:
        print("Adding is_composite column to subject table...")
        cursor.execute("ALTER TABLE subject ADD COLUMN is_composite BOOLEAN DEFAULT 0")
        conn.commit()

    # Check if subject_component table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subject_component'")
    subject_component_exists = cursor.fetchone() is not None
    
    print(f"subject_component table exists: {subject_component_exists}")
    
    if not subject_component_exists:
        print("Creating subject_component table...")
        cursor.execute('''
        CREATE TABLE subject_component (
            id INTEGER PRIMARY KEY,
            subject_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            max_raw_mark INTEGER DEFAULT 100,
            FOREIGN KEY (subject_id) REFERENCES subject (id)
        )
        ''')
        conn.commit()

    # Check if component_mark table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='component_mark'")
    component_mark_exists = cursor.fetchone() is not None
    
    print(f"component_mark table exists: {component_mark_exists}")
    
    if not component_mark_exists:
        print("Creating component_mark table...")
        cursor.execute('''
        CREATE TABLE component_mark (
            id INTEGER PRIMARY KEY,
            mark_id INTEGER NOT NULL,
            component_id INTEGER NOT NULL,
            raw_mark REAL NOT NULL,
            max_raw_mark INTEGER DEFAULT 100,
            percentage REAL NOT NULL,
            FOREIGN KEY (mark_id) REFERENCES mark (id),
            FOREIGN KEY (component_id) REFERENCES subject_component (id)
        )
        ''')
        conn.commit()

    # Check English and Kiswahili subjects
    cursor.execute("SELECT id, name, is_composite FROM subject WHERE name IN ('ENGLISH', 'KISWAHILI')")
    subjects = cursor.fetchall()

    print("\nCurrent English and Kiswahili subjects:")
    for subject in subjects:
        print(f"ID: {subject[0]}, Name: {subject[1]}, Is Composite: {subject[2]}")

    # Update English and Kiswahili to be composite if they're not already
    cursor.execute("UPDATE subject SET is_composite = 1 WHERE id IN (2, 7)")
    conn.commit()
    
    # Check components
    cursor.execute("SELECT * FROM subject_component")
    components = cursor.fetchall()

    print("\nCurrent components:")
    for component in components:
        print(f"ID: {component[0]}, Subject ID: {component[1]}, Name: {component[2]}, Weight: {component[3]}, Max Raw Mark: {component[4]}")

    # If no components exist for English and Kiswahili, add them
    if not any(comp[1] == 2 for comp in components):
        print("\nAdding components for English (ID 2)...")
        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (2, 'Grammar', 0.6, 60)
        ''')

        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (2, 'Composition', 0.4, 40)
        ''')
        conn.commit()

    if not any(comp[1] == 7 for comp in components):
        print("Adding components for Kiswahili (ID 7)...")
        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (7, 'Lugha', 0.6, 60)
        ''')

        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (7, 'Insha', 0.4, 40)
        ''')
        conn.commit()

    # Check components again after adding
    cursor.execute("SELECT * FROM subject_component")
    components = cursor.fetchall()

    print("\nUpdated components:")
    for component in components:
        print(f"ID: {component[0]}, Subject ID: {component[1]}, Name: {component[2]}, Weight: {component[3]}, Max Raw Mark: {component[4]}")

    conn.close()
    print("\nTest completed.")

if __name__ == "__main__":
    test_composite_subjects()
