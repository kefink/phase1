#!/usr/bin/env python3
"""
Update Kevin's children to be in existing grades/streams with real data
"""
import requests
import json

def update_kevin_children():
    """Login as parent and check what we need to update"""
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
        
        # Check children page
        children_response = session.get(f"{base_url}/parent/children")
        children_html = children_response.text
        
        # Check for any child data
        if 'Sarah' in children_html or 'Michael' in children_html:
            print("✅ Found Kevin's children in the system")
        else:
            print("❌ Kevin's children not found or not visible")
        
        # Try to access a child's reports page to see what happens
        # Let's look at the HTML source to understand the structure
        print("\n📝 Analyzing children page structure...")
        
        # Look for child IDs or report links
        import re
        
        # Look for child IDs in URLs
        child_id_pattern = r'child[/_](\d+)'
        child_ids = re.findall(child_id_pattern, children_html)
        
        # Look for report links
        report_link_pattern = r'href="[^"]*child[^"]*reports[^"]*"'
        report_links = re.findall(report_link_pattern, children_html)
        
        print(f"Found child IDs: {child_ids}")
        print(f"Found report links: {report_links}")
        
        # Try accessing a child reports page if we found IDs
        if child_ids:
            child_id = child_ids[0]
            reports_url = f"{base_url}/parent/child/{child_id}/reports"
            print(f"\n🔍 Checking reports for child ID {child_id}: {reports_url}")
            
            reports_response = session.get(reports_url)
            if reports_response.status_code == 200:
                reports_html = reports_response.text
                print("✅ Accessed child reports page")
                
                # Look for report data in the HTML
                if 'No Reports Available' in reports_html or 'No marks' in reports_html:
                    print("⚠️ Child has no report data available")
                elif 'Error' in reports_html:
                    print("❌ Error loading child reports")
                else:
                    print("✅ Child appears to have report data!")
                    
                    # Look for specific report information
                    report_pattern = r'Grade\s+\d+|Stream\s+[A-Z]|Term\s+\d+'
                    report_info = re.findall(report_pattern, reports_html)
                    print(f"Report info found: {report_info}")
            else:
                print(f"❌ Could not access child reports: {reports_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 CHECKING KEVIN'S CHILDREN STATUS")
    print("=" * 40)
    update_kevin_children()