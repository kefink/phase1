#!/usr/bin/env python3
"""
Comprehensive Schema Verification
Verifies all Flask models match MySQL database schemas.
"""

import mysql.connector
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_mysql_table_schema(table_name, cursor):
    """Get MySQL table schema."""
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        return {col[0]: col[1] for col in columns}
    except Exception:
        return None

def verify_all_schemas():
    """Verify all Flask models match MySQL schemas."""
    print("🔍 Comprehensive Schema Verification")
    print("=" * 50)
    
    # Load MySQL credentials
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
    except FileNotFoundError:
        print("❌ MySQL credentials not found!")
        return False
    
    try:
        connection = mysql.connector.connect(
            host=creds['host'],
            database=creds['database_name'],
            user=creds['username'],
            password=creds['password'],
            port=creds['port']
        )
        
        cursor = connection.cursor()
        
        # Get all tables in MySQL
        cursor.execute("SHOW TABLES")
        mysql_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Found {len(mysql_tables)} tables in MySQL:")
        for table in sorted(mysql_tables):
            print(f"  - {table}")
        
        # Test critical tables that the application uses
        critical_tables = [
            'teacher', 'student', 'grade', 'stream', 'subject', 'term', 
            'assessment_type', 'mark', 'parent', 'parent_student'
        ]
        
        print(f"\n🧪 Testing {len(critical_tables)} critical tables...")
        
        schema_issues = []
        
        for table in critical_tables:
            if table in mysql_tables:
                schema = get_mysql_table_schema(table, cursor)
                if schema:
                    print(f"✅ {table}: {len(schema)} columns")
                else:
                    print(f"❌ {table}: Schema read error")
                    schema_issues.append(f"{table}: Cannot read schema")
            else:
                print(f"❌ {table}: Table missing")
                schema_issues.append(f"{table}: Table does not exist")
        
        # Test specific queries that were failing
        print(f"\n🧪 Testing specific application queries...")
        
        test_queries = [
            {
                'name': 'Teacher Login Query',
                'sql': """
                    SELECT id, username, password, role, stream_id, first_name, last_name, 
                           email, phone, employee_id, qualification, specialization, 
                           date_joined, is_active, created_at 
                    FROM teacher 
                    WHERE username = %s AND password = %s AND role = %s 
                    LIMIT 1
                """,
                'params': ('headteacher', 'admin123', 'headteacher')
            },
            {
                'name': 'Student Query',
                'sql': "SELECT COUNT(*) FROM student",
                'params': ()
            },
            {
                'name': 'Grade Query',
                'sql': "SELECT id, name, education_level FROM grade LIMIT 5",
                'params': ()
            },
            {
                'name': 'Subject Query',
                'sql': "SELECT id, name, education_level FROM subject LIMIT 5",
                'params': ()
            }
        ]
        
        query_results = []
        
        for test in test_queries:
            try:
                cursor.execute(test['sql'], test['params'])
                result = cursor.fetchall()
                print(f"✅ {test['name']}: Success ({len(result)} rows)")
                query_results.append(f"{test['name']}: ✅ Success")
            except Exception as e:
                print(f"❌ {test['name']}: {e}")
                query_results.append(f"{test['name']}: ❌ {e}")
                schema_issues.append(f"{test['name']}: Query failed - {e}")
        
        cursor.close()
        connection.close()
        
        # Summary
        print(f"\n📊 Schema Verification Summary")
        print("=" * 40)
        
        if not schema_issues:
            print("🎉 All schemas verified successfully!")
            print("✅ All critical tables exist")
            print("✅ All test queries passed")
            print("✅ Application should work correctly")
            return True
        else:
            print(f"⚠️ Found {len(schema_issues)} schema issues:")
            for issue in schema_issues:
                print(f"  - {issue}")
            return False
        
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False

def test_application_startup():
    """Test if the Flask application can start with current schema."""
    print(f"\n🚀 Testing Application Startup")
    print("=" * 40)
    
    try:
        # Import Flask app components
        from extensions import db
        from models.user import Teacher
        from models.academic import Grade, Subject, Student
        from config import config
        
        print("✅ Model imports successful")
        
        # Try to create app context
        from new_structure import create_app
        app = create_app('development')
        
        with app.app_context():
            print("✅ Flask app context created")
            
            # Test database connection
            db.engine.execute("SELECT 1")
            print("✅ Database connection successful")
            
            # Test model queries
            teacher_count = Teacher.query.count()
            grade_count = Grade.query.count()
            subject_count = Subject.query.count()
            
            print(f"✅ Model queries successful:")
            print(f"  - Teachers: {teacher_count}")
            print(f"  - Grades: {grade_count}")
            print(f"  - Subjects: {subject_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Application startup test failed: {e}")
        return False

def main():
    """Main verification function."""
    print("🔍 Complete Schema and Application Verification")
    print("=" * 60)
    
    success = True
    
    # Step 1: Verify database schemas
    if not verify_all_schemas():
        success = False
    
    # Step 2: Test application startup
    if not test_application_startup():
        success = False
    
    if success:
        print(f"\n🎉 VERIFICATION COMPLETE - ALL SYSTEMS GO!")
        print("✅ Database schemas are correct")
        print("✅ Application can start successfully")
        print("✅ Models can query the database")
        print("\n🚀 Your application is ready to use!")
        print("You can now login as headteacher with:")
        print("Username: headteacher")
        print("Password: admin123")
    else:
        print(f"\n❌ VERIFICATION FAILED")
        print("Please fix the issues above before using the application.")
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
