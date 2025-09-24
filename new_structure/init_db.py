#!/usr/bin/env python3
"""
Database initialization script
"""

import os
import sys

# Set up path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from extensions import db
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def initialize_database():
    app = create_app()
    
    with app.app_context():
        # Import models to register them with SQLAlchemy
        from models import user, academic, assignment, assessment_config, parent, report_config, school_setup, grading_system, rounding_config
        
        try:
            from models import permission, function_permission
        except ImportError:
            pass
        
        print("Creating database tables...")
        db.create_all()
        print("✅ Tables created successfully")
        
        # Check if we need to seed data
        from models.user import Teacher
        if not Teacher.query.first():
            print("Seeding default data...")
            seed_default_data()
        else:
            print("Database already has data, skipping seeding")

def seed_default_data():
    from models.user import Teacher
    from models.academic import Grade, Stream, Term, AssessmentType
    from models.subject import Subject
    
    # Create default users
    default_users = [
        {"username": "headteacher", "password": "admin123", "role": "headteacher", 
         "first_name": "Head", "last_name": "Teacher", "employee_id": "HT001"},
        {"username": "classteacher1", "password": "class123", "role": "classteacher", 
         "first_name": "Class", "last_name": "Teacher One", "employee_id": "CT001"},
    ]
    
    for data in default_users:
        pwd = data.pop("password")
        t = Teacher(**data)
        t.set_password(pwd)
        db.session.add(t)
    print("👥 Default users added")
    
    # Create grades including pre-primary
    grade_level_map = [
        ("PP1", "lower_primary"),
        ("PP2", "lower_primary"), 
        ("Grade 1", "lower_primary"),
        ("Grade 2", "lower_primary"),
        ("Grade 3", "lower_primary"),
        ("Grade 4", "upper_primary"),
        ("Grade 5", "upper_primary"),
        ("Grade 6", "upper_primary"),
        ("Grade 7", "junior_secondary"),
        ("Grade 8", "junior_secondary"),
        ("Grade 9", "junior_secondary"),
    ]
    
    grades = []
    for name, level in grade_level_map:
        g = Grade(name=name, education_level=level)
        db.session.add(g)
        grades.append(g)
    
    db.session.flush()  # Get IDs
    print(f"📚 {len(grades)} grades added (including PP1, PP2)")
    
    # Create streams (A, B) for each grade
    for g in grades:
        for stream_name in ("A", "B"):
            db.session.add(Stream(name=stream_name, grade_id=g.id))
    
    print("🏫 Streams added")
    
    # Create terms
    terms = ["Term 1", "Term 2", "Term 3"]
    for term_name in terms:
        db.session.add(Term(name=term_name))
    
    # Create assessment types
    assessment_types = ["CAT 1", "CAT 2", "End Term Exam"]
    for at_name in assessment_types:
        db.session.add(AssessmentType(name=at_name))
    
    print("📅 Terms and assessment types added")
    
    # Basic subjects
    subjects = [
        {"name": "Mathematics", "education_level": "lower_primary"},
        {"name": "English", "education_level": "lower_primary"},
        {"name": "Kiswahili", "education_level": "lower_primary"},
        {"name": "Mathematics", "education_level": "upper_primary"},
        {"name": "English", "education_level": "upper_primary"},
        {"name": "Kiswahili", "education_level": "upper_primary"},
        {"name": "Science", "education_level": "upper_primary"},
        {"name": "Mathematics", "education_level": "junior_secondary"},
        {"name": "English", "education_level": "junior_secondary"},
        {"name": "Kiswahili", "education_level": "junior_secondary"},
        {"name": "Science", "education_level": "junior_secondary"},
        {"name": "Social Studies", "education_level": "junior_secondary"},
    ]
    
    try:
        from models.subject import Subject
        for subject_data in subjects:
            db.session.add(Subject(**subject_data))
        print("📖 Basic subjects added")
    except ImportError:
        print("⚠️ Subject model not found, skipping subjects")
    
    try:
        db.session.commit()
        print("✅ Database seeded successfully")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding database: {e}")
        raise

if __name__ == "__main__":
    initialize_database()