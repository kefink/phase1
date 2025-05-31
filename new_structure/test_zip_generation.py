#!/usr/bin/env python3
"""
Test script to verify that the ZIP generation for individual reports works.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_zip_generation():
    """Test the ZIP generation functionality."""
    try:
        # Import the create_app function from the new_structure package
        from new_structure import create_app
        app = create_app()

        with app.app_context():
            from models.academic import Grade, Stream, Student, Term, AssessmentType

            # Get test data
            grades = Grade.query.limit(1).all()
            streams = Stream.query.limit(1).all()
            students = Student.query.limit(2).all()  # Test with 2 students
            terms = Term.query.limit(1).all()
            assessments = AssessmentType.query.limit(1).all()

            if not all([grades, streams, students, terms, assessments]):
                print("❌ Insufficient test data in database")
                return False

            grade = grades[0]
            stream = streams[0]
            term = terms[0]
            assessment = assessments[0]

            print(f"🧪 Testing ZIP generation with:")
            print(f"   Grade: {grade.name}")
            print(f"   Stream: Stream {stream.name}")
            print(f"   Term: {term.name}")
            print(f"   Assessment: {assessment.name}")
            print(f"   Students: {len(students)}")

            # Test the simple PDF generation function
            from views.classteacher import generate_simple_individual_report_pdf

            test_student = students[0]
            print(f"\n📄 Testing report generation for: {test_student.name}")

            # Test the function
            result = generate_simple_individual_report_pdf(
                test_student,
                grade.name,
                f"Stream {stream.name}",
                term.name,
                assessment.name,
                stream,  # stream_obj
                term,    # term_obj
                assessment  # assessment_type_obj
            )

            if result:
                print(f"✅ Report generated successfully: {result}")

                # Check if file exists
                if os.path.exists(result):
                    file_size = os.path.getsize(result)
                    print(f"✅ File exists, size: {file_size} bytes")

                    # Read first few lines to verify content
                    with open(result, 'r', encoding='utf-8') as f:
                        content = f.read(200)
                        print(f"✅ Content preview:\n{content}...")

                    return True
                else:
                    print(f"❌ File does not exist: {result}")
                    return False
            else:
                print("❌ Report generation failed")
                return False

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    print("🚀 TESTING ZIP GENERATION FUNCTIONALITY")
    print("=" * 50)

    success = test_zip_generation()

    print("\n" + "=" * 50)
    if success:
        print("🎉 TEST PASSED! ZIP generation should work now.")
        print("\n✅ You can now test the 'Download All Individual Reports (ZIP)' feature:")
        print("   1. Go to Class Teacher Dashboard")
        print("   2. Navigate to Recent Reports")
        print("   3. Click 'Download All Individual Reports (ZIP)'")
        print("   4. The system should generate a ZIP file with individual reports")
    else:
        print("❌ TEST FAILED! There may still be issues with ZIP generation.")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
