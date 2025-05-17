"""
Script to add the percentage column to the Mark table.
"""
import os
import sqlite3

def add_percentage_column():
    """Add the percentage column to the Mark table if it doesn't exist."""
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'kirima_primary.db')

    print(f"Using database at: {db_path}")

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the percentage column already exists in the Mark table
    cursor.execute("PRAGMA table_info(mark);")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]

    if 'percentage' not in column_names:
        print("Adding percentage column to Mark table...")
        cursor.execute("ALTER TABLE mark ADD COLUMN percentage FLOAT;")

        # Update existing records to calculate and store the percentage
        cursor.execute("UPDATE mark SET percentage = (mark / total_marks) * 100 WHERE total_marks > 0;")

        # Commit the changes
        conn.commit()
        print("Percentage column added and existing records updated.")
    else:
        print("Percentage column already exists in Mark table.")

    # Close the connection
    conn.close()

if __name__ == "__main__":
    add_percentage_column()
