#!/usr/bin/env python3
"""
Direct database connection to link Kevin automatically
"""
import pymysql
import os

def direct_db_link_kevin():
    """Use direct MySQL connection to link Kevin"""
    
    print("🔗 DIRECT DATABASE AUTO-LINKING")
    print("=" * 35)
    
    # Database connection details from config
    db_config = {
        'host': os.environ.get('MYSQL_HOST', 'localhost'),
        'port': int(os.environ.get('MYSQL_PORT', 3306)),
        'user': os.environ.get('MYSQL_USER', 'root'),
        'password': os.environ.get('MYSQL_PASSWORD', ''),
        'database': os.environ.get('MYSQL_DATABASE', 'hillview_demo001'),
        'charset': 'utf8mb4'
    }
    
    try:
        print("🔌 Connecting to MySQL database...")
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        
        print("✅ Connected to database!")
        
        # Step 1: Find Kevin's parent ID
        print("\n📋 Step 1: Finding Kevin's parent account...")
        cursor.execute("SELECT id, first_name, last_name, email FROM parent WHERE email='kevin_parent@gmail.com'")
        kevin_parent = cursor.fetchone()
        
        if not kevin_parent:
            print("❌ Kevin's parent account not found!")
            return False
            
        kevin_id = kevin_parent[0]
        print(f"✅ Found Kevin's parent: ID={kevin_id}, Name={kevin_parent[1]} {kevin_parent[2]}")
        
        # Step 2: Find students with real marks
        print("\n📋 Step 2: Finding students with real report data...")
        find_students_sql = """
        SELECT DISTINCT s.id, s.first_name, s.last_name, s.admission_number, 
               g.name as grade, st.name as stream, COUNT(m.id) as mark_count
        FROM student s
        JOIN grade g ON s.grade_id = g.id
        JOIN stream st ON s.stream_id = st.id
        LEFT JOIN mark m ON s.id = m.student_id
        WHERE (g.name LIKE '%9%' OR g.name LIKE '%Grade 9%') 
          AND (st.name LIKE '%B%' OR st.name LIKE '%Stream B%')
        GROUP BY s.id, s.first_name, s.last_name, s.admission_number, g.name, st.name
        HAVING COUNT(m.id) > 0
        ORDER BY mark_count DESC
        LIMIT 3
        """
        
        cursor.execute(find_students_sql)
        students = cursor.fetchall()
        
        if not students:
            print("❌ No students found with marks in Grade 9 Stream B")
            
            # Try broader search
            print("🔍 Trying broader search...")
            cursor.execute("""
            SELECT DISTINCT s.id, s.first_name, s.last_name, s.admission_number, 
                   g.name as grade, st.name as stream, COUNT(m.id) as mark_count
            FROM student s
            JOIN grade g ON s.grade_id = g.id
            JOIN stream st ON s.stream_id = st.id
            LEFT JOIN mark m ON s.id = m.student_id
            GROUP BY s.id, s.first_name, s.last_name, s.admission_number, g.name, st.name
            HAVING COUNT(m.id) > 0
            ORDER BY mark_count DESC
            LIMIT 3
            """)
            students = cursor.fetchall()
        
        if not students:
            print("❌ No students found with any marks!")
            return False
            
        print(f"✅ Found {len(students)} students with report data:")
        for student in students:
            print(f"   - ID: {student[0]}, Name: {student[1]} {student[2]}, Grade: {student[4]}, Stream: {student[5]}, Marks: {student[6]}")
        
        # Step 3: Remove existing links
        print(f"\n📋 Step 3: Removing existing links for Kevin...")
        cursor.execute("DELETE FROM parent_student WHERE parent_id = %s", (kevin_id,))
        deleted_count = cursor.rowcount
        print(f"✅ Removed {deleted_count} existing links")
        
        # Step 4: Create new links
        print(f"\n📋 Step 4: Creating new parent-student links...")
        linked_count = 0
        for student in students[:2]:  # Link to first 2 students
            student_id = student[0]
            student_name = f"{student[1]} {student[2]}"
            
            try:
                cursor.execute("""
                INSERT INTO parent_student (parent_id, student_id, relationship, created_at, updated_at)
                VALUES (%s, %s, 'parent', NOW(), NOW())
                """, (kevin_id, student_id))
                
                print(f"✅ Linked Kevin to {student_name} (ID: {student_id})")
                linked_count += 1
                
            except Exception as e:
                print(f"⚠️ Error linking to {student_name}: {str(e)}")
        
        # Commit changes
        connection.commit()
        print(f"\n💾 Committed {linked_count} new links to database")
        
        # Step 5: Verify the links
        print(f"\n📋 Step 5: Verifying the links...")
        cursor.execute("""
        SELECT p.first_name as parent_name, p.email, s.first_name as student_name, s.last_name, 
               g.name as grade, st.name as stream
        FROM parent p
        JOIN parent_student ps ON p.id = ps.parent_id
        JOIN student s ON ps.student_id = s.id
        JOIN grade g ON s.grade_id = g.id
        JOIN stream st ON s.stream_id = st.id
        WHERE p.email = 'kevin_parent@gmail.com'
        """)
        
        links = cursor.fetchall()
        print(f"✅ Verification: Found {len(links)} active links:")
        for link in links:
            print(f"   - Parent: {link[0]} -> Student: {link[2]} {link[3]} ({link[4]} {link[5]})")
        
        cursor.close()
        connection.close()
        
        if linked_count > 0:
            print(f"\n🎉 SUCCESS! Kevin is now linked to {linked_count} real students!")
            return True
        else:
            print(f"\n❌ Failed to create any links")
            return False
            
    except pymysql.Error as e:
        print(f"❌ Database error: {str(e)}")
        print("💡 This might be because:")
        print("   - Database credentials are incorrect")
        print("   - MySQL server is not running")
        print("   - Database 'hillview_demo001' doesn't exist")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = direct_db_link_kevin()
    
    if success:
        print(f"\n🚀 READY TO TEST!")
        print(f"=" * 20)
        print(f"1. Go to: http://127.0.0.1:8080/parent/login")
        print(f"2. Login: kevin_parent@gmail.com / password123")
        print(f"3. Visit: http://127.0.0.1:8080/parent/children")
        print(f"4. Click 'Reports' for any child")
        print(f"5. You'll be redirected to the REAL classteacher reports!")
        
        # Test the connection
        print(f"\n🧪 Testing connection...")
        try:
            import requests
            session = requests.Session()
            login_response = session.post("http://127.0.0.1:8080/parent/login", data={
                'email': 'kevin_parent@gmail.com',
                'password': 'password123'
            })
            
            if 'dashboard' in login_response.url or 'children' in login_response.url:
                print("✅ Kevin's login test successful!")
                
                children_response = session.get("http://127.0.0.1:8080/parent/children")
                if children_response.status_code == 200 and 'Reports' in children_response.text:
                    print("✅ Children page shows report links!")
                    print("🎯 EVERYTHING IS WORKING! Kevin can now see real reports!")
                    
        except Exception as e:
            print(f"⚠️ Test failed: {str(e)}")
            print("Try accessing manually using the steps above")
    else:
        print(f"\n💡 If automatic linking failed, you can:")
        print(f"   1. Use phpMyAdmin or MySQL Workbench")
        print(f"   2. Run the SQL commands from previous scripts")
        print(f"   3. Or ask me to help troubleshoot the database connection")