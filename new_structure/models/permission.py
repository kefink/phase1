"""
Permission management models for the Hillview School Management System.
Implements delegation-based permission system where headteacher grants permissions to classteachers.
"""
from new_structure.extensions import db
from datetime import datetime
from sqlalchemy.exc import OperationalError

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
    
    # Permission type field (required by database but missing from original model)
    permission_type = db.Column(db.String(50), default='class_access', nullable=False)

    # Notes/Comments
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships (temporarily commented out due to FK issues)
    teacher = db.relationship(lambda: __import__('new_structure.models.user', fromlist=['Teacher']).Teacher, foreign_keys=[teacher_id], backref='class_permissions')
    granted_by_teacher = db.relationship(lambda: __import__('new_structure.models.user', fromlist=['Teacher']).Teacher, foreign_keys=[granted_by])
    # grade = db.relationship('Grade', backref='permission_assignments')
    # stream = db.relationship('Stream', backref='permission_assignments')
    
    def __repr__(self):
        try:
            teacher_name = None
            try:
                teacher_name = self.teacher.full_name or self.teacher.username
            except Exception:
                teacher_name = f"teacher_id={self.teacher_id}"
            # Resolve grade/stream names defensively to avoid dependency on relationships
            grade_name = None
            stream_name = None
            try:
                from .academic import Grade, Stream
                if self.grade_id:
                    g = Grade.query.get(self.grade_id)
                    grade_name = getattr(g, 'name', None)
                if self.stream_id:
                    s = Stream.query.get(self.stream_id)
                    stream_name = getattr(s, 'name', None)
            except Exception:
                pass
            stream_info = f" Stream {stream_name}" if stream_name else ""
            grade_part = grade_name or f"grade_id={self.grade_id}"
            return f'<ClassTeacherPermission {teacher_name} -> {grade_part}{stream_info}>'
        except Exception:
            return f'<ClassTeacherPermission id={self.id}>'

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
    def _ensure_revoked_at_column(cls):
        """Ensure the 'revoked_at' column exists on class_teacher_permissions.

        This is a runtime self-healing step for environments where the DB schema
        hasn't been migrated yet. It's safe to call repeatedly.
        """
        try:
            engine = db.engine
            table = cls.__tablename__
            from sqlalchemy import inspect
            insp = inspect(engine)
            try:
                cols = [c['name'].lower() for c in insp.get_columns(table)]
            except Exception:
                cols = []
            
            added = False
            
            # Check and add revoked_at column
            if 'revoked_at' not in cols:
                with engine.connect() as conn:
                    try:
                        conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN revoked_at DATETIME NULL")
                        added = True
                    except Exception:
                        try:
                            conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN revoked_at TIMESTAMP NULL")
                            added = True
                        except Exception:
                            pass
            
            # Check and add permission_type column
            if 'permission_type' not in cols:
                with engine.connect() as conn:
                    try:
                        conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN permission_type VARCHAR(50) DEFAULT 'class_access' NOT NULL")
                        added = True
                    except Exception:
                        try:
                            # Fallback without DEFAULT and NOT NULL
                            conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN permission_type VARCHAR(50) NULL")
                            added = True
                        except Exception:
                            pass
            
            # If we added columns, dispose engine to prevent MySQL 1412 errors
            if added:
                try:
                    engine.dispose()
                except Exception:
                    pass
                    
            return added
        except Exception:
            return False

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
            expires_at: Optional expiration datetime (defaults to 1 hour from now)
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
            
            # Set default 1-hour expiration if not specified and not permanent
            if expires_at is None and not is_permanent:
                from datetime import datetime, timedelta
                expires_at = datetime.utcnow() + timedelta(hours=1)
            
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
        try:
            cls._ensure_revoked_at_column()
        except Exception:
            pass
        return cls.query.filter_by(teacher_id=teacher_id, is_active=True).all()

    @classmethod
    def expire_permissions(cls):
        """
        Automatically expire permissions that have passed their expiration date.
        This method should be called periodically or before checking permissions.
        """
        try:
            try:
                cls._ensure_revoked_at_column()
            except Exception:
                pass
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
            # If the failure is due to missing column, attempt self-healing migration once
            try:
                msg = str(e)
                is_unknown_col = 'Unknown column' in msg and 'revoked_at' in msg
                if is_unknown_col or isinstance(e, OperationalError):
                    if cls._ensure_revoked_at_column():
                        # Retry once after creating the column
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
                                print(f"Expired {len(expired_permissions)} permissions (after migration)")
                            return
                        except Exception:
                            pass
            except Exception:
                pass
            # Fallback: don't block app flow
            try:
                db.session.rollback()
            except Exception:
                pass
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
        try:
            cls.expire_permissions()
        except Exception:
            # ignore
            pass

        try:
            try:
                cls._ensure_revoked_at_column()
            except Exception:
                pass
            permission = cls.query.filter_by(
                teacher_id=teacher_id,
                grade_id=grade_id,
                stream_id=stream_id,
                is_active=True
            ).first()
            return permission is not None and not permission.is_expired
        except Exception as e:
            # Attempt self-healing if missing column caused the failure
            msg = str(e)
            is_unknown_col = 'Unknown column' in msg and 'revoked_at' in msg
            if is_unknown_col or isinstance(e, OperationalError):
                if cls._ensure_revoked_at_column():
                    try:
                        permission = cls.query.filter_by(
                            teacher_id=teacher_id,
                            grade_id=grade_id,
                            stream_id=stream_id,
                            is_active=True
                        ).first()
                        return permission is not None and not permission.is_expired
                    except Exception:
                        pass
            return False
    
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

        # Resolve grade/stream names without relying on ORM relationships (robust to partial schemas)
        try:
            from .academic import Grade, Stream
        except Exception:
            Grade = Stream = None

        for perm in permissions:
            try:
                teacher_name = perm.teacher.full_name or perm.teacher.username
            except Exception:
                teacher_name = None
            try:
                granted_by_name = perm.granted_by_teacher.full_name or perm.granted_by_teacher.username
            except Exception:
                granted_by_name = None

            grade_name = None
            stream_name = None
            if Grade and perm.grade_id:
                try:
                    g = Grade.query.get(perm.grade_id)
                    grade_name = getattr(g, 'name', None)
                except Exception:
                    pass
            if Stream and perm.stream_id:
                try:
                    s = Stream.query.get(perm.stream_id)
                    stream_name = getattr(s, 'name', None)
                except Exception:
                    pass

            summary.append({
                'id': perm.id,
                'teacher_name': teacher_name,
                'teacher_id': perm.teacher_id,
                'grade_name': grade_name,
                'grade_id': perm.grade_id,
                'stream_name': stream_name,
                'stream_id': perm.stream_id,
                'granted_at': perm.granted_at,
                'granted_by_name': granted_by_name,
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
    
    # Permission type field (required by database but missing from original model)
    permission_type = db.Column(db.String(50), default='class_access', nullable=False)
    
    # Relationships
    teacher = db.relationship(lambda: __import__('new_structure.models.user', fromlist=['Teacher']).Teacher, foreign_keys=[teacher_id])
    processed_by_teacher = db.relationship(lambda: __import__('new_structure.models.user', fromlist=['Teacher']).Teacher, foreign_keys=[processed_by])
    grade = db.relationship(lambda: __import__('new_structure.models.academic', fromlist=['Grade']).Grade)
    stream = db.relationship(lambda: __import__('new_structure.models.academic', fromlist=['Stream']).Stream)
    
    def __repr__(self):
        if self.grade:
            stream_info = f" Stream {self.stream.name}" if self.stream else ""
            return f'<PermissionRequest {self.teacher.username} -> Grade {self.grade.name}{stream_info} ({self.status})>'
        else:
            # Function permission request
            return f'<PermissionRequest {self.teacher.username} -> Function Request ({self.status})>'

    # --- Runtime schema self-healing helpers ---------------------------------
    @classmethod
    def _ensure_column(cls, column: str, sql_type: str) -> bool:
        """Ensure a column exists on the permission_requests table.

        Returns True if altered (column added), False if already exists or on failure.
        Safe to call repeatedly.
        """
        try:
            engine = db.engine
            table = cls.__tablename__
            from sqlalchemy import inspect
            insp = inspect(engine)
            try:
                cols = [c['name'].lower() for c in insp.get_columns(table)]
            except Exception:
                cols = []
            if column.lower() in cols:
                return False
            with engine.connect() as conn:
                try:
                    # For columns with DEFAULT and constraints, use the full sql_type
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}")
                    return True
                except Exception as e:
                    # Fallback: try simpler syntax if the complex one fails
                    if 'DEFAULT' in sql_type.upper() or 'NOT NULL' in sql_type.upper():
                        try:
                            # Extract just the base type for fallback
                            base_type = sql_type.split()[0]
                            conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {base_type} NULL")
                            return True
                        except Exception:
                            pass
                    return False
        except Exception:
            return False

    @classmethod
    def ensure_core_columns(cls) -> None:
        """Best-effort creation of core columns used by the app logic.

        Specifically ensures minimal set required by current ORM mapping so SELECTs don't fail
        on partially-migrated databases. Adds columns if missing (idempotent, no FKs):
        - grade_id INT
        - stream_id INT
        - requested_at DATETIME
        - status VARCHAR(20)
        - processed_at DATETIME
        - processed_by INT
        - reason TEXT
        - admin_notes TEXT
        """
        try:
            from new_structure.extensions import db as _db
            added = False

            # INT type fits MySQL/SQLite generically
            added = cls._ensure_column('grade_id', 'INT') or added
            added = cls._ensure_column('stream_id', 'INT') or added

            # Timestamps and status fields
            # Try DATETIME; if the engine rejects, _ensure_column returns False and we ignore silently
            added = cls._ensure_column('requested_at', 'DATETIME') or added
            added = cls._ensure_column('status', 'VARCHAR(20)') or added
            added = cls._ensure_column('processed_at', 'DATETIME') or added
            added = cls._ensure_column('processed_by', 'INT') or added

            # Text fields
            added = cls._ensure_column('reason', 'TEXT') or added
            added = cls._ensure_column('admin_notes', 'TEXT') or added
            
            # Permission type field (required by database)
            added = cls._ensure_column('permission_type', 'VARCHAR(50) DEFAULT \'class_access\' NOT NULL') or added

            # If we altered the table, dispose engine connections to avoid MySQL 1412
            if added:
                try:
                    _db.engine.dispose()
                except Exception:
                    pass
        except Exception:
            # Never block on migration helper
            pass
