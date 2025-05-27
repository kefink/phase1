#!/usr/bin/env python3
"""
Debug script to check what data is being passed to the template.
"""

from new_structure import create_app
from new_structure.models import Subject
from new_structure.extensions import db

def debug_template_data():
    """Debug the data being passed to the template."""
    app = create_app()
    
    with app.app_context():
        print("=== DEBUGGING TEMPLATE DATA ===\n")
        
        # Get all subjects initially (will be filtered by education level on frontend)
        all_subjects = Subject.query.all()
        subjects_by_education_level = {
            'lower_primary': [s.name for s in all_subjects if s.education_level == 'lower_primary'],
            'upper_primary': [s.name for s in all_subjects if s.education_level == 'upper_primary'],
            'junior_secondary': [s.name for s in all_subjects if s.education_level == 'junior_secondary']
        }
        
        print("subjects_by_education_level data:")
        for level, subjects in subjects_by_education_level.items():
            print(f"  {level}: {len(subjects)} subjects")
            for subject in subjects:
                print(f"    - {subject}")
        
        print(f"\nJSON representation:")
        import json
        print(json.dumps(subjects_by_education_level, indent=2))
        
        # Check specific subjects
        print(f"\n=== CHECKING SPECIFIC SUBJECTS ===")
        english_subjects = Subject.query.filter(Subject.name.ilike('%english%')).all()
        print(f"English subjects found: {len(english_subjects)}")
        for subj in english_subjects:
            print(f"  - {subj.name} ({subj.education_level}) - Composite: {getattr(subj, 'is_composite', 'N/A')}")
        
        kiswahili_subjects = Subject.query.filter(Subject.name.ilike('%kiswahili%')).all()
        print(f"Kiswahili subjects found: {len(kiswahili_subjects)}")
        for subj in kiswahili_subjects:
            print(f"  - {subj.name} ({subj.education_level}) - Composite: {getattr(subj, 'is_composite', 'N/A')}")

if __name__ == "__main__":
    debug_template_data()
