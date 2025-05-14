#!/usr/bin/env python
"""
Script to check teacher assignments.
"""
from new_structure import create_app
from new_structure.models import Teacher, Stream, Grade
from new_structure.extensions import db

def check_teacher_assignment():
    """Check teacher assignments."""
    app = create_app("development")
    
    with app.app_context():
        # Get all teachers
        teachers = Teacher.query.all()
        
        for teacher in teachers:
            print(f"Teacher ID: {teacher.id}, Username: {teacher.username}, Role: {teacher.role}, Stream ID: {teacher.stream_id}")
            
            if teacher.stream_id:
                stream = Stream.query.get(teacher.stream_id)
                if stream:
                    grade = Grade.query.get(stream.grade_id)
                    print(f"  Assigned to: Grade {grade.level if grade else 'Unknown'} Stream {stream.name}")
                else:
                    print("  Assigned to: Unknown stream")
            else:
                print("  Not assigned to any stream")

if __name__ == "__main__":
    check_teacher_assignment()
