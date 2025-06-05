"""
Enhanced function-level permission system for granular access control.
Allows headteacher to grant specific function permissions to classteachers.
"""
from ..extensions import db
from datetime import datetime

class FunctionPermission(db.Model):
    """
    Model to track function-level permissions granted to classteachers.
    Provides granular control over what functions each teacher can access.
    """
    __tablename__ = 'function_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Teacher receiving the permission
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    
    # Function identification
    function_name = db.Column(db.String(100), nullable=False)  # e.g., 'manage_students'
    function_category = db.Column(db.String(50), nullable=False)  # e.g., 'student_management'
    
    # Permission scope
    scope_type = db.Column(db.String(20), default='global')  # global, grade, stream, class
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)
    
    # Permission management
    granted_by = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiration
    revoked_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Additional metadata
    notes = db.Column(db.Text, nullable=True)
    auto_granted = db.Column(db.Boolean, default=False)  # True for default permissions
    
    # Relationships
    teacher = db.relationship('Teacher', foreign_keys=[teacher_id])
    granted_by_teacher = db.relationship('Teacher', foreign_keys=[granted_by])
    grade = db.relationship('Grade')
    stream = db.relationship('Stream')
    
    def __repr__(self):
        scope = f" ({self.scope_type})" if self.scope_type != 'global' else ""
        return f"<FunctionPermission {self.teacher.username}: {self.function_name}{scope}>"
    
    @classmethod
    def grant_function_permission(cls, teacher_id, function_name, function_category, 
                                 granted_by_id, scope_type='global', grade_id=None, 
                                 stream_id=None, expires_at=None, notes=None, auto_granted=False):
        """
        Grant a specific function permission to a teacher.
        
        Args:
            teacher_id: ID of teacher receiving permission
            function_name: Name of the function (e.g., 'manage_students')
            function_category: Category of the function (e.g., 'student_management')
            granted_by_id: ID of headteacher granting permission
            scope_type: 'global', 'grade', 'stream', or 'class'
            grade_id: Grade ID for scoped permissions
            stream_id: Stream ID for scoped permissions
            expires_at: Optional expiration date
            notes: Optional notes
            auto_granted: Whether this was automatically granted
            
        Returns:
            FunctionPermission object if successful, None otherwise
        """
        try:
            # Check if permission already exists
            existing = cls.query.filter_by(
                teacher_id=teacher_id,
                function_name=function_name,
                scope_type=scope_type,
                grade_id=grade_id,
                stream_id=stream_id,
                is_active=True
            ).first()
            
            if existing:
                return existing
            
            # Create new permission
            permission = cls(
                teacher_id=teacher_id,
                function_name=function_name,
                function_category=function_category,
                granted_by=granted_by_id,
                scope_type=scope_type,
                grade_id=grade_id,
                stream_id=stream_id,
                expires_at=expires_at,
                notes=notes,
                auto_granted=auto_granted
            )
            
            db.session.add(permission)
            db.session.commit()
            return permission
            
        except Exception as e:
            db.session.rollback()
            print(f"Error granting function permission: {e}")
            return None
    
    @classmethod
    def revoke_function_permission(cls, teacher_id, function_name, scope_type='global', 
                                  grade_id=None, stream_id=None):
        """
        Revoke a specific function permission from a teacher.
        """
        try:
            permission = cls.query.filter_by(
                teacher_id=teacher_id,
                function_name=function_name,
                scope_type=scope_type,
                grade_id=grade_id,
                stream_id=stream_id,
                is_active=True
            ).first()
            
            if permission:
                permission.is_active = False
                permission.revoked_at = datetime.utcnow()
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            db.session.rollback()
            print(f"Error revoking function permission: {e}")
            return False
    
    @classmethod
    def has_function_permission(cls, teacher_id, function_name, grade_id=None, stream_id=None):
        """
        Check if a teacher has permission for a specific function.
        Checks in order: specific scope -> grade scope -> global scope
        """
        # Check for specific class/stream permission
        if grade_id and stream_id:
            specific_perm = cls.query.filter_by(
                teacher_id=teacher_id,
                function_name=function_name,
                scope_type='stream',
                grade_id=grade_id,
                stream_id=stream_id,
                is_active=True
            ).first()
            if specific_perm and not cls._is_expired(specific_perm):
                return True
        
        # Check for grade-level permission
        if grade_id:
            grade_perm = cls.query.filter_by(
                teacher_id=teacher_id,
                function_name=function_name,
                scope_type='grade',
                grade_id=grade_id,
                is_active=True
            ).first()
            if grade_perm and not cls._is_expired(grade_perm):
                return True
        
        # Check for global permission
        global_perm = cls.query.filter_by(
            teacher_id=teacher_id,
            function_name=function_name,
            scope_type='global',
            is_active=True
        ).first()
        if global_perm and not cls._is_expired(global_perm):
            return True
        
        return False
    
    @classmethod
    def _is_expired(cls, permission):
        """Check if a permission has expired."""
        if permission.expires_at:
            return datetime.utcnow() > permission.expires_at
        return False
    
    @classmethod
    def get_teacher_function_permissions(cls, teacher_id):
        """Get all active function permissions for a teacher."""
        permissions = cls.query.filter_by(teacher_id=teacher_id, is_active=True).all()
        return [p for p in permissions if not cls._is_expired(p)]
    
    @classmethod
    def get_all_function_permissions_summary(cls):
        """Get summary of all function permissions for admin dashboard."""
        permissions = cls.query.filter_by(is_active=True).all()
        summary = []
        
        for perm in permissions:
            if not cls._is_expired(perm):
                summary.append({
                    'id': perm.id,
                    'teacher_name': perm.teacher.full_name or perm.teacher.username,
                    'teacher_id': perm.teacher_id,
                    'function_name': perm.function_name,
                    'function_category': perm.function_category,
                    'scope_type': perm.scope_type,
                    'grade_name': perm.grade.name if perm.grade else None,
                    'stream_name': perm.stream.name if perm.stream else None,
                    'granted_at': perm.granted_at,
                    'expires_at': perm.expires_at,
                    'granted_by_name': perm.granted_by_teacher.full_name or perm.granted_by_teacher.username,
                    'notes': perm.notes,
                    'auto_granted': perm.auto_granted
                })
        
        return summary


