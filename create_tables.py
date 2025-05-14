"""
Script to create all necessary tables for the new structure.
"""
from new_structure import create_app
from new_structure.extensions import db
from new_structure.models.academic import Subject, Grade, Stream, Term, AssessmentType, Student, Mark
from new_structure.models.user import Teacher, teacher_subjects
from new_structure.models.assignment import TeacherSubjectAssignment

def create_tables():
    """Create all necessary tables."""
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        print("All tables created successfully!")

if __name__ == "__main__":
    create_tables()
