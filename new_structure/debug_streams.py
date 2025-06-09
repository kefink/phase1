#!/usr/bin/env python3
"""
Debug script to check stream population issue for teacher telvo.
This script will help identify why streams are not populating in the marks upload form.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import app
    from models import Teacher, Grade, Stream, TeacherSubjectAssignment, Subject
    from extensions import db
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative imports...")
    try:
        from models.user import Teacher
        from models.academic import Grade, Stream, Subject
        from models.assignment import TeacherSubjectAssignment
        from extensions import db

        # Create a simple Flask app for database context
        from flask import Flask
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kirima_primary.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
    except ImportError as e2:
        print(f"Alternative import also failed: {e2}")
        sys.exit(1)

def debug_streams():
    """Debug the stream population issue."""

    with app.app_context():
        print("=== STREAM POPULATION DEBUG ===")
        print()
        
        # 1. Check if teacher 'telvo' exists
        print("1. Checking teacher 'telvo'...")
        teacher = Teacher.query.filter_by(username='telvo').first()
        if teacher:
            print(f"   ✅ Teacher found: {teacher.username} (ID: {teacher.id}, Role: {teacher.role})")
        else:
            print("   ❌ Teacher 'telvo' not found!")
            # List all teachers
            all_teachers = Teacher.query.all()
            print(f"   Available teachers: {[t.username for t in all_teachers]}")
            return
        
        print()
        
        # 2. Check grades in database
        print("2. Checking grades in database...")
        grades = Grade.query.all()
        if grades:
            print(f"   ✅ Found {len(grades)} grades:")
            for grade in grades:
                print(f"      - {grade.name} (ID: {grade.id})")
        else:
            print("   ❌ No grades found in database!")
            return
        
        print()
        
        # 3. Check streams for each grade
        print("3. Checking streams for each grade...")
        for grade in grades:
            streams = Stream.query.filter_by(grade_id=grade.id).all()
            print(f"   Grade {grade.name}: {len(streams)} streams")
            for stream in streams:
                print(f"      - Stream {stream.name} (ID: {stream.id})")
        
        print()
        
        # 4. Check teacher assignments
        print("4. Checking teacher assignments...")
        assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher.id).all()
        if assignments:
            print(f"   ✅ Teacher has {len(assignments)} assignments:")
            for assignment in assignments:
                subject = Subject.query.get(assignment.subject_id)
                grade = Grade.query.get(assignment.grade_id)
                stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None
                
                subject_name = subject.name if subject else f"Subject ID {assignment.subject_id}"
                grade_name = grade.name if grade else f"Grade ID {assignment.grade_id}"
                stream_name = stream.name if stream else "All Streams"
                
                print(f"      - {subject_name} | {grade_name} | {stream_name} | Class Teacher: {assignment.is_class_teacher}")
        else:
            print("   ⚠️  Teacher has no assignments!")
        
        print()
        
        # 5. Test specific grade lookup (simulate the API call)
        print("5. Testing grade lookup (simulating API calls)...")
        test_grades = ["1", "2", "3", "4", "5", "6", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"]
        
        for test_grade in test_grades:
            print(f"   Testing grade: '{test_grade}'")
            
            # Handle both "Grade X" format and just "X" format
            if test_grade.isdigit():
                grade_name = f"Grade {test_grade}"
            else:
                grade_name = test_grade
            
            # Get the grade object by name
            grade_obj = Grade.query.filter_by(name=grade_name).first()
            
            if not grade_obj:
                # Try alternative formats
                if grade_name.startswith("Grade "):
                    alt_grade = grade_name.replace("Grade ", "")
                    grade_obj = Grade.query.filter_by(name=alt_grade).first()
            
            if grade_obj:
                streams = Stream.query.filter_by(grade_id=grade_obj.id).all()
                print(f"      ✅ Found grade '{grade_obj.name}' with {len(streams)} streams: {[s.name for s in streams]}")
            else:
                print(f"      ❌ Grade not found")
        
        print()
        
        # 6. Check if there are any streams at all
        print("6. Overall stream check...")
        all_streams = Stream.query.all()
        print(f"   Total streams in database: {len(all_streams)}")
        if all_streams:
            for stream in all_streams:
                grade = Grade.query.get(stream.grade_id)
                grade_name = grade.name if grade else f"Grade ID {stream.grade_id}"
                print(f"      - Stream {stream.name} (ID: {stream.id}) in {grade_name}")
        
        print()
        print("=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_streams()
