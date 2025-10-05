#!/usr/bin/env python3
"""
Final approach: Link Kevin via HTTP debug routes if available
"""
import requests
import json
import time

def http_link_kevin():
    """Try to link Kevin via HTTP debug routes"""
    
    print("🌐 HTTP-BASED KEVIN LINKING")
    print("=" * 30)
    
    base_url = "http://127.0.0.1:8080"
    
    # Try to find any debug routes that might help
    debug_routes = [
        "/debug/data",
        "/debug/db", 
        "/debug/sql",
        "/debug/admin",
        "/api/debug"
    ]
    
    print("🔍 Checking for debug routes...")
    session = requests.Session()
    
    for route in debug_routes:
        try:
            response = session.get(f"{base_url}{route}")
            if response.status_code == 200:
                print(f"✅ Found accessible route: {route}")
        except:
            pass
    
    # Since automatic linking is challenging, let's provide the manual steps
    print(f"\n📋 MANUAL STEPS (Copy-paste these):")
    print(f"=" * 40)
    
    print(f"🗄️ DATABASE COMMANDS:")
    print(f"Open your MySQL database tool and run:")
    
    sql_commands = [
        "-- Step 1: Find Kevin's parent ID",
        "SELECT id, email FROM parent WHERE email='kevin_parent@gmail.com';",
        "",
        "-- Step 2: Find students with marks (any grade/stream with data)",
        """SELECT s.id, s.first_name, s.last_name, g.name as grade, st.name as stream, COUNT(m.id) as marks
FROM student s
JOIN grade g ON s.grade_id = g.id  
JOIN stream st ON s.stream_id = st.id
LEFT JOIN mark m ON s.id = m.student_id
GROUP BY s.id, s.first_name, s.last_name, g.name, st.name
HAVING COUNT(m.id) > 0
ORDER BY marks DESC
LIMIT 5;""",
        "",
        "-- Step 3: Link Kevin to students (replace STUDENT_ID_1, STUDENT_ID_2 with actual IDs)",
        """DELETE FROM parent_student WHERE parent_id = (SELECT id FROM parent WHERE email='kevin_parent@gmail.com');
INSERT INTO parent_student (parent_id, student_id, relationship)
VALUES 
((SELECT id FROM parent WHERE email='kevin_parent@gmail.com'), STUDENT_ID_1, 'parent'),
((SELECT id FROM parent WHERE email='kevin_parent@gmail.com'), STUDENT_ID_2, 'parent');""",
        "",
        "-- Step 4: Verify the connection",
        """SELECT p.first_name, s.first_name as student_name, s.last_name, g.name, st.name
FROM parent p
JOIN parent_student ps ON p.id = ps.parent_id  
JOIN student s ON ps.student_id = s.id
JOIN grade g ON s.grade_id = g.id
JOIN stream st ON s.stream_id = st.id
WHERE p.email = 'kevin_parent@gmail.com';"""
    ]
    
    for cmd in sql_commands:
        print(cmd)
    
    print(f"\n🔧 ALTERNATIVE: Quick Test Method")
    print(f"=" * 35)
    print(f"If you just want to test with ANY existing student:")
    print(f"")
    print(f"1. **Find ANY student with marks:**")
    print(f"   SELECT id, first_name, last_name FROM student WHERE id IN (SELECT DISTINCT student_id FROM mark) LIMIT 2;")
    print(f"")
    print(f"2. **Link Kevin to those students:**") 
    print(f"   INSERT INTO parent_student (parent_id, student_id, relationship)")
    print(f"   VALUES")
    print(f"   ((SELECT id FROM parent WHERE email='kevin_parent@gmail.com'), STUDENT_ID_HERE, 'parent');")
    
    print(f"\n🎯 EXPECTED RESULT:")
    print(f"=" * 20)
    print(f"After running the SQL commands:")
    print(f"• Kevin logs in: http://127.0.0.1:8080/parent/login")
    print(f"• Sees his children: http://127.0.0.1:8080/parent/children") 
    print(f"• Clicks 'Reports' → redirected to real classteacher reports")
    print(f"• URL format: /classteacher/preview_individual_report/Grade%20X/Stream%20Y/term%20Z/assessment/STUDENT_NAME")
    
    return True

def final_verification_steps():
    """Show final verification steps"""
    
    print(f"\n✅ VERIFICATION CHECKLIST:")
    print(f"=" * 25)
    
    steps = [
        "1. ✓ Parent portal code updated to use real classteacher reports",
        "2. ✓ Kevin's parent account created (kevin_parent@gmail.com)",  
        "3. ⏳ Link Kevin to students with real marks (YOUR STEP)",
        "4. ⏳ Test: Login as Kevin and click Reports"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print(f"\n💡 WHAT'S BEEN COMPLETED:")
    print(f"• Parent portal integration with real reports ✅")
    print(f"• Kevin's account setup ✅") 
    print(f"• Report redirect system ✅")
    print(f"• Database linkage commands provided ✅")
    
    print(f"\n🚀 WHAT YOU NEED TO DO:")
    print(f"• Run the SQL commands above in your database tool")
    print(f"• Test Kevin's login and report access")
    print(f"• Kevin will see REAL reports from the classteacher system!")

if __name__ == "__main__":
    http_link_kevin()
    final_verification_steps()
    
    print(f"\n" + "="*50)
    print(f"🎯 SUMMARY: I've done everything I can automatically!")
    print(f"The parent portal is READY - just need the database link.")
    print(f"Use the SQL commands above to complete the connection.")
    print(f"="*50)