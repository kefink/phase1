from new_structure import create_app
from new_structure.models import Subject, Mark
from new_structure.extensions import db

app = create_app()

def clean_subjects():
    with app.app_context():
        # Get all subjects
        subjects = Subject.query.all()
        print(f'Total subjects before cleanup: {len(subjects)}')
        
        # Group subjects by name (case-insensitive) and education level
        subject_groups = {}
        for subject in subjects:
            key = (subject.name.upper(), subject.education_level)
            if key not in subject_groups:
                subject_groups[key] = []
            subject_groups[key].append(subject)
        
        # Find duplicate groups
        duplicates = {key: group for key, group in subject_groups.items() if len(group) > 1}
        
        if not duplicates:
            print("No duplicate subjects found.")
            return
        
        print(f"Found {len(duplicates)} groups of duplicate subjects.")
        
        # Process each group of duplicates
        for key, group in duplicates.items():
            name_upper, education_level = key
            print(f"\nProcessing duplicates for {name_upper} ({education_level}):")
            
            # Sort by ID (keep the oldest one)
            group.sort(key=lambda x: x.id)
            
            # Keep the first one (with lowest ID)
            keep = group[0]
            print(f"  Keeping: ID {keep.id}, Name: {keep.name}")
            
            # Process the rest (duplicates to remove)
            for duplicate in group[1:]:
                print(f"  Removing: ID {duplicate.id}, Name: {duplicate.name}")
                
                # First, update any marks that reference this subject
                marks = Mark.query.filter_by(subject_id=duplicate.id).all()
                if marks:
                    print(f"    Updating {len(marks)} marks to reference subject ID {keep.id}")
                    for mark in marks:
                        mark.subject_id = keep.id
                
                # Now delete the duplicate subject
                db.session.delete(duplicate)
            
        # Commit all changes
        db.session.commit()
        
        # Verify the cleanup
        remaining_subjects = Subject.query.all()
        print(f'\nTotal subjects after cleanup: {len(remaining_subjects)}')
        
        # Print remaining subjects
        print("\nRemaining subjects:")
        for subject in remaining_subjects:
            print(f'ID: {subject.id}, Name: {subject.name}, Education Level: {subject.education_level}')

if __name__ == "__main__":
    clean_subjects()
