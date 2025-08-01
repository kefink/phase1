#!/usr/bin/env python3
"""
Debug script to check student and teacher counts
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from new_structure import create_app
from new_structure.models.academic import Student, Subject, Grade, Stream
from new_structure.models.user import Teacher

def debug_counts():
    app = create_app('development')
    with app.app_context():
        print("=== DEBUGGING STUDENT AND TEACHER COUNTS ===")
        
        # Count students
        total_students = Student.query.count()
        print(f"📊 Total Students: {total_students}")
        
        # List some students
        students = Student.query.limit(5).all()
        print(f"📋 Sample students:")
        for student in students:
            print(f"  - {student.name} (ID: {student.id}, Admission: {student.admission_number})")
        
        # Count teachers
        total_teachers = Teacher.query.count()
        print(f"👨‍🏫 Total Teachers: {total_teachers}")
        
        # List teachers
        teachers = Teacher.query.all()
        print(f"📋 All teachers:")
        for teacher in teachers:
            print(f"  - {teacher.username} (ID: {teacher.id}, Role: {teacher.role})")
        
        # Count other entities
        total_subjects = Subject.query.count()
        total_grades = Grade.query.count()
        total_streams = Stream.query.count()
        
        print(f"\n📚 Total Subjects: {total_subjects}")
        print(f"📖 Total Grades: {total_grades}")
        print(f"🏫 Total Streams: {total_streams}")

if __name__ == "__main__":
    debug_counts()
