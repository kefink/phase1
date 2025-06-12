#!/usr/bin/env python3
"""
Database cleanup script to remove all test data and reset to clean state.
This will preserve the table structure but remove all test data.
"""

import sqlite3
import os
from datetime import datetime

def clean_database():
    """Clean all test data from the database while preserving structure."""
    db_path = 'kirima_primary.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    print(f"🧹 Cleaning test data from: {db_path}")
    print("⚠️  This will remove ALL existing data but preserve table structure")
    
    # Ask for confirmation
    confirm = input("Are you sure you want to proceed? (yes/no): ").lower().strip()
    if confirm not in ['yes', 'y']:
        print("❌ Operation cancelled")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        print("\n📊 Current database content:")
        show_current_data(cursor)
        
        print("\n🗑️  Removing all test data...")
        
        # Delete data in correct order (respecting foreign key constraints)
        tables_to_clean = [
            'mark',                      # Has foreign keys to student, subject, term, assessment_type
            'student',                   # Has foreign keys to stream, grade
            'teacher_subjects',          # Junction table
            'teacher_subject_assignment', # Has foreign keys to teacher, subject, grade, stream
            'class_teacher_permissions', # Has foreign keys to teacher, grade, stream
            'function_permissions',      # Has foreign keys to teacher, grade, stream
            'permission_requests',       # Has foreign keys to teacher, grade, stream
            'teacher',                   # Has foreign key to stream
            'subject_component',         # Has foreign key to subject
            'subject',                   # Referenced by marks, teachers
            'stream',                    # Has foreign key to grade, referenced by students, teachers
            'grade',                     # Referenced by streams, students
            'assessment_type',           # Referenced by marks
            'term',                      # Referenced by marks
            'school_configuration'       # Configuration data
        ]
        
        deleted_counts = {}
        for table in tables_to_clean:
            try:
                # Get count before deletion
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count_before = cursor.fetchone()[0]
                
                # Delete all records
                cursor.execute(f"DELETE FROM {table}")
                deleted_counts[table] = count_before
                
                # Reset auto-increment counter
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                
                print(f"  ✅ {table}: {count_before} records deleted")
                
            except sqlite3.Error as e:
                if "no such table" in str(e).lower():
                    print(f"  ⚠️  {table}: Table doesn't exist (skipping)")
                else:
                    print(f"  ❌ {table}: Error - {e}")
        
        # Commit the changes
        conn.commit()
        
        print("\n✅ All test data removed successfully!")
        
        # Show final state
        print("\n📊 Database after cleanup:")
        show_current_data(cursor)
        
        # Show summary
        print(f"\n📋 CLEANUP SUMMARY:")
        print(f"{'Table':<25} {'Records Deleted':<15}")
        print("-" * 40)
        total_deleted = 0
        for table, count in deleted_counts.items():
            if count > 0:
                print(f"{table:<25} {count:<15}")
                total_deleted += count
        print("-" * 40)
        print(f"{'TOTAL':<25} {total_deleted:<15}")
        
        conn.close()
        
        print("\n🎯 Database is now clean and ready for your fresh data!")
        print("\n📝 Next steps:")
        print("1. Start the Flask application: python run.py")
        print("2. Login as headteacher to create:")
        print("   - New grades and streams")
        print("   - New subjects")
        print("   - New terms and assessments")
        print("   - New teachers")
        print("   - New students")
        print("3. Login as classteacher to upload marks")
        print("4. Use analytics with your fresh data!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning database: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_current_data(cursor):
    """Show current data counts in all tables."""
    tables = [
        'grade', 'stream', 'subject', 'term', 'assessment_type', 
        'teacher', 'student', 'mark', 'teacher_subjects',
        'teacher_subject_assignment', 'class_teacher_permissions',
        'function_permissions', 'permission_requests', 'school_configuration'
    ]
    
    print(f"{'Table':<25} {'Records':<10}")
    print("-" * 35)
    
    total_records = 0
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"{table:<25} {count:<10}")
                total_records += count
        except sqlite3.Error:
            # Table doesn't exist
            pass
    
    print("-" * 35)
    print(f"{'TOTAL':<25} {total_records:<10}")

def create_minimal_admin():
    """Create a minimal headteacher account for initial setup."""
    db_path = 'kirima_primary.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n👤 Creating minimal headteacher account...")
        
        # Insert minimal headteacher account
        cursor.execute("""
            INSERT INTO teacher (username, password, role, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        """, ('headteacher', 'admin123', 'headteacher', 'System', 'Administrator'))
        
        conn.commit()
        conn.close()
        
        print("✅ Headteacher account created:")
        print("   Username: headteacher")
        print("   Password: admin123")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin account: {e}")
        return False

if __name__ == '__main__':
    print("🧹 DATABASE CLEANUP UTILITY")
    print("=" * 50)
    print("This script will remove ALL test data from your database.")
    print("Table structure will be preserved.")
    print("=" * 50)
    
    success = clean_database()
    
    if success:
        # Ask if user wants to create minimal admin account
        create_admin = input("\nCreate minimal headteacher account? (yes/no): ").lower().strip()
        if create_admin in ['yes', 'y']:
            create_minimal_admin()
        
        print("\n🎉 Database cleanup completed successfully!")
        print("Your database is now ready for fresh data entry.")
    else:
        print("\n❌ Database cleanup failed!")
