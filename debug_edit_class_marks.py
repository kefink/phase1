"""
Script to debug the edit_class_marks route.
"""
from new_structure import create_app
from new_structure.models.academic import Subject, SubjectComponent, Grade, Stream, Term, AssessmentType
from new_structure.extensions import db

def debug_edit_class_marks():
    """Debug the edit_class_marks route."""
    app = create_app()
    with app.app_context():
        print("Debugging edit_class_marks route...")
        
        # Get a grade, stream, term, and assessment type
        grade = Grade.query.first()
        stream = Stream.query.filter_by(grade_id=grade.id).first()
        term = Term.query.first()
        assessment_type = AssessmentType.query.first()
        
        if not (grade and stream and term and assessment_type):
            print("Could not find grade, stream, term, or assessment type.")
            return
        
        print(f"Using Grade: {grade.level}, Stream: {stream.name}, Term: {term.name}, Assessment Type: {assessment_type.name}")
        
        # Determine education level based on grade
        education_level = ""
        grade_num = int(grade.level.split()[1]) if len(grade.level.split()) > 1 else int(grade.level)
        if 1 <= grade_num <= 3:
            education_level = "lower primary"
        elif 4 <= grade_num <= 6:
            education_level = "upper primary"
        elif 7 <= grade_num <= 9:
            education_level = "junior secondary"
        
        print(f"Education Level: {education_level}")
        
        # Get subjects for this grade based on education level
        if education_level == "lower primary":
            filtered_subjects = Subject.query.filter_by(education_level="lower_primary").all()
        elif education_level == "upper primary":
            filtered_subjects = Subject.query.filter_by(education_level="upper_primary").all()
        elif education_level == "junior secondary":
            filtered_subjects = Subject.query.filter_by(education_level="junior_secondary").all()
        else:
            filtered_subjects = Subject.query.all()
        
        # Get subject names, IDs, and objects
        subject_names = [subject.name for subject in filtered_subjects]
        subject_ids = [subject.id for subject in filtered_subjects]
        subject_objects = filtered_subjects  # Pass the actual subject objects
        
        print("\n=== SUBJECTS BEING PASSED TO TEMPLATE ===")
        for subject in filtered_subjects:
            print(f"Subject: {subject.name}, ID: {subject.id}, Is Composite: {subject.is_composite}")
            if subject.is_composite:
                components = subject.get_components()
                print(f"  Components: {[comp.name for comp in components]}")
        print("=========================================")
        
        # Check if English and Kiswahili are in the filtered subjects
        english = next((s for s in filtered_subjects if s.name == "ENGLISH"), None)
        kiswahili = next((s for s in filtered_subjects if s.name == "KISWAHILI"), None)
        
        if english:
            print(f"\nEnglish in filtered subjects: ID: {english.id}, Is Composite: {english.is_composite}")
            if english.is_composite:
                components = english.get_components()
                print(f"  Components: {[comp.name for comp in components]}")
        else:
            print("\nEnglish not found in filtered subjects.")
        
        if kiswahili:
            print(f"Kiswahili in filtered subjects: ID: {kiswahili.id}, Is Composite: {kiswahili.is_composite}")
            if kiswahili.is_composite:
                components = kiswahili.get_components()
                print(f"  Components: {[comp.name for comp in components]}")
        else:
            print("Kiswahili not found in filtered subjects.")
        
        print("\nDebug completed.")

if __name__ == "__main__":
    debug_edit_class_marks()
