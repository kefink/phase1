"""
Test script to check if component marks are being retrieved correctly.
"""
import sqlite3
import sys
import os

def test_component_marks():
    """Test if component marks are being retrieved correctly."""
    try:
        conn = sqlite3.connect('kirima_primary.db')
        cursor = conn.cursor()
        print("Connected to database successfully.")

        # First, let's check if we have any component marks in the database
        cursor.execute("SELECT * FROM component_mark")
        component_marks = cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return

    print(f"Number of component marks in the database: {len(component_marks)}")

    if component_marks:
        print("\nExisting component marks:")
        for mark in component_marks:
            print(f"ID: {mark[0]}, Mark ID: {mark[1]}, Component ID: {mark[2]}, Raw Mark: {mark[3]}, Max Raw Mark: {mark[4]}, Percentage: {mark[5]}")

    # Let's add some test component marks if there aren't any
    if not component_marks:
        print("\nAdding test component marks...")

        # First, we need to find a mark for English or Kiswahili
        cursor.execute("""
        SELECT m.id, m.student_id, s.name, m.subject_id
        FROM mark m
        JOIN student s ON m.student_id = s.id
        WHERE m.subject_id IN (2, 7)
        LIMIT 5
        """)
        marks = cursor.fetchall()

        if not marks:
            print("No marks found for English or Kiswahili. Please add some marks first.")
            conn.close()
            return

        print("\nFound marks for English or Kiswahili:")
        for mark in marks:
            print(f"Mark ID: {mark[0]}, Student ID: {mark[1]}, Student Name: {mark[2]}, Subject ID: {mark[3]}")

            # Get components for this subject
            cursor.execute("SELECT id, name FROM subject_component WHERE subject_id = ?", (mark[3],))
            components = cursor.fetchall()

            for component in components:
                # Check if component mark already exists
                cursor.execute("SELECT id FROM component_mark WHERE mark_id = ? AND component_id = ?", (mark[0], component[0]))
                existing = cursor.fetchone()

                if not existing:
                    # Add component mark
                    raw_mark = 30 if component[1] == 'Grammar' or component[1] == 'Lugha' else 20
                    max_raw_mark = 60 if component[1] == 'Grammar' or component[1] == 'Lugha' else 40
                    percentage = (raw_mark / max_raw_mark) * 100

                    cursor.execute("""
                    INSERT INTO component_mark (mark_id, component_id, raw_mark, max_raw_mark, percentage)
                    VALUES (?, ?, ?, ?, ?)
                    """, (mark[0], component[0], raw_mark, max_raw_mark, percentage))

                    print(f"Added component mark for {component[1]}: Raw Mark: {raw_mark}, Max Raw Mark: {max_raw_mark}, Percentage: {percentage:.2f}%")

        conn.commit()

    # Now let's check the component marks again
    cursor.execute("SELECT * FROM component_mark")
    component_marks = cursor.fetchall()

    print("\nUpdated component marks:")
    for mark in component_marks:
        # Get the component name
        cursor.execute("SELECT name FROM subject_component WHERE id = ?", (mark[2],))
        component_name = cursor.fetchone()[0]

        # Get the mark details
        cursor.execute("""
        SELECT s.name, sub.name
        FROM mark m
        JOIN student s ON m.student_id = s.id
        JOIN subject sub ON m.subject_id = sub.id
        WHERE m.id = ?
        """, (mark[1],))
        mark_details = cursor.fetchone()

        print(f"ID: {mark[0]}, Mark ID: {mark[1]}, Component: {component_name}, Raw Mark: {mark[3]}, Max Raw Mark: {mark[4]}, Percentage: {mark[5]:.2f}%")
        print(f"  Student: {mark_details[0]}, Subject: {mark_details[1]}")

    try:
        conn.close()
        print("\nTest completed.")
    except Exception as e:
        print(f"Error closing connection: {e}")

if __name__ == "__main__":
    test_component_marks()
