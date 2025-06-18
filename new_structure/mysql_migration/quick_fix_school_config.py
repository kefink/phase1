#!/usr/bin/env python3
"""
Quick Fix for School Configuration
Adds the missing columns that are causing 500 errors.
"""

import mysql.connector
import json

def quick_fix_school_config():
    """Quick fix for school configuration table."""
    print("🔧 Quick Fix for School Configuration")
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
        
        # Check current columns
        cursor.execute("DESCRIBE school_configuration")
        columns = [row[0] for row in cursor.fetchall()]
        print(f"Current columns: {', '.join(columns)}")
        
        # Add the specific missing columns that are causing errors
        missing_columns = [
            ('school_name', 'VARCHAR(200) DEFAULT "Your School Name"'),
            ('school_motto', 'VARCHAR(500) DEFAULT "Excellence in Education"'),
            ('school_address', 'TEXT'),
            ('school_phone', 'VARCHAR(50)'),
            ('school_email', 'VARCHAR(100)'),
            ('school_website', 'VARCHAR(100)'),
            ('current_academic_year', 'VARCHAR(20) DEFAULT "2024"'),
            ('current_term', 'VARCHAR(50) DEFAULT "Term 1"'),
            ('headteacher_name', 'VARCHAR(100) DEFAULT "Head Teacher"'),
            ('deputy_headteacher_name', 'VARCHAR(100) DEFAULT "Deputy Head Teacher"'),
            ('logo_filename', 'VARCHAR(200)'),
            ('primary_color', 'VARCHAR(7) DEFAULT "#1f7d53"'),
            ('secondary_color', 'VARCHAR(7) DEFAULT "#18230f"'),
            ('use_streams', 'BOOLEAN DEFAULT TRUE'),  # This is the key missing column
            ('grading_system', 'VARCHAR(50) DEFAULT "CBC"'),
            ('show_position', 'BOOLEAN DEFAULT TRUE'),
            ('show_class_average', 'BOOLEAN DEFAULT TRUE'),
            ('show_subject_teacher', 'BOOLEAN DEFAULT FALSE'),
            ('max_raw_marks_default', 'INTEGER DEFAULT 100'),
            ('pass_mark_percentage', 'DECIMAL(5,2) DEFAULT 50.0')
        ]
        
        added_count = 0
        for col_name, col_def in missing_columns:
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE school_configuration ADD COLUMN {col_name} {col_def}")
                    print(f"✅ Added: {col_name}")
                    added_count += 1
                except Exception as e:
                    print(f"⚠️ Error adding {col_name}: {e}")
        
        print(f"\n📊 Added {added_count} missing columns")
        
        # Insert default data if table is empty
        cursor.execute("SELECT COUNT(*) FROM school_configuration")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📝 Inserting default configuration...")
            cursor.execute("""
                INSERT INTO school_configuration (
                    school_name, school_motto, current_academic_year, current_term,
                    use_streams, grading_system, headteacher_name, deputy_headteacher_name
                ) VALUES (
                    'Your School Name', 'Excellence in Education', '2024', 'Term 1',
                    TRUE, 'CBC', 'Head Teacher', 'Deputy Head Teacher'
                )
            """)
            print("✅ Default configuration inserted")
        
        # Test the problematic query
        print("\n🧪 Testing problematic queries...")
        test_queries = [
            "SELECT school_name FROM school_configuration LIMIT 1",
            "SELECT use_streams FROM school_configuration LIMIT 1",
            "SELECT grading_system FROM school_configuration LIMIT 1"
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
        
        print("\n🎉 Quick fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Quick fix failed: {e}")
        return False

def main():
    """Main function."""
    print("🚀 QUICK SCHOOL CONFIGURATION FIX")
    print("Fixing the immediate 500 error issues")
    print("=" * 50)
    
    success = quick_fix_school_config()
    
    if success:
        print("\n✅ QUICK FIX COMPLETED!")
        print("The dashboard should now work without school configuration errors.")
        print("Try accessing the headteacher dashboard again.")
    else:
        print("\n❌ QUICK FIX FAILED!")
        print("Please check the errors above.")
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
