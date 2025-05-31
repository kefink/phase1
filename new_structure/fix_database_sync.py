#!/usr/bin/env python3
"""
Fix database synchronization issues.
This script ensures the database and SQLAlchemy models are properly synchronized.
"""

import os
import sys
import sqlite3
from datetime import datetime

def fix_database_sync():
    """Fix database synchronization issues."""
    print("🔧 Fixing database synchronization...")
    
    db_path = 'kirima_primary.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False
    
    try:
        # Create a backup first
        backup_path = f'kirima_primary.db.backup_sync_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current teacher table structure
        cursor.execute("PRAGMA table_info(teacher)")
        columns = cursor.fetchall()
        print(f"📋 Current teacher table columns: {len(columns)}")
        
        existing_columns = [col[1] for col in columns]
        print(f"📋 Column names: {existing_columns}")
        
        # Required columns for enhanced teacher model
        required_columns = [
            ('full_name', 'TEXT'),
            ('employee_id', 'TEXT'),
            ('phone_number', 'TEXT'),
            ('email', 'TEXT'),
            ('qualification', 'TEXT'),
            ('specialization', 'TEXT'),
            ('is_active', 'BOOLEAN DEFAULT 1'),
            ('date_joined', 'DATE')
        ]
        
        # Add missing columns
        for col_name, col_type in required_columns:
            if col_name not in existing_columns:
                print(f"🔧 Adding missing column: {col_name}")
                try:
                    cursor.execute(f"ALTER TABLE teacher ADD COLUMN {col_name} {col_type}")
                    conn.commit()
                    print(f"✅ Added column: {col_name}")
                except Exception as e:
                    print(f"⚠️  Column {col_name} might already exist: {e}")
        
        # Check school_configuration table
        cursor.execute("PRAGMA table_info(school_configuration)")
        config_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 School config columns: {config_columns}")
        
        # Required columns for school configuration
        config_required = [
            ('headteacher_id', 'INTEGER'),
            ('deputy_headteacher_id', 'INTEGER')
        ]
        
        for col_name, col_type in config_required:
            if col_name not in config_columns:
                print(f"🔧 Adding missing config column: {col_name}")
                try:
                    cursor.execute(f"ALTER TABLE school_configuration ADD COLUMN {col_name} {col_type}")
                    conn.commit()
                    print(f"✅ Added config column: {col_name}")
                except Exception as e:
                    print(f"⚠️  Config column {col_name} might already exist: {e}")
        
        # Update existing teacher records with default values if they're NULL
        print("🔧 Updating existing teacher records...")
        
        # Get all teachers
        cursor.execute("SELECT id, username FROM teacher")
        teachers = cursor.fetchall()
        
        for teacher_id, username in teachers:
            updates = []
            
            # Check and update full_name
            cursor.execute("SELECT full_name FROM teacher WHERE id = ?", (teacher_id,))
            full_name = cursor.fetchone()[0]
            if not full_name:
                updates.append(f"full_name = '{username}'")
            
            # Check and update employee_id
            cursor.execute("SELECT employee_id FROM teacher WHERE id = ?", (teacher_id,))
            employee_id = cursor.fetchone()[0]
            if not employee_id:
                updates.append(f"employee_id = 'EMP{teacher_id:03d}'")
            
            # Check and update is_active
            cursor.execute("SELECT is_active FROM teacher WHERE id = ?", (teacher_id,))
            is_active = cursor.fetchone()[0]
            if is_active is None:
                updates.append("is_active = 1")
            
            # Apply updates if needed
            if updates:
                update_sql = f"UPDATE teacher SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(update_sql, (teacher_id,))
                print(f"✅ Updated teacher {username} (ID: {teacher_id})")
        
        conn.commit()
        
        # Verify the final structure
        cursor.execute("PRAGMA table_info(teacher)")
        final_columns = [col[1] for col in cursor.fetchall()]
        print(f"✅ Final teacher table columns: {final_columns}")
        
        # Test a simple query
        cursor.execute("SELECT id, username, full_name, employee_id FROM teacher LIMIT 1")
        test_result = cursor.fetchone()
        if test_result:
            print(f"✅ Test query successful: {test_result}")
        
        conn.close()
        print("✅ Database synchronization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database sync failed: {e}")
        return False

def clear_sqlalchemy_cache():
    """Clear any SQLAlchemy metadata cache."""
    print("🔧 Clearing SQLAlchemy cache...")
    
    try:
        # Remove any .pyc files that might be caching old model definitions
        import glob
        pyc_files = glob.glob("**/*.pyc", recursive=True)
        for pyc_file in pyc_files:
            try:
                os.remove(pyc_file)
            except:
                pass
        
        # Remove __pycache__ directories
        pycache_dirs = glob.glob("**/__pycache__", recursive=True)
        for pycache_dir in pycache_dirs:
            try:
                import shutil
                shutil.rmtree(pycache_dir)
            except:
                pass
        
        print("✅ Cache cleared successfully!")
        return True
        
    except Exception as e:
        print(f"⚠️  Cache clearing failed: {e}")
        return False

def test_flask_models():
    """Test that Flask models work with the database."""
    print("🔧 Testing Flask models...")
    
    try:
        # Add the current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        # Import Flask components
        from new_structure import create_app
        from new_structure.extensions import db
        
        app = create_app('development')
        
        with app.app_context():
            # Test database connection
            try:
                # Import models after app context is created
                from new_structure.models.user import Teacher
                from new_structure.models.academic import SchoolConfiguration
                
                # Test a simple query
                teacher_count = Teacher.query.count()
                print(f"✅ Teacher model working - found {teacher_count} teachers")
                
                # Test getting a specific teacher
                first_teacher = Teacher.query.first()
                if first_teacher:
                    print(f"✅ First teacher: {first_teacher.username}")
                    if hasattr(first_teacher, 'full_name'):
                        print(f"✅ Full name: {first_teacher.full_name}")
                    if hasattr(first_teacher, 'employee_id'):
                        print(f"✅ Employee ID: {first_teacher.employee_id}")
                
                # Test school configuration
                config = SchoolConfiguration.query.first()
                if config:
                    print(f"✅ School config working: {config.school_name}")
                
                print("✅ Flask models test completed successfully!")
                return True
                
            except Exception as e:
                print(f"❌ Flask models test failed: {e}")
                return False
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def main():
    """Run all fixes."""
    print("🚀 Database Synchronization Fix")
    print("=" * 50)
    
    success = True
    
    # Step 1: Fix database structure
    if not fix_database_sync():
        success = False
    
    # Step 2: Clear cache
    clear_sqlalchemy_cache()
    
    # Step 3: Test Flask models
    if not test_flask_models():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Database synchronization completed successfully!")
        print("\n🚀 Your application should now work properly.")
        print("Try starting your Flask app again: python run.py")
    else:
        print("⚠️  Some issues detected. Please check the output above.")
    
    return success

if __name__ == "__main__":
    main()
