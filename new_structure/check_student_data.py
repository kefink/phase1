#!/usr/bin/env python3
"""
Data integrity checker and fixer for student grade/stream assignments.
This script will identify and optionally fix data integrity issues.
"""

def check_student_data_integrity():
    """Check for and report data integrity issues with student assignments."""
    try:
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        from models import db, Student, Grade, Stream
        from __init__ import create_app

        app = create_app()
        
        with app.app_context():
            print("=== STUDENT DATA INTEGRITY CHECK ===\n")
            
            # Check 1: Students with stream but no grade
            print("1. Students with Stream but NO Grade:")
            students_stream_no_grade = db.session.query(Student, Grade, Stream)\
                .outerjoin(Grade, Student.grade_id == Grade.id)\
                .outerjoin(Stream, Student.stream_id == Stream.id)\
                .filter(Student.grade_id.is_(None), Student.stream_id.isnot(None)).all()
            
            if students_stream_no_grade:
                for student, grade, stream in students_stream_no_grade:
                    print(f"  ⚠️  {student.name} (ID: {student.id})")
                    print(f"       Grade ID: {student.grade_id} (NULL)")
                    print(f"       Stream ID: {student.stream_id} -> '{stream.name}' (Grade {stream.grade_id})")
                    
                    # Find the correct grade for this stream
                    correct_grade = Grade.query.get(stream.grade_id) if stream else None
                    if correct_grade:
                        print(f"       🔧 Should be: Grade '{correct_grade.name}' (ID: {correct_grade.id})")
                    print()
            else:
                print("  ✅ No students with stream but missing grade")
            
            # Check 2: Students with neither grade nor stream
            print("\n2. Students with NO Grade and NO Stream:")
            students_no_assignment = Student.query.filter(
                Student.grade_id.is_(None), 
                Student.stream_id.is_(None)
            ).all()
            
            if students_no_assignment:
                for student in students_no_assignment:
                    print(f"  ⚠️  {student.name} (ID: {student.id}) - Completely unassigned")
            else:
                print("  ✅ No completely unassigned students")
            
            # Check 3: Students with grade but invalid stream
            print("\n3. Students with Grade but Invalid Stream:")
            students_invalid_stream = db.session.query(Student, Grade, Stream)\
                .join(Grade, Student.grade_id == Grade.id)\
                .outerjoin(Stream, Student.stream_id == Stream.id)\
                .filter(Student.stream_id.isnot(None), Stream.grade_id != Grade.id).all()
            
            if students_invalid_stream:
                for student, grade, stream in students_invalid_stream:
                    print(f"  ⚠️  {student.name} - Grade {grade.name} with Stream {stream.name} from different grade")
            else:
                print("  ✅ No students with invalid grade-stream combinations")
            
            # Check 4: Show all available grades and streams
            print("\n4. Available Grades and Streams:")
            grades = Grade.query.order_by(Grade.name).all()
            for grade in grades:
                streams = Stream.query.filter_by(grade_id=grade.id).all()
                stream_names = [s.name for s in streams]
                print(f"  📚 {grade.name} (ID: {grade.id}, Level: {grade.education_level})")
                print(f"      Streams: {', '.join(stream_names) if stream_names else 'None'}")
            
            print(f"\n=== SUMMARY ===")
            print(f"Total students: {Student.query.count()}")
            print(f"Students with grades: {Student.query.filter(Student.grade_id.isnot(None)).count()}")
            print(f"Students with streams: {Student.query.filter(Student.stream_id.isnot(None)).count()}")
            print(f"Students needing grade assignment: {len(students_stream_no_grade) + len(students_no_assignment)}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def fix_student_assignments():
    """Fix student grade assignments based on their stream assignments."""
    try:
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        from models import db, Student, Grade, Stream
        from __init__ import create_app

        app = create_app()
        
        with app.app_context():
            print("=== FIXING STUDENT ASSIGNMENTS ===\n")
            
            # Fix students with stream but no grade
            students_to_fix = db.session.query(Student, Stream)\
                .outerjoin(Stream, Student.stream_id == Stream.id)\
                .filter(Student.grade_id.is_(None), Student.stream_id.isnot(None)).all()
            
            fixed_count = 0
            for student, stream in students_to_fix:
                if stream and stream.grade_id:
                    print(f"🔧 Fixing {student.name}: Setting grade_id to {stream.grade_id}")
                    student.grade_id = stream.grade_id
                    fixed_count += 1
            
            if fixed_count > 0:
                db.session.commit()
                print(f"\n✅ Fixed {fixed_count} student assignments!")
            else:
                print("✅ No assignments needed fixing.")
                
    except Exception as e:
        print(f"Error fixing assignments: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        print("Running in FIX mode...\n")
        fix_student_assignments()
        print("\nRechecking after fix...")
        check_student_data_integrity()
    else:
        print("Running in CHECK mode (use --fix to apply fixes)...\n")
        check_student_data_integrity()
        print("\nTo fix issues automatically, run: python check_student_data.py --fix")