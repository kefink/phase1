#!/usr/bin/env python3
"""
Fix Dashboard Schema Issues
Adds missing columns that are causing 500 errors in the dashboard.
"""

import mysql.connector
import json

def fix_school_configuration_schema():
    """Fix school_configuration table to include all required columns."""
    print("🔧 Fixing School Configuration Schema for Dashboard")
    print("=" * 50)
    
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
        
        connection_params = {
            'host': creds['host'],
            'database': creds['database_name'],
            'user': creds['username'],
            'password': creds['password'],
            'port': creds['port']
        }
        
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor()
        
        # Check current columns
        cursor.execute("DESCRIBE school_configuration")
        current_columns = [row[0] for row in cursor.fetchall()]
        print(f"Current columns: {', '.join(current_columns)}")
        
        # Add missing columns that the dashboard expects
        missing_columns = [
            ('headteacher_id', 'INTEGER'),
            ('deputy_headteacher_id', 'INTEGER'),
            ('principal_id', 'INTEGER'),
            ('headteacher_name', 'VARCHAR(100) DEFAULT "Head Teacher"'),
            ('deputy_headteacher_name', 'VARCHAR(100) DEFAULT "Deputy Head Teacher"'),
            ('principal_name', 'VARCHAR(100) DEFAULT "Principal"'),
            ('school_name', 'VARCHAR(200) DEFAULT "Your School Name"'),
            ('school_motto', 'VARCHAR(500) DEFAULT "Excellence in Education"'),
            ('school_address', 'TEXT'),
            ('school_phone', 'VARCHAR(50)'),
            ('school_email', 'VARCHAR(100)'),
            ('school_website', 'VARCHAR(100)'),
            ('current_academic_year', 'VARCHAR(20) DEFAULT "2024"'),
            ('current_term', 'VARCHAR(50) DEFAULT "Term 1"'),
            ('use_streams', 'BOOLEAN DEFAULT TRUE'),
            ('grading_system', 'VARCHAR(50) DEFAULT "CBC"'),
            ('show_position', 'BOOLEAN DEFAULT TRUE'),
            ('show_class_average', 'BOOLEAN DEFAULT TRUE'),
            ('show_subject_teacher', 'BOOLEAN DEFAULT FALSE'),
            ('max_raw_marks_default', 'INTEGER DEFAULT 100'),
            ('pass_mark_percentage', 'DECIMAL(5,2) DEFAULT 50.0'),
            ('logo_filename', 'VARCHAR(200)'),
            ('primary_color', 'VARCHAR(7) DEFAULT "#1f7d53"'),
            ('secondary_color', 'VARCHAR(7) DEFAULT "#18230f"'),
            ('accent_color', 'VARCHAR(7) DEFAULT "#4ade80"')
        ]
        
        added_count = 0
        for col_name, col_def in missing_columns:
            if col_name not in current_columns:
                try:
                    cursor.execute(f"ALTER TABLE school_configuration ADD COLUMN {col_name} {col_def}")
                    print(f"✅ Added: {col_name}")
                    added_count += 1
                except Exception as e:
                    print(f"⚠️ Error adding {col_name}: {e}")
        
        print(f"\n📊 Added {added_count} missing columns")
        
        # Insert default configuration if table is empty
        cursor.execute("SELECT COUNT(*) FROM school_configuration")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📝 Inserting default school configuration...")
            cursor.execute("""
                INSERT INTO school_configuration (
                    config_key, config_value, config_type, description, is_active,
                    school_name, school_motto, current_academic_year, current_term,
                    use_streams, grading_system, headteacher_name, deputy_headteacher_name,
                    principal_name, show_position, show_class_average, show_subject_teacher
                ) VALUES (
                    'default_config', 'main_configuration', 'system', 'Main school configuration', TRUE,
                    'Your School Name', 'Excellence in Education', '2024', 'Term 1',
                    TRUE, 'CBC', 'Head Teacher', 'Deputy Head Teacher',
                    'Principal', TRUE, TRUE, FALSE
                )
            """)
            print("✅ Default configuration inserted")
        
        # Test the problematic query
        print("\n🧪 Testing dashboard queries...")
        test_queries = [
            "SELECT school_name FROM school_configuration LIMIT 1",
            "SELECT headteacher_id FROM school_configuration LIMIT 1",
            "SELECT headteacher_name FROM school_configuration LIMIT 1",
            "SELECT use_streams FROM school_configuration LIMIT 1"
        ]
        
        for query in test_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                print(f"✅ {query} -> {result}")
            except Exception as e:
                print(f"❌ {query} -> {e}")
                return False
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n🎉 School configuration schema fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Schema fix failed: {e}")
        return False

def fix_subject_management_schema():
    """Fix any schema issues with subject management."""
    print("\n🔧 Checking Subject Management Schema")
    print("=" * 40)
    
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
        
        connection_params = {
            'host': creds['host'],
            'database': creds['database_name'],
            'user': creds['username'],
            'password': creds['password'],
            'port': creds['port']
        }
        
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor()
        
        # Check subject table structure
        cursor.execute("DESCRIBE subject")
        subject_columns = [row[0] for row in cursor.fetchall()]
        print(f"Subject table columns: {', '.join(subject_columns)}")
        
        # Add missing columns for subject management
        missing_subject_columns = [
            ('description', 'TEXT'),
            ('is_active', 'BOOLEAN DEFAULT TRUE'),
            ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
            ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
        ]
        
        for col_name, col_def in missing_subject_columns:
            if col_name not in subject_columns:
                try:
                    cursor.execute(f"ALTER TABLE subject ADD COLUMN {col_name} {col_def}")
                    print(f"✅ Added subject.{col_name}")
                except Exception as e:
                    print(f"⚠️ Error adding subject.{col_name}: {e}")
        
        # Test subject queries
        cursor.execute("SELECT COUNT(*) FROM subject")
        subject_count = cursor.fetchone()[0]
        print(f"✅ Subject table accessible: {subject_count} subjects")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Subject schema check failed: {e}")
        return False

def main():
    """Main function to fix all dashboard schema issues."""
    print("🔧 DASHBOARD SCHEMA FIX")
    print("Fixing all schema issues causing 500 errors")
    print("=" * 60)
    
    success1 = fix_school_configuration_schema()
    success2 = fix_subject_management_schema()
    
    if success1 and success2:
        print("\n🎉 ALL DASHBOARD SCHEMA ISSUES FIXED!")
        print("✅ School configuration table updated")
        print("✅ Subject management schema verified")
        print("✅ Dashboard should now work without 500 errors")
        return True
    else:
        print("\n❌ SOME SCHEMA FIXES FAILED!")
        print("Please check the errors above")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
