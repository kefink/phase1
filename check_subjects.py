from new_structure import create_app
from new_structure.models import Subject

app = create_app()

with app.app_context():
    subjects = Subject.query.all()
    print(f'Total subjects: {len(subjects)}')
    
    if subjects:
        print("\nSubjects and their education levels:")
        for subject in subjects:
            print(f'Subject: {subject.name}, Education Level: {subject.education_level}')
        
        # Get unique education levels
        education_levels = set([s.education_level for s in subjects])
        print(f"\nUnique education levels: {education_levels}")
    else:
        print("No subjects found in the database.")
