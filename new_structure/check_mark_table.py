#!/usr/bin/env python3
"""
Check Mark Table Structure
Checks the actual structure of the mark table in MySQL.
"""

import mysql.connector
import json

def check_mark_table():
    """Check the mark table structure."""
    print("🔍 Checking Mark Table Structure")
    print("=" * 40)
    
    try:
        with open('mysql_migration/mysql_credentials.json', 'r') as f:
            creds = json.load(f)
        
        # Remove any extra keys that might cause issues
        connection_params = {
            'host': creds['host'],
            'database': creds['database_name'],
            'user': creds['username'],
            'password': creds['password'],
            'port': creds['port']
        }
        
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor()
        
        # Check mark table structure
        cursor.execute("DESCRIBE mark")
        columns = cursor.fetchall()
        
        print("Mark table columns:")
        print("-" * 50)
        for col in columns:
            print(f"  {col[0]:<20} {col[1]:<20} {col[2]}")
        
        # Check if 'mark' column exists
        column_names = [col[0] for col in columns]
        
        if 'mark' in column_names:
            print("\n✅ 'mark' column exists")
        else:
            print("\n❌ 'mark' column is missing!")
            print("Available columns:", ', '.join(column_names))
            
            # Check what columns might be used for marks
            mark_like_columns = [col for col in column_names if 'mark' in col.lower() or 'score' in col.lower() or 'grade' in col.lower()]
            if mark_like_columns:
                print(f"Possible mark columns: {', '.join(mark_like_columns)}")
        
        cursor.close()
        connection.close()
        
        return 'mark' in column_names
        
    except Exception as e:
        print(f"❌ Error checking mark table: {e}")
        return False

def main():
    """Main function."""
    success = check_mark_table()
    
    if not success:
        print("\n🔧 ISSUE IDENTIFIED:")
        print("The 'mark' table is missing the 'mark' column that the application expects.")
        print("This needs to be fixed for the dashboard to work properly.")
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
