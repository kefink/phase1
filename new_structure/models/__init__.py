"""
Models package for the Hillview School Management System.
This file imports and exposes all models for easy access.
"""
from .user import Teacher, teacher_subjects
from .academic import (
    SchoolConfiguration, Subject, Grade, Stream, Term,
    AssessmentType, Student, Mark
)
from .assignment import TeacherSubjectAssignment
from .report_config import ReportConfiguration, ClassReportConfiguration, ReportTemplate
from .school_setup import SchoolSetup, SchoolBranding, SchoolCustomization
from .permission import ClassTeacherPermission, PermissionRequest
from .function_permission import FunctionPermission, DefaultFunctionPermissions