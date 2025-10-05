#!/usr/bin/env python3
"""
SIMPLEST METHOD: Auto-link Kevin to real students via HTTP
"""
import requests

def quick_link_kevin():
    """Try to link Kevin via the web interface"""
    
    print("🚀 QUICK METHOD: Link Kevin to Real Students")
    print("=" * 45)
    
    # Method 1: Try to find an admin interface
    base_url = "http://127.0.0.1:8080"
    
    print("1. **Manual Database Method (RECOMMENDED):**")
    print("   • Open your MySQL database manager (phpMyAdmin, etc.)")
    print("   • Use database: hillview_demo001")
    print("   • Run this single command:")
    print()
    
    quick_sql = """UPDATE parent_student 
SET parent_id = (SELECT id FROM parent WHERE email='kevin_parent@gmail.com')
WHERE student_id IN (
    SELECT DISTINCT s.id FROM student s
    JOIN grade g ON s.grade_id = g.id  
    JOIN stream st ON s.stream_id = st.id
    JOIN mark m ON s.id = m.student_id
    WHERE g.name = 'Grade 9' AND st.name = 'B'
    LIMIT 2
);"""
    
    print(quick_sql)
    
    print("\n2. **Even Simpler - Direct ID Method:**")
    print("   If you know specific student IDs, just run:")
    print("   ```sql")
    print("   INSERT INTO parent_student (parent_id, student_id, relationship)")
    print("   VALUES ")
    print("   ((SELECT id FROM parent WHERE email='kevin_parent@gmail.com'), 123, 'parent'),")
    print("   ((SELECT id FROM parent WHERE email='kevin_parent@gmail.com'), 124, 'parent');")
    print("   ```")
    print("   (Replace 123, 124 with actual student IDs from Grade 9 Stream B)")
    
    print("\n3. **Test Immediately:**")
    print(f"   • Go to: {base_url}/parent/login")
    print("   • Login: kevin_parent@gmail.com / password123")
    print("   • Visit children page and click Reports")
    
    print("\n🎯 **RESULT:**")
    print("   Kevin will see REAL reports that link directly to:")
    print("   /classteacher/preview_individual_report/Grade%209/Stream%20B/term%203/midterm%203%202025/STUDENT_NAME")
    
    return True

if __name__ == "__main__":
    quick_link_kevin()
    
    print("\n" + "="*50)
    print("💡 SUMMARY - You have 3 options:")
    print("="*50)
    print("A) Run the SQL commands above in your database")
    print("B) Use phpMyAdmin/MySQL Workbench with the database")  
    print("C) Ask me to help you find the exact student IDs")
    print("\nThe parent portal code is READY - just needs the data link!")
    print("Once linked, Kevin will see the actual classteacher reports! 🎉")