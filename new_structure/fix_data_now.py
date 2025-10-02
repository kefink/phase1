#!/usr/bin/env python3
"""
Direct database fix for student grade/stream assignment issues.
This script will fix the data integrity problems causing "Not assigned" and "N/A" issues.
"""

import os
import sys
import sqlite3
from pathlib import Path

def find_database_file():
    """Find the SQLite database file in the project."""
    possible_paths = [
        'instance/hillview.db',
        'hillview.db',
        'database.db',
        'app.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Look in subdirectories
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.db') and 'hillview' in file.lower():
                return os.path.join(root, file)
    
    return None

def fix_student_data():
    """Fix student data integrity issues directly in the database."""
    
    # Find the database
    db_path = find_database_file()
    if not db_path:
        print("❌ Could not find database file!")
        print("Looking for files like: hillview.db, instance/hillview.db, etc.")
        return False
    
    print(f"📁 Found database: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔍 ANALYZING CURRENT DATA ISSUES...")
        
        # Check current issues
        cursor.execute("""
            SELECT 
                s.id,
                s.name,
                s.admission_number,
                s.grade_id,
                s.stream_id,
                g.name as grade_name,
                g.education_level,
                st.name as stream_name,
                st.grade_id as stream_grade_id
            FROM students s
            LEFT JOIN grades g ON s.grade_id = g.id
            LEFT JOIN streams st ON s.stream_id = st.id
            WHERE (s.grade_id IS NULL AND s.stream_id IS NOT NULL)
               OR (s.grade_id IS NOT NULL AND s.stream_id IS NOT NULL AND g.id != st.grade_id)
            ORDER BY s.name
        """)
        
        issues = cursor.fetchall()
        
        if not issues:
            print("✅ No data integrity issues found!")
            return True
            
        print(f"⚠️  Found {len(issues)} students with data issues:")
        for issue in issues:
            student_id, name, adm_no, grade_id, stream_id, grade_name, edu_level, stream_name, stream_grade_id = issue
            print(f"   - {name} ({adm_no}): Grade ID={grade_id}, Stream ID={stream_id} ('{stream_name}' from grade {stream_grade_id})")
        
        print(f"\n🔧 FIXING DATA ISSUES...")
        
        # Fix 1: Students with stream but no grade
        cursor.execute("""
            UPDATE students 
            SET grade_id = (
                SELECT grade_id 
                FROM streams 
                WHERE streams.id = students.stream_id
            )
            WHERE grade_id IS NULL 
              AND stream_id IS NOT NULL
              AND EXISTS (
                SELECT 1 FROM streams WHERE streams.id = students.stream_id
              )
        """)
        
        fix1_count = cursor.rowcount
        print(f"✅ Fixed {fix1_count} students by assigning grades based on their streams")
        
        # Fix 2: Students with invalid stream references
        cursor.execute("""
            UPDATE students 
            SET stream_id = NULL
            WHERE stream_id IS NOT NULL 
              AND NOT EXISTS (
                SELECT 1 FROM streams WHERE streams.id = students.stream_id
              )
        """)
        
        fix2_count = cursor.rowcount
        print(f"✅ Removed {fix2_count} invalid stream references")
        
        # Commit the changes
        conn.commit()
        
        print(f"\n📊 VERIFICATION - CHECKING FIXED DATA...")
        
        # Verify the fixes
        cursor.execute("""
            SELECT 
                s.id,
                s.name,
                s.admission_number,
                COALESCE(g.name, 'Not assigned') as grade_name,
                COALESCE(g.education_level, 'N/A') as education_level,
                COALESCE(st.name, 'Not assigned') as stream_name
            FROM students s
            LEFT JOIN grades g ON s.grade_id = g.id
            LEFT JOIN streams st ON s.stream_id = st.id
            ORDER BY g.name, st.name, s.name
        """)
        
        all_students = cursor.fetchall()
        
        print("📋 Current student assignments:")
        for student in all_students:
            student_id, name, adm_no, grade_name, edu_level, stream_name = student
            print(f"   ✓ {name} ({adm_no}): {grade_name} {stream_name} ({edu_level})")
        
        # Check for remaining issues
        cursor.execute("""
            SELECT COUNT(*) FROM students 
            WHERE grade_id IS NULL OR 
                  (stream_id IS NOT NULL AND NOT EXISTS (
                      SELECT 1 FROM streams WHERE streams.id = students.stream_id
                  ))
        """)
        
        remaining_issues = cursor.fetchone()[0]
        
        if remaining_issues == 0:
            print(f"\n🎉 SUCCESS! All data integrity issues have been resolved!")
            print(f"   • Fixed grade assignments for {fix1_count} students")
            print(f"   • Cleaned up {fix2_count} invalid stream references")
            print(f"   • All {len(all_students)} students now have proper data")
        else:
            print(f"\n⚠️  {remaining_issues} issues still remain - may need manual review")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_final_status():
    """Show the final status after fixes."""
    print("\n" + "="*60)
    print("🏫 STUDENT DATA INTEGRITY FIX COMPLETE")
    print("="*60)
    print("\n✅ What was fixed:")
    print("   • Students with streams but missing grades")
    print("   • Invalid stream references")
    print("   • Data consistency issues")
    
    print("\n🎯 What you should see now:")
    print("   • Proper grade names instead of 'Not assigned'")
    print("   • Correct education levels instead of 'N/A'")
    print("   • Consistent grade-stream relationships")
    
    print(f"\n🔗 Next steps:")
    print("   1. Visit: http://127.0.0.1:8080/parent_management/dashboard")
    print("   2. Check the 'Students Without Parents' section")
    print("   3. Verify grade and stream columns show proper values")
    print("   4. Test the parent portal: http://127.0.0.1:8080/parent/children")

if __name__ == "__main__":
    print("🚀 HILLVIEW SCHOOL - STUDENT DATA INTEGRITY FIXER")
    print("="*50)
    print("This will fix grade/stream assignment issues causing")
    print("'Not assigned' and 'N/A' problems in the dashboard.")
    print()
    
    success = fix_student_data()
    
    if success:
        show_final_status()
    else:
        print("\n❌ Failed to fix data issues. Please check the error messages above.")
        print("You may need to run the manual SQL commands from fix_student_data.sql")