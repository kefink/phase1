#!/usr/bin/env python3
"""
Download and analyze analytics page content
"""
import urllib.request

def analyze_analytics_page():
    analytics_url = 'http://127.0.0.1:8080/classteacher/analytics'
    
    try:
        print(f"🔍 Downloading analytics page...")
        response = urllib.request.urlopen(analytics_url)
        content = response.read().decode('utf-8')
        
        # Save content to file for analysis
        with open('analytics_page_content.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Content saved to analytics_page_content.html")
        
        # Look for key elements
        if 'Quick Insights' in content:
            print("✅ Quick Insights section found")
        
        if 'Students Analyzed' in content:
            print("✅ Students Analyzed section found")
            
        if 'subjects_analyzed' in content:
            print("✅ subjects_analyzed variable found")
            
        # Look for our test values
        if '25' in content:
            print("✅ Value 25 found (our test students_analyzed)")
            
        if '85.5' in content:
            print("✅ Value 85.5 found (our test best_subject_average)")
            
        if '78.2' in content:
            print("✅ Value 78.2 found (our test top_student_average)")
            
        # Look for zero values that might indicate the problem
        zero_count = content.count('>0<')
        print(f"🔍 Found {zero_count} zero values in displayed elements")
        
        # Look for loading indicators
        if 'Loading...' in content:
            print("⚠️ Loading indicators found - might indicate async loading")
        
        print(f"\n📄 Content length: {len(content)} characters")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    analyze_analytics_page()
