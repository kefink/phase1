"""
Enhanced School configuration service for plug-and-play deployment.
Handles school-specific settings, branding, and customization.
"""
import os
import json
from werkzeug.utils import secure_filename
from PIL import Image
from ..models import SchoolConfiguration
from ..models.school_setup import SchoolSetup, SchoolBranding, SchoolCustomization
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
        # Check if enhanced school setup is completed and use that data
        try:
            from ..models.school_setup import SchoolSetup
            setup = SchoolSetup.query.first()

            if setup and setup.setup_completed and setup.school_name:
                return setup.school_name
        except ImportError:
            pass
        except Exception as e:
            print(f"Error getting school name from setup: {e}")

        # Fallback to old school configuration
        config = SchoolConfiguration.get_config()
        return config.school_name
    
    @staticmethod
    def get_school_logo_path():
        """Get the path to the school logo."""
        # Check if enhanced school setup is completed and use that data
        try:
            from ..models.school_setup import SchoolSetup
            setup = SchoolSetup.query.first()

            if setup and setup.setup_completed and setup.logo_filename:
                return f"images/{setup.logo_filename}"
        except ImportError:
            pass
        except Exception as e:
            print(f"Error getting school logo from setup: {e}")

        # Fallback to old school configuration
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
        # Check if enhanced school setup is completed and use that data
        try:
            from ..models.school_setup import SchoolSetup
            setup = SchoolSetup.query.first()

            if setup and setup.setup_completed:
                # Use data from the completed school setup
                return {
                    'school_name': setup.school_name or 'School Management System',
                    'school_motto': setup.school_motto,
                    'school_address': setup.school_address,
                    'school_phone': setup.school_phone,
                    'school_email': setup.school_email,
                    'school_website': setup.school_website,
                    'current_academic_year': setup.current_academic_year,
                    'current_term': setup.current_term,
                    'headteacher_name': 'Head Teacher',  # TODO: Get from teacher table
                    'deputy_headteacher_name': 'Deputy Head Teacher',  # TODO: Get from teacher table
                    'logo_path': f"images/{setup.logo_filename}" if setup.logo_filename else 'hv.jpg',
                    'primary_color': setup.primary_color,
                    'secondary_color': setup.secondary_color,
                    'uses_streams': setup.uses_streams,
                    'grading_system': setup.grading_system,
                    'report_footer': setup.report_footer or 'Powered by CbcTeachkit'
                }
        except ImportError:
            pass
        except Exception as e:
            print(f"Error getting school setup data: {e}")

        # Fallback to old school configuration
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
            'grading_system': config.grading_system,
            'report_footer': 'Powered by CbcTeachkit'
        }

class EnhancedSchoolSetupService:
    """Enhanced service for comprehensive school setup and configuration."""

    @staticmethod
    def get_school_setup():
        """Get the current school setup configuration."""
        return SchoolSetup.get_current_setup()

    @staticmethod
    def get_school_branding():
        """Get the current school branding configuration."""
        return SchoolBranding.get_current_branding()

    @staticmethod
    def get_school_customization():
        """Get the current school customization settings."""
        return SchoolCustomization.get_current_customization()

    @staticmethod
    def is_setup_completed():
        """Check if the school setup has been completed."""
        setup = SchoolSetup.get_current_setup()
        return setup.setup_completed

    @staticmethod
    def get_setup_progress():
        """Get the current setup progress as a percentage."""
        setup = SchoolSetup.get_current_setup()

        # Define required fields for complete setup
        required_fields = [
            'school_name', 'school_motto', 'school_address', 'school_phone',
            'school_email', 'current_academic_year', 'current_term',
            'county', 'sub_county', 'school_type', 'education_system'
        ]

        completed_fields = 0
        for field in required_fields:
            value = getattr(setup, field, None)
            if value and str(value).strip():
                completed_fields += 1

        return int((completed_fields / len(required_fields)) * 100)

    @staticmethod
    def update_school_setup(step=None, **kwargs):
        """Update school setup configuration."""
        setup = SchoolSetup.get_current_setup()

        # Update step if provided
        if step:
            setup.setup_step = step

        # Update fields
        setup.update_setup(**kwargs)

        return setup

    @staticmethod
    def complete_setup(completed_by_id=None):
        """Mark the school setup as completed."""
        setup = SchoolSetup.get_current_setup()
        setup.mark_setup_completed(completed_by_id)
        return setup

    @staticmethod
    def save_school_logo(logo_file):
        """Save and process school logo."""
        if not logo_file or not logo_file.filename:
            return None

        try:
            # Create uploads directory
            upload_dir = os.path.join(current_app.static_folder, 'uploads', 'logos')
            os.makedirs(upload_dir, exist_ok=True)

            # Secure filename
            filename = secure_filename(logo_file.filename)
            timestamp = int(datetime.now().timestamp())
            filename = f"school_logo_{timestamp}_{filename}"

            # Save original file
            filepath = os.path.join(upload_dir, filename)
            logo_file.save(filepath)

            # Process image (resize, optimize)
            processed_filename = EnhancedSchoolSetupService._process_logo_image(filepath, filename)

            # Update school setup
            setup = SchoolSetup.get_current_setup()
            setup.update_setup(logo_filename=processed_filename)

            return processed_filename

        except Exception as e:
            print(f"Error saving logo: {e}")
            return None

    @staticmethod
    def _process_logo_image(filepath, filename):
        """Process and optimize logo image."""
        try:
            # Open and process image
            with Image.open(filepath) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Resize to standard logo size (maintain aspect ratio)
                max_size = (200, 200)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save optimized version
                optimized_filename = f"optimized_{filename}"
                optimized_path = os.path.join(os.path.dirname(filepath), optimized_filename)
                img.save(optimized_path, 'JPEG', quality=85, optimize=True)

                # Remove original if different
                if optimized_filename != filename:
                    os.remove(filepath)

                return optimized_filename

        except Exception as e:
            print(f"Error processing logo image: {e}")
            return filename  # Return original filename if processing fails

    @staticmethod
    def get_comprehensive_school_info():
        """Get comprehensive school information for templates and reports."""
        setup = SchoolSetup.get_current_setup()
        branding = SchoolBranding.get_current_branding()
        customization = SchoolCustomization.get_current_customization()

        return {
            **setup.to_dict(),
            'branding': {
                'logo_filename': branding.logo_filename,
                'primary_color': branding.primary_color,
                'secondary_color': branding.secondary_color,
                'accent_color': branding.accent_color,
                'text_color': branding.text_color,
                'background_color': branding.background_color,
                'primary_font': branding.primary_font,
                'secondary_font': branding.secondary_font
            },
            'features': {
                'enable_analytics': customization.enable_analytics,
                'enable_parent_portal': customization.enable_parent_portal,
                'enable_sms_notifications': customization.enable_sms_notifications,
                'enable_email_notifications': customization.enable_email_notifications,
                'enable_mobile_app': customization.enable_mobile_app
            }
        }
