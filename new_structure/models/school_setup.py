"""
Enhanced School Setup and Configuration models for plug-and-play deployment.
"""

from ..extensions import db
from datetime import datetime
import json

class SchoolSetup(db.Model):
    """Enhanced school setup model for plug-and-play deployment."""
    __tablename__ = 'school_setup'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic School Information
    school_name = db.Column(db.String(200), nullable=False)
    school_motto = db.Column(db.String(500), nullable=True)
    school_vision = db.Column(db.Text, nullable=True)
    school_mission = db.Column(db.Text, nullable=True)
    
    # Contact Information
    school_address = db.Column(db.Text, nullable=True)
    postal_address = db.Column(db.String(200), nullable=True)
    school_phone = db.Column(db.String(50), nullable=True)
    school_mobile = db.Column(db.String(50), nullable=True)
    school_email = db.Column(db.String(100), nullable=True)
    school_website = db.Column(db.String(100), nullable=True)
    
    # Registration and Legal Information
    registration_number = db.Column(db.String(100), nullable=True)
    ministry_code = db.Column(db.String(50), nullable=True)
    county = db.Column(db.String(100), nullable=True)
    sub_county = db.Column(db.String(100), nullable=True)
    ward = db.Column(db.String(100), nullable=True)
    constituency = db.Column(db.String(100), nullable=True)
    
    # School Type and Category
    school_type = db.Column(db.String(50), nullable=True)  # Public, Private, Faith-based
    school_category = db.Column(db.String(50), nullable=True)  # Primary, Secondary, Mixed
    education_system = db.Column(db.String(50), default='CBC')  # CBC, 8-4-4, International
    
    # Academic Configuration
    current_academic_year = db.Column(db.String(20), nullable=False)
    current_term = db.Column(db.String(50), nullable=False)
    total_terms_per_year = db.Column(db.Integer, default=3)
    
    # School Structure
    uses_streams = db.Column(db.Boolean, default=True)
    lowest_grade = db.Column(db.String(20), default='PP1')
    highest_grade = db.Column(db.String(20), default='Grade 6')
    
    # Branding and Appearance
    logo_filename = db.Column(db.String(200), nullable=True)
    primary_color = db.Column(db.String(7), default='#1f7d53')
    secondary_color = db.Column(db.String(7), default='#18230f')
    accent_color = db.Column(db.String(7), default='#4ade80')
    
    # Assessment Configuration
    grading_system = db.Column(db.String(50), default='CBC')
    max_raw_marks_default = db.Column(db.Integer, default=100)
    pass_mark_percentage = db.Column(db.Float, default=50.0)
    
    # Report Configuration
    show_position = db.Column(db.Boolean, default=True)
    show_class_average = db.Column(db.Boolean, default=True)
    show_subject_teacher = db.Column(db.Boolean, default=False)
    report_footer = db.Column(db.Text, default='Powered by CbcTeachkit')
    
    # System Configuration
    timezone = db.Column(db.String(50), default='Africa/Nairobi')
    language = db.Column(db.String(10), default='en')
    currency = db.Column(db.String(10), default='KES')
    
    # Setup Status
    setup_completed = db.Column(db.Boolean, default=False)
    setup_step = db.Column(db.Integer, default=1)
    setup_completed_at = db.Column(db.DateTime, nullable=True)
    setup_completed_by = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    setup_completed_by_teacher = db.relationship('Teacher', backref='completed_setups')
    
    @classmethod
    def get_current_setup(cls):
        """Get the current school setup, creating default if none exists."""
        setup = cls.query.first()
        if not setup:
            setup = cls(
                school_name='Your School Name',
                school_motto='Excellence in Education',
                current_academic_year='2024',
                current_term='Term 1'
            )
            db.session.add(setup)
            db.session.commit()
        return setup
    
    def update_setup(self, **kwargs):
        """Update school setup with provided values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def mark_setup_completed(self, completed_by_id=None):
        """Mark the school setup as completed."""
        self.setup_completed = True
        self.setup_completed_at = datetime.utcnow()
        if completed_by_id:
            self.setup_completed_by = completed_by_id
        db.session.commit()
    
    def to_dict(self):
        """Convert school setup to dictionary for easy access."""
        return {
            'school_name': self.school_name,
            'school_motto': self.school_motto,
            'school_vision': self.school_vision,
            'school_mission': self.school_mission,
            'school_address': self.school_address,
            'postal_address': self.postal_address,
            'school_phone': self.school_phone,
            'school_mobile': self.school_mobile,
            'school_email': self.school_email,
            'school_website': self.school_website,
            'registration_number': self.registration_number,
            'ministry_code': self.ministry_code,
            'county': self.county,
            'sub_county': self.sub_county,
            'ward': self.ward,
            'constituency': self.constituency,
            'school_type': self.school_type,
            'school_category': self.school_category,
            'education_system': self.education_system,
            'current_academic_year': self.current_academic_year,
            'current_term': self.current_term,
            'total_terms_per_year': self.total_terms_per_year,
            'uses_streams': self.uses_streams,
            'lowest_grade': self.lowest_grade,
            'highest_grade': self.highest_grade,
            'logo_filename': self.logo_filename,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'grading_system': self.grading_system,
            'max_raw_marks_default': self.max_raw_marks_default,
            'pass_mark_percentage': self.pass_mark_percentage,
            'show_position': self.show_position,
            'show_class_average': self.show_class_average,
            'show_subject_teacher': self.show_subject_teacher,
            'report_footer': self.report_footer,
            'timezone': self.timezone,
            'language': self.language,
            'currency': self.currency,
            'setup_completed': self.setup_completed,
            'setup_step': self.setup_step
        }

class SchoolBranding(db.Model):
    """School branding and visual identity configuration."""
    __tablename__ = 'school_branding'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Logo Management
    logo_filename = db.Column(db.String(200), nullable=True)
    logo_width = db.Column(db.Integer, default=100)
    logo_height = db.Column(db.Integer, default=100)
    
    # Additional Images
    header_image = db.Column(db.String(200), nullable=True)
    background_image = db.Column(db.String(200), nullable=True)
    watermark_image = db.Column(db.String(200), nullable=True)
    
    # Color Scheme
    primary_color = db.Column(db.String(7), default='#1f7d53')
    secondary_color = db.Column(db.String(7), default='#18230f')
    accent_color = db.Column(db.String(7), default='#4ade80')
    text_color = db.Column(db.String(7), default='#1e293b')
    background_color = db.Column(db.String(7), default='#ffffff')
    
    # Typography
    primary_font = db.Column(db.String(100), default='Arial, sans-serif')
    secondary_font = db.Column(db.String(100), default='Georgia, serif')
    
    # Report Styling
    report_header_style = db.Column(db.Text, nullable=True)
    report_footer_style = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_current_branding(cls):
        """Get the current school branding, creating default if none exists."""
        branding = cls.query.first()
        if not branding:
            branding = cls()
            db.session.add(branding)
            db.session.commit()
        return branding

class SchoolCustomization(db.Model):
    """School-specific customizations and preferences."""
    __tablename__ = 'school_customization'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Feature Toggles
    enable_analytics = db.Column(db.Boolean, default=True)
    enable_parent_portal = db.Column(db.Boolean, default=False)
    enable_sms_notifications = db.Column(db.Boolean, default=False)
    enable_email_notifications = db.Column(db.Boolean, default=True)
    enable_mobile_app = db.Column(db.Boolean, default=False)
    
    # Custom Fields (JSON storage for flexibility)
    custom_student_fields = db.Column(db.Text, nullable=True)  # JSON
    custom_teacher_fields = db.Column(db.Text, nullable=True)  # JSON
    custom_report_fields = db.Column(db.Text, nullable=True)   # JSON
    
    # Integration Settings
    ministry_integration = db.Column(db.Boolean, default=False)
    parent_portal_url = db.Column(db.String(200), nullable=True)
    sms_provider = db.Column(db.String(50), nullable=True)
    email_provider = db.Column(db.String(50), nullable=True)
    
    # Backup and Security
    auto_backup_enabled = db.Column(db.Boolean, default=True)
    backup_frequency = db.Column(db.String(20), default='daily')
    data_retention_days = db.Column(db.Integer, default=365)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_current_customization(cls):
        """Get the current school customization, creating default if none exists."""
        customization = cls.query.first()
        if not customization:
            customization = cls()
            db.session.add(customization)
            db.session.commit()
        return customization
    
    def get_custom_fields(self, field_type):
        """Get custom fields for a specific type (student, teacher, report)."""
        field_attr = f'custom_{field_type}_fields'
        if hasattr(self, field_attr):
            field_json = getattr(self, field_attr)
            if field_json:
                try:
                    return json.loads(field_json)
                except json.JSONDecodeError:
                    return []
        return []
    
    def set_custom_fields(self, field_type, fields):
        """Set custom fields for a specific type."""
        field_attr = f'custom_{field_type}_fields'
        if hasattr(self, field_attr):
            setattr(self, field_attr, json.dumps(fields))
            db.session.commit()
