import sqlite3
import os

def check_database(db_path, name):
    print(f"\n🔍 Checking {name}: {db_path}")
    print(f"Exists: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check users
        cursor.execute("SELECT id, username, password, role FROM teacher")
        users = cursor.fetchall()
        
        print(f"Users found: {len(users)}")
        for user in users:
            print(f"  - {user[1]} (password: {user[2]}, role: {user[3]})")
        
        # Check for kevin
        cursor.execute("SELECT * FROM teacher WHERE username = 'kevin'")
        kevin = cursor.fetchone()
        
        if kevin:
            print(f"✅ Kevin found in {name}")
        else:
            print(f"❌ Kevin NOT found in {name}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

# Check both databases
check_database("../kirima_primary.db", "Parent Directory Database")
check_database("kirima_primary.db", "Current Directory Database")

print("\n" + "="*50)
print("SOLUTION:")
print("The Flask app is likely using the parent directory database.")
print("We need to add Kevin to the correct database.")

# Add kevin to the parent directory database
try:
    conn = sqlite3.connect("../kirima_primary.db")
    cursor = conn.cursor()
    
    # Check if kevin exists
    cursor.execute("SELECT id FROM teacher WHERE username = 'kevin'")
    if cursor.fetchone():
        print("✅ Kevin already exists in parent database")
    else:
        print("🔧 Adding Kevin to parent database...")
        cursor.execute("""
            INSERT INTO teacher (username, password, role, full_name, employee_id, is_active)
            VALUES ('kevin', 'kev123', 'classteacher', 'Kevin Teacher', 'EMP002', 1)
        """)
        conn.commit()
        print("✅ Kevin added successfully!")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error adding Kevin: {e}")

print("\n🎉 Try logging in now with kevin/kev123")
