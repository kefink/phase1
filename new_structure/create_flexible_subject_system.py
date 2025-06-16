#!/usr/bin/env python3
"""
Create flexible subject configuration system for English and Kiswahili
Supports case-insensitive matching and composite/non-composite toggle
"""

import sqlite3
import os

def create_flexible_subject_system():
    """Create flexible subject configuration system."""
    
    db_path = 'kirima_primary.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Creating flexible subject configuration system...")
        
        # Create subject_configuration table for flexible settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subject_configuration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL,
                education_level TEXT NOT NULL,
                is_composite BOOLEAN DEFAULT 0,
                component_1_name TEXT,
                component_1_weight REAL DEFAULT 50.0,
                component_2_name TEXT,
                component_2_weight REAL DEFAULT 50.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(subject_name, education_level)
            )
        """)
        
        print("✅ Created subject_configuration table")
        
        # Insert default configurations for English and Kiswahili
        education_levels = ['lower_primary', 'upper_primary', 'junior_secondary']
        
        print("\n📝 Setting up default subject configurations...")
        
        for level in education_levels:
            # English configurations (composite by default)
            cursor.execute("""
                INSERT OR REPLACE INTO subject_configuration 
                (subject_name, education_level, is_composite, component_1_name, component_1_weight, component_2_name, component_2_weight)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('english', level, 1, 'Grammar', 60.0, 'Composition', 40.0))
            
            # Kiswahili configurations (composite by default)
            cursor.execute("""
                INSERT OR REPLACE INTO subject_configuration 
                (subject_name, education_level, is_composite, component_1_name, component_1_weight, component_2_name, component_2_weight)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('kiswahili', level, 1, 'Lugha', 50.0, 'Insha', 50.0))
            
            print(f"  ✅ Configured English and Kiswahili for {level}")
        
        # Create function to get subject configuration
        print("\n🔧 Creating helper functions...")
        
        # Create a view for easy subject configuration lookup
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_subject_config AS
            SELECT 
                sc.subject_name,
                sc.education_level,
                sc.is_composite,
                sc.component_1_name,
                sc.component_1_weight,
                sc.component_2_name,
                sc.component_2_weight,
                s.id as subject_id,
                s.name as actual_subject_name
            FROM subject_configuration sc
            LEFT JOIN subject s ON (
                LOWER(s.name) LIKE '%' || sc.subject_name || '%' 
                AND s.education_level = sc.education_level
            )
        """)
        
        print("✅ Created subject configuration view")
        
        # Update existing subjects to match configuration
        print("\n🔄 Updating existing subjects...")
        
        # Get all subjects that contain 'english' (case-insensitive)
        cursor.execute("""
            SELECT id, name, education_level 
            FROM subject 
            WHERE LOWER(name) LIKE '%english%'
        """)
        english_subjects = cursor.fetchall()
        
        for subject_id, subject_name, education_level in english_subjects:
            # Get configuration for this level
            cursor.execute("""
                SELECT is_composite, component_1_name, component_1_weight, component_2_name, component_2_weight
                FROM subject_configuration 
                WHERE subject_name = 'english' AND education_level = ?
            """, (education_level,))
            
            config = cursor.fetchone()
            if config:
                is_composite, comp1_name, comp1_weight, comp2_name, comp2_weight = config
                
                # Update subject to be composite
                cursor.execute("UPDATE subject SET is_composite = ? WHERE id = ?", (is_composite, subject_id))
                
                if is_composite:
                    # Remove existing components
                    cursor.execute("DELETE FROM subject_component WHERE subject_id = ?", (subject_id,))
                    
                    # Add new components based on configuration
                    cursor.execute("""
                        INSERT INTO subject_component (subject_id, name, weight) 
                        VALUES (?, ?, ?)
                    """, (subject_id, comp1_name, comp1_weight))
                    
                    cursor.execute("""
                        INSERT INTO subject_component (subject_id, name, weight) 
                        VALUES (?, ?, ?)
                    """, (subject_id, comp2_name, comp2_weight))
                    
                    print(f"  ✅ Updated {subject_name} ({education_level}) - Composite with {comp1_name} ({comp1_weight}%) and {comp2_name} ({comp2_weight}%)")
                else:
                    print(f"  ✅ Updated {subject_name} ({education_level}) - Non-composite")
        
        # Get all subjects that contain 'kiswahili' (case-insensitive)
        cursor.execute("""
            SELECT id, name, education_level 
            FROM subject 
            WHERE LOWER(name) LIKE '%kiswahili%'
        """)
        kiswahili_subjects = cursor.fetchall()
        
        for subject_id, subject_name, education_level in kiswahili_subjects:
            # Get configuration for this level
            cursor.execute("""
                SELECT is_composite, component_1_name, component_1_weight, component_2_name, component_2_weight
                FROM subject_configuration 
                WHERE subject_name = 'kiswahili' AND education_level = ?
            """, (education_level,))
            
            config = cursor.fetchone()
            if config:
                is_composite, comp1_name, comp1_weight, comp2_name, comp2_weight = config
                
                # Update subject to be composite
                cursor.execute("UPDATE subject SET is_composite = ? WHERE id = ?", (is_composite, subject_id))
                
                if is_composite:
                    # Remove existing components
                    cursor.execute("DELETE FROM subject_component WHERE subject_id = ?", (subject_id,))
                    
                    # Add new components based on configuration
                    cursor.execute("""
                        INSERT INTO subject_component (subject_id, name, weight) 
                        VALUES (?, ?, ?)
                    """, (subject_id, comp1_name, comp1_weight))
                    
                    cursor.execute("""
                        INSERT INTO subject_component (subject_id, name, weight) 
                        VALUES (?, ?, ?)
                    """, (subject_id, comp2_name, comp2_weight))
                    
                    print(f"  ✅ Updated {subject_name} ({education_level}) - Composite with {comp1_name} ({comp1_weight}%) and {comp2_name} ({comp2_weight}%)")
                else:
                    print(f"  ✅ Updated {subject_name} ({education_level}) - Non-composite")
        
        # Verify the configuration
        print("\n🔍 Verifying configuration...")
        cursor.execute("""
            SELECT 
                sc.subject_name,
                sc.education_level,
                sc.is_composite,
                sc.component_1_name || ' (' || sc.component_1_weight || '%)' as component_1,
                sc.component_2_name || ' (' || sc.component_2_weight || '%)' as component_2,
                COUNT(s.id) as matching_subjects
            FROM subject_configuration sc
            LEFT JOIN subject s ON (
                LOWER(s.name) LIKE '%' || sc.subject_name || '%' 
                AND s.education_level = sc.education_level
            )
            GROUP BY sc.subject_name, sc.education_level
            ORDER BY sc.subject_name, sc.education_level
        """)
        
        configs = cursor.fetchall()
        
        print("\n=== SUBJECT CONFIGURATIONS ===")
        for config in configs:
            subject_name, education_level, is_composite, comp1, comp2, matching_subjects = config
            composite_status = "Composite" if is_composite else "Non-composite"
            components = f"{comp1}, {comp2}" if is_composite else "N/A"
            print(f"📚 {subject_name.title()} ({education_level}) - {composite_status}")
            print(f"    Components: {components}")
            print(f"    Matching subjects in DB: {matching_subjects}")
        
        # Commit changes
        conn.commit()
        print("\n✅ Flexible subject configuration system created successfully!")
        
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
    print("🔧 Creating flexible subject configuration system...")
    success = create_flexible_subject_system()
    if success:
        print("\n🎉 Flexible subject system created!")
        print("📝 Schools can now configure English and Kiswahili as composite or non-composite.")
        print("🔄 System supports case-insensitive subject matching.")
    else:
        print("\n❌ Failed to create flexible subject system.")
