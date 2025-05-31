#!/usr/bin/env python3
"""
Simple script to run database migrations.
Run this script to update your database schema with the new teacher fields.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from migrations.add_teacher_fields import run_migration, verify_migration

def main():
    print("🔧 Database Migration Tool")
    print("=" * 50)
    print("This will add new fields to your database for enhanced staff management.")
    print("The following changes will be made:")
    print("  • Add new fields to Teacher table (full_name, employee_id, etc.)")
    print("  • Add new fields to SchoolConfiguration table")
    print("  • Update existing records with default values")
    print("=" * 50)
    
    # Ask for confirmation
    response = input("Do you want to proceed with the migration? (y/N): ").strip().lower()
    
    if response not in ['y', 'yes']:
        print("Migration cancelled.")
        return
    
    print("\nStarting migration...")
    
    # Run the migration
    success = run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        
        # Verify the migration
        print("\nVerifying migration...")
        verify_success = verify_migration()
        
        if verify_success:
            print("\n🎉 All checks passed! Your database is ready.")
            print("\nNext steps:")
            print("1. Restart your Flask application")
            print("2. The enhanced staff management features are now available")
            print("3. You can assign class teachers and headteachers dynamically")
        else:
            print("\n⚠️  Verification failed. Please check the output above.")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure the Flask application is not running")
        print("2. Check that the database file exists and is writable")
        print("3. Ensure you have proper permissions")

if __name__ == "__main__":
    main()
