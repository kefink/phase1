import sqlite3

# Check users in database
conn = sqlite3.connect('../kirima_primary.db')
cursor = conn.cursor()

print("Users in database:")
cursor.execute("SELECT id, username, password, role FROM teacher")
users = cursor.fetchall()

for user in users:
    print(f"ID: {user[0]}, Username: '{user[1]}', Password: '{user[2]}', Role: '{user[3]}'")

# Check for kevin specifically
cursor.execute("SELECT * FROM teacher WHERE username = 'kevin'")
kevin = cursor.fetchone()

if kevin:
    print(f"\nKevin found: {kevin}")
else:
    print(f"\nKevin NOT found - adding him now...")
    
    # Add kevin
    cursor.execute("""
        INSERT INTO teacher (username, password, role, full_name, employee_id, is_active)
        VALUES ('kevin', 'kev123', 'classteacher', 'Kevin Teacher', 'EMP002', 1)
    """)
    conn.commit()
    print("Kevin added!")

conn.close()
print("Done!")
