#!/usr/bin/env python3
"""
Debug Kevin's login session and route access
"""
import requests
import sys

def test_kevin_login_and_routes():
    base_url = "http://127.0.0.1:8080"
    
    print("🔍 DEBUGGING KEVIN'S PARENT ACCESS")
    print("=" * 50)
    
    # Create a session
    session = requests.Session()
    
    print("1️⃣ Testing parent login page access...")
    try:
        login_page = session.get(f"{base_url}/parent/login")
        print(f"   Login page status: {login_page.status_code}")
        if login_page.status_code != 200:
            print(f"   ❌ Can't access login page!")
            return
    except Exception as e:
        print(f"   ❌ Error accessing login page: {e}")
        return
    
    print("2️⃣ Attempting Kevin's parent login...")
    login_data = {
        'email': 'kevinmugo359@gmail.com',
        'password': 'e3fKkXhi'
    }
    
    try:
        login_response = session.post(f"{base_url}/parent/login", data=login_data, allow_redirects=False)
        print(f"   Login response status: {login_response.status_code}")
        
        if login_response.status_code == 302:  # Redirect after successful login
            print("   ✅ Login successful (redirect received)")
            redirect_location = login_response.headers.get('Location', 'No location')
            print(f"   Redirected to: {redirect_location}")
        elif login_response.status_code == 200:
            if 'Invalid email or password' in login_response.text:
                print("   ❌ Invalid credentials!")
                return
            else:
                print("   ⚠️ Login returned 200 - checking content...")
        else:
            print(f"   ❌ Login failed with status {login_response.status_code}")
            return
            
    except Exception as e:
        print(f"   ❌ Error during login: {e}")
        return
    
    print("3️⃣ Testing parent dashboard access...")
    try:
        dashboard_response = session.get(f"{base_url}/parent/dashboard")
        print(f"   Dashboard status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            print("   ✅ Dashboard accessible")
        else:
            print("   ❌ Dashboard not accessible - login may have failed")
            
    except Exception as e:
        print(f"   ❌ Error accessing dashboard: {e}")
        return
    
    print("4️⃣ Testing children page access...")
    try:
        children_response = session.get(f"{base_url}/parent/children")
        print(f"   Children page status: {children_response.status_code}")
        
        if children_response.status_code == 200:
            print("   ✅ Children page accessible")
        else:
            print("   ❌ Children page not accessible")
            return
            
    except Exception as e:
        print(f"   ❌ Error accessing children page: {e}")
        return
    
    print("5️⃣ Testing child reports route (the problematic one)...")
    try:
        # Try child ID 28 as mentioned in the logs
        reports_response = session.get(f"{base_url}/parent/child/28/reports")
        print(f"   Child 28 reports status: {reports_response.status_code}")
        
        if reports_response.status_code == 200:
            print("   ✅ Child reports accessible!")
        elif reports_response.status_code == 403:
            print("   ❌ 403 Forbidden - this is our problem!")
            print("   Response text preview:")
            print("   " + reports_response.text[:200] + "...")
        elif reports_response.status_code == 404:
            print("   ❌ 404 Not Found - route might not exist")
        else:
            print(f"   ❌ Unexpected status: {reports_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error accessing child reports: {e}")
    
    print("\n🔧 DEBUGGING COMPLETE")
    print("Check server logs for more details!")

if __name__ == "__main__":
    test_kevin_login_and_routes()