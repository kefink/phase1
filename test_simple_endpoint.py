#!/usr/bin/env python3
"""
Simple test to check if endpoints are accessible.
"""

import urllib.request
import json

def test_simple():
    """Test endpoints without authentication."""
    base_url = "http://127.0.0.1:5001"
    
    print("=== SIMPLE ENDPOINT TEST ===\n")
    
    # Test 1: Check if server is running
    try:
        response = urllib.request.urlopen(f"{base_url}/")
        print(f"✅ Server is running - Status: {response.status}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Test 2: Check teacher login page
    try:
        response = urllib.request.urlopen(f"{base_url}/teacher_login")
        print(f"✅ Teacher login page - Status: {response.status}")
    except Exception as e:
        print(f"❌ Teacher login page error: {e}")
    
    # Test 3: Check if teacher dashboard redirects (should redirect to login)
    try:
        response = urllib.request.urlopen(f"{base_url}/teacher/")
        print(f"✅ Teacher dashboard accessible - Status: {response.status}")
    except urllib.error.HTTPError as e:
        if e.code == 302:
            print(f"✅ Teacher dashboard redirects to login - Status: {e.code}")
        else:
            print(f"❌ Teacher dashboard error: {e.code}")
    except Exception as e:
        print(f"❌ Teacher dashboard error: {e}")

if __name__ == "__main__":
    test_simple()
