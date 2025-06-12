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

    @property
    def full_name(self):
        """Get the full name of the teacher."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username