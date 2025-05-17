"""
Migration script to update the database schema.
"""
import sqlite3
import os

def migrate_database():
    """Migrate the database schema to add new columns."""
    db_path = os.path.join(os.path.dirname(__file__), 'hillview.db')

    print(f"Using database at: {db_path}")

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if the columns already exist in the term table
        cursor.execute("PRAGMA table_info(term)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add new columns to the term table if they don't exist
        if 'academic_year' not in columns:
            print("Adding academic_year column to term table...")
            try:
                cursor.execute("ALTER TABLE term ADD COLUMN academic_year TEXT")
            except sqlite3.OperationalError as e:
                print(f"Error adding academic_year column: {str(e)}")

        if 'is_current' not in columns:
            print("Adding is_current column to term table...")
            try:
                cursor.execute("ALTER TABLE term ADD COLUMN is_current BOOLEAN DEFAULT 0")
            except sqlite3.OperationalError as e:
                print(f"Error adding is_current column: {str(e)}")

        if 'start_date' not in columns:
            print("Adding start_date column to term table...")
            try:
                cursor.execute("ALTER TABLE term ADD COLUMN start_date DATE")
            except sqlite3.OperationalError as e:
                print(f"Error adding start_date column: {str(e)}")

        if 'end_date' not in columns:
            print("Adding end_date column to term table...")
            try:
                cursor.execute("ALTER TABLE term ADD COLUMN end_date DATE")
            except sqlite3.OperationalError as e:
                print(f"Error adding end_date column: {str(e)}")
    except Exception as e:
        print(f"Error checking term table: {str(e)}")

    try:
        # Check if the columns already exist in the assessment_type table
        cursor.execute("PRAGMA table_info(assessment_type)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add new columns to the assessment_type table if they don't exist
        if 'weight' not in columns:
            print("Adding weight column to assessment_type table...")
            try:
                cursor.execute("ALTER TABLE assessment_type ADD COLUMN weight INTEGER")
            except sqlite3.OperationalError as e:
                print(f"Error adding weight column: {str(e)}")

        if 'group' not in columns:
            print("Adding group column to assessment_type table...")
            try:
                cursor.execute("ALTER TABLE assessment_type ADD COLUMN \"group\" TEXT")
            except sqlite3.OperationalError as e:
                print(f"Error adding group column: {str(e)}")

        if 'show_on_reports' not in columns:
            print("Adding show_on_reports column to assessment_type table...")
            try:
                cursor.execute("ALTER TABLE assessment_type ADD COLUMN show_on_reports BOOLEAN DEFAULT 1")
            except sqlite3.OperationalError as e:
                print(f"Error adding show_on_reports column: {str(e)}")
    except Exception as e:
        print(f"Error checking assessment_type table: {str(e)}")

    try:
        # Set the first term as the current term if no term is set as current
        cursor.execute("SELECT COUNT(*) FROM term WHERE is_current = 1")
        current_term_count = cursor.fetchone()[0]

        if current_term_count == 0:
            cursor.execute("SELECT id FROM term ORDER BY id LIMIT 1")
            first_term = cursor.fetchone()
            if first_term:
                print(f"Setting term with ID {first_term[0]} as the current term...")
                try:
                    cursor.execute("UPDATE term SET is_current = 1 WHERE id = ?", (first_term[0],))
                except sqlite3.OperationalError as e:
                    print(f"Error setting current term: {str(e)}")
    except Exception as e:
        print(f"Error setting current term: {str(e)}")

    # Commit the changes
    try:
        conn.commit()
        print("Changes committed successfully!")
    except Exception as e:
        print(f"Error committing changes: {str(e)}")

    # Close the connection
    conn.close()

    print("Database migration completed!")

if __name__ == "__main__":
    migrate_database()
