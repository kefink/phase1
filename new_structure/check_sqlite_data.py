#!/usr/bin/env python3
"""
Quick check to see if we can use SQLite database for parent reports data
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Set environment to use SQLite
os.environ['FLASK_ENV'] = 'testing'

try:
    from __init__ import create_app
    from models.academic import Mark, Student, Subject, Term, AssessmentType
    from models.parent_management import Parent, ParentStudent
    
    print("📊 SQLITE DATABASE DATA CHECK:")
    print("=" * 30)
    
    app = create_app('testing')  # Use testing config which has SQLite
    
    with app.app_context():
        try:
            # Check if we can query basic counts
            marks_count = Mark.query.count()
            students_count = Student.query.count()
            subjects_count = Subject.query.count()
            terms_count = Term.query.count()
            parents_count = Parent.query.count()
            parent_student_count = ParentStudent.query.count()
            
            print(f"✅ Database connection working!")
            print(f"📝 Total Marks: {marks_count}")
            print(f"👥 Total Students: {students_count}")
            print(f"📚 Total Subjects: {subjects_count}")
            print(f"📅 Total Terms: {terms_count}")
            print(f"👨‍👩‍👧‍👦 Total Parents: {parents_count}")
            print(f"🔗 Parent-Student Links: {parent_student_count}")
            
            # Check for specific Kevin parent/student data
            kevin_parent = Parent.query.filter_by(username='kevin_parent').first()
            if kevin_parent:
                print(f"\n🎯 Found Kevin Parent: {kevin_parent.full_name}")
                linked_children = ParentStudent.query.filter_by(parent_id=kevin_parent.id).all()
                print(f"👶 Kevin's Children Count: {len(linked_children)}")
                
                for link in linked_children:
                    child = Student.query.get(link.student_id)
                    if child:
                        child_marks = Mark.query.filter_by(student_id=child.id).count()
                        print(f"   - {child.full_name} (ID: {child.id}): {child_marks} marks")
            else:
                print("\n❌ No Kevin parent found in database")
                # Show available parents
                all_parents = Parent.query.limit(5).all()
                print("🔍 Available parents:")
                for p in all_parents:
                    print(f"   - {p.username}: {p.full_name}")
            
        except Exception as e:
            print(f"❌ Error querying database: {str(e)}")
            
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()