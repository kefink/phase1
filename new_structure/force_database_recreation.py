#!/usr/bin/env python3
"""
Force database recreation with proper schema.
This script will backup existing data and recreate the database with the correct schema.
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime

def backup_existing_data():
    """Backup existing data from the database."""
    print("📦 Backing up existing data...")
    
    db_path = 'kirima_primary.db'
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Backup data
        backup_data = {}
        
        # Backup teachers
        cursor.execute("SELECT id, username, password, role, stream_id FROM teacher")
        backup_data['teachers'] = cursor.fetchall()
        print(f"✅ Backed up {len(backup_data['teachers'])} teachers")
        
        # Backup school configuration
        cursor.execute("SELECT * FROM school_configuration")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        backup_data['school_config'] = {'columns': columns, 'data': rows}
        print(f"✅ Backed up school configuration")
        
        # Backup other important tables
        tables_to_backup = ['student', 'subject', 'grade', 'stream', 'term', 'assessment_type']
        for table in tables_to_backup:
            try:
                cursor.execute(f"SELECT * FROM {table}")
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                backup_data[table] = {'columns': columns, 'data': rows}
                print(f"✅ Backed up {table}: {len(rows)} records")
            except Exception as e:
                print(f"⚠️  Could not backup {table}: {e}")
        
        conn.close()
        return backup_data
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def create_enhanced_database():
    """Create database with enhanced schema."""
    print("🔧 Creating enhanced database schema...")
    
    db_path = 'kirima_primary.db'
    
    # Create backup of current database
    backup_path = f'kirima_primary.db.backup_recreation_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backup created: {backup_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop and recreate teacher table with enhanced schema
        cursor.execute("DROP TABLE IF EXISTS teacher_new")
        
        create_teacher_sql = """
        CREATE TABLE teacher_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(100) NOT NULL,
            password VARCHAR(100) NOT NULL,
            role VARCHAR(50) NOT NULL,
            stream_id INTEGER,
            full_name TEXT,
            employee_id TEXT,
            phone_number TEXT,
            email TEXT,
            qualification TEXT,
            specialization TEXT,
            is_active BOOLEAN DEFAULT 1,
            date_joined DATE,
            FOREIGN KEY (stream_id) REFERENCES stream (id)
        )
        """
        
        cursor.execute(create_teacher_sql)
        print("✅ Created enhanced teacher table")
        
        # Copy existing teacher data
        cursor.execute("""
            INSERT INTO teacher_new (id, username, password, role, stream_id, full_name, employee_id, is_active)
            SELECT 
                id, 
                username, 
                password, 
                role, 
                stream_id,
                username as full_name,
                'EMP' || printf('%03d', id) as employee_id,
                1 as is_active
            FROM teacher
        """)
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE teacher")
        cursor.execute("ALTER TABLE teacher_new RENAME TO teacher")
        print("✅ Migrated teacher data to enhanced schema")
        
        # Ensure school_configuration has enhanced columns
        cursor.execute("PRAGMA table_info(school_configuration)")
        config_columns = [col[1] for col in cursor.fetchall()]
        
        if 'headteacher_id' not in config_columns:
            cursor.execute("ALTER TABLE school_configuration ADD COLUMN headteacher_id INTEGER")
            print("✅ Added headteacher_id to school_configuration")
        
        if 'deputy_headteacher_id' not in config_columns:
            cursor.execute("ALTER TABLE school_configuration ADD COLUMN deputy_headteacher_id INTEGER")
            print("✅ Added deputy_headteacher_id to school_configuration")
        
        conn.commit()
        conn.close()
        
        print("✅ Enhanced database schema created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False

def verify_database_schema():
    """Verify the database schema is correct."""
    print("🔍 Verifying database schema...")
    
    try:
        conn = sqlite3.connect('kirima_primary.db')
        cursor = conn.cursor()
        
        # Check teacher table
        cursor.execute("PRAGMA table_info(teacher)")
        teacher_columns = [col[1] for col in cursor.fetchall()]
        
        required_teacher_columns = [
            'id', 'username', 'password', 'role', 'stream_id',
            'full_name', 'employee_id', 'phone_number', 'email',
            'qualification', 'specialization', 'is_active', 'date_joined'
        ]
        
        missing_columns = [col for col in required_teacher_columns if col not in teacher_columns]
        
        if missing_columns:
            print(f"❌ Missing teacher columns: {missing_columns}")
            return False
        else:
            print(f"✅ Teacher table has all required columns: {len(teacher_columns)} total")
        
        # Check school_configuration table
        cursor.execute("PRAGMA table_info(school_configuration)")
        config_columns = [col[1] for col in cursor.fetchall()]
        
        required_config_columns = ['headteacher_id', 'deputy_headteacher_id']
        missing_config = [col for col in required_config_columns if col not in config_columns]
        
        if missing_config:
            print(f"❌ Missing config columns: {missing_config}")
            return False
        else:
            print(f"✅ School configuration has all required columns")
        
        # Test a query
        cursor.execute("SELECT id, username, full_name, employee_id FROM teacher LIMIT 1")
        test_result = cursor.fetchone()
        if test_result:
            print(f"✅ Test query successful: {test_result}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False

def test_flask_integration():
    """Test Flask integration with the new schema."""
    print("🔧 Testing Flask integration...")
    
    try:
        # Clear Python cache
        import glob
        pyc_files = glob.glob("**/*.pyc", recursive=True)
        for pyc_file in pyc_files:
            try:
                os.remove(pyc_file)
            except:
                pass
        
        # Clear __pycache__ directories
        pycache_dirs = glob.glob("**/__pycache__", recursive=True)
        for pycache_dir in pycache_dirs:
            try:
                shutil.rmtree(pycache_dir)
            except:
                pass
        
        print("✅ Cleared Python cache")
        
        # Test Flask app
        sys.path.insert(0, os.getcwd())
        
        from new_structure import create_app
        from new_structure.extensions import db
        
        app = create_app('development')
        
        with app.app_context():
            # Force SQLAlchemy to reflect the new schema
            db.engine.dispose()  # Close all connections
            
            from new_structure.models.user import Teacher
            from new_structure.models.academic import SchoolConfiguration
            
            # Test queries
            teacher_count = Teacher.query.count()
            print(f"✅ Teacher model working - found {teacher_count} teachers")
            
            if teacher_count > 0:
                first_teacher = Teacher.query.first()
                print(f"✅ First teacher: {first_teacher.username}")
                print(f"✅ Full name: {first_teacher.full_name}")
                print(f"✅ Employee ID: {first_teacher.employee_id}")
            
            config = SchoolConfiguration.query.first()
            if config:
                print(f"✅ School config working: {config.school_name}")
            
            print("✅ Flask integration test successful!")
            return True
        
    except Exception as e:
        print(f"❌ Flask integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the database recreation process."""
    print("🚀 Database Recreation and Enhancement")
    print("=" * 60)
    
    # Step 1: Backup existing data
    backup_data = backup_existing_data()
    if not backup_data:
        print("❌ Could not backup data. Aborting.")
        return False
    
    # Step 2: Create enhanced database
    if not create_enhanced_database():
        print("❌ Could not create enhanced database. Aborting.")
        return False
    
    # Step 3: Verify schema
    if not verify_database_schema():
        print("❌ Schema verification failed. Aborting.")
        return False
    
    # Step 4: Test Flask integration
    if not test_flask_integration():
        print("❌ Flask integration test failed.")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Database recreation completed successfully!")
    print("\n🚀 Your Flask application should now work properly.")
    print("Try starting your app: python run.py")
    
    return True

if __name__ == "__main__":
    main()
