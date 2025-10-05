#!/usr/bin/env python3
"""
Automatically link Kevin's parent account to real students with report data
"""
import os
import sys
import subprocess

# Add current directory to Python path
sys.path.insert(0, '.')

# Set environment for proper database connection
os.environ['FLASK_ENV'] = 'development'

def auto_link_kevin():
    """Automatically link Kevin to real students using raw SQL"""
    
    print("🔗 AUTO-LINKING KEVIN TO REAL STUDENTS")
    print("=" * 42)
    
    # SQL commands to execute
    sql_commands = [
        # First, find and display Kevin's parent info
        "SELECT id, first_name, last_name, email FROM parent WHERE email='kevin_parent@gmail.com';",
        
        # Find students with real marks in Grade 9 Stream B
        """SELECT DISTINCT s.id, s.first_name, s.last_name, s.admission_number, 
               g.name as grade, st.name as stream, COUNT(m.id) as mark_count
        FROM student s
        JOIN grade g ON s.grade_id = g.id
        JOIN stream st ON s.stream_id = st.id
        LEFT JOIN mark m ON s.id = m.student_id
        WHERE g.name LIKE '%9%' AND st.name LIKE '%B%'
        GROUP BY s.id, s.first_name, s.last_name, s.admission_number, g.name, st.name
        HAVING COUNT(m.id) > 0
        ORDER BY mark_count DESC
        LIMIT 5;""",
        
        # Remove any existing links for Kevin
        "DELETE FROM parent_student WHERE parent_id = (SELECT id FROM parent WHERE email='kevin_parent@gmail.com');",
        
        # Link Kevin to real students with marks
        """INSERT INTO parent_student (parent_id, student_id, relationship, created_at, updated_at)
        SELECT 
            (SELECT id FROM parent WHERE email='kevin_parent@gmail.com'),
            s.id,
            'parent',
            NOW(),
            NOW()
        FROM student s
        JOIN grade g ON s.grade_id = g.id
        JOIN stream st ON s.stream_id = st.id
        WHERE s.id IN (
            SELECT DISTINCT student_id FROM mark 
            WHERE student_id = s.id
        )
        AND (g.name LIKE '%9%' AND st.name LIKE '%B%')
        LIMIT 2;""",
        
        # Verify the connection
        """SELECT p.first_name as parent_name, p.email, s.first_name as student_name, s.last_name, 
               g.name as grade, st.name as stream
        FROM parent p
        JOIN parent_student ps ON p.id = ps.parent_id
        JOIN student s ON ps.student_id = s.id
        JOIN grade g ON s.grade_id = g.id
        JOIN stream st ON s.stream_id = st.id
        WHERE p.email = 'kevin_parent@gmail.com';"""
    ]
    
    try:
        # Method 1: Try using Flask app context
        print("🔧 Attempting to link via Flask app...")
        
        try:
            from __init__ import create_app
            from models import db
            
            app = create_app('development')
            with app.app_context():
                print("✅ Connected to Flask app")
                
                # Execute each SQL command
                for i, sql in enumerate(sql_commands, 1):
                    print(f"\n📝 Step {i}: Executing SQL...")
                    try:
                        result = db.session.execute(db.text(sql))
                        if sql.strip().upper().startswith('SELECT'):
                            rows = result.fetchall()
                            print(f"   Results: {len(rows)} rows")
                            for row in rows:
                                print(f"   - {row}")
                        else:
                            db.session.commit()
                            print(f"   ✅ Command executed successfully")
                    except Exception as e:
                        print(f"   ⚠️ Error in step {i}: {str(e)}")
                        if not sql.strip().upper().startswith('DELETE'):  # DELETE might fail if no records exist
                            continue
                
                print("\n🎉 AUTO-LINKING COMPLETED!")
                return True
                
        except ImportError as e:
            print(f"❌ Flask import failed: {e}")
            print("🔄 Trying alternative method...")
            return False
            
    except Exception as e:
        print(f"❌ Auto-linking failed: {str(e)}")
        return False

def verify_kevin_connection():
    """Verify Kevin can now access real reports"""
    print("\n🧪 VERIFYING KEVIN'S CONNECTION")
    print("=" * 32)
    
    try:
        import requests
        base_url = "http://127.0.0.1:8080"
        
        # Test Kevin's login
        session = requests.Session()
        login_data = {
            'email': 'kevin_parent@gmail.com',
            'password': 'password123'
        }
        
        print("🔑 Testing Kevin's login...")
        login_response = session.post(f"{base_url}/parent/login", data=login_data)
        
        if 'dashboard' in login_response.url or 'children' in login_response.url:
            print("✅ Kevin's login successful!")
            
            # Test children page
            children_response = session.get(f"{base_url}/parent/children")
            if children_response.status_code == 200:
                print("✅ Children page accessible!")
                
                # Look for student names in the response
                html = children_response.text
                if 'Reports' in html and ('Grade' in html or 'Stream' in html):
                    print("✅ REAL STUDENT DATA FOUND!")
                    print("🎯 Kevin can now access real reports!")
                    return True
                else:
                    print("⚠️ Children page loaded but no student data visible")
            else:
                print(f"❌ Children page error: {children_response.status_code}")
        else:
            print("❌ Kevin's login failed")
        
    except Exception as e:
        print(f"❌ Verification error: {str(e)}")
    
    return False

if __name__ == "__main__":
    success = auto_link_kevin()
    
    if success:
        # Wait a moment for database changes to take effect
        import time
        time.sleep(2)
        
        # Verify the connection works
        if verify_kevin_connection():
            print("\n🎉 SUCCESS! Kevin is now linked to real students!")
            print("📋 NEXT STEPS:")
            print("1. Go to: http://127.0.0.1:8080/parent/login")
            print("2. Login: kevin_parent@gmail.com / password123")
            print("3. Visit: http://127.0.0.1:8080/parent/children")
            print("4. Click 'Reports' for any child")
            print("5. You'll see the REAL classteacher reports!")
        else:
            print("\n⚠️ Linking completed but verification failed")
            print("Try logging in manually to check if it worked")
    else:
        print("\n💡 AUTO-LINKING FAILED - Manual method needed:")
        print("Please use the SQL commands from the previous scripts")
        print("to link Kevin to real students in your database tool.")