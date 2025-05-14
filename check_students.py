#!/usr/bin/env python
"""
Script to check students in the database.
"""
from new_structure import create_app
from new_structure.models import Student, Stream, Grade
from new_structure.extensions import db

def check_students():
    """Check students in the database."""
    app = create_app("development")
    
    with app.app_context():
        # Get all students
        students = Student.query.all()
        
        if not students:
            print("No students found in the database.")
            return
        
        print(f"Found {len(students)} students:")
        for student in students:
            stream = Stream.query.get(student.stream_id) if student.stream_id else None
            grade = Grade.query.get(stream.grade_id) if stream else None
            print(f"Student ID: {student.id}, Name: {student.name}, Admission Number: {student.admission_number}, Stream: {stream.name if stream else 'None'}, Grade: {grade.level if grade else 'None'}")

if __name__ == "__main__":
    check_students()
