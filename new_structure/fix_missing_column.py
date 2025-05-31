#!/usr/bin/env python3
"""
Quick fix script to add the missing deputy_headteacher_id column.
"""

import sqlite3
import os

def fix_missing_column():
    """Add the missing deputy_headteacher_id column."""

    db_path = 'kirima_primary.db'

    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if deputy_headteacher_id exists
        cursor.execute("PRAGMA table_info(school_configuration)")
        columns = [column[1] for column in cursor.fetchall()]

        print(f"Current columns: {columns}")

        if 'deputy_headteacher_id' not in columns:
            print("🔧 Adding missing deputy_headteacher_id column...")
            try:
                cursor.execute("ALTER TABLE school_configuration ADD COLUMN deputy_headteacher_id INTEGER")
                conn.commit()
                print("✅ Column added successfully!")
            except Exception as e:
                print(f"❌ Failed to add column: {e}")
        else:
            print("✅ Column already exists!")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    fix_missing_column()
