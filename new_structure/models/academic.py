"""
Academic-related models for the Hillview School Management System.
"""
from ..extensions import db
from .user import teacher_subjects

class SchoolConfiguration(db.Model):
    """Model for storing school-specific configuration settings."""
    __tablename__ = 'school_configuration'
    id = db.Column(db.Integer, primary_key=True)

    # School Identity
    school_name = db.Column(db.String(200), nullable=False, default="School Name")
    school_motto = db.Column(db.String(500), nullable=True)
    school_address = db.Column(db.Text, nullable=True)
    school_phone = db.Column(db.String(50), nullable=True)
    school_email = db.Column(db.String(100), nullable=True)
    school_website = db.Column(db.String(100), nullable=True)

    # Academic Configuration
    current_academic_year = db.Column(db.String(20), nullable=False, default="2024")
    current_term = db.Column(db.String(50), nullable=False, default="Term 1")

    # System Configuration
    use_streams = db.Column(db.Boolean, default=True)  # Whether school uses streams/classes
    grading_system = db.Column(db.String(20), default="CBC")  # CBC, 8-4-4, etc.

    # Report Configuration
    show_position = db.Column(db.Boolean, default=True)
    show_class_average = db.Column(db.Boolean, default=True)
    show_subject_teacher = db.Column(db.Boolean, default=False)

    # Logo and Branding
    logo_filename = db.Column(db.String(100), nullable=True)
    primary_color = db.Column(db.String(7), default="#1f7d53")  # Hex color
    secondary_color = db.Column(db.String(7), default="#18230f")  # Hex color

    # Contact Information
    headteacher_name = db.Column(db.String(100), nullable=True)
    deputy_headteacher_name = db.Column(db.String(100), nullable=True)

    # Dynamic Staff Assignment IDs (references to Teacher table)
    headteacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    deputy_headteacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)

    # Relationships for dynamic staff assignment
    headteacher = db.relationship('Teacher', foreign_keys=[headteacher_id],
                                 backref='headteacher_schools')
    deputy_headteacher = db.relationship('Teacher', foreign_keys=[deputy_headteacher_id],
                                        backref='deputy_headteacher_schools')



    # Assessment Configuration
    max_raw_marks_default = db.Column(db.Integer, default=100)
    pass_mark_percentage = db.Column(db.Float, default=50.0)

    # Created and updated timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    @classmethod
    def get_config(cls):
        """Get the school configuration, creating default if none exists."""
        config = cls.query.first()
        if not config:
            config = cls()
            db.session.add(config)
            db.session.commit()
        return config

    def update_config(self, **kwargs):
        """Update configuration with provided values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

class Subject(db.Model):
    """Subject model representing courses taught in the school."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    education_level = db.Column(db.String(50), nullable=False)
    is_composite = db.Column(db.Boolean, default=False)  # Whether this subject has components
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
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
    name = db.Column(db.String(50), nullable=False, unique=True)  # e.g., Grade 1, Grade 2
    education_level = db.Column(db.String(50), nullable=False)  # e.g., lower_primary, upper_primary
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
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    marks = db.relationship('Mark', backref='term', lazy=True)

class AssessmentType(db.Model):
    """AssessmentType model representing types of assessments."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # e.g., Mid Term, End Term
    weight = db.Column(db.Float, nullable=True)  # Percentage weight in final grade calculation (0-100)
    category = db.Column(db.String(50), nullable=True)  # Category of assessment (e.g., "Exams", "Projects")
    is_active = db.Column(db.Boolean, default=True)  # Whether this assessment type is active
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    marks = db.relationship('Mark', backref='assessment_type', lazy=True)

class Student(db.Model):
    """Student model representing learners in the school."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    admission_number = db.Column(db.String(50), nullable=False, unique=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=True)
    gender = db.Column(db.String(10), nullable=False, default="Unknown")
    marks = db.relationship('Mark', backref='student', lazy=True)

