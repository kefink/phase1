#!/usr/bin/env python3
"""
Script to add default permissions for classteachers.
This will grant necessary permissions so that classteachers can access
core functions like manage_subjects, manage_students, etc.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Database path
DB_PATH = 'hillview_school.db'

def add_default_permissions():
    """Add default permissions for classteachers."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # First, let's find all classteachers
        print("🔍 Finding classteachers in the system...")
        cursor.execute("SELECT id, username, first_name, last_name, role FROM teacher WHERE role = 'classteacher'")
        classteachers = cursor.fetchall()
        
        if not classteachers:
            print("❌ No classteachers found in the system.")
            return False
        
        print(f"Found {len(classteachers)} classteacher(s):")
        for teacher in classteachers:
            print(f"  - {teacher[1]} ({teacher[2]} {teacher[3]}) - ID: {teacher[0]}")
        
        # Find a headteacher to be the grantor (typically ID 1 or the first headteacher)
        cursor.execute("SELECT id, username FROM teacher WHERE role = 'headteacher' LIMIT 1")
        headteacher = cursor.fetchone()
        
        if not headteacher:
            print("❌ No headteacher found to grant permissions.")
            return False
        
        grantor_id = headteacher[0]
        print(f"📋 Permissions will be granted by: {headteacher[1]} (ID: {grantor_id})")
        
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
        for teacher_id, username, first_name, last_name, role in classteachers:
            print(f"\n  Adding permissions for {username}...")
            
            for function_name, function_category in default_permissions:
                # Check if permission already exists
                cursor.execute("""
                    SELECT id FROM function_permissions 
                    WHERE teacher_id = ? AND function_name = ? AND is_active = 1
                """, (teacher_id, function_name))
                
                existing = cursor.fetchone()
                if existing:
                    print(f"    ⚠️  {function_name} - already exists")
                    continue
                
                # Add the permission
                cursor.execute("""
                    INSERT INTO function_permissions 
                    (teacher_id, function_name, function_category, scope_type, granted_by, granted_at, is_active, auto_granted, notes)
                    VALUES (?, ?, ?, 'global', ?, ?, 1, 1, 'Default permission granted automatically')
                """, (teacher_id, function_name, function_category, grantor_id, datetime.now()))
                
                permissions_added += 1
                print(f"    ✅ {function_name} - granted")
        
        # Also add class teacher permissions for their assigned classes
        print("\n🏫 Adding class teacher permissions...")
        
        for teacher_id, username, first_name, last_name, role in classteachers:
            # Check if they already have class permissions
            cursor.execute("""
                SELECT id FROM class_teacher_permissions 
                WHERE teacher_id = ? AND is_active = 1
            """, (teacher_id,))
            
            existing_class_perms = cursor.fetchone()
            if existing_class_perms:
                print(f"    ⚠️  {username} - already has class permissions")
                continue
            
            # Find their teacher assignments to determine their classes
            cursor.execute("""
                SELECT DISTINCT grade_id, stream_id 
                FROM teacher_assignment 
                WHERE teacher_id = ? AND is_class_teacher = 1
            """, (teacher_id,))
            
            assignments = cursor.fetchall()
            
            for grade_id, stream_id in assignments:
                # Add class teacher permission
                cursor.execute("""
                    INSERT INTO class_teacher_permissions 
                    (teacher_id, grade_id, stream_id, granted_by, granted_at, is_active, is_permanent, auto_granted, permission_scope, notes)
                    VALUES (?, ?, ?, ?, ?, 1, 1, 1, 'full_class_admin', 'Auto-granted based on teacher assignments')
                """, (teacher_id, grade_id, stream_id, grantor_id, datetime.now()))
                
                print(f"    ✅ {username} - class permission for Grade {grade_id}, Stream {stream_id}")
        
        # Commit all changes
        conn.commit()
        
        print(f"\n✅ Successfully added {permissions_added} function permissions!")
        print("🎉 Default permissions setup complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding default permissions: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
        
    finally:
        conn.close()

def main():
    """Main function to add default permissions."""
    print("🔐 Setting up default permissions for classteachers...")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found: {DB_PATH}")
        return False
    
    success = add_default_permissions()
    
    if success:
        print("\n✅ Default permissions added successfully!")
        print("Classteachers now have access to core management functions.")
        print("You can test the system by accessing the classteacher dashboard.")
    else:
        print("\n❌ Failed to add default permissions.")
        print("Please check the error messages above.")
    
    return success

if __name__ == '__main__':
    main()
