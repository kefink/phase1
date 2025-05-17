import os
import sqlite3

def check_databases():
    """Check both database files and add Kevin to the correct one."""
    # Paths to both database files
    hillview_db_path = os.path.join('new_structure', 'hillview.db')
    kirima_db_path = 'kirima_primary.db'
    
    print(f"Checking database files:")
    print(f"1. hillview.db: {os.path.exists(hillview_db_path)}")
    print(f"2. kirima_primary.db: {os.path.exists(kirima_db_path)}")
    
    # Check hillview.db
    if os.path.exists(hillview_db_path):
        print("\nChecking hillview.db:")
        conn = sqlite3.connect(hillview_db_path)
        cursor = conn.cursor()
        
        # Check if teacher table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher';")
        if cursor.fetchone():
            # Check for Kevin
            cursor.execute("SELECT id, username, password, role FROM teacher WHERE username='kevin';")
            kevin = cursor.fetchone()
            if kevin:
                print(f"Kevin found in hillview.db: ID: {kevin[0]}, Username: {kevin[1]}, Password: {kevin[2]}, Role: {kevin[3]}")
            else:
                print("Kevin not found in hillview.db. Adding him...")
                cursor.execute("INSERT INTO teacher (username, password, role) VALUES ('kevin', 'password', 'classteacher');")
                conn.commit()
                print("Kevin added to hillview.db")
        else:
            print("Teacher table not found in hillview.db")
        
        conn.close()
    
    # Check kirima_primary.db
    if os.path.exists(kirima_db_path):
        print("\nChecking kirima_primary.db:")
        conn = sqlite3.connect(kirima_db_path)
        cursor = conn.cursor()
        
        # Check if teacher table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher';")
        if cursor.fetchone():
            # Check for Kevin
            cursor.execute("SELECT id, username, password, role FROM teacher WHERE username='kevin';")
            kevin = cursor.fetchone()
            if kevin:
                print(f"Kevin found in kirima_primary.db: ID: {kevin[0]}, Username: {kevin[1]}, Password: {kevin[2]}, Role: {kevin[3]}")
            else:
                print("Kevin not found in kirima_primary.db. Adding him...")
                cursor.execute("INSERT INTO teacher (username, password, role) VALUES ('kevin', 'password', 'classteacher');")
                conn.commit()
                print("Kevin added to kirima_primary.db")
                
                # Also add classteacher1 if not exists
                cursor.execute("SELECT id FROM teacher WHERE username='classteacher1';")
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO teacher (username, password, role) VALUES ('classteacher1', 'class123', 'classteacher');")
                    conn.commit()
                    print("classteacher1 added to kirima_primary.db")
        else:
            print("Teacher table not found in kirima_primary.db")
        
        conn.close()

if __name__ == '__main__':
    check_databases()
