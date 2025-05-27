#!/usr/bin/env python3
"""
Debug script to check subject distribution and fix missing subjects.
"""

from new_structure import create_app
from new_structure.models import Subject, Grade
from new_structure.extensions import db

def debug_subject_distribution():
    """Debug current subject distribution by education level."""
    app = create_app()
    
    with app.app_context():
        print("=== CURRENT SUBJECT DISTRIBUTION ===\n")
        
        education_levels = ['lower_primary', 'upper_primary', 'junior_secondary']
        
        for level in education_levels:
            subjects = Subject.query.filter_by(education_level=level).all()
            print(f"{level.upper()} ({len(subjects)} subjects):")
            for subject in subjects:
                composite_info = " (COMPOSITE)" if hasattr(subject, 'is_composite') and subject.is_composite else ""
                print(f"  - {subject.name}{composite_info}")
            print()
        
        # Check for missing non-ministry subjects
        print("=== CHECKING FOR NON-MINISTRY SUBJECTS ===")
        non_ministry_subjects = ['FRENCH', 'CHINESE', 'MANDARIN', 'GERMAN', 'COMPUTER', 'COMPUTER STUDIES']
        
        for subject_name in non_ministry_subjects:
            subject = Subject.query.filter_by(name=subject_name).first()
            if subject:
                print(f"✓ {subject_name} - Found in {subject.education_level}")
            else:
                print(f"✗ {subject_name} - NOT FOUND")
        
        # Check grades
        print("\n=== GRADE DISTRIBUTION ===")
        grades = Grade.query.all()
        for grade in grades:
            print(f"Grade: {grade.level} (ID: {grade.id})")

def add_missing_subjects():
    """Add missing non-ministry subjects."""
    app = create_app()
    
    with app.app_context():
        print("\n=== ADDING MISSING NON-MINISTRY SUBJECTS ===")
        
        # Subjects to add for upper primary and junior secondary
        subjects_to_add = [
            # Upper Primary (Grades 4-6)
            ('FRENCH', 'upper_primary', False),
            ('CHINESE', 'upper_primary', False),
            ('COMPUTER STUDIES', 'upper_primary', False),
            ('GERMAN', 'upper_primary', False),
            
            # Junior Secondary (Grades 7-9)
            ('FRENCH', 'junior_secondary', False),
            ('CHINESE', 'junior_secondary', False),
            ('COMPUTER STUDIES', 'junior_secondary', False),
            ('GERMAN', 'junior_secondary', False),
            ('MANDARIN', 'junior_secondary', False),
        ]
        
        added_count = 0
        
        for subject_name, education_level, is_composite in subjects_to_add:
            # Check if subject already exists for this education level
            existing = Subject.query.filter_by(
                name=subject_name,
                education_level=education_level
            ).first()
            
            if existing:
                print(f"  ≈ {subject_name} ({education_level}) - Already exists")
                continue
            
            # Create new subject
            try:
                new_subject = Subject(
                    name=subject_name,
                    education_level=education_level,
                    is_composite=is_composite
                )
                db.session.add(new_subject)
                print(f"  ✓ {subject_name} ({education_level}) - Added")
                added_count += 1
                
            except Exception as e:
                print(f"  ✗ {subject_name} ({education_level}) - Error: {e}")
        
        if added_count > 0:
            try:
                db.session.commit()
                print(f"\n✅ Successfully added {added_count} subjects!")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error committing: {e}")
        else:
            print("\n📝 No new subjects to add.")

if __name__ == "__main__":
    debug_subject_distribution()
    add_missing_subjects()
    print("\n" + "="*50)
    print("Re-running debug to verify changes...")
    debug_subject_distribution()
