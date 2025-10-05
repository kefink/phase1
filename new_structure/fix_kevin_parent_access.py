#!/usr/bin/env python3
"""
Fix Kevin's parent access by clearing role conflicts and ensuring proper parent session
"""
import requests
import json

def fix_kevin_parent_access():
    """Fix Kevin's parent access issues"""
    
    print("🔧 FIXING KEVIN'S PARENT ACCESS")
    print("=" * 35)
    
    base_url = "http://127.0.0.1:8080"
    
    # Step 1: Clear any existing sessions that might conflict
    print("🧹 Step 1: Clear existing sessions...")
    
    session = requests.Session()
    
    # Try to logout from any existing role
    try:
        session.get(f"{base_url}/logout")
        print("✅ Cleared existing sessions")
    except:
        pass
    
    # Step 2: Login as Kevin's parent with correct credentials
    print("🔑 Step 2: Login as Kevin's parent...")
    
    parent_login_data = {
        'email': 'kevinmugo359@gmail.com',
        'password': 'e3fKkXhi'
    }
    
    login_response = session.post(f"{base_url}/parent/login", data=parent_login_data)
    
    if login_response.status_code == 200:
        if 'dashboard' in login_response.url or 'children' in login_response.url:
            print("✅ Successfully logged in as Kevin's parent!")
        else:
            print("⚠️ Login completed but unexpected redirect")
            print(f"   Redirected to: {login_response.url}")
    else:
        print(f"❌ Login failed with status: {login_response.status_code}")
        print("💡 Check if the credentials are correct:")
        print("   Email: kevinmugo359@gmail.com")
        print("   Password: e3fKkXhi")
        return False
    
    # Step 3: Test access to children page
    print("👶 Step 3: Testing children page access...")
    
    children_response = session.get(f"{base_url}/parent/children")
    if children_response.status_code == 200:
        print("✅ Children page accessible!")
        
        # Check if children are visible
        children_html = children_response.text
        if 'Reports' in children_html:
            print("✅ Found report links for children")
        else:
            print("⚠️ No report links found")
            print("   This might mean no children are linked to this parent")
    else:
        print(f"❌ Children page error: {children_response.status_code}")
        return False
    
    # Step 4: Test specific child report access
    print("📊 Step 4: Testing child report access...")
    
    child_report_url = f"{base_url}/parent/child/25/reports"
    report_response = session.get(child_report_url)
    
    if report_response.status_code == 200:
        print("✅ Child reports page accessible!")
        
        # Check for report data
        report_html = report_response.text
        if 'No Reports Available' in report_html:
            print("⚠️ No reports available for this child")
        elif 'Error' in report_html:
            print("⚠️ Error loading reports")
        else:
            print("✅ Reports data found!")
            
    elif report_response.status_code == 403:
        print("❌ Still getting 403 Forbidden error")
        print("💡 This suggests a role/permission issue")
        return False
    else:
        print(f"❌ Report access failed: {report_response.status_code}")
        return False
    
    print("✅ All access tests passed!")
    return True

def check_parent_student_link():
    """Check if Kevin's parent account is properly linked to child ID 25"""
    
    print("\n🔗 CHECKING PARENT-STUDENT LINKAGE")
    print("=" * 35)
    
    print("📋 Manual verification needed:")
    print("Run this SQL query to check the linkage:")
    print()
    
    sql_check = """
-- Check if Kevin's parent is linked to student ID 25
SELECT p.id as parent_id, p.first_name, p.last_name, p.email,
       s.id as student_id, s.first_name as student_name, s.last_name as student_lastname,
       ps.relationship
FROM parent p
JOIN parent_student ps ON p.id = ps.parent_id
JOIN student s ON ps.student_id = s.id
WHERE p.email = 'kevinmugo359@gmail.com' AND s.id = 25;
"""
    
    print(sql_check)
    
    print("💡 If no results, run this to create the link:")
    
    sql_fix = """
-- Link Kevin's parent to student ID 25
INSERT INTO parent_student (parent_id, student_id, relationship, created_at, updated_at)
SELECT p.id, 25, 'parent', NOW(), NOW()
FROM parent p
WHERE p.email = 'kevinmugo359@gmail.com'
AND NOT EXISTS (
    SELECT 1 FROM parent_student ps 
    WHERE ps.parent_id = p.id AND ps.student_id = 25
);
"""
    
    print(sql_fix)

def diagnose_403_error():
    """Diagnose the 403 Forbidden error"""
    
    print("\n🔍 DIAGNOSING 403 ERROR")
    print("=" * 25)
    
    print("The error 'headteacher cannot access child' suggests:")
    print("1. Kevin might have a teacher role session active")
    print("2. There's a role conflict in the session")
    print("3. The parent_required decorator isn't working properly")
    
    print("\n🔧 SOLUTIONS:")
    print("1. **Clear browser cookies/session completely**")
    print("2. **Use incognito/private browser window**") 
    print("3. **Login directly as parent at: http://127.0.0.1:8080/parent/login**")
    print("4. **Verify Kevin doesn't have teacher account with same email**")
    
    print("\n📋 SQL to check for role conflicts:")
    
    role_check = """
-- Check if Kevin has accounts in multiple role tables
SELECT 'parent' as role, id, first_name, last_name, email FROM parent WHERE email = 'kevinmugo359@gmail.com'
UNION ALL
SELECT 'teacher' as role, id, first_name, last_name, email FROM teacher WHERE email = 'kevinmugo359@gmail.com'
UNION ALL  
SELECT 'student' as role, id, first_name, last_name, email FROM student WHERE email = 'kevinmugo359@gmail.com';
"""
    
    print(role_check)

if __name__ == "__main__":
    success = fix_kevin_parent_access()
    
    if not success:
        check_parent_student_link()
        diagnose_403_error()
        
        print(f"\n🎯 QUICK FIX STEPS:")
        print(f"=" * 20)
        print(f"1. Open incognito/private browser window")
        print(f"2. Go to: http://127.0.0.1:8080/parent/login") 
        print(f"3. Login: kevinmugo359@gmail.com / e3fKkXhi")
        print(f"4. Visit: http://127.0.0.1:8080/parent/children")
        print(f"5. Click Reports for child")
        
    print(f"\n🔧 If still getting 403:")
    print(f"The parent portal code needs role session fix!")
    print(f"I can update the code to properly handle parent sessions.")