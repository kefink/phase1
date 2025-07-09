#!/usr/bin/env python3
"""
Debug script to check grades and streams in the database.
This will help identify what data exists and test the API endpoints.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from __init__ import create_app
from models import Grade, Stream, Subject, Teacher
from extensions import db
import json

def main():
    """Main function to check grades and streams."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("🔍 HILLVIEW SYSTEM - GRADES & STREAMS DEBUG")
        print("=" * 60)
        
        # Check database connection
        try:
            db.engine.execute("SELECT 1")
            print("✅ Database connection: SUCCESS")
        except Exception as e:
            print(f"❌ Database connection: FAILED - {e}")
            return
        
        print("\n" + "=" * 40)
        print("📊 GRADES IN SYSTEM:")
        print("=" * 40)
        
        grades = Grade.query.all()
        if not grades:
            print("❌ NO GRADES FOUND!")
            print("The grade table is empty. You need to add grades first.")
            return
        
        print(f"Found {len(grades)} grades:")
        for grade in grades:
            print(f"  • Grade ID: {grade.id}, Name: '{grade.name}'")
            
            # Check streams for this grade
            streams = Stream.query.filter_by(grade_id=grade.id).all()
            if streams:
                print(f"    └─ Streams ({len(streams)}): {[s.name for s in streams]}")
            else:
                print(f"    └─ No streams found for this grade")
        
        print("\n" + "=" * 40)
        print("🏫 STREAMS IN SYSTEM:")
        print("=" * 40)
        
        all_streams = Stream.query.all()
        if not all_streams:
            print("❌ NO STREAMS FOUND!")
            print("The stream table is empty. You need to add streams first.")
        else:
            print(f"Found {len(all_streams)} streams:")
            for stream in all_streams:
                grade = Grade.query.get(stream.grade_id)
                grade_name = grade.name if grade else "Unknown Grade"
                print(f"  • Stream ID: {stream.id}, Name: '{stream.name}', Grade: {grade_name} (ID: {stream.grade_id})")
        
        print("\n" + "=" * 40)
        print("🧪 API ENDPOINT TEST:")
        print("=" * 40)
        
        if grades:
            # Test with the first grade
            test_grade = grades[0]
            print(f"Testing with Grade ID: {test_grade.id} ('{test_grade.name}')")
            
            # Simulate the API call
            test_streams = Stream.query.filter_by(grade_id=test_grade.id).all()
            
            # Classteacher API format
            classteacher_response = {
                'streams': [{'id': stream.id, 'name': stream.name} for stream in test_streams]
            }
            
            # Universal API format  
            universal_response = {
                'success': True,
                'streams': [{'id': stream.id, 'name': stream.name} for stream in test_streams]
            }
            
            print(f"\nClassteacher API Response (/classteacher/get_grade_streams/{test_grade.id}):")
            print(json.dumps(classteacher_response, indent=2))
            
            print(f"\nUniversal API Response (/universal/api/streams/{test_grade.id}):")
            print(json.dumps(universal_response, indent=2))
            
            if not test_streams:
                print("\n⚠️  WARNING: No streams found for this grade!")
                print("This explains why the frontend shows 'Error loading streams'")
                print("You need to add streams to your grades.")
        
        print("\n" + "=" * 40)
        print("👥 TEACHERS IN SYSTEM:")
        print("=" * 40)
        
        teachers = Teacher.query.all()
        if not teachers:
            print("❌ NO TEACHERS FOUND!")
        else:
            print(f"Found {len(teachers)} teachers:")
            for teacher in teachers:
                print(f"  • Teacher ID: {teacher.id}, Username: '{teacher.username}', Role: {teacher.role}")
        
        print("\n" + "=" * 40)
        print("📚 SUBJECTS IN SYSTEM:")
        print("=" * 40)
        
        subjects = Subject.query.all()
        if not subjects:
            print("❌ NO SUBJECTS FOUND!")
        else:
            print(f"Found {len(subjects)} subjects:")
            for subject in subjects[:10]:  # Show first 10
                print(f"  • Subject ID: {subject.id}, Name: '{subject.name}', Level: {subject.education_level}")
            if len(subjects) > 10:
                print(f"  ... and {len(subjects) - 10} more subjects")
        
        print("\n" + "=" * 60)
        print("🎯 DIAGNOSIS:")
        print("=" * 60)
        
        if not grades:
            print("❌ CRITICAL: No grades in database")
            print("   Solution: Add grades through admin panel")
        elif not all_streams:
            print("❌ CRITICAL: No streams in database") 
            print("   Solution: Add streams to grades through admin panel")
        elif not subjects:
            print("⚠️  WARNING: No subjects in database")
            print("   Solution: Add subjects through admin panel")
        else:
            print("✅ Basic data structure looks good")
            print("   If streams still don't load, it's likely an authentication issue")

if __name__ == '__main__':
    main()
