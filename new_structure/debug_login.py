#!/usr/bin/env python3
"""
Debug login issues by testing authentication directly.
"""
import sqlite3
import os
import sys

def test_direct_authentication():
    """Test authentication directly without Flask context."""
    print("🔐 DIRECT AUTHENTICATION TEST")
    print("=" * 50)
    
    # Check database directly
    db_path = 'kirima_primary.db'
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test the exact query that authenticate_teacher uses
        test_credentials = [
            ('classteacher1', 'password123', 'classteacher'),
            ('headteacher', 'admin123', 'headteacher'),
            ('teacher1', 'teacher123', 'teacher')
        ]
        
        for username, password, role in test_credentials:
            print(f"\n🧪 Testing: {username} / {password} / {role}")
            
            # This is exactly what authenticate_teacher does
            cursor.execute(
                "SELECT id, username, password, role FROM teacher WHERE username = ? AND password = ? AND role = ?",
                (username, password, role)
            )
            result = cursor.fetchone()
            
            if result:
                print(f"   ✅ SUCCESS: Found teacher ID {result[0]}")
                print(f"      Username: {result[1]}")
                print(f"      Password: {result[2]}")
                print(f"      Role: {result[3]}")
            else:
                print(f"   ❌ FAILED: No match found")
                
                # Check if user exists with different password/role
                cursor.execute("SELECT id, username, password, role FROM teacher WHERE username = ?", (username,))
                user_check = cursor.fetchone()
                
                if user_check:
                    print(f"      User exists but with different credentials:")
                    print(f"      Stored password: '{user_check[2]}'")
                    print(f"      Stored role: '{user_check[3]}'")
                    print(f"      Expected password: '{password}'")
                    print(f"      Expected role: '{role}'")
                else:
                    print(f"      User '{username}' does not exist at all")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_flask_authentication():
    """Test authentication using Flask context."""
    print("\n🌐 FLASK AUTHENTICATION TEST")
    print("=" * 50)
    
    try:
        # Add current directory to path
        sys.path.insert(0, '.')
        
        # Import Flask app and create context
        from __init__ import create_app
        from services.auth_service import authenticate_teacher
        
        app = create_app()
        
        with app.app_context():
            print("✅ Flask app context created")
            
            # Test authentication
            test_credentials = [
                ('classteacher1', 'password123', 'classteacher'),
                ('headteacher', 'admin123', 'headteacher'),
                ('teacher1', 'teacher123', 'teacher')
            ]
            
            for username, password, role in test_credentials:
                print(f"\n🧪 Testing Flask auth: {username} / {password} / {role}")
                
                teacher = authenticate_teacher(username, password, role)
                
                if teacher:
                    print(f"   ✅ SUCCESS: Authenticated!")
                    print(f"      Teacher ID: {teacher.id}")
                    print(f"      Username: {teacher.username}")
                    print(f"      Role: {teacher.role}")
                    print(f"      Stream ID: {teacher.stream_id}")
                else:
                    print(f"   ❌ FAILED: Authentication returned None")
                    
                    # Check if user exists at all
                    from models.user import Teacher
                    user = Teacher.query.filter_by(username=username).first()
                    if user:
                        print(f"      User exists: {user.username} / {user.password} / {user.role}")
                        if user.password != password:
                            print(f"      Password mismatch: expected '{password}', got '{user.password}'")
                        if user.role != role:
                            print(f"      Role mismatch: expected '{role}', got '{user.role}'")
                    else:
                        print(f"      User '{username}' not found in database")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask authentication error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_csrf_form_submission():
    """Test form submission with CSRF token."""
    print("\n📝 CSRF FORM SUBMISSION TEST")
    print("=" * 50)
    
    try:
        import requests
        import re

        session = requests.Session()

        # Get login page
        login_url = "http://localhost:5000/classteacher_login"
        response = session.get(login_url)

        if response.status_code != 200:
            print(f"❌ Cannot access login page: {response.status_code}")
            return False

        print(f"✅ Login page accessible: {response.status_code}")

        # Extract CSRF token using regex (simpler than BeautifulSoup)
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)

        if not csrf_match:
            print("❌ No CSRF token found in form")
            return False

        csrf_token = csrf_match.group(1)
        print(f"✅ CSRF token extracted: {csrf_token[:20]}...")
        
        # Submit login form
        login_data = {
            'username': 'classteacher1',
            'password': 'password123',
            'csrf_token': csrf_token
        }
        
        print("📤 Submitting login form...")
        post_response = session.post(login_url, data=login_data, allow_redirects=False)
        
        print(f"📥 Response status: {post_response.status_code}")
        
        if post_response.status_code == 302:
            redirect_url = post_response.headers.get('Location', '')
            print(f"✅ Redirected to: {redirect_url}")
            
            if 'classteacher' in redirect_url:
                print("✅ Login successful - redirected to classteacher dashboard")
                return True
            else:
                print("❌ Unexpected redirect location")
                return False
        elif post_response.status_code == 200:
            # Check for error message
            if 'Invalid credentials' in post_response.text:
                print("❌ Login failed - Invalid credentials")
            elif 'error' in post_response.text.lower():
                print("❌ Login failed - Error found in response")
                # Extract error message
                import re
                error_match = re.search(r'<div class="error-message"[^>]*>.*?<i[^>]*></i>\s*([^<]+)', post_response.text, re.DOTALL)
                if error_match:
                    error_msg = error_match.group(1).strip()
                    print(f"   Error message: {error_msg}")
            else:
                print("❌ Login failed - stayed on login page")
                print(f"   Response length: {len(post_response.text)} characters")
                # Check if we're still on login page
                if 'login-container' in post_response.text:
                    print("   Still on login page")
                if 'csrf_token' in post_response.text:
                    print("   CSRF token present in response")
            return False
        else:
            print(f"❌ Unexpected response status: {post_response.status_code}")
            print(f"Response text: {post_response.text[:200]}...")
            return False
        
    except Exception as e:
        print(f"❌ CSRF test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all login debug tests."""
    print("🐛 LOGIN DEBUG TOOL")
    print("=" * 60)
    
    # Test 1: Direct database authentication
    db_auth_ok = test_direct_authentication()
    
    # Test 2: Flask authentication
    flask_auth_ok = test_flask_authentication()
    
    # Test 3: CSRF form submission
    csrf_ok = test_csrf_form_submission()
    
    # Summary
    print("\n📋 DEBUG SUMMARY")
    print("=" * 50)
    print(f"Database Auth: {'✅ OK' if db_auth_ok else '❌ FAILED'}")
    print(f"Flask Auth: {'✅ OK' if flask_auth_ok else '❌ FAILED'}")
    print(f"CSRF Form: {'✅ OK' if csrf_ok else '❌ FAILED'}")
    
    if db_auth_ok and flask_auth_ok and csrf_ok:
        print("\n🎯 ALL TESTS PASSED!")
        print("Login should work. Try the web interface now.")
    else:
        print("\n❌ ISSUES FOUND:")
        if not db_auth_ok:
            print("- Database authentication failed")
        if not flask_auth_ok:
            print("- Flask authentication failed")
        if not csrf_ok:
            print("- CSRF form submission failed")

if __name__ == '__main__':
    main()
