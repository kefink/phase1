#!/usr/bin/env python3
"""
Script to assign subjects to teachers for testing the teacher dashboard.
"""

from new_structure import create_app
from new_structure.models import Teacher, Subject, TeacherSubjectAssignment, Grade
from new_structure.extensions import db

def assign_subjects_to_teacher():
    """Assign subjects to teacher1 for testing."""
    app = create_app()
    
    with app.app_context():
        print("=== ASSIGNING SUBJECTS TO TEACHER ===\n")
        
        # Get teacher1
        teacher = Teacher.query.filter_by(username='teacher1').first()
        if not teacher:
            print("Teacher 'teacher1' not found!")
            return
        
        print(f"Assigning subjects to: {teacher.username} (ID: {teacher.id})")
        
        # Define assignments for different education levels
        assignments_to_create = [
            # Junior Secondary (Grades 7-9)
            ('junior_secondary', 'MATHEMATICS', ['Grade 7', 'Grade 8', 'Grade 9']),
            ('junior_secondary', 'ENGLISH', ['Grade 7', 'Grade 8', 'Grade 9']),
            ('junior_secondary', 'INTEGRATED SCIENCE', ['Grade 7', 'Grade 8', 'Grade 9']),
            
            # Upper Primary (Grades 4-6)
            ('upper_primary', 'MATHEMATICS', ['Grade 4', 'Grade 5', 'Grade 6']),
            ('upper_primary', 'ENGLISH', ['Grade 4', 'Grade 5', 'Grade 6']),
            ('upper_primary', 'SCIENCE AND TECHNOLOGY', ['Grade 4', 'Grade 5', 'Grade 6']),
            
            # Lower Primary (Grades 1-3)
            ('lower_primary', 'MATHEMATICAL ACTIVITIES', ['Grade 1', 'Grade 2', 'Grade 3']),
            ('lower_primary', 'ENGLISH ACTIVITIES', ['Grade 1', 'Grade 2', 'Grade 3']),
        ]
        
        created_count = 0
        
        for education_level, subject_name, grade_levels in assignments_to_create:
            # Get the subject
            subject = Subject.query.filter_by(
                name=subject_name, 
                education_level=education_level
            ).first()
            
            if not subject:
                print(f"  ✗ Subject '{subject_name}' not found for {education_level}")
                continue
            
            print(f"\nAssigning {subject_name} ({education_level}):")
            
            for grade_level in grade_levels:
                # Get the grade
                grade = Grade.query.filter_by(level=grade_level).first()
                
                if not grade:
                    print(f"    ✗ Grade '{grade_level}' not found")
                    continue
                
                # Check if assignment already exists
                existing = TeacherSubjectAssignment.query.filter_by(
                    teacher_id=teacher.id,
                    subject_id=subject.id,
                    grade_id=grade.id,
                    stream_id=None  # All streams
                ).first()
                
                if existing:
                    print(f"    ≈ {grade_level} (already assigned)")
                    continue
                
                # Create new assignment
                try:
                    assignment = TeacherSubjectAssignment(
                        teacher_id=teacher.id,
                        subject_id=subject.id,
                        grade_id=grade.id,
                        stream_id=None,  # All streams
                        is_class_teacher=False
                    )
                    db.session.add(assignment)
                    print(f"    ✓ {grade_level}")
                    created_count += 1
                    
                except Exception as e:
                    print(f"    ✗ {grade_level} - Error: {e}")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully created {created_count} subject assignments!")
            
            # Verify assignments
            print("\n=== VERIFICATION ===")
            verify_teacher_assignments(teacher.id)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error committing assignments: {e}")

def verify_teacher_assignments(teacher_id):
    """Verify the assignments were created correctly."""
    education_levels = ['lower_primary', 'upper_primary', 'junior_secondary']
    
    for level in education_levels:
        assigned_subjects = db.session.query(Subject).join(
            TeacherSubjectAssignment, Subject.id == TeacherSubjectAssignment.subject_id
        ).filter(
            TeacherSubjectAssignment.teacher_id == teacher_id,
            Subject.education_level == level
        ).distinct().all()
        
        print(f"\n{level.upper()} ({len(assigned_subjects)} subjects):")
        for subject in assigned_subjects:
            composite_info = " (COMPOSITE)" if hasattr(subject, 'is_composite') and subject.is_composite else ""
            print(f"  ✓ {subject.name}{composite_info}")

if __name__ == "__main__":
    assign_subjects_to_teacher()
