#!/usr/bin/env python3
"""
Test script to verify the student count fix for Grade 7 Y.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_structure import create_app
from new_structure.models import db, Student, Grade, Stream, Mark, Term, AssessmentType

def test_student_count_fix():
    """Test the student count fix for Grade 7 Y."""
    app = create_app('development')
    
    with app.app_context():
        print("Testing Student Count Fix for Grade 7 Y")
        print("=" * 50)
        
        # Find Grade 7 Stream Y
        grade_7 = Grade.query.filter_by(level='7').first()
        if not grade_7:
            print("❌ Grade 7 not found in database")
            return
            
        stream_y = Stream.query.filter_by(grade_id=grade_7.id, name='Y').first()
        if not stream_y:
            print("❌ Stream Y not found for Grade 7")
            return
            
        print(f"✅ Found Grade 7 Stream Y (ID: {stream_y.id})")
        
        # Count total enrolled students in Grade 7 Y
        total_enrolled = Student.query.filter_by(stream_id=stream_y.id).count()
        print(f"📊 Total enrolled students in Grade 7 Y: {total_enrolled}")
        
        # Count students with marks in Grade 7 Y
        students_with_marks = db.session.query(Student.id).join(
            Mark, Student.id == Mark.student_id
        ).filter(
            Student.stream_id == stream_y.id,
            Mark.percentage.isnot(None),
            Mark.raw_mark.isnot(None),
            Mark.max_raw_mark.isnot(None)
        ).distinct().count()
        
        print(f"📝 Students with assessment marks in Grade 7 Y: {students_with_marks}")
        
        # Get sample marks for verification
        sample_marks = db.session.query(
            Student.name,
            Mark.percentage,
            Mark.raw_mark,
            Mark.max_raw_mark,
            Term.name.label('term'),
            AssessmentType.name.label('assessment')
        ).join(
            Mark, Student.id == Mark.student_id
        ).join(
            Term, Mark.term_id == Term.id
        ).join(
            AssessmentType, Mark.assessment_type_id == AssessmentType.id
        ).filter(
            Student.stream_id == stream_y.id,
            Mark.percentage.isnot(None)
        ).limit(10).all()
        
        print(f"\n📋 Sample marks from Grade 7 Y:")
        for mark in sample_marks:
            print(f"   - {mark.name}: {mark.raw_mark}/{mark.max_raw_mark} ({mark.percentage}%) - {mark.term} {mark.assessment}")
        
        # Test the new performance assessment function
        print(f"\n🔧 Testing new performance assessment function...")
        try:
            from new_structure.views.admin import generate_performance_assessment_data
            performance_data = generate_performance_assessment_data()
            
            # Find Grade 7 Y data
            grade_7_y_data = [data for data in performance_data 
                             if data['grade'] == '7' and data['stream'] == 'Y']
            
            if grade_7_y_data:
                print(f"✅ Found {len(grade_7_y_data)} performance records for Grade 7 Y")
                for data in grade_7_y_data:
                    print(f"   📊 {data['term']} {data['assessment_type']}: {data['total_students']} students")
                    print(f"      Class Average: {data['total_raw_marks']}/{data['total_possible_marks']}")
                    print(f"      Performance: {data['performance_category']} ({data['mean_percentage']}%)")
                    
                    # Show grade distribution
                    counts = data['performance_counts']
                    total_in_grades = sum(counts.values())
                    print(f"      Grade Distribution (Total: {total_in_grades}):")
                    for grade, count in counts.items():
                        if count > 0:
                            print(f"        {grade}: {count} students")
                    print()
            else:
                print("❌ No performance data found for Grade 7 Y")
                
        except Exception as e:
            print(f"❌ Error testing performance function: {e}")
        
        print("=" * 50)
        print("✅ Student Count Test Completed!")
        
        if students_with_marks == 3:
            print("🎉 SUCCESS: Grade 7 Y shows correct count of 3 students with marks!")
        else:
            print(f"⚠️  ISSUE: Expected 3 students, but found {students_with_marks} students with marks")

if __name__ == '__main__':
    test_student_count_fix()
