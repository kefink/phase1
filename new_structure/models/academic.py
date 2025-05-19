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
    is_standard = db.Column(db.Boolean, default=True)  # Whether this is a standard subject
    is_composite = db.Column(db.Boolean, default=False)  # Whether this subject has components
    marks = db.relationship('Mark', backref='subject', lazy=True)
    teachers = db.relationship('Teacher', secondary=teacher_subjects, back_populates='subjects')
    components = db.relationship('SubjectComponent', backref='subject', lazy=True)

    def get_components(self):
        """Get the components of this subject if it's composite."""
        if not self.is_composite:
            return []
        return SubjectComponent.query.filter_by(subject_id=self.id).all()

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
    academic_year = db.Column(db.String(20), nullable=True)  # e.g., 2023, 2024
    is_current = db.Column(db.Boolean, default=False)  # Whether this is the current active term
    start_date = db.Column(db.Date, nullable=True)  # Start date of the term
    end_date = db.Column(db.Date, nullable=True)  # End date of the term
    marks = db.relationship('Mark', backref='term', lazy=True)

class AssessmentType(db.Model):
    """AssessmentType model representing types of assessments."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # e.g., Mid Term, End Term
    weight = db.Column(db.Integer, nullable=True)  # Percentage weight in final grade calculation (0-100)
    group = db.Column(db.String(50), nullable=True)  # Group related assessments (e.g., "Exams", "Projects")
    show_on_reports = db.Column(db.Boolean, default=True)  # Whether to show this assessment type on reports
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
    # Keep both old and new column names during migration
    mark = db.Column(db.Float, nullable=False)  # Old column name
    total_marks = db.Column(db.Float, nullable=False)  # Old column name
    raw_mark = db.Column(db.Float, nullable=False)  # New column name
    max_raw_mark = db.Column(db.Float, nullable=False)  # New column name
    percentage = db.Column(db.Float, nullable=False)  # Always store the calculated percentage
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # Relationship with component marks
    component_marks = db.relationship('ComponentMark', backref='mark', lazy=True)

    def __init__(self, **kwargs):
        """Initialize a Mark instance with validation."""
        # Sanitize raw_mark and max_raw_mark before setting
        from ..services.mark_conversion_service import MarkConversionService

        # Get values from kwargs
        raw_mark = kwargs.get('raw_mark', 0)
        max_raw_mark = kwargs.get('max_raw_mark', 100)

        # Sanitize values
        sanitized_raw_mark, sanitized_max_raw_mark = MarkConversionService.sanitize_raw_mark(raw_mark, max_raw_mark)

        # Update kwargs with sanitized values
        kwargs['raw_mark'] = sanitized_raw_mark
        kwargs['max_raw_mark'] = sanitized_max_raw_mark
        kwargs['mark'] = sanitized_raw_mark  # Update old field name too
        kwargs['total_marks'] = sanitized_max_raw_mark  # Update old field name too

        # Calculate percentage if not provided
        if 'percentage' not in kwargs:
            kwargs['percentage'] = MarkConversionService.calculate_percentage(sanitized_raw_mark, sanitized_max_raw_mark)
        elif kwargs['percentage'] > 100:  # Ensure percentage doesn't exceed 100%
            kwargs['percentage'] = 100.0

        # Call parent constructor with sanitized values
        super(Mark, self).__init__(**kwargs)

    def get_component_marks(self):
        """Get the component marks for this mark if the subject is composite."""
        return ComponentMark.query.filter_by(mark_id=self.id).all()

    def calculate_from_components(self):
        """Calculate the overall mark from component marks for composite subjects."""
        from ..services.mark_conversion_service import MarkConversionService

        # Get the subject
        subject = Subject.query.get(self.subject_id)
        if not subject or not subject.is_composite:
            return

        # Get the components and their marks
        components = subject.get_components()
        component_marks = self.get_component_marks()

        if not components or not component_marks:
            return

        # Calculate weighted percentage
        total_weighted_percentage = 0
        total_weight = 0

        for component_mark in component_marks:
            component = next((c for c in components if c.id == component_mark.component_id), None)
            if component:
                total_weighted_percentage += component_mark.percentage * component.weight
                total_weight += component.weight

        if total_weight > 0:
            # Update the overall mark with the weighted percentage
            self.percentage = total_weighted_percentage / total_weight

            # Calculate raw mark based on percentage (for backward compatibility)
            self.raw_mark = (self.percentage / 100) * self.max_raw_mark
            self.mark = self.raw_mark  # Update old field name too

            # Save changes
            db.session.commit()

    @staticmethod
    def sanitize_mark_data(data):
        """
        Static method to sanitize mark data before it's used to create or update a Mark.

        Args:
            data (dict): Dictionary containing mark data

        Returns:
            dict: Sanitized mark data
        """
        from ..services.mark_conversion_service import MarkConversionService

        # Get values from data
        raw_mark = data.get('raw_mark', 0)
        max_raw_mark = data.get('max_raw_mark', 100)

        # Sanitize values
        sanitized_raw_mark, sanitized_max_raw_mark = MarkConversionService.sanitize_raw_mark(raw_mark, max_raw_mark)

        # Update data with sanitized values
        data['raw_mark'] = sanitized_raw_mark
        data['max_raw_mark'] = sanitized_max_raw_mark
        data['mark'] = sanitized_raw_mark  # Update old field name too
        data['total_marks'] = sanitized_max_raw_mark  # Update old field name too

        # Calculate percentage if not provided
        if 'percentage' not in data:
            data['percentage'] = MarkConversionService.calculate_percentage(sanitized_raw_mark, sanitized_max_raw_mark)
        elif data['percentage'] > 100:  # Ensure percentage doesn't exceed 100%
            data['percentage'] = 100.0

        return data


class SubjectComponent(db.Model):
    """Model for components of composite subjects like English (Grammar/Composition) and Kiswahili (Lugha/Insha)."""
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, default=1.0)  # Weight of this component in the subject (e.g., 0.6 for 60%)
    max_raw_mark = db.Column(db.Integer, default=100)  # Default maximum raw mark for this component
    component_marks = db.relationship('ComponentMark', backref='component', lazy=True)

    def __repr__(self):
        return f"<SubjectComponent {self.name} for Subject {self.subject_id}>"


class ComponentMark(db.Model):
    """Model for marks of individual components of composite subjects."""
    id = db.Column(db.Integer, primary_key=True)
    mark_id = db.Column(db.Integer, db.ForeignKey('mark.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('subject_component.id'), nullable=False)
    raw_mark = db.Column(db.Float, nullable=False)
    max_raw_mark = db.Column(db.Integer, default=100)
    percentage = db.Column(db.Float, nullable=False)

    def __init__(self, **kwargs):
        """Initialize a ComponentMark instance with validation."""
        from ..services.mark_conversion_service import MarkConversionService

        # Get values from kwargs
        raw_mark = kwargs.get('raw_mark', 0)
        max_raw_mark = kwargs.get('max_raw_mark', 100)

        # Sanitize values
        sanitized_raw_mark, sanitized_max_raw_mark = MarkConversionService.sanitize_raw_mark(raw_mark, max_raw_mark)

        # Update kwargs with sanitized values
        kwargs['raw_mark'] = sanitized_raw_mark
        kwargs['max_raw_mark'] = sanitized_max_raw_mark

        # Calculate percentage if not provided
        if 'percentage' not in kwargs:
            kwargs['percentage'] = MarkConversionService.calculate_percentage(sanitized_raw_mark, sanitized_max_raw_mark)
        elif kwargs['percentage'] > 100:  # Ensure percentage doesn't exceed 100%
            kwargs['percentage'] = 100.0

        # Call parent constructor with sanitized values
        super(ComponentMark, self).__init__(**kwargs)

    def __repr__(self):
        return f"<ComponentMark {self.raw_mark}/{self.max_raw_mark} for Component {self.component_id}>"