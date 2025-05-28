"""
School configuration service for the Hillview School Management System.
Handles school-specific settings and customization.
"""
import os
from ..models import SchoolConfiguration
from ..extensions import db
from flask import current_app

class SchoolConfigService:
    """Service for managing school configuration settings."""
    
    @staticmethod
    def get_school_config():
        """Get the current school configuration."""
        return SchoolConfiguration.get_config()
    
    @staticmethod
    def update_school_config(**kwargs):
        """Update school configuration with provided values."""
        config = SchoolConfiguration.get_config()
        return config.update_config(**kwargs)
    
    @staticmethod
    def get_school_name():
        """Get the school name."""
        config = SchoolConfiguration.get_config()
        return config.school_name
    
    @staticmethod
    def get_school_logo_path():
        """Get the path to the school logo."""
        config = SchoolConfiguration.get_config()
        if config.logo_filename:
            return f"images/{config.logo_filename}"
        return "hv.jpg"  # Default logo
    
    @staticmethod
    def get_current_academic_year():
        """Get the current academic year."""
        config = SchoolConfiguration.get_config()
        return config.current_academic_year
    
    @staticmethod
    def get_current_term():
        """Get the current term."""
        config = SchoolConfiguration.get_config()
        return config.current_term
    
    @staticmethod
    def uses_streams():
        """Check if the school uses streams/classes."""
        config = SchoolConfiguration.get_config()
        return config.use_streams
    
    @staticmethod
    def get_grading_system():
        """Get the grading system used by the school."""
        config = SchoolConfiguration.get_config()
        return config.grading_system
    
    @staticmethod
    def get_primary_color():
        """Get the school's primary color."""
        config = SchoolConfiguration.get_config()
        return config.primary_color
    
    @staticmethod
    def get_secondary_color():
        """Get the school's secondary color."""
        config = SchoolConfiguration.get_config()
        return config.secondary_color
    
    @staticmethod
    def get_default_max_marks():
        """Get the default maximum marks for assessments."""
        config = SchoolConfiguration.get_config()
        return config.max_raw_marks_default
    
    @staticmethod
    def get_pass_mark_percentage():
        """Get the pass mark percentage."""
        config = SchoolConfiguration.get_config()
        return config.pass_mark_percentage
    
    @staticmethod
    def should_show_position():
        """Check if position should be shown in reports."""
        config = SchoolConfiguration.get_config()
        return config.show_position
    
    @staticmethod
    def should_show_class_average():
        """Check if class average should be shown in reports."""
        config = SchoolConfiguration.get_config()
        return config.show_class_average
    
    @staticmethod
    def should_show_subject_teacher():
        """Check if subject teacher should be shown in reports."""
        config = SchoolConfiguration.get_config()
        return config.show_subject_teacher
    
    @staticmethod
    def get_headteacher_name():
        """Get the headteacher's name."""
        config = SchoolConfiguration.get_config()
        return config.headteacher_name or "Headteacher"
    
    @staticmethod
    def get_deputy_headteacher_name():
        """Get the deputy headteacher's name."""
        config = SchoolConfiguration.get_config()
        return config.deputy_headteacher_name or "Deputy Headteacher"
    
    @staticmethod
    def initialize_default_config():
        """Initialize default configuration for a new school installation."""
        config = SchoolConfiguration.get_config()
        
        # If this is a fresh installation, set up some defaults
        if not config.school_name or config.school_name == "School Name":
            default_config = {
                'school_name': 'Your School Name',
                'school_motto': 'Excellence in Education',
                'current_academic_year': '2024',
                'current_term': 'Term 1',
                'use_streams': True,
                'grading_system': 'CBC',
                'show_position': True,
                'show_class_average': True,
                'show_subject_teacher': False,
                'max_raw_marks_default': 100,
                'pass_mark_percentage': 50.0,
                'primary_color': '#1f7d53',
                'secondary_color': '#18230f'
            }
            config.update_config(**default_config)
        
        return config
    
    @staticmethod
    def save_logo(logo_file):
        """Save uploaded logo file and update configuration."""
        if logo_file and logo_file.filename:
            # Create images directory if it doesn't exist
            images_dir = os.path.join(current_app.static_folder, 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            # Generate unique filename
            filename = f"school_logo_{logo_file.filename}"
            filepath = os.path.join(images_dir, filename)
            
            # Save the file
            logo_file.save(filepath)
            
            # Update configuration
            config = SchoolConfiguration.get_config()
            config.update_config(logo_filename=filename)
            
            return filename
        return None
    
    @staticmethod
    def get_school_info_dict():
        """Get all school information as a dictionary for templates."""
        config = SchoolConfiguration.get_config()
        return {
            'school_name': config.school_name,
            'school_motto': config.school_motto,
            'school_address': config.school_address,
            'school_phone': config.school_phone,
            'school_email': config.school_email,
            'school_website': config.school_website,
            'current_academic_year': config.current_academic_year,
            'current_term': config.current_term,
            'headteacher_name': config.headteacher_name,
            'deputy_headteacher_name': config.deputy_headteacher_name,
            'logo_path': SchoolConfigService.get_school_logo_path(),
            'primary_color': config.primary_color,
            'secondary_color': config.secondary_color,
            'uses_streams': config.use_streams,
            'grading_system': config.grading_system
        }
