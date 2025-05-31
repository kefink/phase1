#!/usr/bin/env python3
"""
Quick fix for the database column issue.
"""

import sqlite3
import os
from datetime import datetime

def quick_fix():
    """Quick fix for missing columns."""
    print("🔧 Quick database fix...")
    
    db_path = 'kirima_primary.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False
    
    try:
        # Create backup
        backup_path = f'kirima_primary.db.backup_quickfix_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current teacher table structure
        cursor.execute("PRAGMA table_info(teacher)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Check if we need to recreate the table
        required_columns = ['full_name', 'employee_id', 'phone_number', 'email', 'qualification', 'specialization', 'is_active', 'date_joined']
        missing = [col for col in required_columns if col not in columns]
        
        if missing:
            print(f"Missing columns: {missing}")
            
            # Get existing data
            cursor.execute("SELECT id, username, password, role, stream_id FROM teacher")
            existing_teachers = cursor.fetchall()
            print(f"Found {len(existing_teachers)} existing teachers")
            
            # Create new table with correct schema
            cursor.execute("""
                CREATE TABLE teacher_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(100) NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    stream_id INTEGER,
                    full_name TEXT,
                    employee_id TEXT,
                    phone_number TEXT,
                    email TEXT,
                    qualification TEXT,
                    specialization TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    date_joined DATE
                )
            """)
            
            # Insert existing data with enhanced fields
            for teacher in existing_teachers:
                teacher_id, username, password, role, stream_id = teacher
                cursor.execute("""
                    INSERT INTO teacher_new 
                    (id, username, password, role, stream_id, full_name, employee_id, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (teacher_id, username, password, role, stream_id, username, f'EMP{teacher_id:03d}', 1))
            
            # Replace old table
            cursor.execute("DROP TABLE teacher")
            cursor.execute("ALTER TABLE teacher_new RENAME TO teacher")
            print("✅ Teacher table recreated with enhanced schema")
        
        # Check school_configuration
        cursor.execute("PRAGMA table_info(school_configuration)")
        config_columns = [col[1] for col in cursor.fetchall()]
        
        if 'headteacher_id' not in config_columns:
            cursor.execute("ALTER TABLE school_configuration ADD COLUMN headteacher_id INTEGER")
            print("✅ Added headteacher_id")
        
        if 'deputy_headteacher_id' not in config_columns:
            cursor.execute("ALTER TABLE school_configuration ADD COLUMN deputy_headteacher_id INTEGER")
            print("✅ Added deputy_headteacher_id")
        
        conn.commit()
        
        # Verify
        cursor.execute("PRAGMA table_info(teacher)")
        final_columns = [col[1] for col in cursor.fetchall()]
        print(f"Final teacher columns: {final_columns}")
        
        # Test query
        cursor.execute("SELECT id, username, full_name, employee_id FROM teacher LIMIT 1")
        test = cursor.fetchone()
        print(f"Test query result: {test}")
        
        conn.close()
        print("✅ Quick fix completed!")
        return True
        
    except Exception as e:
        print(f"❌ Quick fix failed: {e}")
        return False

if __name__ == "__main__":
    quick_fix()