class Mark(db.Model):
    """Mark model representing student grades for subjects."""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)
    assessment_type_id = db.Column(db.Integer, db.ForeignKey('assessment_type.id'), nullable=False)
    # Match actual database structure
    mark = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    raw_mark = db.Column(db.Float, nullable=False)
    raw_total_marks = db.Column(db.Float, nullable=False)  # Match database column name
    percentage = db.Column(db.Float, nullable=False)
    grade_letter = db.Column(db.String(5), nullable=True)  # Match database column
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # Relationship with component marks
    component_marks = db.relationship('ComponentMark', backref='mark', lazy=True)

    # Backward compatibility property
    @property
    def max_raw_mark(self):
        """Backward compatibility property for max_raw_mark."""
        return self.raw_total_marks

    @max_raw_mark.setter
    def max_raw_mark(self, value):
        """Backward compatibility setter for max_raw_mark."""
        self.raw_total_marks = value

    def __init__(self, **kwargs):
        """Initialize a Mark instance with validation."""
        # Sanitize raw_mark and max_raw_mark before setting
        from ..services.mark_conversion_service import MarkConversionService

        # Get values from kwargs - handle both old and new column names
        raw_mark = kwargs.get('raw_mark', 0)
        max_raw_mark = kwargs.get('max_raw_mark', kwargs.get('raw_total_marks', 100))

        # Sanitize values
        sanitized_raw_mark, sanitized_max_raw_mark = MarkConversionService.sanitize_raw_mark(raw_mark, max_raw_mark)

        # Update kwargs with sanitized values for both old and new column names
        kwargs['raw_mark'] = sanitized_raw_mark
        kwargs['raw_total_marks'] = sanitized_max_raw_mark  # New database column name
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
                # Calculate percentage from raw mark and max raw mark
                component_percentage = (component_mark.raw_mark / component_mark.max_raw_mark) * 100 if component_mark.max_raw_mark > 0 else 0
                # Cap at 100%
                component_percentage = min(component_percentage, 100)
                total_weighted_percentage += component_percentage * component.weight
                total_weight += component.weight

        if total_weight > 0:
            # Update the overall mark with the weighted percentage
            self.percentage = total_weighted_percentage / total_weight

            # Calculate raw mark based on percentage (for backward compatibility)
            self.raw_mark = (self.percentage / 100) * self.raw_total_marks
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

        # Get values from data - handle both old and new column names
        raw_mark = data.get('raw_mark', 0)
        max_raw_mark = data.get('max_raw_mark', data.get('raw_total_marks', 100))

        # Sanitize values
        sanitized_raw_mark, sanitized_max_raw_mark = MarkConversionService.sanitize_raw_mark(raw_mark, max_raw_mark)

        # Update data with sanitized values for both old and new column names
        data['raw_mark'] = sanitized_raw_mark
        data['raw_total_marks'] = sanitized_max_raw_mark  # New database column name
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
    __tablename__ = 'subject_component'  # Explicitly set the table name
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
    __tablename__ = 'component_mark'  # Explicitly set the table name
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


class SubjectMarksStatus(db.Model):
    """Track the status of marks upload for each subject in a class."""
    __tablename__ = 'subject_marks_status'

    id = db.Column(db.Integer, primary_key=True)
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)
    assessment_type_id = db.Column(db.Integer, db.ForeignKey('assessment_type.id'), nullable=False)

    # Status tracking
    is_uploaded = db.Column(db.Boolean, default=False)
    uploaded_by_teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    upload_date = db.Column(db.DateTime, nullable=True)
    last_modified = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Statistics
    total_students = db.Column(db.Integer, default=0)
    students_with_marks = db.Column(db.Integer, default=0)
    completion_percentage = db.Column(db.Float, default=0.0)

    # Relationships
    grade = db.relationship('Grade')
    stream = db.relationship('Stream')
    subject = db.relationship('Subject')
    term = db.relationship('Term')
    assessment_type = db.relationship('AssessmentType')
    uploaded_by = db.relationship('Teacher')

    def __repr__(self):
        return f"<SubjectMarksStatus {self.subject.name if self.subject else 'Unknown'} - Grade {self.grade.name if self.grade else 'Unknown'} - {'Complete' if self.is_uploaded else 'Pending'}>"

    @staticmethod
    def update_status(grade_id, stream_id, subject_id, term_id, assessment_type_id, teacher_id=None):
        """Update the marks upload status for a subject."""
        try:
            # Find or create status record
            status = SubjectMarksStatus.query.filter_by(
                grade_id=grade_id,
                stream_id=stream_id,
                subject_id=subject_id,
                term_id=term_id,
                assessment_type_id=assessment_type_id
            ).first()

            if not status:
                status = SubjectMarksStatus(
                    grade_id=grade_id,
                    stream_id=stream_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    assessment_type_id=assessment_type_id
                )
                db.session.add(status)

            # Count students and marks
            from ..models.user import Student
            total_students = Student.query.filter_by(stream_id=stream_id).count()

            students_with_marks = Mark.query.join(Student).filter(
                Student.stream_id == stream_id,
                Mark.subject_id == subject_id,
                Mark.term_id == term_id,
                Mark.assessment_type_id == assessment_type_id
            ).count()

            # Update status
            status.total_students = total_students
            status.students_with_marks = students_with_marks
            status.completion_percentage = (students_with_marks / total_students * 100) if total_students > 0 else 0
            status.is_uploaded = students_with_marks >= total_students and total_students > 0

            if teacher_id and status.is_uploaded:
                status.uploaded_by_teacher_id = teacher_id
                status.upload_date = db.func.current_timestamp()

            db.session.commit()
            return status

        except Exception as e:
            print(f"Error updating subject marks status: {str(e)}")
            db.session.rollback()
            return None