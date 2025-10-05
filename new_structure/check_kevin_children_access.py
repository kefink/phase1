#!/usr/bin/env python3
"""
Check if Kevin's children exist in the real report data and link them properly
"""
import requests
import json

def check_kevin_children_reports():
    """Check what reports exist for Kevin's children"""
    base_url = "http://127.0.0.1:8080"
    
    try:
        # Login as Kevin's parent
        session = requests.Session()
        login_data = {
            'email': 'kevin_parent@gmail.com',
            'password': 'password123'
        }
        
        login_response = session.post(f"{base_url}/parent/login", data=login_data)
        if 'dashboard' not in login_response.url and 'children' not in login_response.url:
            print("❌ Could not login as Kevin's parent")
            return False
        
        print("✅ Logged in as Kevin's parent")
        
        # Access the children page
        children_response = session.get(f"{base_url}/parent/children")
        if children_response.status_code != 200:
            print("❌ Could not access children page")
            return False
        
        print("✅ Accessed children page")
        
        # Check what the children page shows
        children_html = children_response.text
        
        # Look for child names in the HTML
        if 'Sarah' in children_html and 'Michael' in children_html:
            print("✅ Found Kevin's children (Sarah and Michael) on the page")
        else:
            print("⚠️ Kevin's children not visible on the page")
            print("Let me check what children are shown...")
            
            # Simple extraction of student names from HTML
            import re
            name_patterns = re.findall(r'<h5[^>]*>([^<]+)</h5>', children_html)
            print(f"Found names: {name_patterns}")
        
        # Check the class teacher reports to see what real students exist
        print("\n🔍 Checking what real students exist in the system...")
        reports_response = session.get(f"{base_url}/classteacher/view_all_reports")
        
        if reports_response.status_code == 200:
            print("✅ Accessed class teacher reports")
            
            # Look for specific patterns in the reports HTML
            reports_html = reports_response.text
            
            # Extract grade/stream combinations
            import re
            grade_stream_patterns = re.findall(r'Grade \d+[^"]*Stream [A-Z][^"]*', reports_html)
            print(f"Available grade/stream combinations: {set(grade_stream_patterns)}")
            
            # Look for specific terms and assessments
            term_patterns = re.findall(r'(Term \d+|term \d+)', reports_html, re.IGNORECASE)
            assessment_patterns = re.findall(r'(Mid Term|End Term|midterm|end term)', reports_html, re.IGNORECASE)
            
            print(f"Available terms: {set(term_patterns)}")
            print(f"Available assessments: {set(assessment_patterns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 CHECKING KEVIN'S CHILDREN REPORT ACCESS")
    print("=" * 50)
    check_kevin_children_reports()