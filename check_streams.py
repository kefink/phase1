#!/usr/bin/env python
"""
Script to check streams in the database.
"""
from new_structure import create_app
from new_structure.models import Stream, Grade
from new_structure.extensions import db

def check_streams():
    """Check streams in the database."""
    app = create_app("development")
    
    with app.app_context():
        # Get all streams
        streams = Stream.query.all()
        
        if not streams:
            print("No streams found in the database.")
            return
        
        print(f"Found {len(streams)} streams:")
        for stream in streams:
            grade = Grade.query.get(stream.grade_id)
            print(f"Stream ID: {stream.id}, Name: {stream.name}, Grade: {grade.level if grade else 'Unknown'}")

if __name__ == "__main__":
    check_streams()
