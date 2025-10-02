#!/usr/bin/env python3
"""
Debug script to check parent and student data in the database.
Run this to see what's causing the "B" values in the parent portal.
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_parent_data():
    """Debug parent and student data."""
    try:
        # Set PYTHONPATH to avoid module import issues
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            
        # Try different import methods
        try:
            from models import db, Student, Grade, Stream
            from models.parent import Parent, ParentStudent
            from __init__ import create_app
        except ImportError:
            # Try importing directly
            sys.path.insert(0, os.path.join(current_dir, '..'))
            import new_structure
            from new_structure.models import db, Student, Grade, Stream
            from new_structure.models.parent import Parent, ParentStudent
            from new_structure import create_app

        app = create_app()
        
        with app.app_context():
            print("=== DEBUG: Parent Portal Data ===\n")
            
            # Get all grades and streams
            print("All Grades in database:")
            grades = Grade.query.all()
            for grade in grades:
                print(f"  - ID: {grade.id}, Name: '{grade.name}', Education Level: {grade.education_level}")
            
            print("\nAll Streams in database:")
            streams = Stream.query.all()
            for stream in streams:
                grade = Grade.query.get(stream.grade_id)
                print(f"  - ID: {stream.id}, Name: '{stream.name}', Grade: {grade.name if grade else 'None'}")
            
            # Get all parent-student links
            print("\nParent-Student Links:")
            links = ParentStudent.query.all()
            for i, link in enumerate(links[:10]):  # Show first 10
                parent = Parent.query.get(link.parent_id)
                student = Student.query.get(link.student_id)
                grade = Grade.query.get(student.grade_id) if student and student.grade_id else None
                stream = Stream.query.get(student.stream_id) if student and student.stream_id else None
                
                print(f"  {i+1}. Parent: {parent.email if parent else 'None'}")
                print(f"     Student: {student.name if student else 'None'}")
                print(f"     Grade ID: {student.grade_id if student else None} -> '{grade.name if grade else 'None'}'")
                print(f"     Stream ID: {student.stream_id if student else None} -> '{stream.name if stream else 'None'}'")
                print(f"     Display would be: Grade='{grade.name if grade else 'Not assigned'}', Stream='{stream.name if stream else 'Not assigned'}'")
                print()
            
            if len(links) > 10:
                print(f"... and {len(links) - 10} more links")
            
            print("\n=== End Debug ===")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_parent_data()