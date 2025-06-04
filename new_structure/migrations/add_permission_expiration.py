"""
Database migration to add expiration functionality to permissions.
Run this script to update the database schema.
"""

import sqlite3
from datetime import datetime
import os

def migrate_permission_expiration(db_path):
    """
    Add expiration columns to class_teacher_permissions table.
    
    Args:
        db_path: Path to the SQLite database file
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting permission expiration migration...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(class_teacher_permissions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns if they don't exist
        new_columns = [
            ('expires_at', 'DATETIME'),
            ('is_permanent', 'BOOLEAN DEFAULT 0'),
            ('auto_granted', 'BOOLEAN DEFAULT 0')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                print(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE class_teacher_permissions ADD COLUMN {column_name} {column_type}")
            else:
                print(f"Column {column_name} already exists, skipping...")
        
        # Update existing permissions to be permanent by default
        print("Updating existing permissions to be permanent...")
        cursor.execute("""
            UPDATE class_teacher_permissions 
            SET is_permanent = 1, auto_granted = 0 
            WHERE is_permanent IS NULL OR is_permanent = 0
        """)
        
        conn.commit()
        print("Migration completed successfully!")
        
        # Show updated table structure
        cursor.execute("PRAGMA table_info(class_teacher_permissions)")
        columns = cursor.fetchall()
        print("\nUpdated table structure:")
        for column in columns:
            print(f"  {column[1]} ({column[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def main():
    """Run the migration."""
    # Default database path (go up one directory from new_structure)
    db_path = "../kirima_primary.db"
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        print("Please ensure you're running this from the correct directory.")
        return
    
    # Backup database first
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating backup: {backup_path}")
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print("Backup created successfully!")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")
        response = input("Continue without backup? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return
    
    # Run migration
    migrate_permission_expiration(db_path)

if __name__ == "__main__":
    main()
