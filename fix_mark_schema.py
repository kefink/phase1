"""
Script to fix the Mark model schema in the database.
This script will:
1. Check the current schema
2. Add the missing columns if needed
3. Update the model to use both old and new column names
"""
import sqlite3
import os
import sys

# Enable debug output
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')}")

def fix_mark_schema():
    """Fix the Mark table schema in the database."""
    db_path = 'kirima_primary.db'

    print(f"Using database at: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the mark table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mark';")
    if not cursor.fetchone():
        print("Mark table does not exist. This is unexpected.")
        return

    # Check the current schema
    cursor.execute("PRAGMA table_info(mark);")
    columns = cursor.fetchall()
    print("\nCurrent columns in mark table:")
    column_names = []
    for column in columns:
        column_names.append(column[1])
        print(f"- {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'}")

    # Check if we need to add the raw_mark and max_raw_mark columns
    needs_raw_mark = 'raw_mark' not in column_names
    needs_max_raw_mark = 'max_raw_mark' not in column_names
    needs_percentage = 'percentage' not in column_names

    # Add missing columns
    if needs_raw_mark:
        print("\nAdding raw_mark column...")
        cursor.execute("ALTER TABLE mark ADD COLUMN raw_mark FLOAT;")
        print("Copying data from mark to raw_mark...")
        cursor.execute("UPDATE mark SET raw_mark = mark WHERE raw_mark IS NULL;")

    if needs_max_raw_mark:
        print("\nAdding max_raw_mark column...")
        cursor.execute("ALTER TABLE mark ADD COLUMN max_raw_mark FLOAT;")
        print("Copying data from total_marks to max_raw_mark...")
        cursor.execute("UPDATE mark SET max_raw_mark = total_marks WHERE max_raw_mark IS NULL;")

    if needs_percentage:
        print("\nAdding percentage column...")
        cursor.execute("ALTER TABLE mark ADD COLUMN percentage FLOAT;")
        print("Calculating percentage values...")
        cursor.execute("""
            UPDATE mark
            SET percentage = (raw_mark / max_raw_mark) * 100
            WHERE percentage IS NULL AND max_raw_mark > 0;
        """)
        cursor.execute("""
            UPDATE mark
            SET percentage = 0
            WHERE percentage IS NULL AND max_raw_mark = 0;
        """)

    # Commit changes
    conn.commit()

    # Verify the changes
    cursor.execute("PRAGMA table_info(mark);")
    columns = cursor.fetchall()
    print("\nUpdated columns in mark table:")
    for column in columns:
        print(f"- {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'}")

    # Check if there are any records in the mark table
    cursor.execute("SELECT COUNT(*) FROM mark;")
    count = cursor.fetchone()[0]
    print(f"\nNumber of records in mark table: {count}")

    if count > 0:
        # Show a sample record
        cursor.execute("SELECT * FROM mark LIMIT 1;")
        sample = cursor.fetchone()
        print(f"\nSample record: {sample}")

    # Close connection
    conn.close()

    print("\nSchema update completed.")

if __name__ == "__main__":
    fix_mark_schema()
