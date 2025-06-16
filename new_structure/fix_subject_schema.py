#!/usr/bin/env python3
"""
Fix subject table schema to allow same subject names for different education levels
"""

import sqlite3
import os

def fix_subject_schema():
    """Fix the subject table schema to remove UNIQUE constraint on name."""
    
    # Database path
    db_path = 'kirima_primary.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking current subject table schema...")
        
        # Get current table info
        cursor.execute('PRAGMA table_info(subject)')
        current_schema = cursor.fetchall()
        
        print("\n=== CURRENT SUBJECT TABLE SCHEMA ===")
        for col in current_schema:
            print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, Default: {col[4]}, PK: {col[5]}")
        
        # Backup current data
        print("\n📋 Backing up current subject data...")
        cursor.execute('SELECT * FROM subject')
        subject_data = cursor.fetchall()
        
        print(f"Found {len(subject_data)} subjects to backup")
        
        # Get foreign key references
        cursor.execute('SELECT * FROM subject_component')
        component_data = cursor.fetchall()
        
        cursor.execute('SELECT * FROM teacher_subjects')
        teacher_subject_data = cursor.fetchall()
        
        cursor.execute('SELECT * FROM mark WHERE subject_id IS NOT NULL')
        mark_data = cursor.fetchall()
        
        print(f"Found {len(component_data)} components, {len(teacher_subject_data)} teacher assignments, {len(mark_data)} marks")
        
        # Drop the old table
        print("\n🗑️ Dropping old subject table...")
        cursor.execute('DROP TABLE IF EXISTS subject')
        
        # Create new table without UNIQUE constraint on name
        print("🔧 Creating new subject table...")
        cursor.execute("""
            CREATE TABLE subject (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                education_level TEXT NOT NULL,
                is_composite BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, education_level)
            )
        """)
        
        # Restore data
        print("📥 Restoring subject data...")
        for subject in subject_data:
            cursor.execute("""
                INSERT INTO subject (id, name, education_level, is_composite, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, subject)
        
        # Restore components
        print("📥 Restoring subject components...")
        for component in component_data:
            cursor.execute("""
                INSERT INTO subject_component (id, subject_id, name, weight, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, component)
        
        # Restore teacher assignments
        print("📥 Restoring teacher-subject assignments...")
        for assignment in teacher_subject_data:
            cursor.execute("""
                INSERT INTO teacher_subjects (teacher_id, subject_id)
                VALUES (?, ?)
            """, assignment)
        
        print("✅ Schema migration completed successfully!")
        
        # Now add missing subjects
        print("\n🔧 Adding missing English and Kiswahili subjects...")
        
        education_levels = ['upper_primary', 'junior_secondary']
        
        for level in education_levels:
            # Add English
            cursor.execute("SELECT id FROM subject WHERE name = 'English' AND education_level = ?", (level,))
            if not cursor.fetchone():
                print(f"➕ Adding English for {level}...")
                cursor.execute("""
                    INSERT INTO subject (name, education_level, is_composite) 
                    VALUES ('English', ?, 1)
                """, (level,))
                
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
                
                print(f"  ✅ Added English for {level} with components")
            
            # Add Kiswahili
            cursor.execute("SELECT id FROM subject WHERE name = 'Kiswahili' AND education_level = ?", (level,))
            if not cursor.fetchone():
                print(f"➕ Adding Kiswahili for {level}...")
                cursor.execute("""
                    INSERT INTO subject (name, education_level, is_composite) 
                    VALUES ('Kiswahili', ?, 1)
                """, (level,))
                
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
                
                print(f"  ✅ Added Kiswahili for {level} with components")
        
        # Verify final state
        print("\n🔍 Final verification...")
        cursor.execute("""
            SELECT s.name, s.education_level, s.is_composite,
                   GROUP_CONCAT(sc.name || ' (' || sc.weight || '%)', ', ') as components
            FROM subject s
            LEFT JOIN subject_component sc ON s.id = sc.subject_id
            WHERE s.name IN ('English', 'Kiswahili')
            GROUP BY s.id, s.name, s.education_level, s.is_composite
            ORDER BY s.name, s.education_level
        """)
        final_subjects = cursor.fetchall()
        
        print("\n=== FINAL COMPOSITE SUBJECTS ===")
        for subject in final_subjects:
            components = subject[3] if subject[3] else "No components"
            print(f"📚 {subject[0]} ({subject[1]}) - Composite: {subject[2]} - Components: {components}")
        
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
    print("🔧 Fixing subject table schema...")
    success = fix_subject_schema()
    if success:
        print("\n🎉 Subject schema fixed and composite subjects added!")
        print("📝 English and Kiswahili are now composite for all education levels.")
    else:
        print("\n❌ Failed to fix subject schema.")
