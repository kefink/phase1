#!/usr/bin/env python3
"""
Quick migration script to add new teacher fields to the database.
This script will add the necessary columns to make the enhanced features work.
"""

import sqlite3
import os
import sys

def run_quick_migration():
    """Run a quick migration to add new teacher fields."""
    
    # Find the database file
    possible_paths = [
        'kirima_primary.db',
        '../kirima_primary.db',
        '../../kirima_primary.db'
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Database file 'kirima_primary.db' not found!")
        print("Please make sure you're running this script from the correct directory.")
        return False
    
    print(f"📁 Found database at: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Starting quick migration...")
        
        # Check current teacher table structure
        cursor.execute("PRAGMA table_info(teacher)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Current teacher columns: {existing_columns}")
        
        # Add new teacher columns
        new_columns = [
            ('full_name', 'TEXT'),
            ('employee_id', 'TEXT'),
            ('phone_number', 'TEXT'),
            ('email', 'TEXT'),
            ('qualification', 'TEXT'),
            ('specialization', 'TEXT'),
            ('is_active', 'BOOLEAN DEFAULT 1'),
            ('date_joined', 'DATE')
        ]
        
        added_columns = []
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE teacher ADD COLUMN {column_name} {column_type}")
                    added_columns.append(column_name)
                    print(f"✅ Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Could not add {column_name}: {e}")
        
        # Check school_configuration table
        cursor.execute("PRAGMA table_info(school_configuration)")
        config_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Current config columns: {config_columns}")
        
        # Add new config columns
        config_new_columns = [
            ('headteacher_id', 'INTEGER'),
            ('deputy_headteacher_id', 'INTEGER')
        ]
        
        for column_name, column_type in config_new_columns:
            if column_name not in config_columns:
                try:
                    cursor.execute(f"ALTER TABLE school_configuration ADD COLUMN {column_name} {column_type}")
                    added_columns.append(column_name)
                    print(f"✅ Added config column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Could not add {column_name}: {e}")
        
        # Update existing data
        print("🔄 Updating existing records...")
        
        # Set default values for new columns
        cursor.execute("UPDATE teacher SET is_active = 1 WHERE is_active IS NULL")
        cursor.execute("UPDATE teacher SET full_name = username WHERE full_name IS NULL OR full_name = ''")
        
        # Generate employee IDs
        cursor.execute("SELECT id, username FROM teacher WHERE employee_id IS NULL OR employee_id = ''")
        teachers = cursor.fetchall()
        
        for teacher_id, username in teachers:
            employee_id = f"EMP{teacher_id:03d}"
            cursor.execute("UPDATE teacher SET employee_id = ? WHERE id = ?", (employee_id, teacher_id))
        
        # Commit changes
        conn.commit()
        
        print(f"✅ Migration completed! Added {len(added_columns)} new columns.")
        print(f"📊 Updated {len(teachers)} teacher records with employee IDs.")
        
        # Verify the migration
        cursor.execute("SELECT COUNT(*) FROM teacher WHERE full_name IS NOT NULL")
        teachers_with_names = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM teacher WHERE employee_id IS NOT NULL")
        teachers_with_ids = cursor.fetchone()[0]
        
        print(f"✅ Verification: {teachers_with_names} teachers have full names")
        print(f"✅ Verification: {teachers_with_ids} teachers have employee IDs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def main():
    print("🚀 Quick Database Migration")
    print("=" * 50)
    print("This will add new fields to your Teacher and SchoolConfiguration tables.")
    print("Your existing data will be preserved and enhanced.")
    print("=" * 50)
    
    # Check if Flask app is running
    print("⚠️  IMPORTANT: Make sure your Flask application is STOPPED before running this migration!")
    response = input("Is your Flask app stopped? (y/N): ").strip().lower()
    
    if response not in ['y', 'yes']:
        print("❌ Please stop your Flask application first, then run this script again.")
        return
    
    print("\n🔧 Starting migration...")
    success = run_quick_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. The database has been updated with new fields")
        print("2. You can now restart your Flask application")
        print("3. The enhanced staff management features are ready to use")
        print("4. Teachers will have employee IDs and can be assigned dynamically")
        
        print("\n💡 What's new:")
        print("• Dynamic staff assignments (no more hardcoded names)")
        print("• Employee IDs for all teachers")
        print("• Enhanced teacher profiles")
        print("• Professional report generation")
        
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above and try again.")
        print("\n🔧 Troubleshooting:")
        print("• Make sure the Flask app is completely stopped")
        print("• Check that you have write permissions to the database")
        print("• Ensure the database file is not locked by another process")

if __name__ == "__main__":
    main()
