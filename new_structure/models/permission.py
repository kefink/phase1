"""
Permission management models for the Hillview School Management System.
Implements delegation-based permission system where headteacher grants permissions to classteachers.
"""
from ..extensions import db
from datetime import datetime

class ClassTeacherPermission(db.Model):
    """
    Model to track permissions granted by headteacher to classteachers for specific classes/streams.
    Handles both single classes and multi-stream scenarios.
    """
    __tablename__ = 'class_teacher_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Teacher receiving the permission
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    
    # Class/Stream assignment
    grade_id = db.Column(db.Integer, nullable=True)  # Temporarily remove FK constraint
    stream_id = db.Column(db.Integer, nullable=True)  # Temporarily remove FK constraint
    
    # Permission management
    granted_by = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)  # Headteacher ID
    granted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # New: Expiration functionality
    expires_at = db.Column(db.DateTime, nullable=True)  # Automatic expiration date
    is_permanent = db.Column(db.Boolean, default=False, nullable=False)  # Permanent permissions
    auto_granted = db.Column(db.Boolean, default=False, nullable=False)  # Direct grant vs request approval

    # Optional: Permission scope (future expansion)
    permission_scope = db.Column(db.String(50), default='full_class_admin')  # full_class_admin, marks_only, etc.

    # Notes/Comments
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships (temporarily commented out due to FK issues)
    teacher = db.relationship('Teacher', foreign_keys=[teacher_id], backref='class_permissions')
    granted_by_teacher = db.relationship('Teacher', foreign_keys=[granted_by])
    # grade = db.relationship('Grade', backref='permission_assignments')
    # stream = db.relationship('Stream', backref='permission_assignments')
    
    def __repr__(self):
        stream_info = f" Stream {self.stream.name}" if self.stream else ""
        return f'<ClassTeacherPermission {self.teacher.username} -> Grade {self.grade.name}{stream_info}>'

    @property
    def is_expired(self):
        """Check if permission has expired."""
        if self.is_permanent or not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def days_until_expiry(self):
        """Get days until expiration."""
        if self.is_permanent or not self.expires_at:
            return None
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    @property
    def status(self):
        """Get permission status."""
        if not self.is_active:
            return 'inactive'
        elif self.is_expired:
            return 'expired'
        elif self.is_permanent:
            return 'permanent'
        elif self.days_until_expiry is not None and self.days_until_expiry <= 7:
            return 'expiring_soon'
        else:
            return 'active'
    
    @classmethod
    def grant_permission(cls, teacher_id, grade_id, stream_id, granted_by_id, notes=None,
                        expires_at=None, is_permanent=False, auto_granted=True):
        """
        Grant permission to a teacher for a specific class/stream with expiration support.

        Args:
            teacher_id: ID of teacher receiving permission
            grade_id: ID of the grade
            stream_id: ID of the stream (None for single classes)
            granted_by_id: ID of headteacher granting permission
            notes: Optional notes about the permission
            expires_at: Optional expiration datetime
            is_permanent: Whether permission is permanent
            auto_granted: Whether this was directly granted (True) or approved from request (False)

        Returns:
            ClassTeacherPermission object if successful, None otherwise
        """
        try:
            # Check if permission already exists and is active
            existing = cls.query.filter_by(
                teacher_id=teacher_id,
                grade_id=grade_id,
                stream_id=stream_id,
                is_active=True
            ).first()
            
            if existing:
                return existing  # Permission already exists
            
            # Create new permission
            permission = cls(
                teacher_id=teacher_id,
                grade_id=grade_id,
                stream_id=stream_id,
                granted_by=granted_by_id,
                notes=notes,
                expires_at=expires_at,
                is_permanent=is_permanent,
                auto_granted=auto_granted
            )
            
            db.session.add(permission)
            db.session.commit()
            return permission
            
        except Exception as e:
            db.session.rollback()
            print(f"Error granting permission: {e}")
            return None
    
    @classmethod
    def revoke_permission(cls, teacher_id, grade_id, stream_id):
        """
        Revoke permission for a teacher from a specific class/stream.
        
        Args:
            teacher_id: ID of teacher losing permission
            grade_id: ID of the grade
            stream_id: ID of the stream (None for single classes)
            
        Returns:
            Boolean indicating success
        """
        try:
            permission = cls.query.filter_by(
                teacher_id=teacher_id,
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
            print(f"Error revoking permission: {e}")
            return False
    
    @classmethod
    def get_teacher_permissions(cls, teacher_id):
        """
        Get all active and non-expired permissions for a teacher.

        Args:
            teacher_id: ID of the teacher

        Returns:
            List of active ClassTeacherPermission objects
        """
        # First, expire any permissions that should be expired
        cls.expire_permissions()

        # Return active permissions
        return cls.query.filter_by(teacher_id=teacher_id, is_active=True).all()

    @classmethod
    def expire_permissions(cls):
        """
        Automatically expire permissions that have passed their expiration date.
        This method should be called periodically or before checking permissions.
        """
        try:
            current_time = datetime.utcnow()
            expired_permissions = cls.query.filter(
                cls.is_active == True,
                cls.is_permanent == False,
                cls.expires_at != None,
                cls.expires_at <= current_time
            ).all()

            for permission in expired_permissions:
                permission.is_active = False
                permission.revoked_at = current_time

            if expired_permissions:
                db.session.commit()
                print(f"Expired {len(expired_permissions)} permissions")

        except Exception as e:
            db.session.rollback()
            print(f"Error expiring permissions: {e}")
    
    @classmethod
    def has_permission(cls, teacher_id, grade_id, stream_id=None):
        """
        Check if a teacher has active, non-expired permission for a specific class/stream.

        Args:
            teacher_id: ID of the teacher
            grade_id: ID of the grade
            stream_id: ID of the stream (None for single classes)

        Returns:
            Boolean indicating if permission exists and is valid
        """
        # First, expire any permissions that should be expired
        cls.expire_permissions()

        permission = cls.query.filter_by(
            teacher_id=teacher_id,
            grade_id=grade_id,
            stream_id=stream_id,
            is_active=True
        ).first()

        return permission is not None and not permission.is_expired
    
    @classmethod
    def get_all_permissions_summary(cls):
        """
        Get a summary of all permissions for headteacher dashboard with expiration info.

        Returns:
            List of dictionaries with permission details
        """
        # First, expire any permissions that should be expired
        cls.expire_permissions()

        permissions = cls.query.filter_by(is_active=True).all()
        summary = []

        for perm in permissions:
            summary.append({
                'id': perm.id,
                'teacher_name': perm.teacher.full_name or perm.teacher.username,
                'teacher_id': perm.teacher_id,
                'grade_name': perm.grade.name,
                'grade_id': perm.grade_id,
                'stream_name': perm.stream.name if perm.stream else None,
                'stream_id': perm.stream_id,
                'granted_at': perm.granted_at,
                'granted_by_name': perm.granted_by_teacher.full_name or perm.granted_by_teacher.username,
                'notes': perm.notes,
                'expires_at': perm.expires_at,
                'is_permanent': perm.is_permanent,
                'auto_granted': perm.auto_granted,
                'status': perm.status,
                'days_until_expiry': perm.days_until_expiry,
                'is_expired': perm.is_expired
            })

        return summary

class PermissionRequest(db.Model):
    """
    Model for teachers to request permissions from headteacher.
    Optional feature for better workflow management.
    """
    __tablename__ = 'permission_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Request details
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=True)  # Allow null for function requests
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)
    
    # Request management
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    
    # Request justification
    reason = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    teacher = db.relationship('Teacher', foreign_keys=[teacher_id])
    processed_by_teacher = db.relationship('Teacher', foreign_keys=[processed_by])
    grade = db.relationship('Grade')
    stream = db.relationship('Stream')
    
    def __repr__(self):
        if self.grade:
            stream_info = f" Stream {self.stream.name}" if self.stream else ""
            return f'<PermissionRequest {self.teacher.username} -> Grade {self.grade.name}{stream_info} ({self.status})>'
        else:
            # Function permission request
            return f'<PermissionRequest {self.teacher.username} -> Function Request ({self.status})>'
