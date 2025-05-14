from new_structure import create_app
from new_structure.models import Subject
from new_structure.extensions import db

app = create_app()

with app.app_context():
    # Check existing subjects
    existing_subjects = Subject.query.all()
    print(f'Existing subjects: {len(existing_subjects)}')
    
    # Define subjects for each education level
    lower_primary_subjects = [
        "LITERACY ACTIVITIES",
        "KISWAHILI LANGUAGE ACTIVITIES",
        "ENGLISH LANGUAGE ACTIVITIES",
        "MATHEMATICAL ACTIVITIES",
        "ENVIRONMENTAL ACTIVITIES",
        "HYGIENE AND NUTRITION ACTIVITIES",
        "RELIGIOUS EDUCATION ACTIVITIES",
        "MOVEMENT AND CREATIVE ACTIVITIES",
    ]
    
    upper_primary_subjects = [
        "ENGLISH",
        "KISWAHILI",
        "MATHEMATICS",
        "SCIENCE AND TECHNOLOGY",
        "SOCIAL STUDIES",
        "RELIGIOUS EDUCATION",
        "CREATIVE ARTS",
        "PHYSICAL AND HEALTH EDUCATION",
        "AGRICULTURE",
    ]
    
    # Add lower primary subjects
    for subject_name in lower_primary_subjects:
        # Check if subject already exists
        if not Subject.query.filter_by(name=subject_name, education_level="lower_primary").first():
            subject = Subject(name=subject_name, education_level="lower_primary")
            db.session.add(subject)
            print(f"Added lower_primary subject: {subject_name}")
    
    # Add upper primary subjects
    for subject_name in upper_primary_subjects:
        # Check if subject already exists
        if not Subject.query.filter_by(name=subject_name, education_level="upper_primary").first():
            subject = Subject(name=subject_name, education_level="upper_primary")
            db.session.add(subject)
            print(f"Added upper_primary subject: {subject_name}")
    
    # Commit changes
    db.session.commit()
    
    # Verify subjects after adding
    all_subjects = Subject.query.all()
    print(f'\nTotal subjects after adding: {len(all_subjects)}')
    
    # Get unique education levels
    education_levels = set([s.education_level for s in all_subjects])
    print(f"Education levels: {education_levels}")
    
    # Print subjects by education level
    for level in education_levels:
        level_subjects = Subject.query.filter_by(education_level=level).all()
        print(f"\n{level} subjects ({len(level_subjects)}):")
        for subject in level_subjects:
            print(f"  - {subject.name}")
