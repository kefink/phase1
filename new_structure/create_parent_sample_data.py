#!/usr/bin/env python3
"""
Create sample parent and student data for testing Kevin's parent portal
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, '.')

# Set environment for proper database connection (if needed)
os.environ['FLASK_ENV'] = 'development'

# Import after setting path and environment
from __init__ import create_app
from models import db
from models.parent_management import Parent, ParentStudent
from models.user import Student
from models.academic import Grade, Stream, Subject, Term, AssessmentType, Mark

def create_sample_data():
    """Create sample parent, student, and marks data for testing"""
    try:
        print("🏗️ Creating sample data for Kevin's parent portal...")
        
        # Create basic academic structure if it doesn't exist
        grade_7 = Grade.query.filter_by(name='Grade 7').first()
        if not grade_7:
            grade_7 = Grade(name='Grade 7')
            db.session.add(grade_7)
            db.session.commit()
        
        stream_a = Stream.query.filter_by(name='Stream A').first()
        if not stream_a:
            stream_a = Stream(name='Stream A')
            db.session.add(stream_a)
            db.session.commit()
        
        # Create subjects if they don't exist
        subjects_data = ['Mathematics', 'English', 'Science', 'Kiswahili', 'Social Studies']
        subjects = {}
        for subject_name in subjects_data:
            subject = Subject.query.filter_by(name=subject_name).first()
            if not subject:
                subject = Subject(name=subject_name, code=subject_name[:3].upper())
                db.session.add(subject)
            subjects[subject_name] = subject
        db.session.commit()
        
        # Create terms if they don't exist
        term_1 = Term.query.filter_by(name='Term 1', academic_year='2025').first()
        if not term_1:
            term_1 = Term(name='Term 1', academic_year='2025')
            db.session.add(term_1)
            db.session.commit()
        
        # Create assessment types if they don't exist
        assessment_types = {}
        for assessment_name in ['Mid Term', 'End Term']:
            assessment = AssessmentType.query.filter_by(name=assessment_name).first()
            if not assessment:
                assessment = AssessmentType(name=assessment_name)
                db.session.add(assessment)
            assessment_types[assessment_name] = assessment
        db.session.commit()
        
        # Create Kevin's parent account
        kevin_parent = Parent.query.filter_by(email='kevin_parent@gmail.com').first()
        if not kevin_parent:
            kevin_parent = Parent(
                first_name='Kevin',
                last_name='Knnyua',
                email='kevin_parent@gmail.com',
                username='kevin_parent',
                phone='+254123456789'
            )
            kevin_parent.set_password('password123')
            kevin_parent.is_active = True
            db.session.add(kevin_parent)
            db.session.commit()
            print(f"✅ Created parent account: {kevin_parent.email}")
        
        # Create Kevin's children (students)
        child_names = [
            {'first': 'Sarah', 'last': 'Knnyua', 'admission': 'SK2025001'},
            {'first': 'Michael', 'last': 'Knnyua', 'admission': 'MK2025002'}
        ]
        
        children = []
        for child_data in child_names:
            student = Student.query.filter_by(admission_number=child_data['admission']).first()
            if not student:
                student = Student(
                    first_name=child_data['first'],
                    last_name=child_data['last'],
                    admission_number=child_data['admission'],
                    grade_id=grade_7.id,
                    stream_id=stream_a.id,
                    email=f"{child_data['first'].lower()}.{child_data['last'].lower()}@student.hillview.ac.ke",
                    date_of_birth='2010-01-15'
                )
                db.session.add(student)
                children.append(student)
            else:
                children.append(student)
        
        db.session.commit()
        print(f"✅ Created {len(children)} student accounts")
        
        # Link children to parent
        for child in children:
            link = ParentStudent.query.filter_by(parent_id=kevin_parent.id, student_id=child.id).first()
            if not link:
                link = ParentStudent(
                    parent_id=kevin_parent.id,
                    student_id=child.id,
                    relationship='parent'
                )
                db.session.add(link)
        
        db.session.commit()
        print("✅ Linked children to parent")
        
        # Create sample marks for the children
        for child in children:
            for subject_name, subject in subjects.items():
                for assessment_name, assessment_type in assessment_types.items():
                    # Check if mark already exists
                    existing_mark = Mark.query.filter_by(
                        student_id=child.id,
                        subject_id=subject.id,
                        term_id=term_1.id,
                        assessment_type_id=assessment_type.id
                    ).first()
                    
                    if not existing_mark:
                        # Generate realistic marks (60-95 range)
                        import random
                        raw_mark = random.randint(60, 95)
                        total_marks = 100
                        
                        mark = Mark(
                            student_id=child.id,
                            subject_id=subject.id,
                            term_id=term_1.id,
                            assessment_type_id=assessment_type.id,
                            grade_id=grade_7.id,
                            stream_id=stream_a.id,
                            raw_mark=raw_mark,
                            raw_total_marks=total_marks,
                            mark=raw_mark,  # Backward compatibility
                            total_marks=total_marks,  # Backward compatibility
                            percentage=(raw_mark / total_marks) * 100,
                            grade_letter='A' if raw_mark >= 90 else 'B' if raw_mark >= 80 else 'C' if raw_mark >= 70 else 'D',
                            is_uploaded=True
                        )
                        db.session.add(mark)
        
        db.session.commit()
        print("✅ Created sample marks for all children and subjects")
        
        # Verify the data
        print("\n📊 VERIFICATION:")
        print(f"Parent: {kevin_parent.get_full_name()} ({kevin_parent.email})")
        
        links = ParentStudent.query.filter_by(parent_id=kevin_parent.id).all()
        for link in links:
            child = Student.query.get(link.student_id)
            marks_count = Mark.query.filter_by(student_id=child.id).count()
            print(f"  Child: {child.get_full_name()} - {marks_count} marks")
        
        print("\n✅ Sample data creation completed!")
        print(f"🔑 Login credentials:")
        print(f"   Email: kevin_parent@gmail.com")
        print(f"   Password: password123")
        print(f"🌐 URL: http://127.0.0.1:8080/parent/login")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    app = create_app('development')
    
    with app.app_context():
        success = create_sample_data()
        if success:
            print("\n🚀 Ready to test parent portal!")
        else:
            print("\n💥 Failed to create sample data")