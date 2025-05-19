import sqlite3

print("Testing database connection...")

try:
    conn = sqlite3.connect("kirima_primary.db")
    print("Connected to database")
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tables in database:")
    for table in tables:
        print(f"- {table[0]}")
    
    conn.close()
    print("Connection closed")
except Exception as e:
    print(f"Error: {e}")
