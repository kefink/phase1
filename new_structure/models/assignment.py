"""
Assignment-related models for the Hillview School Management System.
"""
from new_structure.extensions import db

class TeacherSubjectAssignment(db.Model):
    """Model representing the assignment of teachers to subjects for specific grades and streams."""
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)  # Optional for schools without streams
    is_class_teacher = db.Column(db.Boolean, default=False)  # Indicates if this teacher is the class teacher

    # Relationships
    teacher = db.relationship(lambda: __import__('new_structure.models.user', fromlist=['Teacher']).Teacher, backref=db.backref('subject_assignments', lazy=True, cascade='all, delete-orphan'))
    subject = db.relationship(lambda: __import__('new_structure.models.academic', fromlist=['Subject']).Subject)
    grade = db.relationship(lambda: __import__('new_structure.models.academic', fromlist=['Grade']).Grade)
    stream = db.relationship(lambda: __import__('new_structure.models.academic', fromlist=['Stream']).Stream)

    def __repr__(self):
        teacher_name = self.teacher.username if self.teacher else f"Teacher ID {self.teacher_id}"
        subject_name = self.subject.name if self.subject else f"Subject ID {self.subject_id}"
        grade_level = self.grade.name if self.grade else f"Grade ID {self.grade_id}"
        stream_name = self.stream.name if self.stream else "All"
        return f"<TeacherSubjectAssignment {teacher_name} - {subject_name} - Grade {grade_level} - Stream {stream_name}>"
