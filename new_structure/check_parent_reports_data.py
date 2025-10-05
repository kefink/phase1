#!/usr/bin/env python3

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from new_structure.models import db
    from new_structure.models.academic import Mark, Student, Subject, Term, AssessmentType, Grade, Stream
    from new_structure.models.parent import Parent, ParentStudent  
    from new_structure import create_app
    
    app = create_app()
    
    with app.app_context():
        print("📊 DATABASE DATA CHECK:")
        print("=" * 30)
        
        # Count existing data
        marks_count = Mark.query.count()
        students_count = Student.query.count()
        parents_count = Parent.query.count()
        links_count = ParentStudent.query.count()
        subjects_count = Subject.query.count()
        
        print(f"📝 Total Marks: {marks_count}")
        print(f"👨‍🎓 Total Students: {students_count}") 
        print(f"👨‍👩‍👧 Total Parents: {parents_count}")
        print(f"🔗 Parent-Student Links: {links_count}")
        print(f"📚 Total Subjects: {subjects_count}")
        
        # Check for specific student data if Kevin is linked
        print("\n🔍 CHECKING FOR KEVIN'S DATA:")
        print("=" * 30)
        
        # Find Kevin's parent account
        kevin_parent = Parent.query.filter_by(email='kevin.knnyua@gmail.com').first()
        if not kevin_parent:
            kevin_parent = Parent.query.filter(Parent.email.like('%kevin%')).first()
        
        if kevin_parent:
            print(f"✅ Found Kevin's parent account: {kevin_parent.email}")
            
            # Get Kevin's children
            kevin_links = ParentStudent.query.filter_by(parent_id=kevin_parent.id).all()
            print(f"👶 Kevin has {len(kevin_links)} linked children:")
            
            for link in kevin_links:
                student = Student.query.get(link.student_id)
                if student:
                    print(f"   - {student.name} (ID: {student.id}, Admission: {student.admission_number})")
                    
                    # Check for marks for this student
                    student_marks = Mark.query.filter_by(student_id=student.id).limit(3).all()
                    print(f"     📊 Has {Mark.query.filter_by(student_id=student.id).count()} marks")
                    
                    if student_marks:
                        print("     📝 Sample marks:")
                        for mark in student_marks:
                            subject = Subject.query.get(mark.subject_id) if mark.subject_id else None
                            subject_name = subject.name if subject else "Unknown Subject"
                            print(f"       • {subject_name}: {mark.raw_mark}/{mark.raw_total_marks} = {mark.percentage}%")
                    
        else:
            print("❌ Kevin's parent account not found")
            print("📧 Available parent emails:")
            for parent in Parent.query.limit(5).all():
                print(f"   - {parent.email}")
        
        # Sample marks data if available
        if marks_count > 0:
            print(f"\n📈 SAMPLE MARKS DATA (First 5):")
            print("=" * 40)
            sample_marks = Mark.query.limit(5).all()
            for mark in sample_marks:
                student = Student.query.get(mark.student_id) if mark.student_id else None  
                subject = Subject.query.get(mark.subject_id) if mark.subject_id else None
                term = Term.query.get(mark.term_id) if mark.term_id else None
                assessment = AssessmentType.query.get(mark.assessment_type_id) if mark.assessment_type_id else None
                
                student_name = student.name if student else "Unknown"
                subject_name = subject.name if subject else "Unknown"
                term_name = term.name if term else "Unknown"
                assessment_name = assessment.name if assessment else "Unknown"
                
                print(f"📊 {student_name} | {subject_name} | {term_name} | {assessment_name}")
                print(f"   Score: {mark.raw_mark}/{mark.raw_total_marks} ({mark.percentage}%) Grade: {mark.grade_letter}")
                print()

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()