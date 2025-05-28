#!/usr/bin/env python3
"""
Debug script to check performance data generation.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_structure import create_app
from new_structure.models import Student, Grade, Stream, Mark, Term, AssessmentType
from new_structure.extensions import db

def debug_performance_data():
    """Debug the performance data generation."""
    app = create_app('development')

    with app.app_context():
        print("=== DEBUGGING PERFORMANCE DATA GENERATION ===")

        # Check basic data
        print(f"Total students: {Student.query.count()}")
        print(f"Total marks: {Mark.query.count()}")
        print(f"Total grades: {Grade.query.count()}")
        print(f"Total streams: {Stream.query.count()}")
        print(f"Total terms: {Term.query.count()}")
        print(f"Total assessment types: {AssessmentType.query.count()}")

        # Check what grades exist
        print("\n=== ALL GRADES ===")
        all_grades = Grade.query.all()
        for grade in all_grades:
            print(f"Grade: {grade.level} (ID: {grade.id})")

        # Check Grade 7 Y specifically
        print("\n=== GRADE 7 Y ANALYSIS ===")
        grade_7 = Grade.query.filter_by(level='7').first()
        if not grade_7:
            # Try different variations
            grade_7 = Grade.query.filter_by(level='Grade 7').first()
        if not grade_7:
            grade_7 = Grade.query.filter_by(level='7th').first()

        if grade_7:
            print(f"Grade 7 ID: {grade_7.id}")
            stream_y = Stream.query.filter_by(grade_id=grade_7.id, name='Y').first()
            if stream_y:
                print(f"Stream Y ID: {stream_y.id}")

                # Count students in Grade 7 Y
                students_in_7y = Student.query.filter_by(stream_id=stream_y.id).all()
                print(f"Students enrolled in Grade 7 Y: {len(students_in_7y)}")
                for student in students_in_7y:
                    print(f"  - {student.name} (ID: {student.id})")

                # Count marks for Grade 7 Y students
                marks_for_7y = Mark.query.join(Student).filter(
                    Student.stream_id == stream_y.id,
                    Mark.percentage.isnot(None),
                    Mark.raw_mark.isnot(None),
                    Mark.max_raw_mark.isnot(None)
                ).all()

                print(f"Total marks for Grade 7 Y students: {len(marks_for_7y)}")

                # Group by student
                student_marks = {}
                for mark in marks_for_7y:
                    if mark.student_id not in student_marks:
                        student_marks[mark.student_id] = []
                    student_marks[mark.student_id].append(mark)

                print(f"Students with marks: {len(student_marks)}")
                for student_id, marks in student_marks.items():
                    student = Student.query.get(student_id)
                    print(f"  - {student.name}: {len(marks)} marks")

                # Check unique combinations for Grade 7 Y
                print("\n=== UNIQUE COMBINATIONS FOR GRADE 7 Y ===")
                combinations = db.session.query(
                    Grade.level.label('grade'),
                    Stream.name.label('stream'),
                    Term.name.label('term'),
                    AssessmentType.name.label('assessment_type'),
                    Term.id.label('term_id'),
                    AssessmentType.id.label('assessment_type_id'),
                    Grade.id.label('grade_id'),
                    Stream.id.label('stream_id')
                ).join(
                    Stream, Grade.id == Stream.grade_id
                ).join(
                    Student, Stream.id == Student.stream_id
                ).join(
                    Mark, Student.id == Mark.student_id
                ).join(
                    Term, Mark.term_id == Term.id
                ).join(
                    AssessmentType, Mark.assessment_type_id == AssessmentType.id
                ).filter(
                    Grade.level == '7',
                    Stream.name == 'Y',
                    Mark.percentage.isnot(None),
                    Mark.raw_mark.isnot(None),
                    Mark.max_raw_mark.isnot(None)
                ).distinct().all()

                print(f"Found {len(combinations)} unique combinations for Grade 7 Y")
                for combo in combinations:
                    print(f"  - {combo.grade} {combo.stream} {combo.term} {combo.assessment_type}")

                    # For each combination, get student averages
                    students_with_marks = db.session.query(
                        Student.id,
                        db.func.avg(Mark.percentage).label('avg_percentage'),
                        db.func.sum(Mark.raw_mark).label('total_raw_marks'),
                        db.func.sum(Mark.max_raw_mark).label('total_max_marks'),
                        db.func.count(Mark.id).label('subject_count')
                    ).join(
                        Mark, Student.id == Mark.student_id
                    ).join(
                        Stream, Student.stream_id == Stream.id
                    ).filter(
                        Stream.grade_id == combo.grade_id,
                        Stream.id == combo.stream_id,
                        Mark.term_id == combo.term_id,
                        Mark.assessment_type_id == combo.assessment_type_id,
                        Mark.percentage.isnot(None),
                        Mark.raw_mark.isnot(None),
                        Mark.max_raw_mark.isnot(None)
                    ).group_by(Student.id).all()

                    print(f"    Students with marks: {len(students_with_marks)}")
                    for student in students_with_marks:
                        student_obj = Student.query.get(student.id)
                        print(f"      - {student_obj.name}: avg={student.avg_percentage:.2f}%, raw={student.total_raw_marks}/{student.total_max_marks}, subjects={student.subject_count}")
            else:
                print("Stream Y not found for Grade 7")
        else:
            print("Grade 7 not found")

if __name__ == '__main__':
    debug_performance_data()
