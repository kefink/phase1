#!/usr/bin/env python3
"""
Comprehensive database health check and repair script.
This script checks for missing tables, columns, and data integrity issues.
"""
import sqlite3
import os
import sys

def check_database_health():
    """Perform comprehensive database health check."""
    db_path = 'kirima_primary.db'
    
    print("🔍 Starting Database Health Check...")
    print("=" * 50)
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Found {len(existing_tables)} tables:")
        for table in sorted(existing_tables):
            print(f"  ✓ {table}")
        
        print("\n" + "=" * 50)
        
        # Define required tables and their structures
        required_tables = {
            'grade': ['id', 'name', 'education_level', 'created_at'],
            'stream': ['id', 'name', 'grade_id', 'created_at'],
            'term': ['id', 'name', 'academic_year', 'start_date', 'end_date', 'is_current', 'created_at'],
            'assessment_type': ['id', 'name', 'weight', 'group_name', 'show_on_reports', 'created_at'],
            'subject': ['id', 'name', 'education_level', 'is_composite', 'created_at'],
            'teacher': ['id', 'username', 'password', 'role', 'stream_id', 'first_name', 'last_name', 'email', 'phone', 'created_at'],
            'student': ['id', 'name', 'admission_number', 'stream_id', 'grade_id', 'gender', 'created_at'],
            'mark': ['id', 'student_id', 'subject_id', 'term_id', 'assessment_type_id', 'raw_mark', 'total_marks', 'percentage', 'grade_letter', 'created_at'],
            'teacher_subjects': ['teacher_id', 'subject_id'],
            'teacher_subject_assignment': ['id', 'teacher_id', 'subject_id', 'grade_id', 'stream_id', 'is_class_teacher', 'created_at'],
            'class_teacher_permissions': ['id', 'teacher_id', 'grade_id', 'stream_id', 'granted_by', 'granted_at', 'expires_at', 'is_active', 'permission_scope', 'notes'],
            'function_permissions': ['id', 'teacher_id', 'function_name', 'function_category', 'scope_type', 'grade_id', 'stream_id', 'granted_by', 'granted_at', 'expires_at', 'revoked_at', 'is_active', 'notes', 'auto_granted'],
            'permission_requests': ['id', 'teacher_id', 'grade_id', 'stream_id', 'requested_at', 'status', 'processed_at', 'processed_by', 'reason', 'admin_notes'],
            'subject_component': ['id', 'subject_id', 'name', 'weight', 'created_at'],
            'school_configuration': ['id', 'key', 'value', 'description', 'created_at', 'updated_at']
        }
        
        # Check for missing tables
        missing_tables = []
        for table_name in required_tables:
            if table_name not in existing_tables:
                missing_tables.append(table_name)
        
        if missing_tables:
            print("❌ Missing Tables:")
            for table in missing_tables:
                print(f"  - {table}")
        else:
            print("✅ All required tables present")
        
        # Check table structures
        print("\n🔍 Checking Table Structures...")
        structure_issues = []
        
        for table_name, required_columns in required_tables.items():
            if table_name in existing_tables:
                cursor.execute(f"PRAGMA table_info({table_name})")
                existing_columns = [column[1] for column in cursor.fetchall()]
                
                missing_columns = [col for col in required_columns if col not in existing_columns]
                if missing_columns:
                    structure_issues.append((table_name, missing_columns))
                    print(f"  ⚠️  {table_name}: Missing columns {missing_columns}")
                else:
                    print(f"  ✅ {table_name}: All columns present")
        
        # Check data integrity
        print("\n🔍 Checking Data Integrity...")
        data_issues = []
        
        # Check for orphaned records
        integrity_checks = [
            ("stream", "grade_id", "grade", "id", "Streams without valid grades"),
            ("student", "stream_id", "stream", "id", "Students without valid streams"),
            ("student", "grade_id", "grade", "id", "Students without valid grades"),
            ("mark", "student_id", "student", "id", "Marks without valid students"),
            ("mark", "subject_id", "subject", "id", "Marks without valid subjects"),
            ("mark", "term_id", "term", "id", "Marks without valid terms"),
            ("mark", "assessment_type_id", "assessment_type", "id", "Marks without valid assessment types"),
        ]
        
        if 'teacher_subject_assignment' in existing_tables:
            integrity_checks.extend([
                ("teacher_subject_assignment", "teacher_id", "teacher", "id", "Teacher assignments without valid teachers"),
                ("teacher_subject_assignment", "subject_id", "subject", "id", "Teacher assignments without valid subjects"),
                ("teacher_subject_assignment", "grade_id", "grade", "id", "Teacher assignments without valid grades"),
            ])
        
        for child_table, child_col, parent_table, parent_col, description in integrity_checks:
            if child_table in existing_tables and parent_table in existing_tables:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {child_table} 
                    WHERE {child_col} IS NOT NULL 
                    AND {child_col} NOT IN (SELECT {parent_col} FROM {parent_table})
                """)
                orphaned_count = cursor.fetchone()[0]
                
                if orphaned_count > 0:
                    data_issues.append(f"{description}: {orphaned_count} records")
                    print(f"  ⚠️  {description}: {orphaned_count} records")
                else:
                    print(f"  ✅ {description}: OK")
        
        # Check for essential data
        print("\n🔍 Checking Essential Data...")
        essential_data_checks = [
            ("grade", "Grades"),
            ("subject", "Subjects"),
            ("term", "Terms"),
            ("assessment_type", "Assessment Types"),
            ("teacher", "Teachers")
        ]
        
        for table, description in essential_data_checks:
            if table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count == 0:
                    print(f"  ⚠️  No {description} found")
                else:
                    print(f"  ✅ {description}: {count} records")
            else:
                print(f"  ❌ {description}: Table missing")
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 HEALTH CHECK SUMMARY")
        print("=" * 50)
        
        total_issues = len(missing_tables) + len(structure_issues) + len(data_issues)
        
        if total_issues == 0:
            print("🎉 Database is healthy! No issues found.")
            health_status = "HEALTHY"
        else:
            print(f"⚠️  Found {total_issues} issues:")
            if missing_tables:
                print(f"  - {len(missing_tables)} missing tables")
            if structure_issues:
                print(f"  - {len(structure_issues)} table structure issues")
            if data_issues:
                print(f"  - {len(data_issues)} data integrity issues")
            health_status = "NEEDS_ATTENTION"
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if missing_tables or structure_issues:
            print("  1. Run 'python migrate_database.py' to fix missing tables/columns")
        if data_issues:
            print("  2. Review and fix data integrity issues")
        if total_issues == 0:
            print("  - Database is ready for production use")
            print("  - All analytics features should work correctly")
        
        conn.close()
        return health_status == "HEALTHY"
        
    except Exception as e:
        print(f"❌ Error during health check: {e}")
        import traceback
        traceback.print_exc()
        return False

def quick_fix_database():
    """Apply quick fixes for common database issues."""
    print("\n🔧 Applying Quick Fixes...")
    
    try:
        # Run migration script
        print("Running database migration...")
        import subprocess
        result = subprocess.run([sys.executable, 'migrate_database.py'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print("✅ Migration completed successfully")
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        return False

if __name__ == '__main__':
    print("🏥 Database Health Check & Repair Tool")
    print("=" * 50)
    
    # Perform health check
    is_healthy = check_database_health()
    
    if not is_healthy:
        print("\n🔧 Would you like to apply automatic fixes? (y/n): ", end="")
        try:
            response = input().lower().strip()
            if response in ['y', 'yes']:
                if quick_fix_database():
                    print("\n🔄 Re-running health check...")
                    check_database_health()
                else:
                    print("\n❌ Automatic fixes failed. Manual intervention required.")
        except KeyboardInterrupt:
            print("\n\n👋 Health check cancelled by user")
    
    print("\n🎯 Health check completed!")
