#!/usr/bin/env python3
"""
Test the teacher endpoints directly with proper session.
"""

import requests
import json

def test_teacher_endpoints():
    """Test the teacher endpoints with proper authentication."""
    base_url = "http://127.0.0.1:5001"

    print("=== TESTING TEACHER ENDPOINTS DIRECTLY ===\n")

    # Create session
    session = requests.Session()

    # Step 1: Get login page and extract CSRF token
    print("1. Getting login page...")
    login_page = session.get(f"{base_url}/teacher_login")
    print(f"Login page status: {login_page.status_code}")

    if login_page.status_code != 200:
        print("❌ Cannot access login page")
        return

    # Skip CSRF token for now - just test the endpoints
    csrf_token = None
    print("⚠️ Skipping CSRF token extraction")

    # Step 2: Login
    print("\n2. Logging in...")
    login_data = {
        'username': 'teacher1',
        'password': 'teacher123'
    }
    if csrf_token:
        login_data['csrf_token'] = csrf_token

    login_response = session.post(f"{base_url}/teacher_login", data=login_data, allow_redirects=False)
    print(f"Login response status: {login_response.status_code}")

    if login_response.status_code == 302:
        print("✅ Login successful (redirected)")
        # Follow redirect
        dashboard_response = session.get(f"{base_url}/teacher/")
        print(f"Dashboard status: {dashboard_response.status_code}")
    else:
        print("❌ Login failed")
        print(f"Response: {login_response.text[:200]}")
        return

    # Step 3: Test get_subject_info endpoint
    print("\n3. Testing get_subject_info endpoint...")

    subjects_to_test = ["ENGLISH", "MATHEMATICS", "FRENCH"]

    for subject in subjects_to_test:
        try:
            url = f"{base_url}/teacher/get_subject_info/{subject}"
            print(f"\nTesting: {url}")
            response = session.get(url)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ JSON Response: {json.dumps(data, indent=2)}")
                except:
                    print(f"❌ Not JSON: {response.text[:200]}")
            else:
                print(f"❌ Error response: {response.text[:200]}")

        except Exception as e:
            print(f"❌ Exception: {e}")

    # Step 4: Test get_streams endpoint
    print("\n4. Testing get_streams endpoint...")

    grade_ids = [1, 6, 9]  # Test different grade IDs

    for grade_id in grade_ids:
        try:
            url = f"{base_url}/teacher/get_streams/{grade_id}"
            print(f"\nTesting: {url}")
            response = session.get(url)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ JSON Response: {json.dumps(data, indent=2)}")
                except:
                    print(f"❌ Not JSON: {response.text[:200]}")
            else:
                print(f"❌ Error response: {response.text[:200]}")

        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_teacher_endpoints()
