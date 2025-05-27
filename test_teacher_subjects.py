#!/usr/bin/env python3
"""
Test script to verify teacher subject assignments and debug subject population issues.
"""

from new_structure import create_app
from new_structure.models import Teacher, Subject, TeacherSubjectAssignment, Grade
from new_structure.extensions import db

def test_teacher_subjects():
    """Test teacher subject assignments and debug issues."""
    app = create_app()
    
    with app.app_context():
        print("=== TEACHER SUBJECT ASSIGNMENT DEBUG ===\n")
        
        # 1. Check if we have teachers
        teachers = Teacher.query.all()
        print(f"Total teachers in database: {len(teachers)}")
        
        if teachers:
            for teacher in teachers:
                print(f"Teacher: {teacher.username} (ID: {teacher.id}, Role: {teacher.role})")
        else:
            print("No teachers found!")
            return
        
        print("\n" + "="*50)
        
        # 2. Check subjects by education level
        education_levels = ['lower_primary', 'upper_primary', 'junior_secondary']
        
        for level in education_levels:
            subjects = Subject.query.filter_by(education_level=level).all()
            print(f"\n{level.upper()} SUBJECTS ({len(subjects)} total):")
            for subject in subjects:
                composite_info = " (COMPOSITE)" if hasattr(subject, 'is_composite') and subject.is_composite else ""
                print(f"  - {subject.name} (ID: {subject.id}){composite_info}")
        
        print("\n" + "="*50)
        
        # 3. Check teacher subject assignments
        assignments = TeacherSubjectAssignment.query.all()
        print(f"\nTEACHER SUBJECT ASSIGNMENTS ({len(assignments)} total):")
        
        if assignments:
            for assignment in assignments:
                teacher = Teacher.query.get(assignment.teacher_id)
                subject = Subject.query.get(assignment.subject_id)
                grade = Grade.query.get(assignment.grade_id)
                
                teacher_name = teacher.username if teacher else "Unknown"
                subject_name = subject.name if subject else "Unknown"
                grade_name = grade.level if grade else "Unknown"
                stream_info = f" Stream {assignment.stream_id}" if assignment.stream_id else " (All Streams)"
                
                print(f"  - {teacher_name} → {subject_name} → {grade_name}{stream_info}")
        else:
            print("No teacher subject assignments found!")
            print("\nCreating sample assignments...")
            create_sample_assignments()
        
        print("\n" + "="*50)
        
        # 4. Test specific teacher assignments
        test_teacher = teachers[0] if teachers else None
        if test_teacher:
            print(f"\nTESTING ASSIGNMENTS FOR: {test_teacher.username}")
            
            for level in education_levels:
                # Get subjects assigned to this teacher for this education level
                assigned_subjects = db.session.query(Subject).join(
                    TeacherSubjectAssignment, Subject.id == TeacherSubjectAssignment.subject_id
                ).filter(
                    TeacherSubjectAssignment.teacher_id == test_teacher.id,
                    Subject.education_level == level
                ).distinct().all()
                
                print(f"\n{level} assignments for {test_teacher.username}:")
                if assigned_subjects:
                    for subject in assigned_subjects:
                        print(f"  ✓ {subject.name}")
                else:
                    print(f"  ✗ No subjects assigned for {level}")

def create_sample_assignments():
    """Create sample teacher subject assignments for testing."""
    try:
        # Get first teacher (assuming it exists)
        teacher = Teacher.query.first()
        if not teacher:
            print("No teacher found to create assignments for!")
            return
        
        # Get some subjects for junior secondary
        subjects = Subject.query.filter_by(education_level='junior_secondary').limit(3).all()
        grades = Grade.query.filter(Grade.level.in_(['Grade 7', 'Grade 8', 'Grade 9'])).all()
        
        if not subjects or not grades:
            print("No subjects or grades found for creating assignments!")
            return
        
        print(f"Creating assignments for teacher: {teacher.username}")
        
        # Create assignments
        for subject in subjects:
            for grade in grades:
                # Check if assignment already exists
                existing = TeacherSubjectAssignment.query.filter_by(
                    teacher_id=teacher.id,
                    subject_id=subject.id,
                    grade_id=grade.id
                ).first()
                
                if not existing:
                    assignment = TeacherSubjectAssignment(
                        teacher_id=teacher.id,
                        subject_id=subject.id,
                        grade_id=grade.id,
                        stream_id=None  # All streams
                    )
                    db.session.add(assignment)
                    print(f"  Created: {subject.name} → {grade.level}")
        
        db.session.commit()
        print("Sample assignments created successfully!")
        
    except Exception as e:
        print(f"Error creating sample assignments: {e}")
        db.session.rollback()

if __name__ == "__main__":
    test_teacher_subjects()
