"""
Migration script to create the teacher_subject_assignment table.
"""
from new_structure import create_app
from new_structure.extensions import db
from new_structure.models import TeacherSubjectAssignment

def create_table():
    """Create the teacher_subject_assignment table."""
    app = create_app()
    with app.app_context():
        # Create the table
        db.create_all(tables=[TeacherSubjectAssignment.__table__])
        print("TeacherSubjectAssignment table created successfully!")

if __name__ == "__main__":
    create_table()
