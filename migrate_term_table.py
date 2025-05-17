import sqlite3
import os

def migrate_term_table():
    """Add missing columns to the term table in kirima_primary.db."""
    db_path = 'kirima_primary.db'

    print(f"Using database at: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the term table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='term';")
    if not cursor.fetchone():
        print("Term table does not exist. Creating it...")
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
    else:
        # Check if the academic_year column exists
        cursor.execute("PRAGMA table_info(term);")
        columns = [column[1] for column in cursor.fetchall()]

        # Add missing columns if they don't exist
        if 'academic_year' not in columns:
            print("Adding academic_year column to term table...")
            cursor.execute("ALTER TABLE term ADD COLUMN academic_year VARCHAR(20);")
            # Set default academic year for existing terms
            cursor.execute("UPDATE term SET academic_year = '2024';")

        if 'is_current' not in columns:
            print("Adding is_current column to term table...")
            cursor.execute("ALTER TABLE term ADD COLUMN is_current BOOLEAN DEFAULT 0;")
            # Set the first term as current
            cursor.execute("UPDATE term SET is_current = 1 WHERE id = 1;")

        if 'start_date' not in columns:
            print("Adding start_date column to term table...")
            cursor.execute("ALTER TABLE term ADD COLUMN start_date DATE;")

        if 'end_date' not in columns:
            print("Adding end_date column to term table...")
            cursor.execute("ALTER TABLE term ADD COLUMN end_date DATE;")

    # Commit changes and close connection
    conn.commit()

    # Verify the changes
    cursor.execute("PRAGMA table_info(term);")
    columns = cursor.fetchall()
    print("\nColumns in term table:")
    for column in columns:
        print(f"- {column[1]} ({column[2]})")

    # Show the terms in the table
    cursor.execute("SELECT * FROM term;")
    terms = cursor.fetchall()
    print("\nTerms in the database:")
    for term in terms:
        print(f"- {term}")

    conn.close()
    print("\nMigration completed successfully!")

if __name__ == '__main__':
    migrate_term_table()
