"""
Script to create a test teacher subject assignment directly in the database.
"""
from new_structure import create_app
from new_structure.extensions import db
from new_structure.models.academic import Subject, Grade, Stream
from new_structure.models.user import Teacher
from new_structure.models.assignment import TeacherSubjectAssignment

def create_test_assignment():
    """Create a test teacher subject assignment."""
    app = create_app()
    with app.app_context():
        # Get or create a teacher
        teacher = Teacher.query.filter_by(username='kevin').first()
        if not teacher:
            print("Teacher 'kevin' not found")
            return
        print(f"Found teacher: {teacher.username} (ID: {teacher.id})")
        
        # Get all grades
        grades = Grade.query.all()
        print(f"All grades in database ({len(grades)}):")
        for g in grades:
            print(f"  - ID: {g.id}, Level: {g.level}")
        
        # Get grade 8
        grade = Grade.query.filter_by(id=8).first()
        if not grade:
            print("Grade with ID 8 not found")
            return
        print(f"Found grade: {grade.level} (ID: {grade.id})")
        
        # Get streams for grade 8
        streams = Stream.query.filter_by(grade_id=grade.id).all()
        print(f"Streams for grade {grade.level} (ID: {grade.id}):")
        for s in streams:
            print(f"  - ID: {s.id}, Name: {s.name}")
        
        # Get stream with ID 21
        stream = Stream.query.filter_by(id=21).first()
        if not stream:
            print("Stream with ID 21 not found")
            return
        print(f"Found stream: {stream.name} (ID: {stream.id}, Grade ID: {stream.grade_id})")
        
        # Get all subjects
        subjects = Subject.query.all()
        print(f"All subjects in database ({len(subjects)}):")
        for s in subjects:
            print(f"  - ID: {s.id}, Name: {s.name}, Education Level: {s.education_level}")
        
        # Get subject with ID 1 (MATHEMATICS)
        subject = Subject.query.filter_by(id=1).first()
        if not subject:
            print("Subject with ID 1 not found")
            return
        print(f"Found subject: {subject.name} (ID: {subject.id})")
        
        # Check if assignment already exists
        existing = TeacherSubjectAssignment.query.filter_by(
            teacher_id=teacher.id,
            subject_id=subject.id,
            grade_id=grade.id,
            stream_id=stream.id
        ).first()
        
        if existing:
            print(f"Assignment already exists: {existing}")
            return
        
        # Create the assignment
        new_assignment = TeacherSubjectAssignment(
            teacher_id=teacher.id,
            subject_id=subject.id,
            grade_id=grade.id,
            stream_id=stream.id,
            is_class_teacher=True
        )
        
        db.session.add(new_assignment)
        db.session.commit()
        
        print(f"Created new assignment: {new_assignment}")
        
        # Verify the assignment was created
        assignment = TeacherSubjectAssignment.query.filter_by(
            teacher_id=teacher.id,
            subject_id=subject.id,
            grade_id=grade.id,
            stream_id=stream.id
        ).first()
        
        if assignment:
            print(f"Assignment verified: {assignment}")
        else:
            print("Failed to create assignment")

if __name__ == "__main__":
    create_test_assignment()
