"""
Script to check and fix composite subjects in the database.
"""
import sqlite3
import sys
import os

def check_composite_subjects():
    """Check the status of composite subjects in the database."""
    conn = sqlite3.connect('kirima_primary.db')
    cursor = conn.cursor()

    # Check if subject_component table exists
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

    # First, clear any existing components to avoid duplicates
    cursor.execute("DELETE FROM subject_component WHERE subject_id IN (2, 7)")
    print("Cleared existing components for English and Kiswahili.")

    # Update English and Kiswahili to be composite
    cursor.execute("UPDATE subject SET is_composite = 1 WHERE id IN (2, 7)")
    print("Updated English (ID 2) and Kiswahili (ID 7) to be composite subjects.")

    # Add components for English (ID 2)
    cursor.execute('''
    INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
    VALUES (2, 'Grammar', 0.6, 60)
    ''')

    cursor.execute('''
    INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
    VALUES (2, 'Composition', 0.4, 40)
    ''')
    print("Added Grammar (60%) and Composition (40%) components for English.")

    # Add components for Kiswahili (ID 7)
    cursor.execute('''
    INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
    VALUES (7, 'Lugha', 0.6, 60)
    ''')

    cursor.execute('''
    INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
    VALUES (7, 'Insha', 0.4, 40)
    ''')
    print("Added Lugha (60%) and Insha (40%) components for Kiswahili.")

    conn.commit()

    # Verify the components were added
    cursor.execute("SELECT * FROM subject_component")
    components = cursor.fetchall()

    print("\nVerifying components:")
    for component in components:
        print(f"ID: {component[0]}, Subject ID: {component[1]}, Name: {component[2]}, Weight: {component[3]}, Max Raw Mark: {component[4]}")

    conn.close()

    print("\nComposite subjects fixed successfully!")

def backup_database():
    """Create a backup of the database before making changes."""
    import shutil
    from datetime import datetime

    # Create backups directory if it doesn't exist
    if not os.path.exists('backups'):
        os.makedirs('backups')

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backups/kirima_primary_backup_{timestamp}.db"

    # Copy the database file
    shutil.copy2('kirima_primary.db', backup_file)
    print(f"Database backup created: {backup_file}")

def add_composite_subject():
    """Add a new composite subject with components."""
    conn = sqlite3.connect('kirima_primary.db')
    cursor = conn.cursor()

    # Get subject name
    subject_name = input("Enter the subject name (e.g., ENGLISH): ").strip().upper()
    if not subject_name:
        print("Subject name cannot be empty.")
        conn.close()
        return

    # Get education level
    print("\nEducation Levels:")
    print("1. lower_primary")
    print("2. upper_primary")
    print("3. junior_secondary")
    education_level_choice = input("Choose education level (1-3): ").strip()

    if education_level_choice == '1':
        education_level = "lower_primary"
    elif education_level_choice == '2':
        education_level = "upper_primary"
    elif education_level_choice == '3':
        education_level = "junior_secondary"
    else:
        print("Invalid choice. Using junior_secondary as default.")
        education_level = "junior_secondary"

    # Check if subject already exists
    cursor.execute("SELECT id, is_composite FROM subject WHERE name = ? AND education_level = ?",
                  (subject_name, education_level))
    existing_subject = cursor.fetchone()

    if existing_subject:
        subject_id = existing_subject[0]
        print(f"Subject already exists with ID: {subject_id}")

        # Update to make it composite
        cursor.execute("UPDATE subject SET is_composite = 1 WHERE id = ?", (subject_id,))
        print(f"Updated {subject_name} to be a composite subject.")
    else:
        # Add new subject
        cursor.execute('''
        INSERT INTO subject (name, education_level, is_standard, is_composite)
        VALUES (?, ?, 1, 1)
        ''', (subject_name, education_level))

        subject_id = cursor.lastrowid
        print(f"Added new composite subject {subject_name} with ID: {subject_id}")

    # Clear any existing components
    cursor.execute("DELETE FROM subject_component WHERE subject_id = ?", (subject_id,))

    # Add components
    components = []
    total_weight = 0

    while True:
        component_name = input("\nEnter component name (or leave empty to finish): ").strip()
        if not component_name:
            break

        weight = input(f"Enter weight for {component_name} (0-1, e.g., 0.6 for 60%): ").strip()
        try:
            weight = float(weight)
            if weight <= 0 or weight > 1:
                print("Weight must be between 0 and 1. Using 0.5 as default.")
                weight = 0.5
        except ValueError:
            print("Invalid weight. Using 0.5 as default.")
            weight = 0.5

        max_raw_mark = input(f"Enter maximum raw mark for {component_name} (default 100): ").strip()
        try:
            max_raw_mark = int(max_raw_mark)
            if max_raw_mark <= 0:
                print("Maximum raw mark must be positive. Using 100 as default.")
                max_raw_mark = 100
        except ValueError:
            print("Invalid maximum raw mark. Using 100 as default.")
            max_raw_mark = 100

        components.append((component_name, weight, max_raw_mark))
        total_weight += weight

    if not components:
        print("No components added. Subject will not be composite.")
        cursor.execute("UPDATE subject SET is_composite = 0 WHERE id = ?", (subject_id,))
        conn.commit()
        conn.close()
        return

    # Normalize weights if total is not 1
    if abs(total_weight - 1.0) > 0.01:  # Allow small rounding errors
        print(f"Total weight ({total_weight}) is not 1.0. Normalizing weights...")
        components = [(name, weight/total_weight, max_mark) for name, weight, max_mark in components]

    # Add components to database
    for name, weight, max_mark in components:
        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (?, ?, ?, ?)
        ''', (subject_id, name, weight, max_mark))
        print(f"Added component {name} with weight {weight:.2f} and max mark {max_mark}")

    conn.commit()

    # Verify the components were added
    cursor.execute("SELECT * FROM subject_component WHERE subject_id = ?", (subject_id,))
    db_components = cursor.fetchall()

    print("\nVerifying components:")
    for component in db_components:
        print(f"ID: {component[0]}, Subject ID: {component[1]}, Name: {component[2]}, Weight: {component[3]}, Max Raw Mark: {component[4]}")

    conn.close()
    print(f"\nComposite subject {subject_name} added/updated successfully!")

if __name__ == "__main__":
    print("Composite Subject Management Tool")
    print("================================")

    while True:
        print("\nOptions:")
        print("1. Check composite subjects")
        print("2. Fix English and Kiswahili subjects")
        print("3. Add/update a composite subject")
        print("4. Backup database")
        print("5. Exit")

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == '1':
            check_composite_subjects()
        elif choice == '2':
            backup_database()
            fix_composite_subjects()
            print("Done! Please restart the application.")
        elif choice == '3':
            backup_database()
            add_composite_subject()
            print("Done! Please restart the application.")
        elif choice == '4':
            backup_database()
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
