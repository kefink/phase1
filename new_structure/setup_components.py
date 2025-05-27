#!/usr/bin/env python3
"""
Setup script to ensure composite subject components exist in the database.
"""
import sqlite3
import os

def setup_components():
    """Setup components for English and Kiswahili subjects."""
    db_path = 'kirima_primary.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if subject_component table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subject_component'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("Creating subject_component table...")
            cursor.execute('''
            CREATE TABLE subject_component (
                id INTEGER PRIMARY KEY,
                subject_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                max_raw_mark INTEGER DEFAULT 100,
                FOREIGN KEY (subject_id) REFERENCES subject (id)
            )
            ''')
            conn.commit()
            print("subject_component table created.")
        
        # Check existing components
        cursor.execute("SELECT * FROM subject_component")
        existing_components = cursor.fetchall()
        print(f"Existing components: {len(existing_components)}")
        
        # Check if English components exist (subject_id = 2)
        cursor.execute("SELECT * FROM subject_component WHERE subject_id = 2")
        english_components = cursor.fetchall()
        
        if not english_components:
            print("Adding English components...")
            cursor.execute('''
            INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
            VALUES (2, 'Grammar', 0.6, 60)
            ''')
            cursor.execute('''
            INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
            VALUES (2, 'Composition', 0.4, 40)
            ''')
            conn.commit()
            print("English components added: Grammar (60), Composition (40)")
        else:
            print("English components already exist:")
            for comp in english_components:
                print(f"  {comp[2]}: max_raw_mark = {comp[4]}")
        
        # Check if Kiswahili components exist (subject_id = 7)
        cursor.execute("SELECT * FROM subject_component WHERE subject_id = 7")
        kiswahili_components = cursor.fetchall()
        
        if not kiswahili_components:
            print("Adding Kiswahili components...")
            cursor.execute('''
            INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
            VALUES (7, 'Lugha', 0.6, 60)
            ''')
            cursor.execute('''
            INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
            VALUES (7, 'Insha', 0.4, 40)
            ''')
            conn.commit()
            print("Kiswahili components added: Lugha (60), Insha (40)")
        else:
            print("Kiswahili components already exist:")
            for comp in kiswahili_components:
                print(f"  {comp[2]}: max_raw_mark = {comp[4]}")
        
        # Update subjects to be composite
        cursor.execute("UPDATE subject SET is_composite = 1 WHERE id IN (2, 7)")
        conn.commit()
        print("Updated English and Kiswahili to be composite subjects.")
        
        # Verify final state
        cursor.execute("SELECT * FROM subject_component ORDER BY subject_id, name")
        all_components = cursor.fetchall()
        print("\nFinal components:")
        for comp in all_components:
            print(f"  Subject {comp[1]}: {comp[2]} (weight: {comp[3]}, max_raw_mark: {comp[4]})")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    setup_components()
