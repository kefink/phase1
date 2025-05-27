"""
Automated implementation of composite subjects for the Hillview School Management System.
This script will make all necessary changes to support composite subjects like English and Kiswahili.
"""
import os
import sqlite3
import sys

def update_database_schema(db_path='kirima_primary.db'):
    """Update the database schema to support composite subjects."""
    print(f"Updating database schema at {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if subject table has is_composite column
        cursor.execute("PRAGMA table_info(subject)")
        columns = cursor.fetchall()
        has_is_composite = any(col[1] == 'is_composite' for col in columns)
        
        if not has_is_composite:
            print("Adding is_composite column to subject table...")
            cursor.execute("ALTER TABLE subject ADD COLUMN is_composite BOOLEAN DEFAULT 0")
            conn.commit()
        
        # Check if subject_component table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subject_component'")
        subject_component_exists = cursor.fetchone() is not None
        
        if not subject_component_exists:
            print("Creating subject_component table...")
            cursor.execute('''
            CREATE TABLE subject_component (
                id INTEGER PRIMARY KEY,
                subject_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                weight REAL DEFAULT 0.5,
                max_raw_mark INTEGER DEFAULT 100,
                FOREIGN KEY (subject_id) REFERENCES subject (id)
            )
            ''')
            conn.commit()
        
        # Check if component_mark table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='component_mark'")
        component_mark_exists = cursor.fetchone() is not None
        
        if not component_mark_exists:
            print("Creating component_mark table...")
            cursor.execute('''
            CREATE TABLE component_mark (
                id INTEGER PRIMARY KEY,
                mark_id INTEGER NOT NULL,
                component_id INTEGER NOT NULL,
                raw_mark REAL NOT NULL,
                max_raw_mark INTEGER DEFAULT 100,
                percentage REAL NOT NULL,
                FOREIGN KEY (mark_id) REFERENCES mark (id),
                FOREIGN KEY (component_id) REFERENCES subject_component (id)
            )
            ''')
            conn.commit()
        
        # Set English and Kiswahili as composite subjects
        print("Setting English and Kiswahili as composite subjects...")
        cursor.execute("UPDATE subject SET is_composite = 1 WHERE name IN ('ENGLISH', 'KISWAHILI')")
        conn.commit()
        
        # Add components for English and Kiswahili if they don't exist
        cursor.execute("SELECT id FROM subject WHERE name = 'ENGLISH'")
        english_id = cursor.fetchone()
        
        cursor.execute("SELECT id FROM subject WHERE name = 'KISWAHILI'")
        kiswahili_id = cursor.fetchone()
        
        if english_id:
            english_id = english_id[0]
            cursor.execute("SELECT * FROM subject_component WHERE subject_id = ?", (english_id,))
            english_components = cursor.fetchall()
            
            if not english_components:
                print("Adding components for English...")
                cursor.execute('''
                INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
                VALUES (?, 'Grammar', 0.6, 60)
                ''', (english_id,))
                
                cursor.execute('''
                INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
                VALUES (?, 'Composition', 0.4, 40)
                ''', (english_id,))
                conn.commit()
        
        if kiswahili_id:
            kiswahili_id = kiswahili_id[0]
            cursor.execute("SELECT * FROM subject_component WHERE subject_id = ?", (kiswahili_id,))
            kiswahili_components = cursor.fetchall()
            
            if not kiswahili_components:
                print("Adding components for Kiswahili...")
                cursor.execute('''
                INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
                VALUES (?, 'Lugha', 0.6, 60)
                ''', (kiswahili_id,))
                
                cursor.execute('''
                INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
                VALUES (?, 'Insha', 0.4, 40)
                ''', (kiswahili_id,))
                conn.commit()
        
        print("Database schema updated successfully!")
        
    except Exception as e:
        print(f"Error updating database schema: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'kirima_primary.db'
    update_database_schema(db_path)
