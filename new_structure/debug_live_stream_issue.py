#!/usr/bin/env python3
"""
Debug the actual live stream loading issue
"""

import requests
import json

def test_with_session():
    """Test with a real browser session"""
    print("🔍 DEBUGGING LIVE STREAM ISSUE")
    print("=" * 50)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Test the exact endpoint that should be called
    base_url = "http://localhost:5000"
    grade_id = 21  # Grade 9
    
    # Test the universal API endpoint
    endpoint = f"{base_url}/universal/api/streams/{grade_id}"
    
    print(f"📡 Testing endpoint: {endpoint}")
    
    try:
        response = session.get(endpoint)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ SUCCESS! Data: {json.dumps(data, indent=2)}")
            except:
                print(f"Response text: {response.text}")
        elif response.status_code == 403:
            print("❌ 403 Forbidden - Authentication required")
            print("This means the endpoint exists but needs login")
        elif response.status_code == 404:
            print("❌ 404 Not Found - Endpoint doesn't exist")
            print("This means the URL is wrong or blueprint not registered")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def check_blueprint_routes():
    """Check if the universal blueprint routes are properly registered"""
    print("\n🔗 CHECKING BLUEPRINT ROUTES")
    print("=" * 40)
    
    try:
        # Import the Flask app to check registered routes
        import sys
        sys.path.append('.')
        
        from app import create_app
        app = create_app()
        
        print("📋 Registered routes containing 'universal' or 'streams':")
        with app.app_context():
            for rule in app.url_map.iter_rules():
                if 'universal' in rule.rule or 'streams' in rule.rule:
                    print(f"   {rule.rule} -> {rule.endpoint}")
                    
    except Exception as e:
        print(f"❌ Error checking routes: {e}")

if __name__ == "__main__":
    test_with_session()
    check_blueprint_routes()
    
    print("\n" + "=" * 50)
    print("🚨 IMMEDIATE ACTION NEEDED:")
    print("1. Login to http://localhost:5000/admin_login")
    print("2. Open browser dev tools (F12)")
    print("3. Go to Universal Access → Manage Students")
    print("4. Select Grade 9 and watch Network tab")
    print("5. Look for the exact URL being called")
    print("6. Check Console tab for JavaScript errors")
