"""
Services package for the Hillview School Management System.
This file imports and exposes service functions for easy access.
"""
from .auth_service import authenticate_teacher, get_teacher_by_id, is_authenticated, get_role, logout
from .report_service import get_class_report_data, generate_individual_report, generate_class_report_pdf
from .student_service import (
    get_students_by_stream, get_student_by_id, get_student_by_admission_number,
    add_student, update_student, delete_student
)
from .permission_service import PermissionService, check_class_access_permission
from .role_based_data_service import RoleBasedDataService
from .flexible_subject_service import FlexibleSubjectService
from .student_promotion_service import StudentPromotionService