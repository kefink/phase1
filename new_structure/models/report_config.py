"""
Report Configuration models for the Hillview School Management System.
Manages dynamic staff assignments, term dates, and report settings.
"""

from ..extensions import db
from datetime import datetime

class ReportConfiguration(db.Model):
    """Model for storing report configuration settings."""
    __tablename__ = 'report_configuration'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Term Information
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)  # e.g., "2023/2024"
    
    # Term Dates
    term_start_date = db.Column(db.Date, nullable=True)
    term_end_date = db.Column(db.Date, nullable=True)
    closing_date = db.Column(db.Date, nullable=True)
    opening_date = db.Column(db.Date, nullable=True)  # Next term opening
    
    # Staff Configuration
    headteacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    deputy_headteacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    principal_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    
    # Report Settings
    show_headteacher = db.Column(db.Boolean, default=True)
    show_deputy_headteacher = db.Column(db.Boolean, default=True)
    show_principal = db.Column(db.Boolean, default=False)
    show_class_teacher = db.Column(db.Boolean, default=True)
    
    # School Information
    school_name = db.Column(db.String(200), default="KIRIMA PRIMARY SCHOOL")
    school_address = db.Column(db.Text, default="P.O. BOX 123, KIRIMA")
    school_phone = db.Column(db.String(50), default="+254 123 456789")
    school_email = db.Column(db.String(100), default="info@kirimaprimary.ac.ke")
    school_website = db.Column(db.String(100), default="www.kirimaprimary.ac.ke")
    
    # Report Footer
    report_footer = db.Column(db.Text, default="Powered by CbcTeachkit")
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    
    # Relationships
    term = db.relationship('Term', backref='report_configurations')
    headteacher = db.relationship('Teacher', foreign_keys=[headteacher_id], backref='headteacher_configs')
    deputy_headteacher = db.relationship('Teacher', foreign_keys=[deputy_headteacher_id], backref='deputy_configs')
    principal = db.relationship('Teacher', foreign_keys=[principal_id], backref='principal_configs')
    created_by_teacher = db.relationship('Teacher', foreign_keys=[created_by], backref='created_configs')
    
    def __repr__(self):
        return f'<ReportConfiguration {self.academic_year} - {self.term.name if self.term else "No Term"}>'

class ClassReportConfiguration(db.Model):
    """Model for storing class-specific report configuration."""
    __tablename__ = 'class_report_configuration'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Class Information
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)
    
    # Class Teacher Configuration
    class_teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    
    # Custom Staff for this class (overrides global settings)
    custom_headteacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    custom_deputy_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    custom_principal_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    
    # Class-specific settings
    class_teacher_remarks = db.Column(db.Text, nullable=True)
    headteacher_remarks = db.Column(db.Text, nullable=True)
    
    # Visibility settings for this class
    show_headteacher = db.Column(db.Boolean, default=None)  # None means use global setting
    show_deputy_headteacher = db.Column(db.Boolean, default=None)
    show_principal = db.Column(db.Boolean, default=None)
    show_class_teacher = db.Column(db.Boolean, default=None)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    grade = db.relationship('Grade', backref='class_report_configs')
    stream = db.relationship('Stream', backref='class_report_configs')
    term = db.relationship('Term', backref='class_report_configs')
    class_teacher = db.relationship('Teacher', foreign_keys=[class_teacher_id], backref='class_configs')
    custom_headteacher = db.relationship('Teacher', foreign_keys=[custom_headteacher_id], backref='custom_head_configs')
    custom_deputy = db.relationship('Teacher', foreign_keys=[custom_deputy_id], backref='custom_deputy_configs')
    custom_principal = db.relationship('Teacher', foreign_keys=[custom_principal_id], backref='custom_principal_configs')
    
    def __repr__(self):
        stream_name = f" Stream {self.stream.name}" if self.stream else ""
        return f'<ClassReportConfiguration {self.grade.name}{stream_name} - {self.term.name if self.term else "No Term"}>'

class ReportTemplate(db.Model):
    """Model for storing custom report templates and remarks."""
    __tablename__ = 'report_template'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Template Information
    template_name = db.Column(db.String(100), nullable=False)
    template_type = db.Column(db.String(50), nullable=False)  # 'class_report', 'individual_report', 'stream_report'
    education_level = db.Column(db.String(50), nullable=True)  # 'lower_primary', 'upper_primary', 'junior_secondary'
    
    # Template Content
    header_template = db.Column(db.Text, nullable=True)
    footer_template = db.Column(db.Text, nullable=True)
    
    # Default Remarks Templates
    excellent_remarks = db.Column(db.Text, nullable=True)
    good_remarks = db.Column(db.Text, nullable=True)
    satisfactory_remarks = db.Column(db.Text, nullable=True)
    needs_improvement_remarks = db.Column(db.Text, nullable=True)
    
    # Headteacher Remarks Templates
    headteacher_excellent = db.Column(db.Text, nullable=True)
    headteacher_good = db.Column(db.Text, nullable=True)
    headteacher_satisfactory = db.Column(db.Text, nullable=True)
    headteacher_needs_improvement = db.Column(db.Text, nullable=True)
    
    # Settings
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    
    # Relationships
    created_by_teacher = db.relationship('Teacher', backref='created_templates')
    
    def __repr__(self):
        return f'<ReportTemplate {self.template_name} - {self.template_type}>'
