"""
Script to add test component marks to the database.
"""
from new_structure import create_app
from new_structure.models.academic import Subject, SubjectComponent, Mark, ComponentMark, Term, AssessmentType
from new_structure.extensions import db

def add_test_component_marks():
    """Add test component marks to the database."""
    app = create_app()
    with app.app_context():
        print("Adding test component marks...")
        
        # Get the current term and assessment type
        term = Term.query.order_by(Term.id.desc()).first()
        assessment_type = AssessmentType.query.first()
        
        if not term:
            print("No terms found in the database.")
            return
        
        if not assessment_type:
            print("No assessment types found in the database.")
            return
        
        print(f"Using Term: {term.name}, Assessment Type: {assessment_type.name}")
        
        # Get English and Kiswahili subjects
        english = Subject.query.filter_by(id=2).first()
        kiswahili = Subject.query.filter_by(id=7).first()
        
        if not english or not kiswahili:
            print("English or Kiswahili subject not found in the database.")
            return
        
        print(f"Found English subject: {english.name}, ID: {english.id}")
        print(f"Found Kiswahili subject: {kiswahili.name}, ID: {kiswahili.id}")
        
        # Get English and Kiswahili components
        english_components = SubjectComponent.query.filter_by(subject_id=english.id).all()
        kiswahili_components = SubjectComponent.query.filter_by(subject_id=kiswahili.id).all()
        
        if not english_components or not kiswahili_components:
            print("English or Kiswahili components not found in the database.")
            return
        
        print(f"Found {len(english_components)} English components:")
        for component in english_components:
            print(f"Component ID: {component.id}, Name: {component.name}, Weight: {component.weight}, Max Raw Mark: {component.max_raw_mark}")
        
        print(f"Found {len(kiswahili_components)} Kiswahili components:")
        for component in kiswahili_components:
            print(f"Component ID: {component.id}, Name: {component.name}, Weight: {component.weight}, Max Raw Mark: {component.max_raw_mark}")
        
        # Get some students
        from new_structure.models.academic import Student
        students = Student.query.limit(5).all()
        
        if not students:
            print("No students found in the database.")
            return
        
        print(f"Found {len(students)} students:")
        for student in students:
            print(f"Student ID: {student.id}, Name: {student.name}")
        
        # For each student, add marks for English and Kiswahili
        for student in students:
            # Check if the student already has marks for English and Kiswahili
            english_mark = Mark.query.filter_by(
                student_id=student.id,
                subject_id=english.id,
                term_id=term.id,
                assessment_type_id=assessment_type.id
            ).first()
            
            kiswahili_mark = Mark.query.filter_by(
                student_id=student.id,
                subject_id=kiswahili.id,
                term_id=term.id,
                assessment_type_id=assessment_type.id
            ).first()
            
            # If the student doesn't have a mark for English, create one
            if not english_mark:
                english_mark = Mark(
                    student_id=student.id,
                    subject_id=english.id,
                    term_id=term.id,
                    assessment_type_id=assessment_type.id,
                    raw_mark=0,
                    max_raw_mark=100,
                    percentage=0
                )
                db.session.add(english_mark)
                db.session.commit()
                print(f"Created English mark for {student.name}")
            
            # If the student doesn't have a mark for Kiswahili, create one
            if not kiswahili_mark:
                kiswahili_mark = Mark(
                    student_id=student.id,
                    subject_id=kiswahili.id,
                    term_id=term.id,
                    assessment_type_id=assessment_type.id,
                    raw_mark=0,
                    max_raw_mark=100,
                    percentage=0
                )
                db.session.add(kiswahili_mark)
                db.session.commit()
                print(f"Created Kiswahili mark for {student.name}")
            
            # Add component marks for English
            for component in english_components:
                # Check if the student already has a component mark for this component
                component_mark = ComponentMark.query.filter_by(
                    mark_id=english_mark.id,
                    component_id=component.id
                ).first()
                
                # If the student doesn't have a component mark for this component, create one
                if not component_mark:
                    raw_mark = 30 if component.name == 'Grammar' else 20
                    max_raw_mark = component.max_raw_mark
                    percentage = (raw_mark / max_raw_mark) * 100
                    
                    component_mark = ComponentMark(
                        mark_id=english_mark.id,
                        component_id=component.id,
                        raw_mark=raw_mark,
                        max_raw_mark=max_raw_mark,
                        percentage=percentage
                    )
                    db.session.add(component_mark)
                    db.session.commit()
                    print(f"Created {component.name} mark for {student.name}: Raw Mark: {raw_mark}, Max Raw Mark: {max_raw_mark}, Percentage: {percentage:.2f}%")
            
            # Add component marks for Kiswahili
            for component in kiswahili_components:
                # Check if the student already has a component mark for this component
                component_mark = ComponentMark.query.filter_by(
                    mark_id=kiswahili_mark.id,
                    component_id=component.id
                ).first()
                
                # If the student doesn't have a component mark for this component, create one
                if not component_mark:
                    raw_mark = 30 if component.name == 'Lugha' else 20
                    max_raw_mark = component.max_raw_mark
                    percentage = (raw_mark / max_raw_mark) * 100
                    
                    component_mark = ComponentMark(
                        mark_id=kiswahili_mark.id,
                        component_id=component.id,
                        raw_mark=raw_mark,
                        max_raw_mark=max_raw_mark,
                        percentage=percentage
                    )
                    db.session.add(component_mark)
                    db.session.commit()
                    print(f"Created {component.name} mark for {student.name}: Raw Mark: {raw_mark}, Max Raw Mark: {max_raw_mark}, Percentage: {percentage:.2f}%")
        
        print("Test component marks added successfully.")

if __name__ == "__main__":
    add_test_component_marks()
