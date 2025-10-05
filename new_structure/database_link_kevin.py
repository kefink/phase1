#!/usr/bin/env python3
"""
Direct database approach to link Kevin to existing students with real report data
"""

# Method 1: SQL Commands (Copy and paste these into your database)
sql_commands = """
-- STEP 1: Find Kevin's parent ID
SELECT id, first_name, last_name, email FROM parent WHERE email='kevin_parent@gmail.com';

-- STEP 2: Find students who have actual marks in Grade 9 Stream B for term 3, midterm 3 2025
SELECT DISTINCT s.id, s.first_name, s.last_name, s.admission_number, 
       g.name as grade, st.name as stream, COUNT(m.id) as mark_count
FROM student s
JOIN grade g ON s.grade_id = g.id
JOIN stream st ON s.stream_id = st.id
LEFT JOIN mark m ON s.id = m.student_id
JOIN term t ON m.term_id = t.id
JOIN assessment_type at ON m.assessment_type_id = at.id
WHERE g.name = 'Grade 9' 
  AND st.name = 'B'
  AND t.name = 'term 3'
  AND at.name LIKE '%midterm%'
GROUP BY s.id, s.first_name, s.last_name, s.admission_number, g.name, st.name
HAVING COUNT(m.id) > 0
ORDER BY mark_count DESC;

-- STEP 3: Link Kevin to real students (replace X and Y with actual student IDs from step 2)
-- First, remove any existing links for Kevin
DELETE FROM parent_student WHERE parent_id = (SELECT id FROM parent WHERE email='kevin_parent@gmail.com');

-- Then add links to real students with data
INSERT INTO parent_student (parent_id, student_id, relationship, created_at, updated_at)
SELECT 
    (SELECT id FROM parent WHERE email='kevin_parent@gmail.com'),
    s.id,
    'parent',
    NOW(),
    NOW()
FROM student s
JOIN grade g ON s.grade_id = g.id
JOIN stream st ON s.stream_id = st.id
WHERE g.name = 'Grade 9' AND st.name = 'B'
AND s.id IN (
    SELECT DISTINCT student_id FROM mark m
    JOIN term t ON m.term_id = t.id
    JOIN assessment_type at ON m.assessment_type_id = at.id
    WHERE t.name = 'term 3' AND at.name LIKE '%midterm%'
)
LIMIT 2; -- Link Kevin to 2 students with real data

-- STEP 4: Verify the connection
SELECT p.first_name as parent_name, p.email, s.first_name as student_name, s.last_name, 
       g.name as grade, st.name as stream
FROM parent p
JOIN parent_student ps ON p.id = ps.parent_id
JOIN student s ON ps.student_id = s.id
JOIN grade g ON s.grade_id = g.id
JOIN stream st ON s.stream_id = st.id
WHERE p.email = 'kevin_parent@gmail.com';
"""

print("🗄️ DATABASE COMMANDS TO LINK KEVIN TO REAL STUDENTS")
print("=" * 55)
print("Copy and paste these SQL commands into your database tool:")
print()
print(sql_commands)

print("\n" + "="*55)
print("🌐 ALTERNATIVE WEB-BASED METHOD:")
print("=" * 55)

web_method = f"""
1. **Access MySQL/Database directly:**
   • Use phpMyAdmin, MySQL Workbench, or command line
   • Connect to your 'hillview_demo001' database
   • Run the SQL commands above

2. **Or use Flask shell method:**
   • Open terminal in your project directory
   • Run: python -c "from __init__ import create_app; from models import db; app=create_app(); app.app_context().push(); 
     # Then run Python database queries
   
3. **Test the result:**
   • Go to: http://127.0.0.1:8080/parent/login
   • Login as: kevin_parent@gmail.com / password123
   • Visit: http://127.0.0.1:8080/parent/children
   • Click "Reports" for any child
   • Should redirect to real classteacher reports!
"""

print(web_method)

print("\n🎯 WHAT THIS ACCOMPLISHES:")
print("• Links Kevin's parent account to students who have REAL marks")
print("• These students have actual data in Grade 9 Stream B term 3 midterm 3 2025")
print("• When Kevin clicks 'Reports', he'll see the REAL classteacher reports")
print("• The parent portal will redirect to URLs like:")
print("  http://127.0.0.1:8080/classteacher/preview_individual_report/Grade%209/Stream%20B/term%203/midterm%203%202025/STUDENT_NAME")

if __name__ == "__main__":
    pass