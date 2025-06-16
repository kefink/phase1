#!/usr/bin/env python3
"""
Simple approach: Add English and Kiswahili subjects with level-specific names
"""

import sqlite3
import os

def add_subjects_simple():
    """Add English and Kiswahili subjects for missing education levels."""
    
    # Database path
    db_path = 'kirima_primary.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Current subjects...")
        cursor.execute('SELECT id, name, education_level, is_composite FROM subject ORDER BY name, education_level')
        subjects = cursor.fetchall()
        
        for subject in subjects:
            print(f"  {subject[1]} ({subject[2]}) - Composite: {subject[3]}")
        
        # Add subjects with unique names
        subjects_to_add = [
            ('English (Upper Primary)', 'upper_primary', 1),
            ('English (Junior Secondary)', 'junior_secondary', 1),
            ('Kiswahili (Upper Primary)', 'upper_primary', 1),
            ('Kiswahili (Junior Secondary)', 'junior_secondary', 1),
        ]
        
        print("\n🔧 Adding missing subjects...")
        
        for subject_name, education_level, is_composite in subjects_to_add:
            # Check if already exists
            cursor.execute("SELECT id FROM subject WHERE name = ?", (subject_name,))
            if cursor.fetchone():
                print(f"  ✅ {subject_name} already exists")
                continue
            
            print(f"➕ Adding {subject_name}...")
            cursor.execute("""
                INSERT INTO subject (name, education_level, is_composite) 
                VALUES (?, ?, ?)
            """, (subject_name, education_level, is_composite))
            
            subject_id = cursor.lastrowid
            
            # Add components based on subject type
            if 'English' in subject_name:
                cursor.execute("""
                    INSERT INTO subject_component (subject_id, name, weight) 
                    VALUES (?, 'Grammar', 60.0)
                """, (subject_id,))
                
                cursor.execute("""
                    INSERT INTO subject_component (subject_id, name, weight) 
                    VALUES (?, 'Composition', 40.0)
                """, (subject_id,))
                
                print(f"  📝 Added Grammar (60%) and Composition (40%) components")
                
            elif 'Kiswahili' in subject_name:
                cursor.execute("""
                    INSERT INTO subject_component (subject_id, name, weight) 
                    VALUES (?, 'Lugha', 50.0)
                """, (subject_id,))
                
                cursor.execute("""
                    INSERT INTO subject_component (subject_id, name, weight) 
                    VALUES (?, 'Insha', 50.0)
                """, (subject_id,))
                
                print(f"  📝 Added Lugha (50%) and Insha (50%) components")
        
        # Verify final state
        print("\n🔍 Final verification...")
        cursor.execute("""
            SELECT s.name, s.education_level, s.is_composite,
                   GROUP_CONCAT(sc.name || ' (' || sc.weight || '%)', ', ') as components
            FROM subject s
            LEFT JOIN subject_component sc ON s.id = sc.subject_id
            WHERE s.name LIKE '%English%' OR s.name LIKE '%Kiswahili%'
            GROUP BY s.id, s.name, s.education_level, s.is_composite
            ORDER BY s.name, s.education_level
        """)
        final_subjects = cursor.fetchall()
        
        print("\n=== COMPOSITE SUBJECTS ===")
        for subject in final_subjects:
            components = subject[3] if subject[3] else "No components"
            print(f"📚 {subject[0]} ({subject[1]}) - Composite: {subject[2]}")
            print(f"    Components: {components}")
        
        # Commit changes
        conn.commit()
        print("\n✅ All changes committed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔧 Adding missing composite subjects...")
    success = add_subjects_simple()
    if success:
        print("\n🎉 Composite subjects added successfully!")
        print("📝 English and Kiswahili are now available for all education levels.")
    else:
        print("\n❌ Failed to add composite subjects.")
