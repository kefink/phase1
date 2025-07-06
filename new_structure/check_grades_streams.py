#!/usr/bin/env python3
"""
Simple script to check grades and streams in the database
"""

import pymysql
import json

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '@2494/lK',
    'database': 'hillview_demo001',
    'charset': 'utf8mb4'
}

def check_grades_and_streams():
    """Check grades and streams in the database"""
    try:
        print("🔍 Connecting to database...")
        # Connect to database
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        print("✅ Database connection successful!")

        print("\n🔍 Checking Grades and Streams...")
        print("=" * 50)
        
        # Get all grades
        cursor.execute("SELECT * FROM grade ORDER BY id")
        grades = cursor.fetchall()
        
        print(f"📊 Found {len(grades)} grades:")
        
        for grade in grades:
            print(f"\n  Grade ID: {grade['id']}")
            print(f"  Name: {grade['name']}")
            print(f"  Level: {grade.get('level', 'N/A')}")
            
            # Get streams for this grade
            cursor.execute("SELECT * FROM stream WHERE grade_id = %s ORDER BY id", (grade['id'],))
            streams = cursor.fetchall()
            
            print(f"  Streams ({len(streams)}):")
            if streams:
                for stream in streams:
                    print(f"    - Stream ID: {stream['id']}, Name: {stream['name']}")
            else:
                print("    - No streams found")
        
        # Test the API endpoint format
        print("\n" + "=" * 50)
        print("🧪 API Endpoint Test Data:")
        
        if grades:
            test_grade_id = grades[0]['id']
            cursor.execute("SELECT * FROM stream WHERE grade_id = %s", (test_grade_id,))
            test_streams = cursor.fetchall()
            
            print(f"\nTest Grade ID: {test_grade_id}")
            print("Expected API Response Format:")
            
            # Classteacher format
            classteacher_response = {
                "streams": [{"id": stream['id'], "name": stream['name']} for stream in test_streams]
            }
            print(f"Classteacher API: {json.dumps(classteacher_response, indent=2)}")
            
            # Headteacher format
            headteacher_response = {
                "success": True,
                "streams": [{"id": stream['id'], "name": stream['name']} for stream in test_streams]
            }
            print(f"Headteacher API: {json.dumps(headteacher_response, indent=2)}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database Error: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 Grades and Streams Database Check")
    print("=" * 50)
    
    success = check_grades_and_streams()
    
    if success:
        print("\n✅ Database check completed successfully!")
    else:
        print("\n❌ Database check failed!")

if __name__ == "__main__":
    main()
