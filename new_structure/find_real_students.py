#!/usr/bin/env python3
"""
Find what real students exist in the system with actual report data
"""
import requests
import re

def find_real_students():
    """Find students with real report data by accessing classteacher routes"""
    base_url = "http://127.0.0.1:8080"
    
    try:
        # Access the class teacher reports (might need login)
        session = requests.Session()
        
        # Try to access without login first
        reports_response = session.get(f"{base_url}/classteacher/view_all_reports")
        
        if reports_response.status_code == 403:
            print("🔒 Need to login as class teacher first")
            
            # Try common teacher credentials
            teacher_logins = [
                {'username': 'kevin', 'password': 'kev123'},
                {'username': 'teacher', 'password': 'teacher123'},
                {'username': 'classteacher', 'password': 'password'},
            ]
            
            login_success = False
            for login_data in teacher_logins:
                login_response = session.post(f"{base_url}/login", data=login_data)
                if login_response.status_code == 200 and 'dashboard' in login_response.url:
                    print(f"✅ Logged in as {login_data['username']}")
                    login_success = True
                    break
            
            if not login_success:
                print("❌ Could not login as teacher")
                return []
            
            # Try reports page again
            reports_response = session.get(f"{base_url}/classteacher/view_all_reports")
        
        if reports_response.status_code != 200:
            print(f"❌ Could not access reports page: {reports_response.status_code}")
            return []
        
        print("✅ Accessed classteacher reports page")
        
        # Parse the HTML to find real grade/stream/term/assessment combinations
        html = reports_response.text
        
        # Look for grade/stream combinations in URLs or text
        grade_stream_pattern = r'Grade\s+(\d+)[^"]*Stream\s+([A-Z])'
        grade_streams = re.findall(grade_stream_pattern, html, re.IGNORECASE)
        
        # Look for terms
        term_pattern = r'(Term\s+\d+|term\s+\d+)'
        terms = re.findall(term_pattern, html, re.IGNORECASE)
        
        # Look for assessment types
        assessment_pattern = r'(Mid\s+Term|End\s+Term|midterm\s*\d*|end\s*term\s*\d*)'
        assessments = re.findall(assessment_pattern, html, re.IGNORECASE)
        
        print(f"🎓 Found Grade/Stream combinations: {set(grade_streams)}")
        print(f"📅 Found Terms: {set(terms)}")
        print(f"📝 Found Assessments: {set(assessments)}")
        
        # Try to access a specific student report to see what students exist
        if grade_streams and terms and assessments:
            grade, stream = grade_streams[0] if grade_streams else ('9', 'B')
            term = terms[0] if terms else 'term 3'
            assessment = assessments[0] if assessments else 'midterm 3 2025'
            
            # Try the specific URL format you mentioned
            specific_url = f"{base_url}/classteacher/view_student_reports/Grade%20{grade}/Stream%20{stream}/{term}/{assessment}"
            print(f"🔗 Trying specific URL: {specific_url}")
            
            specific_response = session.get(specific_url)
            if specific_response.status_code == 200:
                print("✅ Accessed specific student reports")
                
                # Look for student names in the response
                student_pattern = r'<[^>]*>([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)</[^>]*>'
                students = re.findall(student_pattern, specific_response.text)
                
                # Filter out common non-student words
                filtered_students = []
                exclude_words = {'Grade', 'Stream', 'Term', 'Report', 'Student', 'Class', 'Teacher', 'School', 'Login', 'Dashboard', 'Average', 'Total', 'Subject'}
                
                for student in students:
                    words = student.split()
                    if len(words) >= 2 and not any(word in exclude_words for word in words):
                        filtered_students.append(student)
                
                print(f"👥 Found potential students: {set(filtered_students[:10])}")  # Show first 10
                
                return {
                    'grade': f"Grade {grade}",
                    'stream': f"Stream {stream}",
                    'term': term,
                    'assessment': assessment,
                    'students': list(set(filtered_students))
                }
        
        return []
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

if __name__ == "__main__":
    print("🔍 FINDING REAL STUDENTS WITH REPORT DATA")
    print("=" * 45)
    real_data = find_real_students()
    
    if real_data:
        print(f"\n✅ Found real report data!")
        print(f"Grade/Stream: {real_data['grade']} {real_data['stream']}")
        print(f"Term/Assessment: {real_data['term']} {real_data['assessment']}")
        print(f"Number of students: {len(real_data['students'])}")
        
        if real_data['students']:
            print(f"Sample students: {real_data['students'][:5]}")
    else:
        print("\n❌ Could not find real report data")