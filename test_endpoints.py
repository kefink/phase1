#!/usr/bin/env python3
"""
Test the teacher endpoints directly.
"""

import requests
import json

def test_endpoints():
    """Test the teacher endpoints."""
    base_url = "http://127.0.0.1:5001"

    print("=== TESTING TEACHER ENDPOINTS ===\n")

    # Test 1: Login and get session
    print("1. Testing login...")
    session = requests.Session()

    # Get login page first to get CSRF token
    login_page = session.get(f"{base_url}/teacher_login")
    print(f"Login page status: {login_page.status_code}")

    # Login
    login_data = {
        'username': 'teacher1',
        'password': 'teacher123'
    }

    login_response = session.post(f"{base_url}/teacher_login", data=login_data)
    print(f"Login response status: {login_response.status_code}")

    if login_response.status_code == 200 and "dashboard" in login_response.url.lower():
        print("✅ Login successful!")
    else:
        print("❌ Login failed!")
        return

    # Test 2: Get subject info
    print("\n2. Testing get_subject_info endpoint...")

    subjects_to_test = ["ENGLISH", "MATHEMATICS", "FRENCH"]

    for subject in subjects_to_test:
        try:
            response = session.get(f"{base_url}/teacher/get_subject_info/{subject}")
            print(f"Subject: {subject} - Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    subject_info = data.get('subject', {})
                    print(f"  ✅ Name: {subject_info.get('name')}")
                    print(f"  ✅ Education Level: {subject_info.get('education_level')}")
                    print(f"  ✅ Is Composite: {subject_info.get('is_composite')}")
                    if subject_info.get('is_composite'):
                        components = subject_info.get('components', [])
                        print(f"  ✅ Components: {len(components)}")
                        for comp in components:
                            print(f"    - {comp.get('name')}: {comp.get('weight')*100:.0f}% (Max: {comp.get('max_raw_mark')})")
                else:
                    print(f"  ❌ Error: {data.get('message')}")
            else:
                print(f"  ❌ HTTP Error: {response.status_code}")
                print(f"  Response: {response.text[:200]}")

        except Exception as e:
            print(f"  ❌ Exception: {e}")

    # Test 3: Get streams
    print("\n3. Testing get_streams endpoint...")

    grade_ids_to_test = [1, 6, 9]  # Grade 8, Grade 4, Grade 7

    for grade_id in grade_ids_to_test:
        try:
            response = session.get(f"{base_url}/teacher/get_streams/{grade_id}")
            print(f"Grade ID: {grade_id} - Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                streams = data.get('streams', [])
                print(f"  ✅ Streams found: {len(streams)}")
                for stream in streams:
                    print(f"    - Stream {stream.get('name')} (ID: {stream.get('id')})")
            else:
                print(f"  ❌ HTTP Error: {response.status_code}")

        except Exception as e:
            print(f"  ❌ Exception: {e}")

if __name__ == "__main__":
    test_endpoints()
