"""
Script to recreate the mark table with the correct schema.
This script will:
1. Backup the existing mark table
2. Create a new mark table with the correct schema
3. Copy data from the backup to the new table
4. Drop the backup table
"""
import sqlite3
import os
import datetime

def recreate_mark_table():
    """Recreate the mark table with the correct schema."""
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
    
    # Create a backup of the mark table
    print("\nCreating backup of mark table...")
    cursor.execute("CREATE TABLE IF NOT EXISTS mark_backup AS SELECT * FROM mark;")
    
    # Check if we have any data in the backup table
    cursor.execute("SELECT COUNT(*) FROM mark_backup;")
    backup_count = cursor.fetchone()[0]
    print(f"Backed up {backup_count} records.")
    
    # Drop the original mark table
    print("\nDropping original mark table...")
    cursor.execute("DROP TABLE mark;")
    
    # Create a new mark table with the correct schema
    print("\nCreating new mark table with correct schema...")
    cursor.execute("""
    CREATE TABLE mark (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        term_id INTEGER NOT NULL,
        assessment_type_id INTEGER NOT NULL,
        mark FLOAT NOT NULL,
        total_marks FLOAT NOT NULL,
        raw_mark FLOAT NOT NULL,
        max_raw_mark FLOAT NOT NULL,
        percentage FLOAT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES student (id),
        FOREIGN KEY (subject_id) REFERENCES subject (id),
        FOREIGN KEY (term_id) REFERENCES term (id),
        FOREIGN KEY (assessment_type_id) REFERENCES assessment_type (id)
    );
    """)
    
    # Copy data from the backup table to the new table
    if backup_count > 0:
        print("\nCopying data from backup to new table...")
        cursor.execute("""
        INSERT INTO mark (id, student_id, subject_id, term_id, assessment_type_id, 
                         mark, total_marks, raw_mark, max_raw_mark, percentage, created_at)
        SELECT id, student_id, subject_id, term_id, assessment_type_id,
               mark, total_marks, 
               COALESCE(raw_mark, mark) as raw_mark, 
               COALESCE(max_raw_mark, total_marks) as max_raw_mark,
               COALESCE(percentage, (CASE WHEN total_marks > 0 THEN (mark / total_marks) * 100 ELSE 0 END)) as percentage,
               COALESCE(created_at, CURRENT_TIMESTAMP) as created_at
        FROM mark_backup;
        """)
    
    # Commit changes
    conn.commit()
    
    # Verify the changes
    cursor.execute("PRAGMA table_info(mark);")
    columns = cursor.fetchall()
    print("\nNew mark table schema:")
    for column in columns:
        print(f"- {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'}")
    
    # Check if there are any records in the new mark table
    cursor.execute("SELECT COUNT(*) FROM mark;")
    new_count = cursor.fetchone()[0]
    print(f"\nNumber of records in new mark table: {new_count}")
    
    if new_count > 0:
        # Show a sample record
        cursor.execute("SELECT * FROM mark LIMIT 1;")
        sample = cursor.fetchone()
        print(f"\nSample record: {sample}")
    
    # Drop the backup table
    print("\nDropping backup table...")
    cursor.execute("DROP TABLE mark_backup;")
    
    # Close connection
    conn.close()
    
    print("\nMark table recreation completed.")

if __name__ == "__main__":
    recreate_mark_table()
