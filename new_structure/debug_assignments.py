#!/usr/bin/env python3
"""
Debug script to check Carol's subject assignments
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from new_structure import create_app
from new_structure.services.role_based_data_service import RoleBasedDataService
from new_structure.models.assignment import TeacherSubjectAssignment
from new_structure.models.user import Teacher

def debug_carol_assignments():
    app = create_app('development')
    with app.app_context():
        print("=== DEBUGGING CAROL'S ASSIGNMENTS ===")
        
        # Check Carol's teacher record
        carol = Teacher.query.filter_by(username='carol').first()
        if carol:
            print(f"✅ Carol found: ID={carol.id}, Role={carol.role}")
        else:
            print("❌ Carol not found in database")
            return
        
        # Check raw assignments in database
        raw_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=carol.id).all()
        print(f"\n📊 Raw assignments for Carol (ID={carol.id}): {len(raw_assignments)}")
        for assignment in raw_assignments:
            subject_name = assignment.subject.name if assignment.subject else 'Unknown Subject'
            grade_name = assignment.grade.name if assignment.grade else 'Unknown Grade'
            stream_name = assignment.stream.name if assignment.stream else 'All Streams'
            print(f"  - {subject_name} for {grade_name} Stream {stream_name}")
        
        # Test RoleBasedDataService
        print(f"\n🔍 Testing RoleBasedDataService for teacher_id={carol.id}, role='teacher'")
        assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(carol.id, 'teacher')
        
        print(f"📋 Assignment summary keys: {list(assignment_summary.keys())}")
        
        if 'error' in assignment_summary:
            print(f"❌ Error in assignment summary: {assignment_summary['error']}")
        else:
            print(f"✅ Assignment summary successful")
            print(f"   - Teacher: {assignment_summary.get('teacher')}")
            print(f"   - Role: {assignment_summary.get('role')}")
            print(f"   - Subject assignments count: {len(assignment_summary.get('subject_assignments', []))}")
            print(f"   - Class teacher assignments count: {len(assignment_summary.get('class_teacher_assignments', []))}")
            print(f"   - Total subjects taught: {assignment_summary.get('total_subjects_taught', 0)}")
            
            # Print subject assignments details
            subject_assignments = assignment_summary.get('subject_assignments', [])
            if subject_assignments:
                print(f"\n📖 Subject assignments details:")
                for i, assignment in enumerate(subject_assignments):
                    print(f"   {i+1}. {assignment}")
            else:
                print(f"\n❌ No subject assignments found")

if __name__ == "__main__":
    debug_carol_assignments()
