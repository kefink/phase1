"""
User-related models for the Hillview School Management System.
"""
from ..extensions import db

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

    # Enhanced teacher information
    full_name = db.Column(db.String(200), nullable=True)  # Full display name
    employee_id = db.Column(db.String(50), nullable=True, unique=True)  # Staff ID
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    qualification = db.Column(db.String(200), nullable=True)  # e.g., "B.Ed Mathematics"
    specialization = db.Column(db.String(200), nullable=True)  # e.g., "Primary Education"
    is_active = db.Column(db.Boolean, default=True)  # Whether teacher is currently active
    date_joined = db.Column(db.Date, nullable=True)

    # Relationships
    stream = db.relationship('Stream', backref=db.backref('teachers', lazy=True))
    subjects = db.relationship('Subject', secondary=teacher_subjects, back_populates='teachers')