#!/usr/bin/env python3
"""
Check user credentials in the database.
"""

import sqlite3
import os

def check_users():
    """Check all users in the database."""
    print("🔍 Checking user credentials...")
    
    # Check the main database
    db_path = '../kirima_primary.db'
    print(f"Database path: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check all users
        cursor.execute("SELECT id, username, password, role FROM teacher")
        users = cursor.fetchall()
        
        print(f"\n📋 All users in database ({len(users)} total):")
        for user in users:
            print(f"  ID: {user[0]}, Username: '{user[1]}', Password: '{user[2]}', Role: '{user[3]}'")
        
        # Check specifically for kevin
        cursor.execute("SELECT * FROM teacher WHERE username = ?", ('kevin',))
        kevin = cursor.fetchone()
        
        if kevin:
            print(f"\n✅ Kevin found:")
            print(f"  ID: {kevin[0]}")
            print(f"  Username: '{kevin[1]}'")
            print(f"  Password: '{kevin[2]}'")
            print(f"  Role: '{kevin[3]}'")
        else:
            print(f"\n❌ Kevin NOT found in database")
            
            # Check for similar usernames
            cursor.execute("SELECT username FROM teacher WHERE username LIKE '%kev%'")
            similar = cursor.fetchall()
            if similar:
                print(f"Similar usernames found: {[u[0] for u in similar]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def add_kevin_user():
    """Add kevin user to the database."""
    print("\n🔧 Adding kevin user...")
    
    try:
        conn = sqlite3.connect('../kirima_primary.db')
        cursor = conn.cursor()
        
        # Check if kevin already exists
        cursor.execute("SELECT id FROM teacher WHERE username = ?", ('kevin',))
        if cursor.fetchone():
            print("⚠️  Kevin already exists!")
            conn.close()
            return
        
        # Add kevin user
        cursor.execute("""
            INSERT INTO teacher (username, password, role, full_name, employee_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('kevin', 'kev123', 'classteacher', 'Kevin Teacher', 'EMP002', 1))
        
        conn.commit()
        print("✅ Kevin user added successfully!")
        
        # Verify
        cursor.execute("SELECT id, username, password, role FROM teacher WHERE username = ?", ('kevin',))
        kevin = cursor.fetchone()
        print(f"✅ Verification - Kevin: {kevin}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error adding kevin: {e}")

if __name__ == "__main__":
    print("🚀 User Credential Check")
    print("=" * 40)
    
    check_users()
    
    # Ask if we should add kevin
    print("\n" + "=" * 40)
    print("Would you like to add kevin user? (This will be done automatically)")
    add_kevin_user()
    
    print("\n" + "=" * 40)
    print("Final check:")
    check_users()
