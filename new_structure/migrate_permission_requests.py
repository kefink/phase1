#!/usr/bin/env python3
"""
Migration script to update permission_requests table to allow nullable grade_id
for function permission requests.
"""

import sqlite3
import os
import sys

def migrate_permission_requests():
    """Update the permission_requests table to allow nullable grade_id."""
    
    # Database path - check both current directory and parent directory
    db_path = os.path.join(os.path.dirname(__file__), 'kirima_primary.db')
    if not os.path.exists(db_path):
        # Try parent directory
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'kirima_primary.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if permission_requests table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='permission_requests'
        """)
        
        if not cursor.fetchone():
            print("permission_requests table does not exist yet. No migration needed.")
            conn.close()
            return True
        
        # Check current schema
        cursor.execute("PRAGMA table_info(permission_requests)")
        columns = cursor.fetchall()
        
        # Check if grade_id is already nullable
        grade_id_nullable = False
        for col in columns:
            if col[1] == 'grade_id' and col[3] == 0:  # notnull = 0 means nullable
                grade_id_nullable = True
                break
        
        if grade_id_nullable:
            print("permission_requests.grade_id is already nullable. No migration needed.")
            conn.close()
            return True
        
        print("Migrating permission_requests table to allow nullable grade_id...")
        
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        
        # 1. Create new table with correct schema
        cursor.execute("""
            CREATE TABLE permission_requests_new (
                id INTEGER PRIMARY KEY,
                teacher_id INTEGER NOT NULL,
                grade_id INTEGER,
                stream_id INTEGER,
                requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending',
                processed_at DATETIME,
                processed_by INTEGER,
                reason TEXT,
                admin_notes TEXT,
                FOREIGN KEY (teacher_id) REFERENCES teacher (id),
                FOREIGN KEY (grade_id) REFERENCES grade (id),
                FOREIGN KEY (stream_id) REFERENCES stream (id),
                FOREIGN KEY (processed_by) REFERENCES teacher (id)
            )
        """)
        
        # 2. Copy data from old table
        cursor.execute("""
            INSERT INTO permission_requests_new 
            SELECT * FROM permission_requests
        """)
        
        # 3. Drop old table
        cursor.execute("DROP TABLE permission_requests")
        
        # 4. Rename new table
        cursor.execute("ALTER TABLE permission_requests_new RENAME TO permission_requests")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = migrate_permission_requests()
    sys.exit(0 if success else 1)
