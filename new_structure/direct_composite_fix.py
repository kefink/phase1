#!/usr/bin/env python3
"""
Direct database implementation of composite subject fix.
"""

import sqlite3
import os
import sys

def implement_composite_fix():
    """Implement the composite subject fix directly via database."""
    print("🎯 Implementing Composite Subject Architecture Fix")
    print("=" * 60)
    
    # Find the database file
    db_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.db') or file.endswith('.sqlite'):
                db_files.append(os.path.join(root, file))
    
    if not db_files:
        print("❌ No database files found!")
        return False
    
    print(f"📊 Found database files: {db_files}")
    
    # Use the first database file found
    db_path = db_files[0]
    print(f"🔗 Using database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current subjects
        cursor.execute("SELECT name, education_level, is_composite, is_component, composite_parent FROM subject")
        subjects = cursor.fetchall()
        
        print(f"\n📚 Found {len(subjects)} subjects in database")
        
        # Show current state
        composite_subjects = [s for s in subjects if s[2]]  # is_composite
        component_subjects = [s for s in subjects if s[3]]  # is_component
        
        print(f"   - Composite subjects: {len(composite_subjects)}")
        print(f"   - Component subjects: {len(component_subjects)}")
        
        # Define the composite mappings we want
        composite_mappings = {
            'English': ['English Grammar', 'English Composition'],
            'Kiswahili': ['Kiswahili Lugha', 'Kiswahili Insha']
        }
        
        print("\n🔧 Implementing enhanced composite architecture...")
        
        # Process each education level
        education_levels = ['lower_primary', 'upper_primary', 'junior_secondary']
        
        for education_level in education_levels:
            print(f"\n📚 Processing {education_level}...")
            
            for composite_name, component_names in composite_mappings.items():
                # Check if composite subject exists
                cursor.execute(
                    "SELECT id FROM subject WHERE name = ? AND education_level = ?",
                    (composite_name, education_level)
                )
                composite_result = cursor.fetchone()
                
                if composite_result:
                    # Update existing composite subject
                    print(f"   ✅ Updating composite subject: {composite_name}")
                    cursor.execute(
                        "UPDATE subject SET is_composite = 1, is_component = 0 WHERE name = ? AND education_level = ?",
                        (composite_name, education_level)
                    )
                else:
                    # Create composite subject
                    print(f"   ➕ Creating composite subject: {composite_name}")
                    cursor.execute(
                        "INSERT INTO subject (name, education_level, is_composite, is_component) VALUES (?, ?, 1, 0)",
                        (composite_name, education_level)
                    )
                
                # Create/update component subjects
                weights = [0.6, 0.4]  # Grammar/Lugha: 60%, Composition/Insha: 40%
                
                for i, component_name in enumerate(component_names):
                    cursor.execute(
                        "SELECT id FROM subject WHERE name = ? AND education_level = ?",
                        (component_name, education_level)
                    )
                    component_result = cursor.fetchone()
                    
                    if component_result:
                        # Update existing component subject
                        print(f"   ✅ Updating component subject: {component_name}")
                        cursor.execute(
                            """UPDATE subject SET 
                               is_composite = 0, 
                               is_component = 1, 
                               composite_parent = ?, 
                               component_weight = ? 
                               WHERE name = ? AND education_level = ?""",
                            (composite_name, weights[i], component_name, education_level)
                        )
                    else:
                        # Create component subject
                        print(f"   ➕ Creating component subject: {component_name}")
                        cursor.execute(
                            """INSERT INTO subject 
                               (name, education_level, is_composite, is_component, composite_parent, component_weight) 
                               VALUES (?, ?, 0, 1, ?, ?)""",
                            (component_name, education_level, composite_name, weights[i])
                        )
        
        # Commit changes
        conn.commit()
        print("\n✅ Database changes committed successfully!")
        
        # Verify the setup
        print("\n🔍 Verifying the setup...")
        
        cursor.execute("SELECT name, education_level, is_composite, is_component, composite_parent, component_weight FROM subject ORDER BY education_level, name")
        updated_subjects = cursor.fetchall()
        
        for education_level in education_levels:
            print(f"\n📚 {education_level}:")
            
            # Show composite subjects
            level_subjects = [s for s in updated_subjects if s[1] == education_level]
            composite_subjects = [s for s in level_subjects if s[2]]  # is_composite
            
            for composite in composite_subjects:
                print(f"   ✅ {composite[0]} (composite)")
                
                # Show components
                components = [s for s in level_subjects if s[3] and s[4] == composite[0]]  # is_component and composite_parent
                for component in components:
                    weight_percent = int(component[5] * 100) if component[5] else 0
                    print(f"      └─ {component[0]} (weight: {weight_percent}%)")
        
        conn.close()
        
        print("\n🎉 Implementation completed successfully!")
        print("=" * 60)
        print("📋 What was implemented:")
        print("✅ English Grammar and English Composition are now separate uploadable subjects")
        print("✅ Kiswahili Lugha and Kiswahili Insha are now separate uploadable subjects")
        print("✅ All subjects properly configured with composite relationships")
        print("✅ Component weights set (Grammar/Lugha: 60%, Composition/Insha: 40%)")
        
        print("\n📝 Next steps:")
        print("1. Restart your Flask application")
        print("2. Test uploading marks for English Grammar separately")
        print("3. Test uploading marks for English Composition separately")
        print("4. Generate a class report to see the new structure")
        print("5. Verify that marks combine properly in reports")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during implementation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    success = implement_composite_fix()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
