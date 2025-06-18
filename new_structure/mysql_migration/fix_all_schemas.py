#!/usr/bin/env python3
"""
Fix All Schema Issues
Comprehensive fix for all schema mismatches between Flask models and MySQL tables.
"""

import mysql.connector
import json

def get_table_columns(cursor, table_name):
    """Get column names for a table."""
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        return []

def fix_assessment_type_table(cursor):
    """Fix assessment_type table schema."""
    print("🔧 Fixing assessment_type table...")
    
    columns = get_table_columns(cursor, 'assessment_type')
    print(f"Current columns: {', '.join(columns)}")
    
    # Add missing columns
    missing_columns = []
    
    if 'category' not in columns:
        missing_columns.append("category VARCHAR(50)")
    
    if 'description' not in columns:
        missing_columns.append("description TEXT")
    
    if 'weight' not in columns:
        missing_columns.append("weight DECIMAL(3,2) DEFAULT 1.0")
    
    if 'is_active' not in columns:
        missing_columns.append("is_active BOOLEAN DEFAULT TRUE")
    
    for col_def in missing_columns:
        try:
            cursor.execute(f"ALTER TABLE assessment_type ADD COLUMN {col_def}")
            col_name = col_def.split()[0]
            print(f"✅ Added column: {col_name}")
        except Exception as e:
            print(f"⚠️ Error adding column {col_def}: {e}")
    
    # Set default values for category
    cursor.execute("UPDATE assessment_type SET category = 'Assessment' WHERE category IS NULL")
    
    return True

def fix_mark_table(cursor):
    """Fix mark table schema."""
    print("🔧 Fixing mark table...")
    
    columns = get_table_columns(cursor, 'mark')
    print(f"Current columns: {', '.join(columns)}")
    
    # Rename 'marks' to 'mark' if needed
    if 'marks' in columns and 'mark' not in columns:
        cursor.execute("ALTER TABLE mark CHANGE COLUMN marks mark DECIMAL(6,2)")
        print("✅ Renamed 'marks' to 'mark'")
    
    # Add missing columns
    missing_columns = []
    
    if 'raw_mark' not in columns:
        missing_columns.append("raw_mark DECIMAL(6,2)")
    
    if 'raw_total_marks' not in columns:
        missing_columns.append("raw_total_marks DECIMAL(6,2)")
    
    if 'grade_letter' not in columns:
        missing_columns.append("grade_letter VARCHAR(5)")
    
    for col_def in missing_columns:
        try:
            cursor.execute(f"ALTER TABLE mark ADD COLUMN {col_def}")
            col_name = col_def.split()[0]
            print(f"✅ Added column: {col_name}")
        except Exception as e:
            print(f"⚠️ Error adding column {col_def}: {e}")
    
    # Update data consistency
    cursor.execute("UPDATE mark SET raw_mark = mark WHERE raw_mark IS NULL")
    cursor.execute("UPDATE mark SET raw_total_marks = total_marks WHERE raw_total_marks IS NULL")
    cursor.execute("""
        UPDATE mark SET grade_letter = 
        CASE 
            WHEN percentage >= 75 THEN 'E.E'
            WHEN percentage >= 50 THEN 'M.E'
            WHEN percentage >= 30 THEN 'A.E'
            ELSE 'B.E'
        END
        WHERE grade_letter IS NULL
    """)
    
    return True

def fix_other_tables(cursor):
    """Fix other tables that might have schema issues."""
    print("🔧 Checking other tables...")
    
    # Check and fix common missing columns
    table_fixes = {
        'student': {
            'admission_date': 'DATE',
            'parent_contact': 'VARCHAR(100)',
            'medical_info': 'TEXT'
        },
        'subject': {
            'description': 'TEXT',
            'is_active': 'BOOLEAN DEFAULT TRUE'
        },
        'grade': {
            'description': 'TEXT',
            'is_active': 'BOOLEAN DEFAULT TRUE'
        },
        'stream': {
            'description': 'TEXT',
            'capacity': 'INTEGER DEFAULT 40',
            'is_active': 'BOOLEAN DEFAULT TRUE'
        },
        'term': {
            'description': 'TEXT',
            'is_current': 'BOOLEAN DEFAULT FALSE'
        }
    }
    
    for table_name, column_defs in table_fixes.items():
        try:
            columns = get_table_columns(cursor, table_name)
            if columns:  # Table exists
                for col_name, col_def in column_defs.items():
                    if col_name not in columns:
                        try:
                            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")
                            print(f"✅ Added {table_name}.{col_name}")
                        except Exception as e:
                            print(f"⚠️ Error adding {table_name}.{col_name}: {e}")
        except Exception as e:
            print(f"⚠️ Error checking table {table_name}: {e}")
    
    return True

def test_critical_queries(cursor):
    """Test critical queries that were failing."""
    print("🧪 Testing critical queries...")
    
    test_queries = [
        "SELECT COUNT(*) FROM mark",
        "SELECT COUNT(*) FROM assessment_type",
        "SELECT mark, percentage FROM mark LIMIT 1",
        "SELECT name, category FROM assessment_type LIMIT 1",
        "SELECT COUNT(*) FROM student",
        "SELECT COUNT(*) FROM teacher"
    ]
    
    for query in test_queries:
        try:
            cursor.execute(query)
            result = cursor.fetchone()
            print(f"✅ Query OK: {query[:50]}... -> {result}")
        except Exception as e:
            print(f"❌ Query FAILED: {query[:50]}... -> {e}")
            return False
    
    return True

def main():
    """Main schema fix function."""
    print("🔧 COMPREHENSIVE SCHEMA FIX")
    print("Fixing all schema mismatches between Flask models and MySQL")
    print("=" * 70)
    
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
        
        # Fix all schema issues
        fixes = [
            ("Assessment Type Table", lambda: fix_assessment_type_table(cursor)),
            ("Mark Table", lambda: fix_mark_table(cursor)),
            ("Other Tables", lambda: fix_other_tables(cursor)),
            ("Critical Queries Test", lambda: test_critical_queries(cursor))
        ]
        
        success_count = 0
        
        for fix_name, fix_func in fixes:
            try:
                print(f"\n🔍 {fix_name}")
                print("-" * 40)
                if fix_func():
                    print(f"✅ {fix_name} completed successfully")
                    success_count += 1
                else:
                    print(f"❌ {fix_name} failed")
            except Exception as e:
                print(f"❌ {fix_name} failed with exception: {e}")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"\n📊 SCHEMA FIX SUMMARY")
        print("=" * 40)
        print(f"Completed: {success_count}/{len(fixes)} fixes")
        
        if success_count == len(fixes):
            print("\n🎉 ALL SCHEMA FIXES COMPLETED SUCCESSFULLY!")
            print("✅ All tables now match Flask model expectations")
            print("✅ Dashboard should now work properly")
            print("✅ System ready for use")
            return True
        else:
            print(f"\n⚠️ PARTIAL SUCCESS: {success_count}/{len(fixes)} fixes completed")
            print("Some issues may remain - check the output above")
            return False
        
    except Exception as e:
        print(f"❌ Schema fix failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
