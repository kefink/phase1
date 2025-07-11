#!/usr/bin/env python3
"""
Debug script to check the database objects needed for report generation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Flask app context first
from __init__ import create_app
app = create_app()

with app.app_context():
    from models.academic import Grade, Stream, Subject, Term, AssessmentType
    from models.user import Teacher
    from models.marks import Mark, Student

    def debug_report_data():
        """Check the database objects needed for report generation."""
        print("🔍 DEBUGGING REPORT DATA")
        print("=" * 50)
        
        # Test parameters from the failing request
        test_subject = "AGRICULTURE"
        test_grade = "Grade 9"
        test_stream = "B"
        test_term = "TERM 2"
        test_assessment_type = "KJSEA"
        
        print(f"Testing with parameters:")
        print(f"  Subject: '{test_subject}'")
        print(f"  Grade: '{test_grade}'")
        print(f"  Stream: '{test_stream}'")
        print(f"  Term: '{test_term}'")
        print(f"  Assessment Type: '{test_assessment_type}'")
        print()
        
        # Check Grade
        print("🔍 Checking Grade...")
        grade_obj = Grade.query.filter_by(name=test_grade).first()
        if grade_obj:
            print(f"✅ Grade found: ID={grade_obj.id}, Name='{grade_obj.name}'")
        else:
            print(f"❌ Grade '{test_grade}' not found")
            # Show available grades
            all_grades = Grade.query.all()
            print(f"Available grades: {[g.name for g in all_grades]}")
        
        # Check Stream
        print("\n🔍 Checking Stream...")
        if grade_obj:
            stream_obj = Stream.query.filter_by(grade_id=grade_obj.id, name=test_stream).first()
            if stream_obj:
                print(f"✅ Stream found: ID={stream_obj.id}, Name='{stream_obj.name}', Grade_ID={stream_obj.grade_id}")
            else:
                print(f"❌ Stream '{test_stream}' not found in grade '{test_grade}'")
                # Show available streams for this grade
                all_streams = Stream.query.filter_by(grade_id=grade_obj.id).all()
                print(f"Available streams for {test_grade}: {[s.name for s in all_streams]}")
        else:
            print("❌ Cannot check stream without valid grade")
        
        # Check Subject
        print("\n🔍 Checking Subject...")
        subject_obj = Subject.query.filter_by(name=test_subject).first()
        if subject_obj:
            print(f"✅ Subject found: ID={subject_obj.id}, Name='{subject_obj.name}', Level='{subject_obj.education_level}'")
        else:
            print(f"❌ Subject '{test_subject}' not found")
            # Show available subjects
            all_subjects = Subject.query.all()
            print(f"Available subjects: {[s.name for s in all_subjects[:10]]}...")
        
        # Check Term
        print("\n🔍 Checking Term...")
        term_obj = Term.query.filter_by(name=test_term).first()
        if term_obj:
            print(f"✅ Term found: ID={term_obj.id}, Name='{term_obj.name}'")
        else:
            print(f"❌ Term '{test_term}' not found")
            # Show available terms
            all_terms = Term.query.all()
            print(f"Available terms: {[t.name for t in all_terms]}")
        
        # Check Assessment Type
        print("\n🔍 Checking Assessment Type...")
        assessment_obj = AssessmentType.query.filter_by(name=test_assessment_type).first()
        if assessment_obj:
            print(f"✅ Assessment Type found: ID={assessment_obj.id}, Name='{assessment_obj.name}'")
        else:
            print(f"❌ Assessment Type '{test_assessment_type}' not found")
            # Show available assessment types
            all_assessments = AssessmentType.query.all()
            print(f"Available assessment types: {[a.name for a in all_assessments]}")
        
        print("\n" + "=" * 50)
        print("🎯 SUMMARY")
        print("=" * 50)
        
        all_objects_found = all([grade_obj, stream_obj, subject_obj, term_obj, assessment_obj])
        if all_objects_found:
            print("✅ All required database objects found!")
            print("✅ Report generation should work")
        else:
            print("❌ Some required database objects are missing")
            print("❌ Report generation will fail")
            
            missing = []
            if not grade_obj: missing.append("Grade")
            if not stream_obj: missing.append("Stream")  
            if not subject_obj: missing.append("Subject")
            if not term_obj: missing.append("Term")
            if not assessment_obj: missing.append("Assessment Type")
            
            print(f"Missing objects: {', '.join(missing)}")

    if __name__ == "__main__":
        debug_report_data()
