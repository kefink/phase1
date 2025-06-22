"""
Enhanced Grading System Models for Hillview School Management System.
Supports multiple grading systems including CBC, percentage, letter grades, and custom systems.
"""

from ..extensions import db
from datetime import datetime
import json

class GradingSystem(db.Model):
    """Model for different grading systems."""
    __tablename__ = 'grading_system'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    is_system_defined = db.Column(db.Boolean, default=True)  # System vs custom
    
    # Grading configuration
    grade_bands = db.Column(db.Text, nullable=False)  # JSON string
    max_marks = db.Column(db.Integer, default=100)
    pass_mark_percentage = db.Column(db.Float, default=50.0)
    
    # Display settings
    show_percentage = db.Column(db.Boolean, default=True)
    show_grade = db.Column(db.Boolean, default=True)
    show_points = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_default_system(cls):
        """Get the default grading system."""
        return cls.query.filter_by(is_default=True, is_active=True).first()
    
    @classmethod
    def get_active_systems(cls):
        """Get all active grading systems."""
        return cls.query.filter_by(is_active=True).order_by(cls.is_default.desc(), cls.name).all()
    
    @classmethod
    def get_cbc_system(cls):
        """Get the CBC grading system."""
        return cls.query.filter_by(code='CBC', is_active=True).first()
    
    def get_grade_bands(self):
        """Get grade bands as a Python object."""
        try:
            return json.loads(self.grade_bands) if self.grade_bands else []
        except:
            return []
    
    def set_grade_bands(self, bands):
        """Set grade bands from a Python object."""
        self.grade_bands = json.dumps(bands)
    
    def get_grade_for_percentage(self, percentage):
        """Get grade for a given percentage."""
        bands = self.get_grade_bands()
        for band in bands:
            if percentage >= band.get('min_percentage', 0):
                return band.get('grade', 'N/A')
        return 'N/A'
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'is_system_defined': self.is_system_defined,
            'grade_bands': self.get_grade_bands(),
            'max_marks': self.max_marks,
            'pass_mark_percentage': self.pass_mark_percentage,
            'show_percentage': self.show_percentage,
            'show_grade': self.show_grade,
            'show_points': self.show_points
        }

class SchoolGradingConfig(db.Model):
    """Configuration for school's grading preferences."""
    __tablename__ = 'school_grading_config'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Primary grading system
    primary_grading_system_id = db.Column(db.Integer, db.ForeignKey('grading_system.id'), nullable=False)
    
    # Secondary grading systems (for comparison/reporting)
    secondary_grading_systems = db.Column(db.Text, nullable=True)  # JSON array of IDs
    
    # Display preferences
    show_multiple_grades = db.Column(db.Boolean, default=False)
    default_display_system = db.Column(db.String(20), default='primary')  # primary, secondary, both
    
    # Report preferences
    include_grade_explanation = db.Column(db.Boolean, default=True)
    show_grade_boundaries = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    primary_system = db.relationship('GradingSystem', foreign_keys=[primary_grading_system_id])
    
    @classmethod
    def get_current_config(cls):
        """Get current grading configuration."""
        config = cls.query.first()
        if not config:
            # Create default configuration
            default_system = GradingSystem.get_default_system()
            if default_system:
                config = cls(primary_grading_system_id=default_system.id)
                db.session.add(config)
                db.session.commit()
        return config
    
    def get_secondary_systems(self):
        """Get secondary grading systems."""
        try:
            if self.secondary_grading_systems:
                ids = json.loads(self.secondary_grading_systems)
                return GradingSystem.query.filter(GradingSystem.id.in_(ids), GradingSystem.is_active == True).all()
        except:
            pass
        return []
    
    def set_secondary_systems(self, system_ids):
        """Set secondary grading systems."""
        self.secondary_grading_systems = json.dumps(system_ids) if system_ids else None
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'primary_system': self.primary_system.to_dict() if self.primary_system else None,
            'secondary_systems': [sys.to_dict() for sys in self.get_secondary_systems()],
            'show_multiple_grades': self.show_multiple_grades,
            'default_display_system': self.default_display_system,
            'include_grade_explanation': self.include_grade_explanation,
            'show_grade_boundaries': self.show_grade_boundaries
        }

