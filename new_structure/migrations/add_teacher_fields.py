"""
Database migration script to add new fields to Teacher model and SchoolConfiguration model.
This script adds the enhanced fields we created for dynamic staff management.
"""
import sqlite3
import os
from datetime import datetime

def run_migration():
    """Run the database migration to add new fields."""
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'kirima_primary.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting database migration...")
        
        # Check if the new columns already exist
        cursor.execute("PRAGMA table_info(teacher)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns to teacher table if they don't exist
        new_teacher_columns = [
            ('full_name', 'TEXT'),
            ('employee_id', 'TEXT'),
            ('phone_number', 'TEXT'),
            ('email', 'TEXT'),
            ('qualification', 'TEXT'),
            ('specialization', 'TEXT'),
            ('is_active', 'BOOLEAN DEFAULT 1'),
            ('date_joined', 'DATE')
        ]
        
        for column_name, column_type in new_teacher_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE teacher ADD COLUMN {column_name} {column_type}")
                    print(f"Added column '{column_name}' to teacher table")
                except sqlite3.OperationalError as e:
                    print(f"Warning: Could not add column '{column_name}': {e}")
        
        # Check if the new columns already exist in school_configuration
        cursor.execute("PRAGMA table_info(school_configuration)")
        existing_config_columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns to school_configuration table if they don't exist
        new_config_columns = [
            ('headteacher_id', 'INTEGER'),
            ('deputy_headteacher_id', 'INTEGER')
        ]
        
        for column_name, column_type in new_config_columns:
            if column_name not in existing_config_columns:
                try:
                    cursor.execute(f"ALTER TABLE school_configuration ADD COLUMN {column_name} {column_type}")
                    print(f"Added column '{column_name}' to school_configuration table")
                except sqlite3.OperationalError as e:
                    print(f"Warning: Could not add column '{column_name}': {e}")
        
        # Update existing teachers with default values
        print("Updating existing teacher records with default values...")
        
        # Set is_active to True for all existing teachers
        cursor.execute("UPDATE teacher SET is_active = 1 WHERE is_active IS NULL")
        
        # Set full_name to username for existing teachers where full_name is NULL
        cursor.execute("UPDATE teacher SET full_name = username WHERE full_name IS NULL OR full_name = ''")
        
        # Generate employee IDs for existing teachers
        cursor.execute("SELECT id, username FROM teacher WHERE employee_id IS NULL OR employee_id = ''")
        teachers = cursor.fetchall()
        
        for teacher_id, username in teachers:
            # Generate a simple employee ID based on username and ID
            employee_id = f"EMP{teacher_id:03d}"
            cursor.execute("UPDATE teacher SET employee_id = ? WHERE id = ?", (employee_id, teacher_id))
        
        # Commit the changes
        conn.commit()
        print("Database migration completed successfully!")
        
        # Display summary
        cursor.execute("SELECT COUNT(*) FROM teacher")
        teacher_count = cursor.fetchone()[0]
        print(f"Updated {teacher_count} teacher records")
        
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def verify_migration():
    """Verify that the migration was successful."""
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'kirima_primary.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\nVerifying migration...")
        
        # Check teacher table structure
        cursor.execute("PRAGMA table_info(teacher)")
        teacher_columns = [column[1] for column in cursor.fetchall()]
        
        expected_teacher_columns = [
            'id', 'username', 'password', 'role', 'stream_id',
            'full_name', 'employee_id', 'phone_number', 'email',
            'qualification', 'specialization', 'is_active', 'date_joined'
        ]
        
        missing_teacher_columns = [col for col in expected_teacher_columns if col not in teacher_columns]
        
        if missing_teacher_columns:
            print(f"Warning: Missing teacher columns: {missing_teacher_columns}")
        else:
            print("✅ All teacher columns present")
        
        # Check school_configuration table structure
        cursor.execute("PRAGMA table_info(school_configuration)")
        config_columns = [column[1] for column in cursor.fetchall()]
        
        expected_config_columns = ['headteacher_id', 'deputy_headteacher_id']
        missing_config_columns = [col for col in expected_config_columns if col not in config_columns]
        
        if missing_config_columns:
            print(f"Warning: Missing school_configuration columns: {missing_config_columns}")
        else:
            print("✅ All school_configuration columns present")
        
        # Check data integrity
        cursor.execute("SELECT COUNT(*) FROM teacher WHERE full_name IS NOT NULL")
        teachers_with_names = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM teacher WHERE employee_id IS NOT NULL")
        teachers_with_ids = cursor.fetchone()[0]
        
        print(f"✅ {teachers_with_names} teachers have full names")
        print(f"✅ {teachers_with_ids} teachers have employee IDs")
        
        return True
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Database Migration Script")
    print("=" * 50)
    
    success = run_migration()
    
    if success:
        verify_migration()
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("You can now restart your Flask application.")
    else:
        print("\n" + "=" * 50)
        print("Migration failed. Please check the errors above.")
