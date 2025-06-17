#!/usr/bin/env python3
import sqlite3

def check_tables():
    conn = sqlite3.connect('kirima_primary.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print('Tables in database:')
    for table in tables:
        print(f'  - {table[0]}')
    
    # Check if parent portal tables exist
    parent_tables = ['parent', 'parent_student', 'parent_email_log', 'email_template']
    print('\nParent portal tables:')
    for table in parent_tables:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        exists = cursor.fetchone()
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f'  - {table}: {status}')
    
    conn.close()

if __name__ == '__main__':
    check_tables()
