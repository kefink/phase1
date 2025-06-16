#!/usr/bin/env python3
"""
Comprehensive analytics debugging script.
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from new_structure import create_app
from extensions import db
from models.academic import Mark, Student, Subject, Grade, Stream, Term, AssessmentType
from sqlalchemy import func, desc

app = create_app('development')

def debug_enhanced_top_performers():
    """Debug the enhanced top performers query."""
    with app.app_context():
        print("=== DEBUGGING ENHANCED TOP PERFORMERS ===")
        
        # Test the exact query from the service
        print("\n1. Testing basic data availability:")
        grades = Grade.query.all()
        print(f"   Grades: {[(g.id, g.name) for g in grades]}")
        
        streams = Stream.query.all()
        print(f"   Streams: {[(s.id, s.name, s.grade_id) for s in streams]}")
        
        students = Student.query.all()
        print(f"   Students: {[(s.id, s.name, s.grade_id, s.stream_id) for s in students]}")
        
        print("\n2. Testing the problematic query:")
        try:
            # This is the exact query from get_enhanced_top_performers
            grade = grades[0] if grades else None
            if not grade:
                print("   No grades found!")
                return
                
            print(f"   Testing for grade: {grade.name} (ID: {grade.id})")
            
            # Get streams for this grade
            streams_for_grade = Stream.query.filter_by(grade_id=grade.id).all()
            print(f"   Streams for this grade: {[(s.id, s.name) for s in streams_for_grade]}")
            
            if streams_for_grade:
                stream = streams_for_grade[0]
                print(f"   Testing for stream: {stream.name} (ID: {stream.id})")
                
                # Test the exact query
                query = db.session.query(
                    Student.id,
                    Student.name,
                    Student.admission_number,
                    Grade.name.label('grade_name'),
                    Stream.name.label('stream_name'),
                    func.avg(Mark.percentage).label('average_percentage'),
                    func.count(Mark.id).label('total_marks')
                ).join(Mark, Student.id == Mark.student_id)\
                 .join(Stream, Student.stream_id == Stream.id)\
                 .join(Grade, Stream.grade_id == Grade.id)\
                 .filter(Grade.id == grade.id)\
                 .filter(Student.stream_id == stream.id)
                
                query = query.group_by(Student.id, Student.name, Student.admission_number,
                                     Grade.name, Stream.name)
                query = query.having(func.count(Mark.id) >= 1)  # At least 1 mark
                query = query.order_by(desc(func.avg(Mark.percentage)))
                query = query.limit(5)
                
                results = query.all()
                print(f"   Query results: {len(results)} students found")
                
                for i, result in enumerate(results):
                    print(f"   {i+1}. {result.name} - {result.average_percentage:.2f}% ({result.total_marks} marks)")
            else:
                print("   No streams found for this grade!")
                
        except Exception as e:
            print(f"   Query failed: {str(e)}")
            import traceback
            traceback.print_exc()

def debug_top_subject_performers():
    """Debug the top subject performers query."""
    with app.app_context():
        print("\n=== DEBUGGING TOP SUBJECT PERFORMERS ===")
        
        try:
            # Test the corrected join logic
            base_query = Mark.query\
                .join(Student, Mark.student_id == Student.id)\
                .join(Subject, Mark.subject_id == Subject.id)\
                .join(Stream, Student.stream_id == Stream.id)\
                .join(Grade, Stream.grade_id == Grade.id)\
                .join(Term, Mark.term_id == Term.id)\
                .join(AssessmentType, Mark.assessment_type_id == AssessmentType.id)
            
            # Get combinations
            combinations = base_query.with_entities(
                Grade.id.label('grade_id'),
                Grade.name.label('grade_name'),
                Stream.id.label('stream_id'),
                Stream.name.label('stream_name'),
                Subject.id.label('subject_id'),
                Subject.name.label('subject_name')
            ).distinct().all()
            
            print(f"Found {len(combinations)} combinations")
            
            if combinations:
                combo = combinations[0]
                print(f"Testing first combination: Grade {combo.grade_name} - Stream {combo.stream_name} - {combo.subject_name}")
                
                # Test top performers for this combination
                top_performers_query = base_query.filter(
                    Grade.id == combo.grade_id,
                    Stream.id == combo.stream_id,
                    Subject.id == combo.subject_id
                ).with_entities(
                    Student.id.label('student_id'),
                    Student.name.label('student_name'),
                    Student.admission_number.label('admission_number'),
                    Mark.mark.label('marks'),
                    Mark.total_marks.label('total_marks'),
                    func.round((Mark.mark * 100.0 / Mark.total_marks), 2).label('percentage')
                ).order_by(desc('percentage')).limit(3)
                
                top_performers = top_performers_query.all()
                print(f"Top performers: {len(top_performers)}")
                for i, performer in enumerate(top_performers):
                    print(f"  {i+1}. {performer.student_name}: {performer.marks}/{performer.total_marks} ({performer.percentage}%)")
            
        except Exception as e:
            print(f"Top subject performers query failed: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    debug_enhanced_top_performers()
    debug_top_subject_performers()
