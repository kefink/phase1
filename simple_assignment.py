"""
Simple script to create teacher subject assignments directly in the database.
"""
import os
import sqlite3
from new_structure import create_app
from new_structure.extensions import db
from new_structure.models.academic import Subject, Grade, Stream
from new_structure.models.user import Teacher
from new_structure.models.assignment import TeacherSubjectAssignment

def create_assignments():
    """Create teacher subject assignments directly."""
    app = create_app()
    with app.app_context():
        # Get the teacher (Kevin)
        teacher = Teacher.query.filter_by(username='kevin').first()
        if not teacher:
            print("Teacher 'kevin' not found. Creating...")
            teacher = Teacher(username='kevin', password='password', role='classteacher')
            db.session.add(teacher)
            db.session.commit()
            print(f"Created teacher: {teacher.username} (ID: {teacher.id})")
        else:
            print(f"Found teacher: {teacher.username} (ID: {teacher.id})")
        
        # Get Grade 8
        grade = Grade.query.filter_by(level='Grade 8').first()
        if not grade:
            print("Grade 8 not found. Creating...")
            grade = Grade(level='Grade 8')
            db.session.add(grade)
            db.session.commit()
            print(f"Created grade: {grade.level} (ID: {grade.id})")
        else:
            print(f"Found grade: {grade.level} (ID: {grade.id})")
        
        # Get Stream A for Grade 8
        stream = Stream.query.filter_by(name='A', grade_id=grade.id).first()
        if not stream:
            print("Stream A for Grade 8 not found. Creating...")
            stream = Stream(name='A', grade_id=grade.id)
            db.session.add(stream)
            db.session.commit()
            print(f"Created stream: {stream.name} (ID: {stream.id})")
        else:
            print(f"Found stream: {stream.name} (ID: {stream.id})")
        
        # Get or create junior secondary subjects
        subjects = []
        subject_names = ["ENGLISH", "KISWAHILI", "MATHEMATICS", "INTEGRATED SCIENCE"]
        for name in subject_names:
            subject = Subject.query.filter_by(name=name, education_level='junior_secondary').first()
            if not subject:
                print(f"Subject '{name}' not found. Creating...")
                subject = Subject(name=name, education_level='junior_secondary')
                db.session.add(subject)
                db.session.commit()
                print(f"Created subject: {subject.name} (ID: {subject.id})")
            else:
                print(f"Found subject: {subject.name} (ID: {subject.id})")
            subjects.append(subject)
        
        # Create assignments
        assignments_created = 0
        for subject in subjects:
            # Check if assignment already exists
            existing = TeacherSubjectAssignment.query.filter_by(
                teacher_id=teacher.id,
                subject_id=subject.id,
                grade_id=grade.id,
                stream_id=stream.id
            ).first()
            
            if existing:
                print(f"Assignment already exists: {existing}")
                continue
            
            # Create the assignment
            new_assignment = TeacherSubjectAssignment(
                teacher_id=teacher.id,
                subject_id=subject.id,
                grade_id=grade.id,
                stream_id=stream.id,
                is_class_teacher=(subject == subjects[0])  # Make Kevin class teacher for English
            )
            
            db.session.add(new_assignment)
            assignments_created += 1
            print(f"Created assignment: {subject.name} for {teacher.username} in Grade {grade.level} Stream {stream.name}")
        
        # Commit changes
        if assignments_created > 0:
            db.session.commit()
            print(f"Successfully created {assignments_created} assignments")
        else:
            print("No new assignments created")

if __name__ == "__main__":
    create_assignments()
