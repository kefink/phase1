#!/usr/bin/env python3
"""
Setup Component Tables Script
Creates the necessary tables for composite subjects and adds test component marks.
"""

import sqlite3
import os
import sys

def setup_component_tables():
    """Set up component tables and add test data."""

    # Connect to the database
    db_path = 'hillview.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("=== Setting up Component Tables ===")

        # 1. Create subject_component table
        print("1. Creating subject_component table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subject_component (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            weight REAL DEFAULT 0.5,
            max_raw_mark INTEGER DEFAULT 100,
            FOREIGN KEY (subject_id) REFERENCES subject (id)
        )
        ''')

        # 2. Create component_mark table
        print("2. Creating component_mark table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS component_mark (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mark_id INTEGER NOT NULL,
            component_id INTEGER NOT NULL,
            raw_mark REAL NOT NULL,
            max_raw_mark INTEGER DEFAULT 100,
            percentage REAL NOT NULL,
            FOREIGN KEY (mark_id) REFERENCES marks (id),
            FOREIGN KEY (component_id) REFERENCES subject_component (id)
        )
        ''')

        # 3. Since this database uses a simpler structure, let's work with what we have
        print("3. Setting up components for existing database structure...")

        # For this simplified database, we'll use subject names directly
        # English = subject_id 1, Kiswahili = subject_id 2 (we'll create these IDs)
        english_id = 1
        kiswahili_id = 2

        # 4. Add components for English
        print("4. Adding English components...")
        cursor.execute("DELETE FROM subject_component WHERE subject_id = ?", (english_id,))

        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (?, 'Grammar', 0.7, 70)
        ''', (english_id,))
        grammar_id = cursor.lastrowid

        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (?, 'Composition', 0.3, 30)
        ''', (english_id,))
        composition_id = cursor.lastrowid

        print(f"   Grammar component: ID {grammar_id} (70 marks)")
        print(f"   Composition component: ID {composition_id} (30 marks)")

        # 5. Add components for Kiswahili
        print("5. Adding Kiswahili components...")
        cursor.execute("DELETE FROM subject_component WHERE subject_id = ?", (kiswahili_id,))

        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (?, 'Lugha', 0.6, 60)
        ''', (kiswahili_id,))
        lugha_id = cursor.lastrowid

        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (?, 'Insha', 0.4, 40)
        ''', (kiswahili_id,))
        insha_id = cursor.lastrowid

        print(f"   Lugha component: ID {lugha_id} (60 marks)")
        print(f"   Insha component: ID {insha_id} (40 marks)")

        # Commit the changes
        conn.commit()
        print("\n✅ Component tables setup completed successfully!")

        # 6. Verify the setup
        print("\n=== Verification ===")
        cursor.execute("SELECT COUNT(*) FROM subject_component")
        component_count = cursor.fetchone()[0]
        print(f"Total components created: {component_count}")

        cursor.execute('''
        SELECT sc.name, sc.max_raw_mark, s.name as subject_name
        FROM subject_component sc
        JOIN subject s ON sc.subject_id = s.id
        ORDER BY s.name, sc.name
        ''')
        components = cursor.fetchall()

        for comp in components:
            print(f"   {comp[2]} - {comp[0]}: {comp[1]} marks")

        return True

    except Exception as e:
        print(f"Error setting up component tables: {str(e)}")
        conn.rollback()
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    success = setup_component_tables()
    if success:
        print("\n🎉 Setup completed! You can now upload component marks.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
