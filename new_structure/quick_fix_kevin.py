#!/usr/bin/env python3
"""
Simple script to fix Kevin's class teacher assignment using the existing service.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def fix_kevin_via_service():
    """Use the existing StaffAssignmentService to fix Kevin's assignment."""
    try:
        from services.staff_assignment_service import StaffAssignmentService
        
        print("🔧 Calling StaffAssignmentService.fix_kevin_class_teacher_assignment()")
        success = StaffAssignmentService.fix_kevin_class_teacher_assignment()
        
        if success:
            print("✅ Kevin's class teacher assignment fixed successfully!")
        else:
            print("❌ Failed to fix Kevin's assignment")
            
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    fix_kevin_via_service()
