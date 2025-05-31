#!/usr/bin/env python3
"""
Check all database files to find where the original users are.
"""

import sqlite3
import os
import glob

def check_database_users(db_path):
    """Check users in a specific database file."""
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if teacher table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher'")
        if not cursor.fetchone():
            conn.close()
            return "No teacher table"
        
        # Get all users
        cursor.execute("SELECT id, username, password, role FROM teacher")
        users = cursor.fetchall()
        
        conn.close()
        return users
        
    except Exception as e:
        return f"Error: {e}"

def main():
    """Check all database files."""
    print("🔍 Checking all database files for users...")
    print("=" * 60)
    
    # List of database files to check
    db_files = [
        "../kirima_primary.db",  # Main database (parent directory)
        "kirima_primary.db",     # Current directory database
    ]
    
    # Add backup files
    backup_files = glob.glob("kirima_primary.db.backup_*")
    backup_files.extend(glob.glob("../kirima_primary.db.backup_*"))
    
    all_files = db_files + backup_files
    
    for db_file in all_files:
        print(f"\n📁 {db_file}")
        print(f"   Exists: {os.path.exists(db_file)}")
        
        if os.path.exists(db_file):
            # Get file size
            size = os.path.getsize(db_file)
            print(f"   Size: {size:,} bytes")
            
            # Check users
            users = check_database_users(db_file)
            
            if isinstance(users, list):
                print(f"   Users: {len(users)} found")
                for user in users:
                    print(f"     - {user[1]} (password: {user[2]}, role: {user[3]})")
                    
                # Check for kevin specifically
                kevin_found = any(user[1] == 'kevin' for user in users)
                if kevin_found:
                    print(f"   ✅ KEVIN FOUND in this database!")
                    
            else:
                print(f"   Status: {users}")
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print("Look for the database file that contains your original users.")
    print("If Kevin is found in a backup, we can restore that data.")

if __name__ == "__main__":
    main()
