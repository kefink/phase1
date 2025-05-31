#!/usr/bin/env python3
"""
Initialize database using Flask-SQLAlchemy.
"""

import os
import sys

# Add parent directory to path
parent_dir = os.path.dirname(os.getcwd())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from new_structure import create_app
from new_structure.extensions import db
from new_structure.models.user import Teacher
from new_structure.models.academic import (
    SchoolConfiguration, Subject, Grade, Stream, Student, 
    Term, AssessmentType, Mark
)

def init_database():
    """Initialize database with all tables."""
    print("🔧 Initializing database with Flask-SQLAlchemy...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # Drop all tables and recreate
            print("🗑️  Dropping existing tables...")
            db.drop_all()
            
            print("🔧 Creating all tables...")
            db.create_all()
            
            # Create default admin user
            admin = Teacher(
                username='admin',
                password='admin',
                role='admin',
                full_name='Administrator',
                employee_id='EMP001',
                is_active=True
            )
            db.session.add(admin)
            
            # Create school configuration
            config = SchoolConfiguration(
                school_name='Hillview School',
                school_motto='Excellence in Education',
                current_academic_year='2024',
                current_term='Term 1',
                headteacher_name='Head Teacher',
                deputy_headteacher_name='Deputy Head Teacher'
            )
            db.session.add(config)
            
            # Create grades
            grades_data = [
                ('Grade 1', 'lower_primary'),
                ('Grade 2', 'lower_primary'),
                ('Grade 3', 'lower_primary'),
                ('Grade 4', 'upper_primary'),
                ('Grade 5', 'upper_primary'),
                ('Grade 6', 'upper_primary'),
                ('Grade 7', 'junior_secondary'),
                ('Grade 8', 'junior_secondary'),
                ('Grade 9', 'junior_secondary')
            ]
            
            grades = []
            for grade_name, education_level in grades_data:
                grade = Grade(name=grade_name, education_level=education_level)
                db.session.add(grade)
                grades.append(grade)
            
            db.session.flush()  # Get IDs
            
            # Create streams
            for grade in grades:
                stream_a = Stream(name='A', grade_id=grade.id)
                stream_b = Stream(name='B', grade_id=grade.id)
                db.session.add(stream_a)
                db.session.add(stream_b)
            
            # Create subjects
            subjects_data = [
                # Lower Primary
                ('English', 'lower_primary'),
                ('Kiswahili', 'lower_primary'),
                ('Mathematics', 'lower_primary'),
                ('Environmental Activities', 'lower_primary'),
                ('Creative Arts', 'lower_primary'),
                ('Physical Education', 'lower_primary'),
                
                # Upper Primary
                ('English', 'upper_primary'),
                ('Kiswahili', 'upper_primary'),
                ('Mathematics', 'upper_primary'),
                ('Science', 'upper_primary'),
                ('Social Studies', 'upper_primary'),
                ('Creative Arts', 'upper_primary'),
                ('Physical Education', 'upper_primary'),
                
                # Junior Secondary
                ('English', 'junior_secondary'),
                ('Kiswahili', 'junior_secondary'),
                ('Mathematics', 'junior_secondary'),
                ('Biology', 'junior_secondary'),
                ('Chemistry', 'junior_secondary'),
                ('Physics', 'junior_secondary'),
                ('Geography', 'junior_secondary'),
                ('History', 'junior_secondary'),
                ('Religious Education', 'junior_secondary'),
                ('Physical Education', 'junior_secondary')
            ]
            
            for subject_name, education_level in subjects_data:
                subject = Subject(
                    name=subject_name,
                    education_level=education_level,
                    is_standard=True,
                    is_composite=False
                )
                db.session.add(subject)
            
            # Create terms
            terms_data = [
                ('Term 1', '2024', True),
                ('Term 2', '2024', False),
                ('Term 3', '2024', False)
            ]
            
            for term_name, academic_year, is_current in terms_data:
                term = Term(
                    name=term_name,
                    academic_year=academic_year,
                    is_current=is_current
                )
                db.session.add(term)
            
            # Create assessment types
            assessment_types = [
                ('End of Term Exam', 'Final examination for the term'),
                ('Mid Term Test', 'Mid-term assessment'),
                ('Continuous Assessment', 'Ongoing classroom assessment')
            ]
            
            for name, description in assessment_types:
                assessment_type = AssessmentType(name=name, description=description)
                db.session.add(assessment_type)
            
            # Commit all changes
            db.session.commit()
            
            print("✅ Database initialized successfully!")
            
            # Verify
            print(f"✅ Teachers: {Teacher.query.count()}")
            print(f"✅ Grades: {Grade.query.count()}")
            print(f"✅ Streams: {Stream.query.count()}")
            print(f"✅ Subjects: {Subject.query.count()}")
            print(f"✅ Terms: {Term.query.count()}")
            print(f"✅ Assessment Types: {AssessmentType.query.count()}")
            
            return True
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🚀 Flask Database Initialization")
    print("=" * 50)
    
    if init_database():
        print("\n🎉 Database initialization completed!")
        print("🚀 Your Flask application should now work properly.")
    else:
        print("\n❌ Database initialization failed.")
