#!/usr/bin/env python3
"""
Debug script to check the data being passed to the manage_students template
"""

import pymysql

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '@2494/lK',
    'database': 'hillview_demo001',
    'charset': 'utf8mb4'
}

def debug_template_data():
    """Debug the data being passed to manage_students template"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        print("🔍 Debugging Template Data for manage_students.html")
        print("=" * 60)

        # Get all grades from database
        cursor.execute("SELECT id, name FROM grade ORDER BY id")
        grade_rows = cursor.fetchall()
        grades = [{"id": row['id'], "name": row['name']} for row in grade_rows]

        # Define educational level mapping (same as in the route)
        educational_level_mapping = {
            "lower_primary": ["Grade 1", "Grade 2", "Grade 3"],
            "upper_primary": ["Grade 4", "Grade 5", "Grade 6"],
            "junior_secondary": ["Grade 7", "Grade 8", "Grade 9"]
        }
        
        print("📊 Grades Data:")
        for grade in grades:
            print(f"  - ID: {grade['id']}, Name: {grade['name']}")
        
        print(f"\n📚 Total Grades: {len(grades)}")
        
        print("\n🎓 Educational Level Mapping:")
        for level, grade_names in educational_level_mapping.items():
            print(f"  - {level}: {grade_names}")
        
        print("\n🧪 Testing Filter Logic:")
        print("-" * 40)
        
        # Test Junior Secondary filtering
        selected_level = "junior_secondary"
        allowed_grades = educational_level_mapping.get(selected_level, [])
        print(f"\n🎯 Selected Level: {selected_level}")
        print(f"📋 Allowed Grades: {allowed_grades}")
        
        matching_grades = []
        for grade in grades:
            if grade['name'] in allowed_grades:
                matching_grades.append(grade)
        
        print(f"✅ Matching Grades Found: {len(matching_grades)}")
        for grade in matching_grades:
            print(f"  - {grade['name']} (ID: {grade['id']})")
        
        if len(matching_grades) == 0:
            print("❌ NO MATCHING GRADES FOUND!")
            print("🔍 This explains why the dropdown is empty!")
            
            print("\n🔧 Debugging Grade Names:")
            print("Database Grade Names:")
            for grade in grades:
                print(f"  - '{grade['name']}'")
            
            print("Expected Grade Names:")
            for grade_name in allowed_grades:
                print(f"  - '{grade_name}'")
        
        print("\n" + "=" * 60)
        
        # Test all levels
        for level_name, expected_grades in educational_level_mapping.items():
            print(f"\n🧪 Testing {level_name}:")
            matches = [g for g in grades if g['name'] in expected_grades]
            print(f"  Expected: {expected_grades}")
            print(f"  Found: {[g['name'] for g in matches]} ({len(matches)} matches)")

        cursor.close()
        connection.close()

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    debug_template_data()
