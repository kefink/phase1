#!/usr/bin/env python3
"""
Link Kevin's parent account to existing real students who have report data
"""
import requests
import json

def link_kevin_to_real_students():
    """Find real students and link them to Kevin's parent account"""
    base_url = "http://127.0.0.1:8080"
    
    print("🔗 LINKING KEVIN TO REAL STUDENTS")
    print("=" * 40)
    
    # Step 1: Find what real students exist by accessing the debug data page
    try:
        response = requests.get(f"{base_url}/debug/data")
        if response.status_code == 200:
            print("✅ Accessed debug data page")
            html = response.text
            
            # Look for student data in the HTML
            import re
            
            # Look for student names, admission numbers, or IDs
            student_patterns = [
                r'Student.*?(\d+).*?([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'name["\']:\s*["\']([A-Z][a-z]+\s+[A-Z][a-z]+)["\']',
                r'admission.*?([A-Z]{2,}\d{4,})'
            ]
            
            students_found = []
            for pattern in student_patterns:
                matches = re.findall(pattern, html)
                students_found.extend(matches)
            
            print(f"🔍 Found potential students: {students_found[:5]}")
            
        else:
            print("❌ Could not access debug data")
            
    except Exception as e:
        print(f"Error accessing debug data: {e}")
    
    print(f"\n📋 MANUAL STEPS TO COMPLETE THE CONNECTION:")
    print(f"=" * 50)
    
    print(f"1. **Access the Database Directly:**")
    print(f"   • Open: {base_url}/debug/data")
    print(f"   • Look for students in 'Grade 9 Stream B' who have marks")
    print(f"   • Note their Student IDs")
    
    print(f"\n2. **Create Parent-Student Links:**")
    print(f"   You need to run SQL commands to link Kevin to real students:")
    print(f"   ```sql")
    print(f"   -- Find Kevin's parent ID")
    print(f"   SELECT id, email FROM parent WHERE email='kevin_parent@gmail.com';")
    print(f"   ")
    print(f"   -- Find real students in Grade 9 Stream B")
    print(f"   SELECT s.id, s.name, g.name as grade, st.name as stream")
    print(f"   FROM student s")
    print(f"   JOIN grade g ON s.grade_id = g.id")
    print(f"   JOIN stream st ON s.stream_id = st.id")
    print(f"   WHERE g.name = 'Grade 9' AND st.name = 'B';")
    print(f"   ")
    print(f"   -- Link Kevin to real students (replace with actual IDs)")
    print(f"   INSERT INTO parent_student (parent_id, student_id, relationship)")
    print(f"   VALUES ")
    print(f"   (KEVIN_PARENT_ID, REAL_STUDENT_ID_1, 'parent'),")
    print(f"   (KEVIN_PARENT_ID, REAL_STUDENT_ID_2, 'parent');")
    print(f"   ```")
    
    print(f"\n3. **Alternative: Use Registration to Link:**")
    print(f"   • Go to: {base_url}/parent/children")
    print(f"   • Look for an 'Add Child' or 'Link Student' option")
    print(f"   • Enter admission numbers of real students")
    
    print(f"\n4. **Verify the Connection:**")
    print(f"   • Login as Kevin: {base_url}/parent/login")
    print(f"   • Email: kevin_parent@gmail.com")
    print(f"   • Password: password123")
    print(f"   • Check: {base_url}/parent/children")
    print(f"   • Click on Reports for any child")

if __name__ == "__main__":
    link_kevin_to_real_students()