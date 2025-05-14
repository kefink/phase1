"""
Assignment-related models for the Hillview School Management System.
"""
from ..extensions import db

class TeacherSubjectAssignment(db.Model):
    """Model representing the assignment of teachers to subjects for specific grades and streams."""
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)  # Optional for schools without streams
    is_class_teacher = db.Column(db.Boolean, default=False)  # Indicates if this teacher is the class teacher
    
    # Relationships
    teacher = db.relationship('Teacher', backref=db.backref('subject_assignments', lazy=True, cascade='all, delete-orphan'))
    subject = db.relationship('Subject')
    grade = db.relationship('Grade')
    stream = db.relationship('Stream')
    
    def __repr__(self):
        return f"<TeacherSubjectAssignment {self.teacher.username} - {self.subject.name} - Grade {self.grade.level} - Stream {self.stream.name if self.stream else 'All'}>"
