"""
Script to fix the Mark model to use both old and new column names.
This script will update the Mark model to ensure it works with both old and new column names.
"""
from new_structure import create_app
from new_structure.models import Mark
from new_structure.extensions import db

def fix_mark_model():
    """Fix the Mark model to use both old and new column names."""
    app = create_app()
    
    with app.app_context():
        # Check if we have any marks
        marks = Mark.query.all()
        print(f"Found {len(marks)} marks in the database.")
        
        # Update the model to use both old and new column names
        for mark in marks:
            # Make sure both old and new columns have values
            if hasattr(mark, 'raw_mark') and mark.raw_mark is None:
                mark.raw_mark = mark.mark
            
            if hasattr(mark, 'max_raw_mark') and mark.max_raw_mark is None:
                mark.max_raw_mark = mark.total_marks
            
            if hasattr(mark, 'percentage') and mark.percentage is None:
                if mark.max_raw_mark > 0:
                    mark.percentage = (mark.raw_mark / mark.max_raw_mark) * 100
                else:
                    mark.percentage = 0
        
        # Commit the changes
        db.session.commit()
        
        print("Mark model fixed successfully.")

if __name__ == "__main__":
    fix_mark_model()
