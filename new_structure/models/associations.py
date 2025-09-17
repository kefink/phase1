"""
Association tables shared across models to avoid circular imports.
"""
from new_structure.extensions import db

# Many-to-many relationship between Teacher and Subject
# Use extend_existing=True to be resilient to module reloads during tests that
# purge and re-import the package while keeping the same SQLAlchemy metadata instance.
teacher_subjects = db.Table(
    'teacher_subjects',
    db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True),
    extend_existing=True,
)

__all__ = [
    'teacher_subjects',
]
