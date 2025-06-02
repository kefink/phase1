#!/usr/bin/env python3
"""
Migration script to add permission management tables to the existing database.
This implements the delegation-based permission system for classteacher access control.
"""

import sys
import os

# Add the parent directory to the path so we can import the app
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import the app factory first
sys.path.insert(0, os.path.dirname(parent_dir))
from new_structure import create_app
from new_structure.extensions import db
from new_structure.models.permission import ClassTeacherPermission, PermissionRequest

def run_migration():
    """Run the permission tables migration."""
    app = create_app('development')

    with app.app_context():
        try:
            print("🔧 Starting permission tables migration...")
            print(f"📍 Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

            # Check if tables already exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"📊 Existing tables: {len(existing_tables)}")

            # Create the permission tables
            print("📋 Creating ClassTeacherPermission table...")
            if 'class_teacher_permissions' in existing_tables:
                print("   ⚠️  Table already exists, skipping...")
            else:
                ClassTeacherPermission.__table__.create(db.engine, checkfirst=True)
                print("   ✅ Table created successfully")

            print("📋 Creating PermissionRequest table...")
            if 'permission_requests' in existing_tables:
                print("   ⚠️  Table already exists, skipping...")
            else:
                PermissionRequest.__table__.create(db.engine, checkfirst=True)
                print("   ✅ Table created successfully")

            # Commit the changes
            db.session.commit()

            # Verify tables were created
            inspector = inspect(db.engine)
            new_tables = inspector.get_table_names()
            print(f"📊 Tables after migration: {len(new_tables)}")

            if 'class_teacher_permissions' in new_tables and 'permission_requests' in new_tables:
                print("✅ Permission tables migration completed successfully!")
                print("\n📊 Migration Summary:")
                print("   - ClassTeacherPermission table: ✅ Created")
                print("   - PermissionRequest table: ✅ Created")
            else:
                print("❌ Tables were not created properly")
                return False

            print("\n🎯 Next Steps:")
            print("   1. Restart the Flask application")
            print("   2. Login as headteacher to access permission management")
            print("   3. Grant permissions to classteachers for specific classes/streams")
            print("   4. Classteachers will see their permission status on their dashboard")

            return True

        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
