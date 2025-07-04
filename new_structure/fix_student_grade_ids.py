#!/usr/bin/env python3
"""
Fix existing students who don't have grade_id set.
This script updates all students to have the correct grade_id based on their stream.
"""

import sys
import os

# Add the parent directory to the path so we can import from new_structure
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Now import from new_structure
from new_structure.models.academic import Student, Stream
from new_structure.extensions import db

# Import the app creation function from run.py
import importlib.util
spec = importlib.util.spec_from_file_location("run", os.path.join(current_dir, "run.py"))
run_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_module)
create_app = run_module.create_app

def fix_student_grade_ids():
    """Update all students to have correct grade_id based on their stream."""
    app = create_app()
    
    with app.app_context():
        print("🔧 Starting to fix student grade_ids...")
        
        # Get all students who don't have grade_id set
        students_without_grade = Student.query.filter_by(grade_id=None).all()
        print(f"📊 Found {len(students_without_grade)} students without grade_id")
        
        # Get all students with stream_id but no grade_id
        students_with_stream = Student.query.filter(
            Student.stream_id.isnot(None),
            Student.grade_id.is_(None)
        ).all()
        print(f"📊 Found {len(students_with_stream)} students with stream but no grade_id")
        
        updated_count = 0
        error_count = 0
        
        for student in students_with_stream:
            try:
                if student.stream_id:
                    stream = Stream.query.get(student.stream_id)
                    if stream and stream.grade_id:
                        student.grade_id = stream.grade_id
                        updated_count += 1
                        print(f"✅ Updated student {student.name} (ID: {student.id}) - Grade ID: {stream.grade_id}")
                    else:
                        print(f"⚠️  Stream not found or has no grade_id for student {student.name} (ID: {student.id})")
                        error_count += 1
            except Exception as e:
                print(f"❌ Error updating student {student.name} (ID: {student.id}): {str(e)}")
                error_count += 1
        
        try:
            db.session.commit()
            print(f"🎉 Successfully updated {updated_count} students")
            if error_count > 0:
                print(f"⚠️  {error_count} students could not be updated")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing changes: {str(e)}")
            return False
        
        # Verify the fix
        remaining_without_grade = Student.query.filter_by(grade_id=None).count()
        print(f"📊 Students still without grade_id: {remaining_without_grade}")
        
        return True

if __name__ == "__main__":
    success = fix_student_grade_ids()
    if success:
        print("✅ Grade ID fix completed successfully!")
    else:
        print("❌ Grade ID fix failed!")
        sys.exit(1)
