#!/usr/bin/env python3
"""
Script to check and fix Kevin's class teacher assignments.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

# Import Flask app and database
import importlib.util
import sys

# Load the app module
spec = importlib.util.spec_from_file_location("app", "__init__.py")
app_module = importlib.util.module_from_spec(spec)
sys.modules["app"] = app_module
spec.loader.exec_module(app_module)

from extensions import db
from models import Teacher, Grade, Stream, Subject
from models.assignment import TeacherSubjectAssignment
from sqlalchemy import and_

def check_kevin_assignments():
    """Check Kevin's current assignments and database status."""
    print("🔍 Checking Kevin's Class Teacher Assignments")
    print("=" * 50)
    
    try:
        # Find Kevin
        kevin = Teacher.query.filter_by(username='kevin').first()
        if not kevin:
            print("❌ Kevin not found in teachers table!")
            return False
            
        print(f"✅ Kevin found:")
        print(f"   - ID: {kevin.id}")
        print(f"   - Username: {kevin.username}")
        print(f"   - Role: {kevin.role}")
        print(f"   - Stream ID: {kevin.stream_id}")
        
        # Check his subject assignments
        assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=kevin.id).all()
        print(f"\n📚 Kevin has {len(assignments)} subject assignments:")
        
        class_teacher_assignments = []
        
        for i, assignment in enumerate(assignments, 1):
            grade = Grade.query.get(assignment.grade_id) if assignment.grade_id else None
            stream = Stream.query.get(assignment.stream_id) if assignment.stream_id else None
            subject = Subject.query.get(assignment.subject_id) if assignment.subject_id else None
            
            grade_name = grade.name if grade else "Unknown"
            stream_name = stream.name if stream else "Unknown"
            subject_name = subject.name if subject else "Unknown"
            is_class_teacher = assignment.is_class_teacher
            
            print(f"   {i}. Subject: {subject_name}")
            print(f"      Grade: {grade_name}")
            print(f"      Stream: {stream_name}")
            print(f"      Class Teacher: {'✅ YES' if is_class_teacher else '❌ NO'}")
            print()
            
            if is_class_teacher:
                class_teacher_assignments.append({
                    'grade': grade_name,
                    'stream': stream_name,
                    'subject': subject_name
                })
        
        if class_teacher_assignments:
            print(f"🎯 Kevin is class teacher for:")
            for ct in class_teacher_assignments:
                print(f"   - Grade {ct['grade']} Stream {ct['stream']} ({ct['subject']})")
        else:
            print("⚠️  Kevin is NOT assigned as class teacher for any class!")
        
        # Show available grades and streams
        print(f"\n🏫 Available grades:")
        grades = Grade.query.all()
        for grade in grades:
            print(f"   - {grade.name} (ID: {grade.id})")
            
        print(f"\n📋 Available streams:")
        streams = Stream.query.all()
        for stream in streams:
            grade = Grade.query.get(stream.grade_id) if stream.grade_id else None
            grade_name = grade.name if grade else "Unknown"
            print(f"   - Stream {stream.name} (ID: {stream.id}) - Grade: {grade_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking assignments: {e}")
        return False

def fix_kevin_assignment():
    """Fix Kevin's class teacher assignment for Grade 9 Stream B."""
    print("\n🔧 Fixing Kevin's Class Teacher Assignment")
    print("=" * 50)
    
    try:
        # Find Kevin
        kevin = Teacher.query.filter_by(username='kevin').first()
        if not kevin:
            print("❌ Kevin not found!")
            return False
        
        # Find Grade 9
        grade_9 = Grade.query.filter_by(name='Grade 9').first()
        if not grade_9:
            print("❌ Grade 9 not found!")
            return False
        
        # Find Stream B
        stream_b = Stream.query.filter_by(name='B', grade_id=grade_9.id).first()
        if not stream_b:
            print("❌ Stream B for Grade 9 not found!")
            return False
        
        print(f"✅ Found: Kevin (ID: {kevin.id}), Grade 9 (ID: {grade_9.id}), Stream B (ID: {stream_b.id})")
        
        # Check if Kevin has any assignments for Grade 9 Stream B
        existing_assignments = TeacherSubjectAssignment.query.filter(
            and_(
                TeacherSubjectAssignment.teacher_id == kevin.id,
                TeacherSubjectAssignment.grade_id == grade_9.id,
                TeacherSubjectAssignment.stream_id == stream_b.id
            )
        ).all()
        
        print(f"📚 Kevin has {len(existing_assignments)} existing assignments for Grade 9 Stream B")
        
        if existing_assignments:
            # Mark the first assignment as class teacher
            assignment = existing_assignments[0]
            assignment.is_class_teacher = True
            
            subject = Subject.query.get(assignment.subject_id)
            subject_name = subject.name if subject else "Unknown"
            
            print(f"✅ Marked Kevin's {subject_name} assignment as class teacher")
        else:
            # Create a new assignment for Kevin as class teacher
            # Get Mathematics subject
            math_subject = Subject.query.filter_by(name='MATHEMATICS').first()
            if not math_subject:
                # Try alternative names
                math_subject = Subject.query.filter(Subject.name.ilike('%math%')).first()
            if not math_subject:
                # Get any subject
                math_subject = Subject.query.first()
            
            if math_subject:
                new_assignment = TeacherSubjectAssignment(
                    teacher_id=kevin.id,
                    subject_id=math_subject.id,
                    grade_id=grade_9.id,
                    stream_id=stream_b.id,
                    is_class_teacher=True
                )
                db.session.add(new_assignment)
                print(f"✅ Created new class teacher assignment for Kevin: {math_subject.name}")
            else:
                print("❌ No subjects found in database!")
                return False
        
        # Remove class teacher flag from other teachers for Grade 9 Stream B
        other_assignments = TeacherSubjectAssignment.query.filter(
            and_(
                TeacherSubjectAssignment.teacher_id != kevin.id,
                TeacherSubjectAssignment.grade_id == grade_9.id,
                TeacherSubjectAssignment.stream_id == stream_b.id,
                TeacherSubjectAssignment.is_class_teacher == True
            )
        ).all()
        
        for assignment in other_assignments:
            assignment.is_class_teacher = False
            teacher = Teacher.query.get(assignment.teacher_id)
            teacher_name = teacher.username if teacher else "Unknown"
            print(f"🔄 Removed class teacher flag from {teacher_name}")
        
        # Also set Kevin's stream_id directly on the teacher record
        kevin.stream_id = stream_b.id
        print(f"✅ Set Kevin's stream_id to {stream_b.id}")
        
        # Commit changes
        db.session.commit()
        print("✅ All changes committed to database!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing assignment: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    # Create app context
    app = app_module.create_app()
    with app.app_context():
        print("🚀 Starting Kevin Assignment Check and Fix")
        print("=" * 60)
        
        # Check current status
        if check_kevin_assignments():
            # Fix assignments
            if fix_kevin_assignment():
                print("\n🎉 SUCCESS! Kevin's class teacher assignment has been fixed.")
                
                # Verify the fix
                print("\n🔍 Verifying the fix...")
                check_kevin_assignments()
            else:
                print("\n❌ Failed to fix Kevin's assignment.")
        else:
            print("\n❌ Failed to check Kevin's assignments.")
