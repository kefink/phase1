#!/usr/bin/env python
"""
Script to unassign teachers from streams.
"""
from new_structure import create_app
from new_structure.models import Teacher
from new_structure.extensions import db

def unassign_teachers():
    """Unassign all teachers from streams."""
    app = create_app("development")
    
    with app.app_context():
        # Get all teachers
        teachers = Teacher.query.all()
        
        for teacher in teachers:
            print(f"Teacher ID: {teacher.id}, Username: {teacher.username}, Role: {teacher.role}, Stream ID: {teacher.stream_id}")
            
            if teacher.stream_id:
                # Unassign the teacher
                teacher.stream_id = None
                print(f"  Unassigned teacher {teacher.username} from stream")
            else:
                print("  Not assigned to any stream")
        
        # Commit the changes
        db.session.commit()
        print("All teachers have been unassigned from streams.")

if __name__ == "__main__":
    unassign_teachers()
