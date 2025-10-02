#!/usr/bin/env python3
"""
Flask-based data integrity fixer for student grade/stream assignments.
Uses the app's database connection to fix data issues.
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def fix_student_data_with_flask():
    """Fix student data using Flask app context and database connection."""
    
    try:
        # Import Flask app components
        print("🔧 Initializing Flask app and database connection...")
        
        # Import the necessary modules
        from models import db, Student, Grade, Stream
        from models.parent import Parent, ParentStudent
        from sqlalchemy import text
        
        # Import create_app function
        try:
            from __init__ import create_app
        except ImportError:
            print("❌ Could not import create_app. Trying alternative import...")
            import importlib.util
            spec = importlib.util.spec_from_file_location("app", "__init__.py")
            app_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(app_module)
            create_app = app_module.create_app

        # Create Flask app
        app = create_app()
        
        with app.app_context():
            print("✅ Connected to database successfully!")
            
            print("\n🔍 ANALYZING CURRENT DATA ISSUES...")
            
            # Check for students with streams but no grades
            problematic_students = db.session.query(Student, Stream).outerjoin(
                Stream, Student.stream_id == Stream.id
            ).filter(
                Student.grade_id.is_(None),
                Student.stream_id.isnot(None)
            ).all()
            
            print(f"⚠️  Found {len(problematic_students)} students with streams but no grades:")
            
            fix_count = 0
            for student, stream in problematic_students:
                if stream and stream.grade_id:
                    grade = Grade.query.get(stream.grade_id)
                    print(f"   - {student.name} ({student.admission_number}): Stream '{stream.name}' → Grade '{grade.name if grade else 'Unknown'}'")
                    
                    # Fix the assignment
                    student.grade_id = stream.grade_id
                    fix_count += 1
                else:
                    print(f"   - {student.name} ({student.admission_number}): Stream reference issue (Stream ID: {student.stream_id})")
            
            # Check for students with invalid stream references
            invalid_stream_students = db.session.query(Student).filter(
                Student.stream_id.isnot(None)
            ).filter(
                ~db.session.query(Stream.id).filter(Stream.id == Student.stream_id).exists()
            ).all()
            
            if invalid_stream_students:
                print(f"\n⚠️  Found {len(invalid_stream_students)} students with invalid stream references:")
                for student in invalid_stream_students:
                    print(f"   - {student.name} ({student.admission_number}): Invalid stream ID {student.stream_id}")
                    student.stream_id = None
                    fix_count += 1
            
            if fix_count > 0:
                print(f"\n🔧 APPLYING FIXES...")
                db.session.commit()
                print(f"✅ Successfully fixed {fix_count} student records!")
            else:
                print(f"\n✅ No data integrity issues found to fix!")
            
            print(f"\n📊 VERIFICATION - CURRENT STUDENT DATA:")
            
            # Show all students with their current assignments
            all_students = db.session.query(Student, Grade, Stream).outerjoin(
                Grade, Student.grade_id == Grade.id
            ).outerjoin(
                Stream, Student.stream_id == Stream.id
            ).order_by(Grade.name, Stream.name, Student.name).all()
            
            for student, grade, stream in all_students:
                grade_name = grade.name if grade else "Not assigned"
                stream_name = stream.name if stream else "Not assigned"
                edu_level = grade.education_level.replace('_', ' ').title() if grade and grade.education_level else "N/A"
                
                print(f"   ✓ {student.name} ({student.admission_number}): {grade_name} {stream_name} ({edu_level})")
            
            # Check parent-student links
            total_links = ParentStudent.query.count()
            students_with_parents = db.session.query(Student.id).join(
                ParentStudent, Student.id == ParentStudent.student_id
            ).join(
                Parent, ParentStudent.parent_id == Parent.id
            ).filter(Parent.is_active == True).distinct().count()
            
            students_without_parents = len(all_students) - students_with_parents
            
            print(f"\n📈 SUMMARY STATISTICS:")
            print(f"   • Total students: {len(all_students)}")
            print(f"   • Students with parent links: {students_with_parents}")
            print(f"   • Students without parent links: {students_without_parents}")
            print(f"   • Total parent-student links: {total_links}")
            
            return True
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the correct directory with all dependencies installed.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_success_message():
    """Show success message and next steps."""
    print("\n" + "="*70)
    print("🎉 STUDENT DATA INTEGRITY FIX COMPLETED SUCCESSFULLY!")
    print("="*70)
    
    print("\n✅ Issues that were resolved:")
    print("   • Students with streams but missing grades → Grades assigned")
    print("   • Invalid stream references → Cleaned up")
    print("   • Data consistency problems → Fixed")
    
    print("\n🎯 What you should see now in the dashboard:")
    print("   • Proper grade names instead of 'Not assigned'")
    print("   • Correct education levels instead of 'N/A'")
    print("   • Consistent grade-stream combinations")
    
    print(f"\n🔗 Next steps:")
    print("   1. 🌐 Visit: http://127.0.0.1:8080/parent_management/dashboard")
    print("   2. 👥 Check 'Students Without Parents' section")
    print("   3. ✅ Verify Grade and Stream columns show proper values")
    print("   4. 🎓 Test parent portal: http://127.0.0.1:8080/parent/children")
    print("   5. 🔗 Create parent-student links as needed")

if __name__ == "__main__":
    print("🚀 HILLVIEW SCHOOL - DATA INTEGRITY FIXER")
    print("="*50)
    print("Fixing student grade/stream assignment issues...")
    print("This will resolve 'Not assigned' and 'N/A' problems.\n")
    
    success = fix_student_data_with_flask()
    
    if success:
        show_success_message()
    else:
        print("\n❌ Fix operation failed. Please check the error messages above.")
        print("\nAlternative solutions:")
        print("1. Make sure your Flask app is properly configured")
        print("2. Check that all dependencies are installed")
        print("3. Try running the fix from within the Flask app interface")
        print("   (Use the 'Fix Data Issues' button in the parent management dashboard)")