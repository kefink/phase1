#!/usr/bin/env python3
"""
Fix Mark Table Schema
Fixes the mark table to match the Flask model expectations.
"""

import mysql.connector
import json

def fix_mark_table_schema():
    """Fix the mark table schema to match Flask model."""
    print("🔧 Fixing Mark Table Schema")
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
        
        print("📊 Current mark table structure:")
        cursor.execute("DESCRIBE mark")
        current_columns = cursor.fetchall()
        for col in current_columns:
            print(f"  {col[0]:<20} {col[1]:<20}")
        
        # Check what columns exist
        column_names = [col[0] for col in current_columns]
        
        # Fix 1: Rename 'marks' to 'mark' if needed
        if 'marks' in column_names and 'mark' not in column_names:
            print("\n🔧 Renaming 'marks' column to 'mark'...")
            cursor.execute("ALTER TABLE mark CHANGE COLUMN marks mark DECIMAL(6,2)")
            print("✅ Renamed 'marks' to 'mark'")
        
        # Fix 2: Add missing columns that the Flask model expects
        missing_columns = []
        
        expected_columns = {
            'raw_mark': 'DECIMAL(6,2)',
            'raw_total_marks': 'DECIMAL(6,2)', 
            'grade_letter': 'VARCHAR(5)'
        }
        
        for col_name, col_type in expected_columns.items():
            if col_name not in column_names:
                missing_columns.append((col_name, col_type))
        
        if missing_columns:
            print(f"\n🔧 Adding {len(missing_columns)} missing columns...")
            for col_name, col_type in missing_columns:
                try:
                    cursor.execute(f"ALTER TABLE mark ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Added column: {col_name}")
                except Exception as e:
                    print(f"⚠️ Error adding {col_name}: {e}")
        
        # Fix 3: Ensure data consistency
        print("\n🔧 Ensuring data consistency...")
        
        # Set raw_mark = mark where raw_mark is NULL
        cursor.execute("UPDATE mark SET raw_mark = mark WHERE raw_mark IS NULL")
        
        # Set raw_total_marks = total_marks where raw_total_marks is NULL  
        cursor.execute("UPDATE mark SET raw_total_marks = total_marks WHERE raw_total_marks IS NULL")
        
        # Set default grade_letter based on percentage
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
        
        print("✅ Data consistency updates completed")
        
        # Verify the final structure
        print("\n📊 Updated mark table structure:")
        cursor.execute("DESCRIBE mark")
        updated_columns = cursor.fetchall()
        for col in updated_columns:
            print(f"  {col[0]:<20} {col[1]:<20}")
        
        # Test a simple query
        print("\n🧪 Testing mark table query...")
        cursor.execute("SELECT COUNT(*) FROM mark")
        count = cursor.fetchone()[0]
        print(f"✅ Mark table accessible: {count} records")
        
        # Test the specific query that was failing
        print("\n🧪 Testing problematic query...")
        cursor.execute("SELECT mark, percentage FROM mark LIMIT 1")
        result = cursor.fetchone()
        if result:
            print(f"✅ Query successful: mark={result[0]}, percentage={result[1]}")
        else:
            print("✅ Query successful: no data found")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n🎉 Mark table schema fixed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing mark table schema: {e}")
        return False

def main():
    """Main function."""
    print("🔧 MARK TABLE SCHEMA FIX")
    print("Fixing mark table to match Flask model expectations")
    print("=" * 60)
    
    success = fix_mark_table_schema()
    
    if success:
        print("\n✅ SCHEMA FIX COMPLETED!")
        print("The mark table now matches the Flask model expectations.")
        print("The dashboard should now work properly.")
    else:
        print("\n❌ SCHEMA FIX FAILED!")
        print("Please check the errors above and try again.")
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
