#!/usr/bin/env python3
"""
Register Kevin's parent account via HTTP requests
"""
import requests
import json

def register_kevin_parent():
    """Register Kevin's parent account"""
    base_url = "http://127.0.0.1:8080"
    
    # Registration data
    registration_data = {
        'first_name': 'Kevin',
        'last_name': 'Knnyua',
        'email': 'kevin_parent@gmail.com',
        'phone': '+254123456789',
        'password': 'password123',
        'confirm_password': 'password123'
    }
    
    try:
        print("📝 Registering Kevin's parent account...")
        
        # Get the registration page first (for CSRF token if needed)
        register_page = requests.get(f"{base_url}/parent/register")
        print(f"Registration page status: {register_page.status_code}")
        
        # Submit registration
        session = requests.Session()
        response = session.post(f"{base_url}/parent/register", data=registration_data)
        
        print(f"Registration response: {response.status_code}")
        print(f"Response URL: {response.url}")
        
        if response.status_code == 200:
            if 'login' in response.url:
                print("✅ Registration successful! Redirected to login page.")
                
                # Now try to login
                login_data = {
                    'email': 'kevin_parent@gmail.com',
                    'password': 'password123'
                }
                
                login_response = session.post(f"{base_url}/parent/login", data=login_data)
                print(f"Login response: {login_response.status_code}")
                
                if 'dashboard' in login_response.url or 'children' in login_response.url:
                    print("✅ Login successful!")
                    
                    # Try to access children page
                    children_response = session.get(f"{base_url}/parent/children")
                    print(f"Children page response: {children_response.status_code}")
                    
                    return True
                else:
                    print("❌ Login failed after registration")
            else:
                print("⚠️ Registration completed but not redirected to login")
        else:
            print("❌ Registration failed")
            print(f"Response text: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("🚀 Registering Kevin's Parent Account")
    print("=" * 40)
    success = register_kevin_parent()
    
    if success:
        print("\n🎉 SUCCESS! Kevin's parent account is ready!")
        print("🔑 Login at: http://127.0.0.1:8080/parent/login")
        print("📧 Email: kevin_parent@gmail.com")
        print("🔒 Password: password123")
    else:
        print("\n💥 Registration failed. You may need to register manually.")