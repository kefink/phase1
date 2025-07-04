#!/usr/bin/env python3
"""
Fix existing students who don't have grade_id set using direct SQL.
"""

import pymysql
import json
import os

def load_mysql_config():
    """Load MySQL configuration from the working config file."""
    config_path = os.path.join(os.path.dirname(__file__), 'mysql_migration', 'mysql_working_config.json')

    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        return None

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Add database name - assuming it's hillview_mvp based on the project
    config['database'] = 'hillview_mvp'

    return config

def fix_student_grade_ids():
    """Update all students to have correct grade_id based on their stream."""
    
    # Load MySQL configuration
    mysql_config = load_mysql_config()
    if not mysql_config:
        print("❌ Could not load MySQL configuration")
        return False
    
    try:
        # First connect without database to check what databases exist
        connection = pymysql.connect(
            host=mysql_config['host'],
            user=mysql_config['user'],
            password=mysql_config['password'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        print("✅ Connected to MySQL server")

        # Check available databases
        with connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print("📊 Available databases:")
            for db in databases:
                print(f"  - {db['Database']}")

        connection.close()

        # Now connect to the correct database (try different names)
        possible_databases = ['hillview_demo001', 'hillview_mvp', 'hillview', 'school_management', 'kirima_primary']
        target_database = None

        for db_name in possible_databases:
            try:
                test_connection = pymysql.connect(
                    host=mysql_config['host'],
                    user=mysql_config['user'],
                    password=mysql_config['password'],
                    database=db_name,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
                test_connection.close()
                target_database = db_name
                print(f"✅ Found target database: {db_name}")
                break
            except:
                continue

        if not target_database:
            print("❌ Could not find a suitable database")
            return False

        # Connect to MySQL database
        connection = pymysql.connect(
            host=mysql_config['host'],
            user=mysql_config['user'],
            password=mysql_config['password'],
            database=target_database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print("✅ Connected to MySQL database")
        
        with connection.cursor() as cursor:
            # First, check how many students need fixing
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM student 
                WHERE grade_id IS NULL AND stream_id IS NOT NULL
            """)
            result = cursor.fetchone()
            students_to_fix = result['count']
            print(f"📊 Found {students_to_fix} students that need grade_id fixed")
            
            if students_to_fix == 0:
                print("✅ All students already have grade_id set!")
                return True
            
            # Update students' grade_id based on their stream's grade_id
            cursor.execute("""
                UPDATE student s
                INNER JOIN stream st ON s.stream_id = st.id
                SET s.grade_id = st.grade_id
                WHERE s.grade_id IS NULL AND s.stream_id IS NOT NULL
            """)
            
            updated_rows = cursor.rowcount
            print(f"✅ Updated {updated_rows} students with correct grade_id")
            
            # Commit the changes
            connection.commit()
            
            # Verify the fix
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM student 
                WHERE grade_id IS NULL
            """)
            result = cursor.fetchone()
            remaining_without_grade = result['count']
            print(f"📊 Students still without grade_id: {remaining_without_grade}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    print("🔧 Starting to fix student grade_ids using direct SQL...")
    success = fix_student_grade_ids()
    if success:
        print("✅ Grade ID fix completed successfully!")
    else:
        print("❌ Grade ID fix failed!")
        exit(1)