def initialize_default_grading_systems():
    """Initialize default grading systems."""
    
    # CBC Grading System
    cbc_bands = [
        {'grade': 'E.E', 'name': 'Exceeds Expectations', 'min_percentage': 80, 'max_percentage': 100, 'points': 4, 'color': '#10b981'},
        {'grade': 'M.E', 'name': 'Meets Expectations', 'min_percentage': 60, 'max_percentage': 79, 'points': 3, 'color': '#3b82f6'},
        {'grade': 'A.E', 'name': 'Approaches Expectations', 'min_percentage': 40, 'max_percentage': 59, 'points': 2, 'color': '#f59e0b'},
        {'grade': 'B.E', 'name': 'Below Expectations', 'min_percentage': 0, 'max_percentage': 39, 'points': 1, 'color': '#ef4444'}
    ]
    
    # Percentage System
    percentage_bands = [
        {'grade': 'A', 'name': 'Excellent', 'min_percentage': 90, 'max_percentage': 100, 'points': 5, 'color': '#10b981'},
        {'grade': 'B', 'name': 'Very Good', 'min_percentage': 80, 'max_percentage': 89, 'points': 4, 'color': '#3b82f6'},
        {'grade': 'C', 'name': 'Good', 'min_percentage': 70, 'max_percentage': 79, 'points': 3, 'color': '#8b5cf6'},
        {'grade': 'D', 'name': 'Satisfactory', 'min_percentage': 60, 'max_percentage': 69, 'points': 2, 'color': '#f59e0b'},
        {'grade': 'E', 'name': 'Needs Improvement', 'min_percentage': 0, 'max_percentage': 59, 'points': 1, 'color': '#ef4444'}
    ]
    
    # Letter Grades System
    letter_bands = [
        {'grade': 'A+', 'name': 'Outstanding', 'min_percentage': 95, 'max_percentage': 100, 'points': 5, 'color': '#10b981'},
        {'grade': 'A', 'name': 'Excellent', 'min_percentage': 85, 'max_percentage': 94, 'points': 4.5, 'color': '#059669'},
        {'grade': 'B+', 'name': 'Very Good', 'min_percentage': 75, 'max_percentage': 84, 'points': 4, 'color': '#3b82f6'},
        {'grade': 'B', 'name': 'Good', 'min_percentage': 65, 'max_percentage': 74, 'points': 3.5, 'color': '#1d4ed8'},
        {'grade': 'C+', 'name': 'Above Average', 'min_percentage': 55, 'max_percentage': 64, 'points': 3, 'color': '#8b5cf6'},
        {'grade': 'C', 'name': 'Average', 'min_percentage': 45, 'max_percentage': 54, 'points': 2.5, 'color': '#7c3aed'},
        {'grade': 'D', 'name': 'Below Average', 'min_percentage': 35, 'max_percentage': 44, 'points': 2, 'color': '#f59e0b'},
        {'grade': 'F', 'name': 'Fail', 'min_percentage': 0, 'max_percentage': 34, 'points': 1, 'color': '#ef4444'}
    ]
    
    systems = [
        {
            'name': 'CBC (Competency Based Curriculum)',
            'code': 'CBC',
            'description': 'Kenya\'s Competency Based Curriculum grading system',
            'bands': cbc_bands,
            'is_default': True,
            'pass_mark_percentage': 40.0
        },
        {
            'name': 'Percentage System',
            'code': 'PERCENTAGE',
            'description': 'Traditional percentage-based grading',
            'bands': percentage_bands,
            'is_default': False,
            'pass_mark_percentage': 50.0
        },
        {
            'name': 'Letter Grades',
            'code': 'LETTER',
            'description': 'Letter-based grading system',
            'bands': letter_bands,
            'is_default': False,
            'pass_mark_percentage': 45.0
        }
    ]
    
    for system_data in systems:
        existing = GradingSystem.query.filter_by(code=system_data['code']).first()
        if not existing:
            system = GradingSystem(
                name=system_data['name'],
                code=system_data['code'],
                description=system_data['description'],
                is_default=system_data['is_default'],
                pass_mark_percentage=system_data['pass_mark_percentage']
            )
            system.set_grade_bands(system_data['bands'])
            db.session.add(system)
    
    db.session.commit()
