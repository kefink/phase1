"""
User-related models for the Hillview School Management System.
"""
import hmac
from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

# Define the many-to-many relationship table
teacher_subjects = db.Table('teacher_subjects',
    db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True)
)

class Teacher(db.Model):
    """Teacher model representing school staff members."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
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
        """Set password hash."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash."""
        # Input validation to prevent SQL injection
        if not password or not isinstance(password, str):
            return False

        # Sanitize password input to prevent injection attacks
        if len(password) > 128:  # Reasonable password length limit
            return False

        # Check for SQL injection patterns in password
        try:
            from ..security.sql_injection_protection import SQLInjectionProtection
            if not SQLInjectionProtection.validate_input(password, "password"):
                return False
        except ImportError:
            # Fallback validation if security module not available
            dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'DROP', 'SELECT', 'INSERT', 'UPDATE', 'DELETE']
            if any(char.upper() in password.upper() for char in dangerous_chars):
                return False

        # Handle both hashed and plain text passwords for backward compatibility
        if self.password.startswith('scrypt:') or self.password.startswith('pbkdf2:'):
            # This is a hashed password
            return check_password_hash(self.password, password)

        # This is a plain text password (legacy) - secure comparison
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(self.password, password)

    def is_password_hashed(self):
        """Check if password is hashed."""
        return self.password.startswith('scrypt:') or self.password.startswith('pbkdf2:')

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