"""
Dynamic School Information Service for Hillview School Management System.
Ensures school information (including logos) is dynamically updated across all pages and reports.
"""

import os
from flask import current_app, url_for
from ..models.school_setup import SchoolSetup, SchoolBranding, SchoolCustomization
from ..extensions import db

class DynamicSchoolInfoService:
    """Service for managing dynamic school information across the application."""
    
    @staticmethod
    def get_school_info():
        """Get comprehensive school information for templates."""
        setup = SchoolSetup.get_current_setup()
        branding = SchoolBranding.get_current_branding()
        customization = SchoolCustomization.get_current_customization()
        
        # Get logo URL
        logo_url = DynamicSchoolInfoService.get_logo_url(setup.logo_filename)
        
        return {
            # Basic Information
            'school_name': setup.school_name or 'Your School Name',
            'school_motto': setup.school_motto or 'Excellence in Education',
            'school_vision': setup.school_vision or '',
            'school_mission': setup.school_mission or '',
            
            # Contact Information
            'school_address': setup.school_address or '',
            'postal_address': setup.postal_address or '',
            'school_phone': setup.school_phone or '',
            'school_mobile': setup.school_mobile or '',
            'school_email': setup.school_email or '',
            'school_website': setup.school_website or '',
            
            # Location
            'county': setup.county or '',
            'sub_county': setup.sub_county or '',
            'ward': setup.ward or '',
            'constituency': setup.constituency or '',
            
            # Academic Information
            'current_academic_year': setup.current_academic_year or '2024/2025',
            'current_term': setup.current_term or 'Term 1',
            'education_system': setup.education_system or 'CBC',
            'school_type': setup.school_type or '',
            'school_category': setup.school_category or '',
            
            # Grading System
            'grading_system': setup.grading_system or 'CBC',
            'secondary_grading_systems': getattr(setup, 'secondary_grading_systems', '') or '',
            'show_multiple_grades': getattr(setup, 'show_multiple_grades', False) or False,
            'max_raw_marks_default': setup.max_raw_marks_default or 100,
            'pass_mark_percentage': setup.pass_mark_percentage or 50.0,
            
            # Visual Branding
            'logo_filename': setup.logo_filename,
            'logo_url': logo_url,
            'logo_path': logo_url,  # Alias for compatibility
            'primary_color': setup.primary_color or '#1f7d53',
            'secondary_color': setup.secondary_color or '#18230f',
            'accent_color': setup.accent_color or '#4ade80',
            
            # Report Configuration
            'show_position': setup.show_position,
            'show_class_average': setup.show_class_average,
            'show_subject_teacher': setup.show_subject_teacher,
            'report_footer': setup.report_footer or 'Powered by Hillview SMS',
            
            # System Configuration
            'timezone': setup.timezone or 'Africa/Nairobi',
            'language': setup.language or 'en',
            'currency': setup.currency or 'KES',
            
            # Setup Status
            'setup_completed': setup.setup_completed,
            'setup_step': setup.setup_step
        }
    
    @staticmethod
    def get_logo_url(logo_filename):
        """Get the URL for the school logo."""
        if not logo_filename:
            return url_for('static', filename='images/default_logo.png')
        
        # Check if logo file exists
        logo_path = os.path.join(current_app.static_folder, 'uploads', 'logos', logo_filename)
        if os.path.exists(logo_path):
            return url_for('static', filename=f'uploads/logos/{logo_filename}')
        else:
            return url_for('static', filename='images/default_logo.png')
    
    @staticmethod
    def get_school_colors():
        """Get school color scheme."""
        setup = SchoolSetup.get_current_setup()
        return {
            'primary': setup.primary_color or '#1f7d53',
            'secondary': setup.secondary_color or '#18230f',
            'accent': setup.accent_color or '#4ade80'
        }
    
    @staticmethod
    def get_report_header_info():
        """Get school information specifically formatted for report headers."""
        info = DynamicSchoolInfoService.get_school_info()
        
        return {
            'school_name': info['school_name'],
            'school_motto': info['school_motto'],
            'school_address': info['school_address'],
            'school_phone': info['school_phone'],
            'school_email': info['school_email'],
            'logo_url': info['logo_url'],
            'academic_year': info['current_academic_year'],
            'term': info['current_term'],
            'primary_color': info['primary_color'],
            'secondary_color': info['secondary_color']
        }
    
    @staticmethod
    def get_grading_system_info():
        """Get comprehensive grading system information."""
        setup = SchoolSetup.get_current_setup()
        
        # Define grading system details
        grading_systems = {
            'CBC': {
                'name': 'CBC (Competency Based Curriculum)',
                'bands': [
                    {'grade': 'E.E', 'name': 'Exceeds Expectations', 'min': 80, 'max': 100, 'color': '#10b981'},
                    {'grade': 'M.E', 'name': 'Meets Expectations', 'min': 60, 'max': 79, 'color': '#3b82f6'},
                    {'grade': 'A.E', 'name': 'Approaches Expectations', 'min': 40, 'max': 59, 'color': '#f59e0b'},
                    {'grade': 'B.E', 'name': 'Below Expectations', 'min': 0, 'max': 39, 'color': '#ef4444'}
                ]
            },
            'Percentage': {
                'name': 'Percentage System',
                'bands': [
                    {'grade': 'A', 'name': 'Excellent', 'min': 90, 'max': 100, 'color': '#10b981'},
                    {'grade': 'B', 'name': 'Very Good', 'min': 80, 'max': 89, 'color': '#3b82f6'},
                    {'grade': 'C', 'name': 'Good', 'min': 70, 'max': 79, 'color': '#8b5cf6'},
                    {'grade': 'D', 'name': 'Satisfactory', 'min': 60, 'max': 69, 'color': '#f59e0b'},
                    {'grade': 'E', 'name': 'Needs Improvement', 'min': 0, 'max': 59, 'color': '#ef4444'}
                ]
            },
            'Letter': {
                'name': 'Letter Grades',
                'bands': [
                    {'grade': 'A+', 'name': 'Outstanding', 'min': 95, 'max': 100, 'color': '#10b981'},
                    {'grade': 'A', 'name': 'Excellent', 'min': 85, 'max': 94, 'color': '#059669'},
                    {'grade': 'B+', 'name': 'Very Good', 'min': 75, 'max': 84, 'color': '#3b82f6'},
                    {'grade': 'B', 'name': 'Good', 'min': 65, 'max': 74, 'color': '#1d4ed8'},
                    {'grade': 'C+', 'name': 'Above Average', 'min': 55, 'max': 64, 'color': '#8b5cf6'},
                    {'grade': 'C', 'name': 'Average', 'min': 45, 'max': 54, 'color': '#7c3aed'},
                    {'grade': 'D', 'name': 'Below Average', 'min': 35, 'max': 44, 'color': '#f59e0b'},
                    {'grade': 'F', 'name': 'Fail', 'min': 0, 'max': 34, 'color': '#ef4444'}
                ]
            }
        }
        
        primary_system = setup.grading_system or 'CBC'
        
        return {
            'primary_system': primary_system,
            'primary_system_info': grading_systems.get(primary_system, grading_systems['CBC']),
            'show_multiple_grades': getattr(setup, 'show_multiple_grades', False),
            'secondary_systems': getattr(setup, 'secondary_grading_systems', ''),
            'max_marks': setup.max_raw_marks_default or 100,
            'pass_mark': setup.pass_mark_percentage or 50.0
        }
    
    @staticmethod
    def get_grade_for_percentage(percentage, system='CBC'):
        """Get grade for a given percentage in the specified system."""
        grading_info = DynamicSchoolInfoService.get_grading_system_info()
        
        if system == 'primary':
            system = grading_info['primary_system']
        
        system_info = grading_info['primary_system_info']
        if system != grading_info['primary_system']:
            # Handle secondary systems
            grading_systems = {
                'CBC': [
                    {'grade': 'E.E', 'min': 80}, {'grade': 'M.E', 'min': 60},
                    {'grade': 'A.E', 'min': 40}, {'grade': 'B.E', 'min': 0}
                ],
                'Percentage': [
                    {'grade': 'A', 'min': 90}, {'grade': 'B', 'min': 80},
                    {'grade': 'C', 'min': 70}, {'grade': 'D', 'min': 60}, {'grade': 'E', 'min': 0}
                ],
                'Letter': [
                    {'grade': 'A+', 'min': 95}, {'grade': 'A', 'min': 85}, {'grade': 'B+', 'min': 75},
                    {'grade': 'B', 'min': 65}, {'grade': 'C+', 'min': 55}, {'grade': 'C', 'min': 45},
                    {'grade': 'D', 'min': 35}, {'grade': 'F', 'min': 0}
                ]
            }
            system_info = {'bands': grading_systems.get(system, grading_systems['CBC'])}
        
        for band in system_info['bands']:
            if percentage >= band['min']:
                return band['grade']
        
        return 'N/A'
    
    @staticmethod
    def inject_school_info():
        """Template context processor to inject school info into all templates."""
        return {
            'school_info': DynamicSchoolInfoService.get_school_info(),
            'school_colors': DynamicSchoolInfoService.get_school_colors(),
            'grading_info': DynamicSchoolInfoService.get_grading_system_info()
        }
    
    @staticmethod
    def create_default_logo():
        """Create a default logo if none exists."""
        default_logo_dir = os.path.join(current_app.static_folder, 'images')
        os.makedirs(default_logo_dir, exist_ok=True)
        
        default_logo_path = os.path.join(default_logo_dir, 'default_logo.png')
        
        # Create a simple default logo if it doesn't exist
        if not os.path.exists(default_logo_path):
            try:
                from PIL import Image, ImageDraw, ImageFont
                
                # Create a simple logo
                img = Image.new('RGB', (200, 200), color='#1f7d53')
                draw = ImageDraw.Draw(img)
                
                # Add text
                try:
                    font = ImageFont.truetype("arial.ttf", 24)
                except:
                    font = ImageFont.load_default()
                
                text = "SCHOOL\nLOGO"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (200 - text_width) // 2
                y = (200 - text_height) // 2
                
                draw.text((x, y), text, fill='white', font=font, align='center')
                
                img.save(default_logo_path, 'PNG')
                
            except Exception as e:
                print(f"Could not create default logo: {e}")
        
        return default_logo_path
