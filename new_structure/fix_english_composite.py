#!/usr/bin/env python3
"""
Fix English subject to be composite like Kiswahili
"""

import sqlite3
import os

def fix_english_composite():
    """Fix English subject to be composite and add components."""
    
    # Database path
    db_path = 'kirima_primary.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking current subject status...")
        
        # Check current subjects and their composite status
        cursor.execute('SELECT id, name, education_level, is_composite FROM subject ORDER BY name')
        subjects = cursor.fetchall()
        
        print("\n=== CURRENT SUBJECTS ===")
        for subject in subjects:
            print(f"ID: {subject[0]}, Name: {subject[1]}, Level: {subject[2]}, Composite: {subject[3]}")
        
        # Check current components
        cursor.execute('''
            SELECT sc.id, s.name as subject_name, sc.name as component_name, sc.weight 
            FROM subject_component sc 
            JOIN subject s ON sc.subject_id = s.id 
            ORDER BY s.name, sc.name
        ''')
        components = cursor.fetchall()
        
        print("\n=== CURRENT COMPONENTS ===")
        for comp in components:
            print(f"Subject: {comp[1]}, Component: {comp[2]}, Weight: {comp[3]}")
        
        # Find ALL English subjects (case-insensitive)
        cursor.execute("SELECT id, name, education_level FROM subject WHERE LOWER(name) = 'english'")
        english_subjects = cursor.fetchall()

        # Find ALL Kiswahili subjects (case-insensitive)
        cursor.execute("SELECT id, name, education_level FROM subject WHERE LOWER(name) = 'kiswahili'")
        kiswahili_subjects = cursor.fetchall()

        print(f"\n🔍 Found {len(english_subjects)} English subjects:")
        for subject in english_subjects:
            print(f"  - ID: {subject[0]}, Name: {subject[1]}, Level: {subject[2]}")

        print(f"\n🔍 Found {len(kiswahili_subjects)} Kiswahili subjects:")
        for subject in kiswahili_subjects:
            print(f"  - ID: {subject[0]}, Name: {subject[1]}, Level: {subject[2]}")

        if not english_subjects and not kiswahili_subjects:
            print("❌ No English or Kiswahili subjects found!")
            return False
        
        # Update English subjects to be composite
        print("\n🔧 Making English subjects composite...")
        for subject in english_subjects:
            subject_id, subject_name, education_level = subject
            
            # Update to composite
            cursor.execute("UPDATE subject SET is_composite = 1 WHERE id = ?", (subject_id,))
            print(f"✅ Updated {subject_name} ({education_level}) to composite")
            
            # Check if components already exist
            cursor.execute("SELECT COUNT(*) FROM subject_component WHERE subject_id = ?", (subject_id,))
            existing_components = cursor.fetchone()[0]
            
            if existing_components == 0:
                # Add English components (Grammar and Composition)
                print(f"📝 Adding components for {subject_name}...")
                
                # Grammar component (60% weight)
                cursor.execute("""
                    INSERT INTO subject_component (subject_id, name, weight) 
                    VALUES (?, 'Grammar', 60.0)
                """, (subject_id,))
                
                # Composition component (40% weight)
                cursor.execute("""
                    INSERT INTO subject_component (subject_id, name, weight) 
                    VALUES (?, 'Composition', 40.0)
                """, (subject_id,))
                
                print(f"  ✅ Added Grammar (60%) and Composition (40%) components")
            else:
                print(f"  ℹ️ Components already exist for {subject_name}")

        # Update Kiswahili subjects to be composite
        print("\n🔧 Making Kiswahili subjects composite...")
        for subject in kiswahili_subjects:
            subject_id, subject_name, education_level = subject

            # Update to composite
            cursor.execute("UPDATE subject SET is_composite = 1 WHERE id = ?", (subject_id,))
            print(f"✅ Updated {subject_name} ({education_level}) to composite")

            # Check if components already exist
            cursor.execute("SELECT COUNT(*) FROM subject_component WHERE subject_id = ?", (subject_id,))
            existing_components = cursor.fetchone()[0]

            if existing_components == 0:
                # Add Kiswahili components (Lugha and Insha)
                print(f"📝 Adding components for {subject_name}...")

                # Lugha component (50% weight)
                cursor.execute("""
                    INSERT INTO subject_component (subject_id, name, weight)
                    VALUES (?, 'Lugha', 50.0)
                """, (subject_id,))

                # Insha component (50% weight)
                cursor.execute("""
                    INSERT INTO subject_component (subject_id, name, weight)
                    VALUES (?, 'Insha', 50.0)
                """, (subject_id,))

                print(f"  ✅ Added Lugha (50%) and Insha (50%) components")
            else:
                print(f"  ℹ️ Components already exist for {subject_name}")

        # Verify the changes
        print("\n🔍 Verifying changes...")
        
        cursor.execute("SELECT id, name, education_level, is_composite FROM subject WHERE LOWER(name) IN ('english', 'kiswahili')")
        updated_subjects = cursor.fetchall()

        print("\n=== UPDATED COMPOSITE SUBJECTS ===")
        for subject in updated_subjects:
            print(f"ID: {subject[0]}, Name: {subject[1]}, Level: {subject[2]}, Composite: {subject[3]}")

        cursor.execute('''
            SELECT sc.id, s.name as subject_name, sc.name as component_name, sc.weight
            FROM subject_component sc
            JOIN subject s ON sc.subject_id = s.id
            WHERE LOWER(s.name) IN ('english', 'kiswahili')
            ORDER BY s.name, sc.name
        ''')
        composite_components = cursor.fetchall()

        print("\n=== COMPOSITE SUBJECT COMPONENTS ===")
        for comp in composite_components:
            print(f"Subject: {comp[1]}, Component: {comp[2]}, Weight: {comp[3]}")
        
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
    print("🔧 Fixing English subject to be composite...")
    success = fix_english_composite()
    if success:
        print("\n🎉 English subject successfully configured as composite!")
        print("📝 English now has Grammar and Composition components like Kiswahili has Lugha and Insha.")
    else:
        print("\n❌ Failed to fix English subject.")
