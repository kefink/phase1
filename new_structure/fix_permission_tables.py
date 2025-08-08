#!/usr/bin/env python3
"""
Script to fix the missing permission tables in the database.
This will create the function_permissions and class_teacher_permissions tables
with the correct structure as defined in the models.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Database path
DB_PATH = 'hillview_school.db'

def create_permission_tables():
    """Create the missing permission tables with the correct structure."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("🔧 Creating permission tables...")
        
        # Create function_permissions table
        print("Creating function_permissions table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS function_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                function_name VARCHAR(100) NOT NULL,
                function_category VARCHAR(50) NOT NULL,
                scope_type VARCHAR(20) DEFAULT 'global',
                grade_id INTEGER,
                stream_id INTEGER,
                granted_by INTEGER NOT NULL,
                granted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                revoked_at DATETIME,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                notes TEXT,
                auto_granted BOOLEAN DEFAULT 0,
                FOREIGN KEY (teacher_id) REFERENCES teacher (id),
                FOREIGN KEY (grade_id) REFERENCES grade (id),
                FOREIGN KEY (stream_id) REFERENCES stream (id),
                FOREIGN KEY (granted_by) REFERENCES teacher (id)
            )
        ''')
        
        # Create class_teacher_permissions table
        print("Creating class_teacher_permissions table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS class_teacher_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                grade_id INTEGER,
                stream_id INTEGER,
                granted_by INTEGER NOT NULL,
                granted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                revoked_at DATETIME,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                expires_at DATETIME,
                is_permanent BOOLEAN NOT NULL DEFAULT 0,
                auto_granted BOOLEAN NOT NULL DEFAULT 0,
                permission_scope VARCHAR(50) DEFAULT 'full_class_admin',
                notes TEXT,
                FOREIGN KEY (teacher_id) REFERENCES teacher (id),
                FOREIGN KEY (granted_by) REFERENCES teacher (id)
            )
        ''')
        
        # Commit the changes
        conn.commit()
        
        print("✅ Permission tables created successfully!")
        
        # Verify the tables were created
        print("\n📋 Verifying table structures...")
        
        tables = ['function_permissions', 'class_teacher_permissions']
        for table in tables:
            print(f"\n=== {table} ===")
            cursor.execute(f'PRAGMA table_info({table})')
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating permission tables: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
        
    finally:
        conn.close()

def main():
    """Main function to fix permission tables."""
    print("🔧 Fixing permission tables in the database...")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found: {DB_PATH}")
        return False
    
    success = create_permission_tables()
    
    if success:
        print("\n✅ Permission tables fixed successfully!")
        print("The database now has the correct permission table structure.")
        print("You can restart the Flask server to test the fixes.")
    else:
        print("\n❌ Failed to fix permission tables.")
        print("Please check the error messages above.")
    
    return success

if __name__ == '__main__':
    main()
