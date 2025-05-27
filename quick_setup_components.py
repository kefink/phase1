#!/usr/bin/env python3
"""
Quick Component Setup Script
Directly adds component data to the database for testing.
"""

import sqlite3
import os

def quick_setup():
    """Quickly set up component data for testing."""

    # Connect to the new_structure database
    db_path = 'new_structure/hillview.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("=== Quick Component Setup ===")

        # 1. Ensure component tables exist
        print("1. Creating component tables...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subject_component (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            weight REAL DEFAULT 0.5,
            max_raw_mark INTEGER DEFAULT 100
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS component_mark (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mark_id INTEGER NOT NULL,
            component_id INTEGER NOT NULL,
            raw_mark REAL NOT NULL,
            max_raw_mark INTEGER DEFAULT 100,
            percentage REAL NOT NULL
        )
        ''')

        # 2. Clear existing component data
        print("2. Clearing existing component data...")
        cursor.execute("DELETE FROM component_mark")
        cursor.execute("DELETE FROM subject_component")

        # 3. Add component definitions
        print("3. Adding component definitions...")

        # English components (subject_id = 1)
        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (1, 'Grammar', 0.7, 70)
        ''')
        grammar_id = cursor.lastrowid

        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (1, 'Composition', 0.3, 30)
        ''')
        composition_id = cursor.lastrowid

        # Kiswahili components (subject_id = 2)
        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (2, 'Lugha', 0.6, 60)
        ''')
        lugha_id = cursor.lastrowid

        cursor.execute('''
        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
        VALUES (2, 'Insha', 0.4, 40)
        ''')
        insha_id = cursor.lastrowid

        print(f"   Created Grammar (ID: {grammar_id}), Composition (ID: {composition_id})")
        print(f"   Created Lugha (ID: {lugha_id}), Insha (ID: {insha_id})")

        # 4. Add sample marks if they don't exist
        print("4. Adding sample marks...")

        # Check if marks table exists and has the right structure
        cursor.execute("PRAGMA table_info(mark)")
        mark_columns = [col[1] for col in cursor.fetchall()]

        if 'student_id' in mark_columns:
            # This is the new structure - add proper marks
            print("   Using new structure mark table...")

            # Add sample marks for testing
            sample_marks = [
                (1, 1, 1, 1, 69, 100),  # student_id, subject_id, term_id, assessment_type_id, mark, total_marks
                (1, 2, 1, 1, 77, 100),  # Kiswahili for same student
                (2, 1, 1, 1, 75, 100),  # English for student 2
                (2, 2, 1, 1, 68, 100),  # Kiswahili for student 2
            ]

            for mark_data in sample_marks:
                cursor.execute('''
                INSERT OR REPLACE INTO mark
                (student_id, subject_id, term_id, assessment_type_id, mark, total_marks)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', mark_data)

            # Get the mark IDs for component marks
            cursor.execute('''
            SELECT id, student_id, subject_id, mark
            FROM mark
            WHERE subject_id IN (1, 2)
            ORDER BY student_id, subject_id
            ''')
            marks = cursor.fetchall()

        else:
            print("   Using old structure marks table...")
            marks = []

        # 5. Add component marks
        print("5. Adding component marks...")

        component_count = 0
        for mark in marks:
            mark_id, student_id, subject_id, total_mark = mark

            if subject_id == 1:  # English
                # Grammar: 70% of total (max 70), Composition: 30% of total (max 30)
                grammar_raw = int(total_mark * 0.7)
                composition_raw = int(total_mark * 0.3)

                # Grammar component mark
                cursor.execute('''
                INSERT INTO component_mark (mark_id, component_id, raw_mark, max_raw_mark, percentage)
                VALUES (?, ?, ?, ?, ?)
                ''', (mark_id, grammar_id, grammar_raw, 70, (grammar_raw/70)*100))

                # Composition component mark
                cursor.execute('''
                INSERT INTO component_mark (mark_id, component_id, raw_mark, max_raw_mark, percentage)
                VALUES (?, ?, ?, ?, ?)
                ''', (mark_id, composition_id, composition_raw, 30, (composition_raw/30)*100))

                component_count += 2
                print(f"   Student {student_id} English: Grammar {grammar_raw}/70, Composition {composition_raw}/30")

            elif subject_id == 2:  # Kiswahili
                # Lugha: 60% of total (max 60), Insha: 40% of total (max 40)
                lugha_raw = int(total_mark * 0.6)
                insha_raw = int(total_mark * 0.4)

                # Lugha component mark
                cursor.execute('''
                INSERT INTO component_mark (mark_id, component_id, raw_mark, max_raw_mark, percentage)
                VALUES (?, ?, ?, ?, ?)
                ''', (mark_id, lugha_id, lugha_raw, 60, (lugha_raw/60)*100))

                # Insha component mark
                cursor.execute('''
                INSERT INTO component_mark (mark_id, component_id, raw_mark, max_raw_mark, percentage)
                VALUES (?, ?, ?, ?, ?)
                ''', (mark_id, insha_id, insha_raw, 40, (insha_raw/40)*100))

                component_count += 2
                print(f"   Student {student_id} Kiswahili: Lugha {lugha_raw}/60, Insha {insha_raw}/40")

        # Commit changes
        conn.commit()
        print(f"\n✅ Setup completed! Created {component_count} component marks.")

        # 6. Verification
        print("\n=== Verification ===")
        cursor.execute("SELECT COUNT(*) FROM subject_component")
        comp_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM component_mark")
        mark_count = cursor.fetchone()[0]

        print(f"Components: {comp_count}")
        print(f"Component marks: {mark_count}")

        if mark_count > 0:
            print("\nSample component marks:")
            cursor.execute('''
            SELECT cm.raw_mark, cm.max_raw_mark, sc.name, m.student_id
            FROM component_mark cm
            JOIN subject_component sc ON cm.component_id = sc.id
            JOIN mark m ON cm.mark_id = m.id
            LIMIT 5
            ''')

            for result in cursor.fetchall():
                print(f"   Student {result[3]} - {result[2]}: {result[0]}/{result[1]}")

        return True

    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    success = quick_setup()
    if success:
        print("\n🎉 Component setup completed! Now test the individual report.")
        print("   The component marks should show actual uploaded raw marks as maximum values.")
        print("   Example: Grammar (48/70) instead of Grammar (48/50)")
    else:
        print("\n❌ Setup failed.")
