#!/usr/bin/env python
"""
Script to assign a stream to a class teacher.
"""
from new_structure import create_app
from new_structure.models import Teacher, Stream, Grade
from new_structure.extensions import db

def assign_stream_to_teacher():
    """Assign a stream to a class teacher."""
    app = create_app("development")
    
    with app.app_context():
        # Get the teacher with ID 3
        teacher = Teacher.query.get(3)
        
        if not teacher:
            print("Teacher with ID 3 not found.")
            return
        
        print(f"Found teacher with ID: {teacher.id}")
        
        # Get a stream to assign to the teacher
        # First, check if there are any streams
        streams = Stream.query.all()
        
        if not streams:
            print("No streams found. Creating a new stream...")
            
            # Create a grade if none exists
            grade = Grade.query.first()
            if not grade:
                print("No grades found. Creating a new grade...")
                grade = Grade(level="Grade 1")
                db.session.add(grade)
                db.session.commit()
                print(f"Created grade: {grade.level}")
            
            # Create a stream
            stream = Stream(name="A", grade_id=grade.id)
            db.session.add(stream)
            db.session.commit()
            print(f"Created stream: {stream.name} for grade: {grade.level}")
        else:
            # Use the first stream
            stream = streams[0]
            print(f"Using existing stream: {stream.name} for grade: {stream.grade.level}")
        
        # Assign the stream to the teacher
        teacher.stream_id = stream.id
        db.session.commit()
        
        print(f"Assigned stream {stream.name} to teacher with ID: {teacher.id}")

if __name__ == "__main__":
    assign_stream_to_teacher()