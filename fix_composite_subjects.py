"""
Script to check and fix composite subjects in the database.
"""
import sqlite3
import sys

def check_composite_subjects():
    """Check the status of composite subjects in the database."""
    conn = sqlite3.connect('kirima_primary.db')
    cursor = conn.cursor()
    
    # Check if subject_components table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subject_component'")
    if not cursor.fetchone():
        print("The subject_component table does not exist. Creating it...")
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
    if not cursor.fetchone():
        print("The component_mark table does not exist. Creating it...")
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
    
    # Check if subject table has is_composite column
    cursor.execute("PRAGMA table_info(subject)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'is_composite' not in columns:
        print("The subject table does not have an is_composite column. Adding it...")
        cursor.execute("ALTER TABLE subject ADD COLUMN is_composite BOOLEAN DEFAULT 0")
        conn.commit()
    
    if 'is_standard' not in columns:
        print("The subject table does not have an is_standard column. Adding it...")
        cursor.execute("ALTER TABLE subject ADD COLUMN is_standard BOOLEAN DEFAULT 1")
        conn.commit()
    
    # Check English and Kiswahili subjects
    cursor.execute("SELECT id, name, is_composite FROM subject WHERE name IN ('ENGLISH', 'KISWAHILI')")
    subjects = cursor.fetchall()
    
    print("\nCurrent English and Kiswahili subjects:")
    for subject in subjects:
        print(f"ID: {subject[0]}, Name: {subject[1]}, Is Composite: {subject[2]}")
    
    # Check components
    cursor.execute("SELECT * FROM subject_component")
    components = cursor.fetchall()
    
    print("\nCurrent components:")
    for component in components:
        print(f"ID: {component[0]}, Subject ID: {component[1]}, Name: {component[2]}, Weight: {component[3]}, Max Raw Mark: {component[4]}")
    
    conn.close()

def fix_composite_subjects():
    """Fix composite subjects in the database."""
    conn = sqlite3.connect('kirima_primary.db')
    cursor = conn.cursor()
    
    # Update English and Kiswahili to be composite
    cursor.execute("UPDATE subject SET is_composite = 1 WHERE id IN (2, 7)")
    
    # Check if components exist
    cursor.execute("SELECT COUNT(*) FROM subject_component WHERE subject_id IN (2, 7)")
    component_count = cursor.fetchone()[0]
    
    if component_count == 0:
        print("Adding components for English and Kiswahili...")
        
        # Add components for English (ID 2)
        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (2, 'Grammar', 0.6, 60)
        ''')
        
        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (2, 'Composition', 0.4, 40)
        ''')
        
        # Add components for Kiswahili (ID 7)
        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (7, 'Lugha', 0.6, 60)
        ''')
        
        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (7, 'Insha', 0.4, 40)
        ''')
    
    conn.commit()
    conn.close()
    
    print("Composite subjects fixed successfully!")

if __name__ == "__main__":
    print("Checking composite subjects...")
    check_composite_subjects()
    
    choice = input("\nDo you want to fix composite subjects? (y/n): ")
    if choice.lower() == 'y':
        fix_composite_subjects()
        print("Done! Please restart the application.")
    else:
        print("No changes made.")
