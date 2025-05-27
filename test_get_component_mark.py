"""
Test script to check if the get_component_mark function is working correctly.
"""
from new_structure import create_app
from new_structure.models.academic import Subject, SubjectComponent, Mark, ComponentMark
from new_structure.extensions import db

def test_get_component_mark():
    """Test if the get_component_mark function is working correctly."""
    app = create_app()
    with app.app_context():
        print("Testing get_component_mark function...")
        
        # Define a function similar to the one in the edit_class_marks route
        def get_component_mark(student_id, component_id):
            """Get the component mark for a student and component."""
            try:
                # Find the mark in the database
                component_mark = ComponentMark.query.filter_by(
                    component_id=component_id
                ).join(
                    Mark, ComponentMark.mark_id == Mark.id
                ).filter(
                    Mark.student_id == student_id
                ).first()
                
                # Debug output
                if component_mark:
                    print(f"Found component mark: student_id={student_id}, component_id={component_id}, raw_mark={component_mark.raw_mark}, max_raw_mark={component_mark.max_raw_mark}, percentage={component_mark.percentage}")
                else:
                    print(f"No component mark found for student_id={student_id}, component_id={component_id}")
                
                return component_mark
            except Exception as e:
                print(f"Error getting component mark: {e}")
                return None
        
        # Get some student IDs
        from new_structure.models.academic import Student
        students = Student.query.limit(5).all()
        
        if not students:
            print("No students found in the database.")
            return
        
        print(f"Found {len(students)} students:")
        for student in students:
            print(f"Student ID: {student.id}, Name: {student.name}")
        
        # Get English and Kiswahili components
        english_components = SubjectComponent.query.filter_by(subject_id=2).all()
        kiswahili_components = SubjectComponent.query.filter_by(subject_id=7).all()
        
        if not english_components:
            print("No English components found in the database.")
        else:
            print(f"Found {len(english_components)} English components:")
            for component in english_components:
                print(f"Component ID: {component.id}, Name: {component.name}, Weight: {component.weight}, Max Raw Mark: {component.max_raw_mark}")
        
        if not kiswahili_components:
            print("No Kiswahili components found in the database.")
        else:
            print(f"Found {len(kiswahili_components)} Kiswahili components:")
            for component in kiswahili_components:
                print(f"Component ID: {component.id}, Name: {component.name}, Weight: {component.weight}, Max Raw Mark: {component.max_raw_mark}")
        
        # Test get_component_mark for each student and component
        print("\nTesting get_component_mark for each student and component:")
        for student in students:
            for component in english_components + kiswahili_components:
                component_mark = get_component_mark(student.id, component.id)
                if component_mark:
                    print(f"Student: {student.name}, Component: {component.name}, Raw Mark: {component_mark.raw_mark}, Max Raw Mark: {component_mark.max_raw_mark}, Percentage: {component_mark.percentage:.2f}%")
                else:
                    print(f"No component mark found for Student: {student.name}, Component: {component.name}")

if __name__ == "__main__":
    test_get_component_mark()
