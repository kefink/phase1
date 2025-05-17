"""
Script to check the database structure.
"""
import sqlite3
import os

def check_database():
    """Check the database structure."""
    db_path = os.path.join(os.path.dirname(__file__), 'hillview.db')
    
    print(f"Using database at: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get a list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tables in the database:")
    for table in tables:
        print(f"- {table[0]}")
        
        # Get the schema for each table
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        
        print(f"  Columns in {table[0]}:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    check_database()
