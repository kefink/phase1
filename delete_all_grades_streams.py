#!/usr/bin/env python
"""
Script to delete all grades and streams from the database.
"""
from new_structure import create_app
from new_structure.models import Grade, Stream, Student, Teacher
from new_structure.extensions import db

def delete_all_grades_streams():
    """Delete all grades and streams from the database."""
    app = create_app("development")
    
    with app.app_context():
        print("Starting cleanup process...")
        
        # First, unassign all teachers from streams
        print("Unassigning teachers from streams...")
        teachers = Teacher.query.all()
        for teacher in teachers:
            if teacher.stream_id:
                print(f"  Unassigning teacher {teacher.username} from stream {teacher.stream_id}")
                teacher.stream_id = None
        db.session.commit()
        print("All teachers unassigned from streams.")
        
        # Next, unassign all students from streams
        print("Unassigning students from streams...")
        students = Student.query.all()
        for student in students:
            if student.stream_id:
                print(f"  Unassigning student {student.name} from stream {student.stream_id}")
                student.stream_id = None
        db.session.commit()
        print("All students unassigned from streams.")
        
        # Now delete all streams
        print("Deleting all streams...")
        streams = Stream.query.all()
        for stream in streams:
            print(f"  Deleting stream {stream.name} (ID: {stream.id})")
            db.session.delete(stream)
        db.session.commit()
        print("All streams deleted.")
        
        # Finally, delete all grades
        print("Deleting all grades...")
        grades = Grade.query.all()
        for grade in grades:
            print(f"  Deleting grade {grade.level} (ID: {grade.id})")
            db.session.delete(grade)
        db.session.commit()
        print("All grades deleted.")
        
        print("Cleanup process completed successfully.")

if __name__ == "__main__":
    delete_all_grades_streams()
