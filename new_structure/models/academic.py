"""
Academic-related models for the Hillview School Management System.
"""
from ..extensions import db
from .user import teacher_subjects

class Subject(db.Model):
    """Subject model representing courses taught in the school."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    education_level = db.Column(db.String(50), nullable=False)
    marks = db.relationship('Mark', backref='subject', lazy=True)
    teachers = db.relationship('Teacher', secondary=teacher_subjects, back_populates='subjects')

class Grade(db.Model):
    """Grade model representing grade levels in the school."""
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(50), nullable=False, unique=True)  # e.g., Grade 1, Grade 2
    streams = db.relationship('Stream', backref='grade', lazy=True)

class Stream(db.Model):
    """Stream model representing class streams within a grade."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)  # e.g., A, B, C
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)
    students = db.relationship('Student', backref='stream', lazy=True)

class Term(db.Model):
    """Term model representing school terms."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # e.g., Term 1, Term 2
    marks = db.relationship('Mark', backref='term', lazy=True)

class AssessmentType(db.Model):
    """AssessmentType model representing types of assessments."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # e.g., Mid Term, End Term
    marks = db.relationship('Mark', backref='assessment_type', lazy=True)

class Student(db.Model):
    """Student model representing learners in the school."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    admission_number = db.Column(db.String(50), nullable=False, unique=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)
    gender = db.Column(db.String(10), nullable=False, default="Unknown")
    marks = db.relationship('Mark', backref='student', lazy=True)

class Mark(db.Model):
    """Mark model representing student grades for subjects."""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)
    assessment_type_id = db.Column(db.Integer, db.ForeignKey('assessment_type.id'), nullable=False)
    mark = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())