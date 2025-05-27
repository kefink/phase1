"""
Script to check if subjects have the is_composite field set correctly.
"""
from new_structure import create_app
from new_structure.models.academic import Subject, SubjectComponent
from new_structure.extensions import db

def check_subject_composite():
    """Check if subjects have the is_composite field set correctly."""
    app = create_app()
    with app.app_context():
        print("Checking subjects for is_composite field...")
        
        # Get all subjects
        subjects = Subject.query.all()
        
        print(f"Found {len(subjects)} subjects:")
        for subject in subjects:
            print(f"ID: {subject.id}, Name: {subject.name}, Is Composite: {subject.is_composite}")
            
            # Check if subject has components
            components = SubjectComponent.query.filter_by(subject_id=subject.id).all()
            if components:
                print(f"  Has {len(components)} components:")
                for component in components:
                    print(f"    Component ID: {component.id}, Name: {component.name}, Weight: {component.weight}, Max Raw Mark: {component.max_raw_mark}")
                
                # If subject has components but is_composite is False, update it
                if not subject.is_composite:
                    print(f"  Updating {subject.name} to be composite...")
                    subject.is_composite = True
                    db.session.commit()
            else:
                # If subject has no components but is_composite is True, update it
                if subject.is_composite:
                    print(f"  Updating {subject.name} to not be composite...")
                    subject.is_composite = False
                    db.session.commit()
        
        # Check English and Kiswahili specifically
        english = Subject.query.filter_by(id=2).first()
        kiswahili = Subject.query.filter_by(id=7).first()
        
        if english:
            print(f"\nEnglish (ID 2): Is Composite: {english.is_composite}")
            if not english.is_composite:
                print("  Setting English to be composite...")
                english.is_composite = True
                db.session.commit()
        else:
            print("\nEnglish (ID 2) not found.")
        
        if kiswahili:
            print(f"Kiswahili (ID 7): Is Composite: {kiswahili.is_composite}")
            if not kiswahili.is_composite:
                print("  Setting Kiswahili to be composite...")
                kiswahili.is_composite = True
                db.session.commit()
        else:
            print("Kiswahili (ID 7) not found.")
        
        # Check again after updates
        english = Subject.query.filter_by(id=2).first()
        kiswahili = Subject.query.filter_by(id=7).first()
        
        if english:
            print(f"\nAfter update - English (ID 2): Is Composite: {english.is_composite}")
        
        if kiswahili:
            print(f"After update - Kiswahili (ID 7): Is Composite: {kiswahili.is_composite}")
        
        print("\nCheck completed.")

if __name__ == "__main__":
    check_subject_composite()
