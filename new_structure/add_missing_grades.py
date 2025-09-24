#!/usr/bin/env python3
"""Add PP1 and PP2 grades to the database if they're missing"""

import sys
import os
# Ensure parent of this directory is on sys.path so 'new_structure' can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from new_structure import create_app
from new_structure.extensions import db
from new_structure.models.academic import Grade, Stream

def add_missing_grades():
    app = create_app()
    with app.app_context():
        # Check current grades
        existing_grades = Grade.query.all()
        grade_names = [g.name for g in existing_grades]
        
        print(f"Current grades: {grade_names}")
        print(f"Total grades: {len(existing_grades)}")
        
        # Add PP1 if missing
        if "PP1" not in grade_names:
            pp1 = Grade(name="PP1", education_level="lower_primary")
            db.session.add(pp1)
            print("Added PP1 grade")
            
            # Add streams for PP1
            db.session.flush()  # Get the ID
            for stream_name in ["A", "B"]:
                stream = Stream(name=stream_name, grade_id=pp1.id)
                db.session.add(stream)
            print("Added PP1 streams")
        else:
            print("PP1 already exists")
        
        # Add PP2 if missing
        if "PP2" not in grade_names:
            pp2 = Grade(name="PP2", education_level="lower_primary")
            db.session.add(pp2)
            print("Added PP2 grade")
            
            # Add streams for PP2
            db.session.flush()  # Get the ID
            for stream_name in ["A", "B"]:
                stream = Stream(name=stream_name, grade_id=pp2.id)
                db.session.add(stream)
            print("Added PP2 streams")
        else:
            print("PP2 already exists")
        
        # Commit changes
        db.session.commit()
        
        # Verify final state
        final_grades = Grade.query.all()
        final_grade_names = [g.name for g in final_grades]
        print(f"Final grades: {final_grade_names}")
        print(f"Final count: {len(final_grades)}")
        
        # Show educational level distribution
        levels = {}
        for grade in final_grades:
            level = grade.education_level
            if level not in levels:
                levels[level] = []
            levels[level].append(grade.name)
        
        print("\nGrades by educational level:")
        for level, grade_list in levels.items():
            print(f"  {level}: {grade_list}")

if __name__ == "__main__":
    add_missing_grades()