#!/usr/bin/env python3
"""
MySQL Database Permission Tables Setup Script
This script creates the missing permission tables in your MySQL database
and adds default permissions for classteachers.
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def create_permission_tables_mysql():
    """Create the missing permission tables in MySQL and add default permissions."""
    
    try:
        # Add current directory to Python path for imports
        sys.path.insert(0, '.')
        
        # Import Flask app and database
        from new_structure import create_app
        
        app = create_app('development')
        with app.app_context():
            # Import after app context is established
            from extensions import db
            from models import Teacher, FunctionPermission, ClassTeacherPermission
            
            print("🔧 Setting up permission tables in MySQL database...")
            
            # Create the permission tables
            print("Creating permission tables...")
            db.create_all()
            
            print("✅ Permission tables created successfully!")
            
            # Check if we have classteachers to set up permissions for
            print("\n🔍 Finding classteachers in the system...")
            classteachers = Teacher.query.filter_by(role='classteacher').all()
            
            if not classteachers:
                print("❌ No classteachers found in the system.")
                print("   Please create classteacher accounts first.")
                return False
            
            print(f"Found {len(classteachers)} classteacher(s):")
            for teacher in classteachers:
                print(f"  - {teacher.username} ({teacher.first_name} {teacher.last_name}) - ID: {teacher.id}")
            
            # Find a headteacher to be the grantor
            headteacher = Teacher.query.filter_by(role='headteacher').first()
            
            if not headteacher:
                print("❌ No headteacher found to grant permissions.")
                print("   Using system user for permissions...")
                grantor_id = 1  # Default to system user
            else:
                grantor_id = headteacher.id
                print(f"📋 Permissions will be granted by: {headteacher.username} (ID: {grantor_id})")
            
            # Define default permissions that classteachers should have
            default_permissions = [
                ('manage_subjects', 'subject_management'),
                ('manage_students', 'student_management'),
                ('manage_grades_streams', 'structure_management'),
                ('manage_terms_assessments', 'structure_management'),
                ('teacher_management_hub', 'teacher_management'),
                ('report_configuration', 'reports_management'),
            ]
            
            print("\n🔐 Adding default permissions...")
            
            permissions_added = 0
            for teacher in classteachers:
                print(f"\n  Adding permissions for {teacher.username}...")
                
                for function_name, function_category in default_permissions:
                    # Check if permission already exists
                    existing = FunctionPermission.query.filter_by(
                        teacher_id=teacher.id,
                        function_name=function_name,
                        is_active=True
                    ).first()
                    
                    if existing:
                        print(f"    ⚠️  {function_name} - already exists")
                        continue
                    
                    # Add the permission
                    permission = FunctionPermission(
                        teacher_id=teacher.id,
                        function_name=function_name,
                        function_category=function_category,
                        scope_type='global',
                        granted_by=grantor_id,
                        granted_at=datetime.utcnow(),
                        is_active=True,
                        auto_granted=True,
                        notes='Default permission granted automatically'
                    )
                    
                    db.session.add(permission)
                    permissions_added += 1
                    print(f"    ✅ {function_name} - granted")
            
            # Also add class teacher permissions for their assigned classes
            print("\n🏫 Adding class teacher permissions...")
            
            for teacher in classteachers:
                # Check if they already have class permissions
                existing_class_perms = ClassTeacherPermission.query.filter_by(
                    teacher_id=teacher.id,
                    is_active=True
                ).first()
                
                if existing_class_perms:
                    print(f"    ⚠️  {teacher.username} - already has class permissions")
                    continue
                
                # Find their teacher assignments to determine their classes
                # This assumes you have a teacher_assignment table
                try:
                    from models import TeacherAssignment
                    assignments = TeacherAssignment.query.filter_by(
                        teacher_id=teacher.id,
                        is_class_teacher=True
                    ).all()
                    
                    for assignment in assignments:
                        # Add class teacher permission
                        class_permission = ClassTeacherPermission(
                            teacher_id=teacher.id,
                            grade_id=assignment.grade_id,
                            stream_id=assignment.stream_id,
                            granted_by=grantor_id,
                            granted_at=datetime.utcnow(),
                            is_active=True,
                            is_permanent=True,
                            auto_granted=True,
                            permission_scope='full_class_admin',
                            notes='Auto-granted based on teacher assignments'
                        )
                        
                        db.session.add(class_permission)
                        print(f"    ✅ {teacher.username} - class permission for Grade {assignment.grade_id}, Stream {assignment.stream_id}")
                        
                except Exception as e:
                    print(f"    ⚠️  Could not add class permissions for {teacher.username}: {e}")
            
            # Commit all changes
            try:
                db.session.commit()
                print(f"\n✅ Successfully added {permissions_added} function permissions!")
                print("🎉 Default permissions setup complete!")
                return True
            except Exception as e:
                print(f"❌ Error committing permissions: {e}")
                db.session.rollback()
                return False
                
    except Exception as e:
        print(f"❌ Error setting up permission tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_mysql_connection():
    """Verify that we can connect to the MySQL database."""
    
    try:
        # Add current directory to Python path for imports
        sys.path.insert(0, '.')
        
        from new_structure import create_app
        
        app = create_app('development')
        with app.app_context():
            # Import db after app context is established
            from extensions import db
            
            # Test the connection
            result = db.engine.execute("SELECT 1").scalar()
            if result == 1:
                print("✅ MySQL database connection successful!")
                return True
            else:
                print("❌ MySQL database connection failed!")
                return False
                
    except Exception as e:
        print(f"❌ MySQL connection error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to set up permission tables in MySQL."""
    print("🔧 MySQL Database Permission Tables Setup")
    print("=========================================")
    
    # First verify MySQL connection
    if not verify_mysql_connection():
        print("\n❌ Cannot connect to MySQL database.")
        print("Please check your database configuration in config.py")
        return False
    
    # Create permission tables and set up default permissions
    success = create_permission_tables_mysql()
    
    if success:
        print("\n✅ Permission tables and default permissions set up successfully!")
        print("🎯 Your classteachers now have access to core management functions.")
        print("🚀 You can restart the Flask server to test the system.")
    else:
        print("\n❌ Failed to set up permission tables.")
        print("Please check the error messages above and your database configuration.")
    
    return success

if __name__ == '__main__':
    main()
