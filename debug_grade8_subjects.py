#!/usr/bin/env python3
"""
Debug script to check Grade 8 subject assignments and composite subjects.
"""

from new_structure import create_app
from new_structure.models import Teacher, Subject, TeacherSubjectAssignment, Grade
from new_structure.models.academic import SubjectComponent
from new_structure.extensions import db

def debug_grade8_subjects():
    """Debug Grade 8 subject assignments and composite subjects."""
    app = create_app()

    with app.app_context():
        print("=== GRADE 8 SUBJECT ASSIGNMENT DEBUG ===\n")

        # Get teacher1
        teacher = Teacher.query.filter_by(username='teacher1').first()
        if not teacher:
            print("Teacher 'teacher1' not found!")
            return

        # Get Grade 8
        grade8 = Grade.query.filter_by(level='Grade 8').first()
        if not grade8:
            print("Grade 8 not found!")
            return

        print(f"Teacher: {teacher.username} (ID: {teacher.id})")
        print(f"Grade: {grade8.level} (ID: {grade8.id})")

        # Check all junior secondary subjects
        print("\n=== ALL JUNIOR SECONDARY SUBJECTS ===")
        all_js_subjects = Subject.query.filter_by(education_level='junior_secondary').all()
        for subject in all_js_subjects:
            composite_info = " (COMPOSITE)" if hasattr(subject, 'is_composite') and subject.is_composite else ""
            print(f"  - {subject.name} (ID: {subject.id}){composite_info}")

        # Check teacher's assignments for Grade 8
        print(f"\n=== TEACHER1 ASSIGNMENTS FOR GRADE 8 ===")
        grade8_assignments = TeacherSubjectAssignment.query.filter_by(
            teacher_id=teacher.id,
            grade_id=grade8.id
        ).all()

        print(f"Found {len(grade8_assignments)} assignments for Grade 8:")
        for assignment in grade8_assignments:
            subject = Subject.query.get(assignment.subject_id)
            stream_info = f" Stream {assignment.stream_id}" if assignment.stream_id else " (All Streams)"
            composite_info = " (COMPOSITE)" if hasattr(subject, 'is_composite') and subject.is_composite else ""
            print(f"  - {subject.name}{composite_info}{stream_info}")

        # Check what subjects should be available for Grade 8
        print(f"\n=== MISSING SUBJECTS FOR GRADE 8 ===")
        important_subjects = ['KISWAHILI', 'SOCIAL STUDIES', 'AGRICULTURE', 'RELIGIOUS']

        for subject_name in important_subjects:
            subject = Subject.query.filter_by(
                name=subject_name,
                education_level='junior_secondary'
            ).first()

            if subject:
                # Check if teacher has assignment for this subject in Grade 8
                assignment = TeacherSubjectAssignment.query.filter_by(
                    teacher_id=teacher.id,
                    subject_id=subject.id,
                    grade_id=grade8.id
                ).first()

                if not assignment:
                    print(f"  ✗ {subject_name} - Not assigned to teacher1 for Grade 8")
                else:
                    print(f"  ✓ {subject_name} - Already assigned")
            else:
                print(f"  ? {subject_name} - Subject not found in database")

        # Check composite subjects specifically
        print(f"\n=== COMPOSITE SUBJECTS ANALYSIS ===")
        composite_subjects = Subject.query.filter_by(
            education_level='junior_secondary',
            is_composite=True
        ).all()

        for subject in composite_subjects:
            print(f"\nSubject: {subject.name} (ID: {subject.id})")

            # Check if teacher is assigned
            assignment = TeacherSubjectAssignment.query.filter_by(
                teacher_id=teacher.id,
                subject_id=subject.id,
                grade_id=grade8.id
            ).first()

            assignment_status = "✓ ASSIGNED" if assignment else "✗ NOT ASSIGNED"
            print(f"  Assignment Status: {assignment_status}")

            # Check components
            components = SubjectComponent.query.filter_by(subject_id=subject.id).all()
            print(f"  Components ({len(components)} total):")
            for comp in components:
                print(f"    - {comp.name}: {comp.weight*100}% (Max: {comp.max_raw_mark})")

def add_missing_grade8_subjects():
    """Add missing subjects for Grade 8."""
    app = create_app()

    with app.app_context():
        print("\n=== ADDING MISSING GRADE 8 SUBJECTS ===")

        teacher = Teacher.query.filter_by(username='teacher1').first()
        grade8 = Grade.query.filter_by(level='Grade 8').first()

        if not teacher or not grade8:
            print("Teacher or Grade 8 not found!")
            return

        # Add more subjects for Grade 8
        subjects_to_add = ['KISWAHILI', 'SOCIAL STUDIES', 'AGRICULTURE', 'RELIGIOUS']

        added_count = 0
        for subject_name in subjects_to_add:
            subject = Subject.query.filter_by(
                name=subject_name,
                education_level='junior_secondary'
            ).first()

            if not subject:
                print(f"  ✗ {subject_name} - Subject not found")
                continue

            # Check if assignment already exists
            existing = TeacherSubjectAssignment.query.filter_by(
                teacher_id=teacher.id,
                subject_id=subject.id,
                grade_id=grade8.id
            ).first()

            if existing:
                print(f"  ≈ {subject_name} - Already assigned")
                continue

            # Create assignment
            try:
                assignment = TeacherSubjectAssignment(
                    teacher_id=teacher.id,
                    subject_id=subject.id,
                    grade_id=grade8.id,
                    stream_id=None,
                    is_class_teacher=False
                )
                db.session.add(assignment)
                print(f"  ✓ {subject_name} - Added")
                added_count += 1
            except Exception as e:
                print(f"  ✗ {subject_name} - Error: {e}")

        if added_count > 0:
            try:
                db.session.commit()
                print(f"\n✅ Successfully added {added_count} subjects to Grade 8!")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error committing: {e}")
        else:
            print("\n📝 No new subjects to add.")

if __name__ == "__main__":
    debug_grade8_subjects()
    add_missing_grade8_subjects()
    print("\n" + "="*50)
    print("Re-running debug to verify changes...")
    debug_grade8_subjects()
