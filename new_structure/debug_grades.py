#!/usr/bin/env python3
"""
Debug script to check what grades are available in the database
"""

import sys
import os

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the proper Python path for imports
os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))

try:
    import sqlite3
    
    # Try to find the database file
    db_paths = [
        'hillview_school.db',
        'instance/hillview_school.db',
        os.path.expanduser('~/hillview_school.db')
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("No database file found. Checked paths:")
        for path in db_paths:
            print(f"  - {path}")
        print("\nThis suggests the database hasn't been created yet.")
        print("You may need to run the Flask app first to initialize the database.")
        sys.exit(1)
    
    print(f"Using database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if grade table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='grade'")
    if not cursor.fetchone():
        print("Grade table doesn't exist in the database")
        sys.exit(1)
    
    # Get all grades
    cursor.execute("SELECT id, name FROM grade ORDER BY id")
    grades = cursor.fetchall()
    
    print("=== Grades in Database ===")
    if grades:
        for grade_id, name in grades:
            print(f'ID: {grade_id}, Name: "{name}"')
        print(f'\nTotal grades: {len(grades)}')
        
        # Check what would be selected for each educational level
        educational_level_mapping = {
            'pre_primary': ['PP1', 'PP2'],
            'lower_primary': ['Grade 1', 'Grade 2', 'Grade 3'],
            'upper_primary': ['Grade 4', 'Grade 5', 'Grade 6'],
            'junior_secondary': ['Grade 7', 'Grade 8', 'Grade 9']
        }
        
        print("\n=== Educational Level Mapping Results ===")
        grade_names = [name for _, name in grades]
        for level, expected_grades in educational_level_mapping.items():
            matches = [name for name in expected_grades if name in grade_names]
            print(f'{level}: Expected {expected_grades} -> Found {matches}')
        
        if not any(matches for _, expected_grades in educational_level_mapping.items() for matches in [[name for name in expected_grades if name in grade_names]]):
            print("\n⚠️  WARNING: No grade names match the expected educational level mapping!")
            print("This explains why the dropdowns are empty.")
            print("\nActual grade names in DB vs expected:")
            print("Expected for junior_secondary: Grade 7, Grade 8, Grade 9")
            print(f"Actual grade names in DB: {grade_names}")
            
    else:
        print("No grades found in database!")
    
    conn.close()
        
except Exception as e:
    print(f"Error: {e}")