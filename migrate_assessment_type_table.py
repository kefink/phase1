import sqlite3
import os

def migrate_assessment_type_table():
    """Add missing columns to the assessment_type table in kirima_primary.db."""
    db_path = 'kirima_primary.db'
    
    print(f"Using database at: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the assessment_type table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assessment_type';")
    if not cursor.fetchone():
        print("Assessment_type table does not exist. Creating it...")
        cursor.execute("""
        CREATE TABLE assessment_type (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL UNIQUE,
            weight INTEGER,
            "group" VARCHAR(50),
            show_on_reports BOOLEAN DEFAULT 1
        );
        """)
        
        # Add some default assessment types
        print("Adding default assessment types...")
        cursor.execute("INSERT INTO assessment_type (name, weight, \"group\", show_on_reports) VALUES (?, ?, ?, ?)", 
                      ("Mid Term", 30, "Exams", 1))
        cursor.execute("INSERT INTO assessment_type (name, weight, \"group\", show_on_reports) VALUES (?, ?, ?, ?)", 
                      ("End Term", 70, "Exams", 1))
    else:
        # Check if the weight column exists
        cursor.execute("PRAGMA table_info(assessment_type);")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add missing columns if they don't exist
        if 'weight' not in columns:
            print("Adding weight column to assessment_type table...")
            cursor.execute("ALTER TABLE assessment_type ADD COLUMN weight INTEGER;")
            # Set default weight for existing assessment types
            cursor.execute("UPDATE assessment_type SET weight = 50;")
        
        if 'group' not in columns:
            print("Adding group column to assessment_type table...")
            cursor.execute("ALTER TABLE assessment_type ADD COLUMN \"group\" VARCHAR(50);")
            # Set default group for existing assessment types
            cursor.execute("UPDATE assessment_type SET \"group\" = 'Exams';")
        
        if 'show_on_reports' not in columns:
            print("Adding show_on_reports column to assessment_type table...")
            cursor.execute("ALTER TABLE assessment_type ADD COLUMN show_on_reports BOOLEAN DEFAULT 1;")
            # Set default show_on_reports for existing assessment types
            cursor.execute("UPDATE assessment_type SET show_on_reports = 1;")
    
    # Commit changes and close connection
    conn.commit()
    
    # Verify the changes
    cursor.execute("PRAGMA table_info(assessment_type);")
    columns = cursor.fetchall()
    print("\nColumns in assessment_type table:")
    for column in columns:
        print(f"- {column[1]} ({column[2]})")
    
    # Show the assessment types in the table
    cursor.execute("SELECT * FROM assessment_type;")
    assessment_types = cursor.fetchall()
    print("\nAssessment types in the database:")
    for assessment_type in assessment_types:
        print(f"- {assessment_type}")
    
    conn.close()
    print("\nMigration completed successfully!")

if __name__ == '__main__':
    migrate_assessment_type_table()
