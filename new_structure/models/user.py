"""
User-related models for the Hillview School Management System.
"""
import hmac
from new_structure.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

# Define the many-to-many relationship table
teacher_subjects = db.Table('teacher_subjects',
    db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True)
)

class Teacher(db.Model):
    """Teacher model representing school staff members.

    The canonical hashed password is stored in the 'password' column.
    Legacy password_hash alias has been removed after migration cleanup.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    # Renamed hashed column (now canonical)
    password = db.Column(db.String(255), nullable=False)
    # Backwards compatibility alias property defined below
    role = db.Column(db.String(50), nullable=False)  # e.g., 'headteacher', 'teacher', 'classteacher'
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)

    # Personal Information
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)

    # Professional Information
    employee_id = db.Column(db.String(50), nullable=True, unique=True)
    qualification = db.Column(db.String(50), nullable=True)  # P1, DIPLOMA, DEGREE, MASTERS, PHD
    specialization = db.Column(db.String(100), nullable=True)  # Subject specialization
    date_joined = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    stream = db.relationship('Stream', backref=db.backref('teachers', lazy=True))
    subjects = db.relationship('Subject', secondary=teacher_subjects, back_populates='teachers')

    def set_password(self, password):
        """Set (and hash) the user's password using secure hashing only.

        Plain-text storage in the legacy `password` column is deprecated. We now
        mirror the hashed value into `password` simply to satisfy the NOT NULL
        constraint until the column is dropped in a future migration.
        """
        if not password:
            return
        hashed = generate_password_hash(str(password))
        self.password = hashed

    def check_password(self, password):
        """Validate password using the canonical hashed 'password' column."""
        if not password or not isinstance(password, str) or len(password) > 128:
            return False
        # Minimal injection style validation (defense in depth)
        try:
            from new_structure.security.sql_injection_protection import SQLInjectionProtection
            if not SQLInjectionProtection.validate_input(password, "password"):
                return False
        except ImportError:
            pass
        if not self.password:
            return False
        if self.password.startswith(('scrypt:', 'pbkdf2:')):
            return check_password_hash(self.password, password)
        return hmac.compare_digest(self.password, password)

    def is_password_hashed(self):
        """Return True if canonical password column stores a modern hash."""
        return bool(self.password and self.password.startswith(('scrypt:', 'pbkdf2:')))

    # Backwards compatibility attribute removed; refer only to 'password'.

    @property
    def full_name(self):
        """Get the full name of the teacher."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        if self.last_name:
            return self.last_name
        return self.username