#!/usr/bin/env python3
"""
Execute SQL script to create missing tables.
"""

import sqlite3
import os

def execute_sql_script():
    """Execute the SQL script to create missing tables."""
    print("🔧 Executing SQL script to create missing tables...")
    
    db_path = '../kirima_primary.db'
    sql_file = 'create_missing_tables.sql'
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL file not found: {sql_file}")
        return False
    
    try:
        # Read SQL script
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Execute script
        cursor.executescript(sql_script)
        conn.commit()
        
        print("✅ SQL script executed successfully!")
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"📋 Tables in database: {tables}")
        
        # Check data counts
        for table in ['subject', 'grade', 'stream', 'term', 'assessment_type']:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count} records")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ SQL execution failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Database Table Creation")
    print("=" * 40)
    
    if execute_sql_script():
        print("\n🎉 Database tables created successfully!")
        print("🚀 Your Flask application should now work.")
    else:
        print("\n❌ Database table creation failed.")
