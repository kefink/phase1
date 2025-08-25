#!/usr/bin/env python3
"""
MySQL implementation of composite subject fix.
"""

import pymysql
import os
import sys
import urllib.parse

def get_mysql_connection():
    """Get MySQL connection using config settings."""
    try:
        # MySQL Configuration from config.py
        MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
        MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
        MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
        MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or urllib.parse.quote_plus('@2494/lK')
        MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'hillview_demo001'
        
        # Decode the password
        password = urllib.parse.unquote_plus(MYSQL_PASSWORD)
        
        print(f"🔗 Connecting to MySQL: {MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
        
        connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=password,
            database=MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        return connection
        
    except Exception as e:
        print(f"❌ Failed to connect to MySQL: {e}")
        return None

def implement_composite_fix():
    """Implement the composite subject fix directly via MySQL."""
    print("🎯 Implementing Composite Subject Architecture Fix (MySQL)")
    print("=" * 60)
    
    # Get MySQL connection
    conn = get_mysql_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check current subjects
        cursor.execute("SELECT name, education_level, is_composite, is_component, composite_parent FROM subject")
        subjects = cursor.fetchall()
        
        print(f"\n📚 Found {len(subjects)} subjects in database")
        
        # Show current state
        composite_subjects = [s for s in subjects if s['is_composite']]
        component_subjects = [s for s in subjects if s['is_component']]
        
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
                    "SELECT id FROM subject WHERE name = %s AND education_level = %s",
                    (composite_name, education_level)
                )
                composite_result = cursor.fetchone()
                
                if composite_result:
                    # Update existing composite subject
                    print(f"   ✅ Updating composite subject: {composite_name}")
                    cursor.execute(
                        "UPDATE subject SET is_composite = 1, is_component = 0 WHERE name = %s AND education_level = %s",
                        (composite_name, education_level)
                    )
                else:
                    # Create composite subject
                    print(f"   ➕ Creating composite subject: {composite_name}")
                    cursor.execute(
                        "INSERT INTO subject (name, education_level, is_composite, is_component) VALUES (%s, %s, 1, 0)",
                        (composite_name, education_level)
                    )
                
                # Create/update component subjects
                weights = [0.6, 0.4]  # Grammar/Lugha: 60%, Composition/Insha: 40%
                
                for i, component_name in enumerate(component_names):
                    cursor.execute(
                        "SELECT id FROM subject WHERE name = %s AND education_level = %s",
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
                               composite_parent = %s, 
                               component_weight = %s 
                               WHERE name = %s AND education_level = %s""",
                            (composite_name, weights[i], component_name, education_level)
                        )
                    else:
                        # Create component subject
                        print(f"   ➕ Creating component subject: {component_name}")
                        cursor.execute(
                            """INSERT INTO subject 
                               (name, education_level, is_composite, is_component, composite_parent, component_weight) 
                               VALUES (%s, %s, 0, 1, %s, %s)""",
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
            level_subjects = [s for s in updated_subjects if s['education_level'] == education_level]
            composite_subjects = [s for s in level_subjects if s['is_composite']]
            
            for composite in composite_subjects:
                print(f"   ✅ {composite['name']} (composite)")
                
                # Show components
                components = [s for s in level_subjects if s['is_component'] and s['composite_parent'] == composite['name']]
                for component in components:
                    weight_percent = int(component['component_weight'] * 100) if component['component_weight'] else 0
                    print(f"      └─ {component['name']} (weight: {weight_percent}%)")
        
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
        if conn:
            conn.rollback()
            conn.close()
        return False

def main():
    """Main function."""
    success = implement_composite_fix()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