class DefaultFunctionPermissions:
    """
    Defines default function permissions for classteachers.
    Only marks upload and report generation are allowed by default.
    """
    
    # Functions that classteachers can access by default (without explicit permission)
    DEFAULT_ALLOWED_FUNCTIONS = {
        'marks_management': [
            'dashboard',  # Main marks upload interface
            'download_marks_template',  # Download marks templates
            'edit_class_marks',  # Edit existing marks
            'update_class_marks',  # Update marks
            'upload_subject_marks',  # Upload subject-specific marks
            'submit_subject_marks',  # Submit subject marks
            'collaborative_marks_dashboard',  # Multi-teacher marks system
            'class_marks_status',  # Marks status tracking
            'get_streams_by_level',  # API to get streams for grade selection
            'get_subjects_by_education_level',  # API to get subjects by education level
            'api_check_stream_status',  # API to check stream status for reports
            'get_streams',  # API to get streams for a grade
            'get_grade_streams',  # API to get grade streams
            'teacher_streams',  # API to get teacher streams
            'api_get_streams',  # Alternative API to get streams
            'get_teacher_assignments',  # API to get teacher assignments
        ],
        'analytics': [
            'analytics_dashboard',  # Academic performance analytics dashboard
        ],
        'reports_management': [
            'preview_class_report',  # Preview class reports
            'download_class_report',  # Download class reports
            'generate_grade_marksheet',  # Generate marksheets
            'preview_grade_marksheet',  # Preview marksheets
            'download_grade_marksheet',  # Download marksheets
            'view_all_reports',  # Browse all reports
            'view_student_reports',  # Student report lists
            'preview_individual_report',  # Preview individual reports
            'print_individual_report',  # Print individual reports
            'download_individual_report',  # Download individual reports
            'generate_all_individual_reports',  # Generate ZIP of reports
            'grade_reports_dashboard',  # Grade analysis dashboard
            'grade_streams_status',  # Stream status tracking
            'generate_individual_stream_report',  # Stream reports
            'generate_consolidated_grade_report',  # Consolidated reports
            'generate_batch_grade_reports',  # Batch report generation
        ]
    }
    
    # Functions that require explicit permission from headteacher
    RESTRICTED_FUNCTIONS = {
        'student_management': [
            'manage_students',  # Student record management
            'download_student_template',  # Student templates
            'download_class_list',  # Class list exports
        ],
        'subject_management': [
            'manage_subjects',  # Subject configuration
            'download_subject_template',  # Subject templates
            'export_subjects',  # Subject exports
        ],
        'teacher_management': [
            'teacher_management_hub',  # Teacher management center
            'manage_teachers',  # Teacher records
            'manage_teacher_subjects',  # Teacher subject assignments
            'assign_subjects',  # Subject assignment
            'bulk_assign_subjects',  # Bulk subject assignment
            'enhanced_bulk_assign_subjects',  # Advanced bulk assignment
            'advanced_assignments',  # Advanced assignment management
            'remove_assignment',  # Remove assignments
            'manage_teacher_assignments',  # Teacher assignment management
            'reassign_class_teacher',  # Reassign class teachers
            'reassign_subject_teacher',  # Reassign subject teachers
            'bulk_transfer_assignments',  # Bulk transfers
        ],
        'system_configuration': [
            'manage_grades_streams',  # Grade and stream configuration
            'manage_terms_assessments',  # Terms and assessment management
        ],
        'advanced_marks': [
            'delete_marksheet',  # Delete marksheets (dangerous operation)
            'delete_report',  # Delete reports (dangerous operation)
        ]
    }
    
    @classmethod
    def is_default_allowed(cls, function_name):
        """Check if a function is allowed by default for classteachers."""
        for category, functions in cls.DEFAULT_ALLOWED_FUNCTIONS.items():
            if function_name in functions:
                return True
        return False
    
    @classmethod
    def is_restricted(cls, function_name):
        """Check if a function requires explicit permission."""
        for category, functions in cls.RESTRICTED_FUNCTIONS.items():
            if function_name in functions:
                return True
        return False
    
    @classmethod
    def get_function_category(cls, function_name):
        """Get the category of a function."""
        for category, functions in {**cls.DEFAULT_ALLOWED_FUNCTIONS, **cls.RESTRICTED_FUNCTIONS}.items():
            if function_name in functions:
                return category
        return 'unknown'

    @classmethod
    def is_management_function(cls, function_name):
        """Check if a function is a management function that should be allowed with class permissions."""
        management_categories = [
            'student_management',
            'subject_management',
            'system_configuration'
        ]

        for category in management_categories:
            if category in cls.RESTRICTED_FUNCTIONS:
                if function_name in cls.RESTRICTED_FUNCTIONS[category]:
                    return True
        return False
