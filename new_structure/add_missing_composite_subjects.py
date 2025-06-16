#!/usr/bin/env python3
"""
Add missing English and Kiswahili subjects for all education levels and make them composite
"""

import sqlite3
import os

def add_missing_composite_subjects():
    """Add missing English and Kiswahili subjects for all education levels."""
    
    # Database path
    db_path = 'kirima_primary.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking current subjects...")
        
        # Check current subjects
        cursor.execute('SELECT id, name, education_level, is_composite FROM subject ORDER BY name, education_level')
        subjects = cursor.fetchall()
        
        print("\n=== CURRENT SUBJECTS ===")
        for subject in subjects:
            print(f"ID: {subject[0]}, Name: {subject[1]}, Level: {subject[2]}, Composite: {subject[3]}")
        
        # Define required education levels
        education_levels = ['lower_primary', 'upper_primary', 'junior_secondary']
        
        # Check and add missing English subjects
        print("\n🔧 Checking English subjects for all education levels...")
        for level in education_levels:
            cursor.execute("SELECT id FROM subject WHERE LOWER(name) = 'english' AND education_level = ?", (level,))
            existing = cursor.fetchone()
            
            if not existing:
                print(f"➕ Adding English for {level}...")
                cursor.execute("""
                    INSERT INTO subject (name, education_level, is_composite) 
                    VALUES ('English', ?, 1)
                """, (level,))
                
                # Get the new subject ID
                subject_id = cursor.lastrowid
                
                # Add components
                cursor.execute("""
                    INSERT INTO subject_component (subject_id, name, weight) 
                    VALUES (?, 'Grammar', 60.0)
                """, (subject_id,))
                
                cursor.execute("""
                    INSERT INTO subject_component (subject_id, name, weight) 
                    VALUES (?, 'Composition', 40.0)
                """, (subject_id,))
                
                print(f"  ✅ Added English for {level} with Grammar (60%) and Composition (40%)")
            else:
                print(f"  ✅ English already exists for {level}")
                
                # Make sure it's composite
                cursor.execute("UPDATE subject SET is_composite = 1 WHERE id = ?", (existing[0],))
                
                # Check components
                cursor.execute("SELECT COUNT(*) FROM subject_component WHERE subject_id = ?", (existing[0],))
                comp_count = cursor.fetchone()[0]
                
                if comp_count == 0:
                    print(f"  📝 Adding missing components for English ({level})...")
                    cursor.execute("""
                        INSERT INTO subject_component (subject_id, name, weight) 
                        VALUES (?, 'Grammar', 60.0)
                    """, (existing[0],))
                    
                    cursor.execute("""
                        INSERT INTO subject_component (subject_id, name, weight) 
                        VALUES (?, 'Composition', 40.0)
                    """, (existing[0],))
                    print(f"    ✅ Added Grammar and Composition components")
        
        # Check and add missing Kiswahili subjects
        print("\n🔧 Checking Kiswahili subjects for all education levels...")
        for level in education_levels:
            cursor.execute("SELECT id FROM subject WHERE LOWER(name) = 'kiswahili' AND education_level = ?", (level,))
            existing = cursor.fetchone()
            
            if not existing:
                print(f"➕ Adding Kiswahili for {level}...")
                cursor.execute("""
                    INSERT INTO subject (name, education_level, is_composite) 
                    VALUES ('Kiswahili', ?, 1)
                """, (level,))
                
                # Get the new subject ID
                subject_id = cursor.lastrowid
                
                # Add components
                cursor.execute("""
                    INSERT INTO subject_component (subject_id, name, weight) 
                    VALUES (?, 'Lugha', 50.0)
                """, (subject_id,))
                
                cursor.execute("""
                    INSERT INTO subject_component (subject_id, name, weight) 
                    VALUES (?, 'Insha', 50.0)
                """, (subject_id,))
                
                print(f"  ✅ Added Kiswahili for {level} with Lugha (50%) and Insha (50%)")
            else:
                print(f"  ✅ Kiswahili already exists for {level}")
                
                # Make sure it's composite
                cursor.execute("UPDATE subject SET is_composite = 1 WHERE id = ?", (existing[0],))
                
                # Check components
                cursor.execute("SELECT COUNT(*) FROM subject_component WHERE subject_id = ?", (existing[0],))
                comp_count = cursor.fetchone()[0]
                
                if comp_count == 0:
                    print(f"  📝 Adding missing components for Kiswahili ({level})...")
                    cursor.execute("""
                        INSERT INTO subject_component (subject_id, name, weight) 
                        VALUES (?, 'Lugha', 50.0)
                    """, (existing[0],))
                    
                    cursor.execute("""
                        INSERT INTO subject_component (subject_id, name, weight) 
                        VALUES (?, 'Insha', 50.0)
                    """, (existing[0],))
                    print(f"    ✅ Added Lugha and Insha components")
        
        # Verify final state
        print("\n🔍 Final verification...")
        
        cursor.execute("""
            SELECT s.id, s.name, s.education_level, s.is_composite,
                   GROUP_CONCAT(sc.name || ' (' || sc.weight || '%)', ', ') as components
            FROM subject s
            LEFT JOIN subject_component sc ON s.id = sc.subject_id
            WHERE LOWER(s.name) IN ('english', 'kiswahili')
            GROUP BY s.id, s.name, s.education_level, s.is_composite
            ORDER BY s.name, s.education_level
        """)
        final_subjects = cursor.fetchall()
        
        print("\n=== FINAL COMPOSITE SUBJECTS ===")
        for subject in final_subjects:
            components = subject[4] if subject[4] else "No components"
            print(f"📚 {subject[1]} ({subject[2]}) - Composite: {subject[3]} - Components: {components}")
        
        # Commit changes
        conn.commit()
        print("\n✅ All changes committed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔧 Adding missing composite subjects for all education levels...")
    success = add_missing_composite_subjects()
    if success:
        print("\n🎉 All English and Kiswahili subjects successfully configured as composite!")
        print("📝 Both subjects now have proper components for all education levels.")
    else:
        print("\n❌ Failed to add missing composite subjects.")
