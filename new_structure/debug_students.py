#!/usr/bin/env python3
"""
Debug students and assignments
"""
import sys
import os
sys.path.append('.')

from flask import Flask
from extensions import db
from config import Config

def debug_students_and_assignments():
    """Check students and teacher assignments"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        from models.academic import Grade, Stream, Student
        from models.user import Teacher
        from models.assignment import TeacherSubjectAssignment
        
        print('=== GRADES AND STREAMS ===')
        grades = Grade.query.all()
        for grade in grades:
            print(f'Grade {grade.id}: {grade.name}')
            streams = Stream.query.filter_by(grade_id=grade.id).all()
            for stream in streams:
                print(f'  Stream {stream.id}: {stream.name} (Grade {stream.grade_id})')
                students = Student.query.filter_by(stream_id=stream.id).all()
                print(f'    Students: {len(students)}')
                for student in students[:3]:  # Show first 3
                    print(f'      {student.id}: {student.name} (Admission: {student.admission_number})')
                if len(students) > 3:
                    print(f'      ... and {len(students) - 3} more students')
        
        print('\n=== KEVIN\'S ASSIGNMENTS (Teacher ID 4) ===')
        kevin = Teacher.query.get(4)
        if kevin:
            print(f'Teacher: {kevin.name} (ID: {kevin.id})')
            assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=4).all()
            print(f'Total assignments: {len(assignments)}')
            for assignment in assignments:
                print(f'  Subject {assignment.subject_id}, Grade {assignment.grade_id}, Stream {assignment.stream_id}')
        else:
            print('Kevin (Teacher ID 4) not found!')
        
        print('\n=== SPECIFIC CHECK: GRADE 9B ===')
        # Find Grade 9
        grade_9 = Grade.query.filter_by(name='9').first()
        if grade_9:
            print(f'Grade 9 found: ID {grade_9.id}')
            stream_b = Stream.query.filter_by(grade_id=grade_9.id, name='B').first()
            if stream_b:
                print(f'Stream B found: ID {stream_b.id}')
                students_9b = Student.query.filter_by(grade_id=grade_9.id, stream_id=stream_b.id).all()
                print(f'Students in Grade 9B: {len(students_9b)}')
                for student in students_9b:
                    print(f'  {student.id}: {student.name}')
            else:
                print('Stream B not found in Grade 9')
        else:
            print('Grade 9 not found')

if __name__ == '__main__':
    debug_students_and_assignments()
