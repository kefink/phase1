"""
Parent portal models for the Hillview School Management System.
"""
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Import db from extensions
try:
    from ..extensions import db
except ImportError:
    # Fallback for direct imports
    from extensions import db

class Parent(db.Model):
    """Parent model for parent portal authentication and information."""
    __tablename__ = 'parent'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # Account Status
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    # Notification Preferences
    email_notifications = db.Column(db.Boolean, default=True)
    notification_frequency = db.Column(db.String(20), default='immediate')  # immediate, daily, weekly
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Email verification
    verification_token = db.Column(db.String(100), nullable=True)
    verification_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Password reset
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    children = db.relationship('ParentStudent', back_populates='parent', lazy=True)
    email_logs = db.relationship('ParentEmailLog', back_populates='parent', lazy=True)
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def is_locked(self):
        """Check if account is locked due to failed login attempts."""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def lock_account(self):
        """Lock account for 30 minutes after failed login attempts."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def unlock_account(self):
        """Unlock account and reset failed login attempts."""
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def get_full_name(self):
        """Get parent's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Parent {self.email}>'


class ParentStudent(db.Model):
    """Association table linking parents to their children (students)."""
    __tablename__ = 'parent_student'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    
    # Relationship details
    relationship_type = db.Column(db.String(20), default='parent')  # parent, guardian, relative
    is_primary_contact = db.Column(db.Boolean, default=False)
    can_receive_reports = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)  # Admin who linked them
    
    # Relationships
    parent = db.relationship('Parent', back_populates='children')
    student = db.relationship('Student', backref='parent_links')
    linked_by = db.relationship('Teacher', backref='parent_student_links')
    
    # Unique constraint to prevent duplicate parent-student links
    __table_args__ = (db.UniqueConstraint('parent_id', 'student_id', name='unique_parent_student'),)
    
    def __repr__(self):
        return f'<ParentStudent parent_id={self.parent_id} student_id={self.student_id}>'


class ParentEmailLog(db.Model):
    """Log of all emails sent to parents."""
    __tablename__ = 'parent_email_log'

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)  # For result notifications

    # Email details
    email_type = db.Column(db.String(50), nullable=False)  # verification, reset, result_notification
    subject = db.Column(db.String(200), nullable=False)
    recipient_email = db.Column(db.String(120), nullable=False)

    # Status tracking
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed, bounced
    sent_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    # Content reference
    template_id = db.Column(db.Integer, db.ForeignKey('email_template.id'), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    parent = db.relationship('Parent', back_populates='email_logs')
    student = db.relationship('Student', backref='parent_emails')
    template = db.relationship('EmailTemplate', backref='email_logs')

    def __repr__(self):
        return f'<ParentEmailLog {self.email_type} to {self.recipient_email}>'


class EmailTemplate(db.Model):
    """Customizable email templates for parent notifications."""
    __tablename__ = 'email_template'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    template_type = db.Column(db.String(50), nullable=False)  # verification, reset, result_notification

    # Template content
    subject_template = db.Column(db.String(200), nullable=False)
    html_template = db.Column(db.Text, nullable=False)
    text_template = db.Column(db.Text, nullable=True)  # Plain text version

    # Template variables documentation
    available_variables = db.Column(db.Text, nullable=True)  # JSON string of available variables

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)

    # Relationships
    creator = db.relationship('Teacher', backref='email_templates')

    def __repr__(self):
        return f'<EmailTemplate {self.name}>'
