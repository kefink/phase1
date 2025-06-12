"""
Report Configuration Service for managing dynamic report settings.
"""

from ..models.report_config import ReportConfiguration, ClassReportConfiguration, ReportTemplate
from ..models import Teacher, Term, Grade, Stream
from ..extensions import db
from datetime import datetime, date
from sqlalchemy import and_, or_

class ReportConfigService:
    """Service for managing report configurations and settings."""
    
    @staticmethod
    def get_or_create_report_config(term_id, academic_year=None):
        """Get or create report configuration for a term."""
        if not academic_year:
            academic_year = str(datetime.now().year)
        
        config = ReportConfiguration.query.filter_by(
            term_id=term_id,
            academic_year=academic_year
        ).first()
        
        if not config:
            config = ReportConfiguration(
                term_id=term_id,
                academic_year=academic_year
            )
            db.session.add(config)
            db.session.commit()
        
        return config
    
    @staticmethod
    def get_report_config_for_term(term_name):
        """Get report configuration for a term by name."""
        term = Term.query.filter_by(name=term_name).first()
        if not term:
            return None
        
        # Get current academic year
        current_year = datetime.now().year
        academic_year = f"{current_year}/{current_year + 1}"
        
        return ReportConfigService.get_or_create_report_config(term.id, academic_year)
    
    @staticmethod
    def update_report_config(term_id, config_data, updated_by=None):
        """Update report configuration with new data."""
        config = ReportConfigService.get_or_create_report_config(
            term_id, 
            config_data.get('academic_year', str(datetime.now().year))
        )
        
        # Update basic information
        for field in ['academic_year', 'term_start_date', 'term_end_date', 
                     'closing_date', 'opening_date', 'school_name', 'school_address',
                     'school_phone', 'school_email', 'school_website', 'report_footer']:
            if field in config_data:
                setattr(config, field, config_data[field])
        
        # Update staff assignments
        for field in ['headteacher_id', 'deputy_headteacher_id', 'principal_id']:
            if field in config_data:
                setattr(config, field, config_data[field])
        
        # Update visibility settings
        for field in ['show_headteacher', 'show_deputy_headteacher', 
                     'show_principal', 'show_class_teacher']:
            if field in config_data:
                setattr(config, field, config_data[field])
        
        config.updated_at = datetime.utcnow()
        if updated_by:
            config.created_by = updated_by
        
        db.session.commit()
        return config
    
    @staticmethod
    def get_class_report_config(grade_id, stream_id, term_id):
        """Get class-specific report configuration."""
        return ClassReportConfiguration.query.filter_by(
            grade_id=grade_id,
            stream_id=stream_id,
            term_id=term_id
        ).first()
    
    @staticmethod
    def update_class_config(grade_id, stream_id, term_id, config_data):
        """Update class-specific report configuration."""
        config = ClassReportConfiguration.query.filter_by(
            grade_id=grade_id,
            stream_id=stream_id,
            term_id=term_id
        ).first()
        
        if not config:
            config = ClassReportConfiguration(
                grade_id=grade_id,
                stream_id=stream_id,
                term_id=term_id
            )
            db.session.add(config)
        
        # Update class-specific settings
        for field in ['class_teacher_id', 'custom_headteacher_id', 'custom_deputy_id',
                     'custom_principal_id', 'class_teacher_remarks', 'headteacher_remarks',
                     'show_headteacher', 'show_deputy_headteacher', 'show_principal', 'show_class_teacher']:
            if field in config_data:
                setattr(config, field, config_data[field])
        
        config.updated_at = datetime.utcnow()
        db.session.commit()
        return config
    
    @staticmethod
    def get_comprehensive_report_data(grade, stream, term, class_teacher_id=None):
        """Get comprehensive report data including all staff and configuration."""
        # Get term object
        term_obj = Term.query.filter_by(name=term).first()
        if not term_obj:
            return None
        
        # Get grade and stream objects
        grade_obj = Grade.query.filter_by(name=grade).first()
        stream_obj = Stream.query.filter_by(name=stream.split()[-1]).first() if stream else None
        
        # Get global report configuration
        global_config = ReportConfigService.get_report_config_for_term(term)
        
        # Get class-specific configuration
        class_config = None
        if grade_obj and stream_obj:
            class_config = ReportConfigService.get_class_report_config(
                grade_obj.id, stream_obj.id, term_obj.id
            )
        
        # Build comprehensive data
        report_data = {
            'term_info': {
                'name': term,
                'academic_year': global_config.academic_year if global_config else str(datetime.now().year),
                'start_date': global_config.term_start_date if global_config else None,
                'end_date': global_config.term_end_date if global_config else None,
                'closing_date': global_config.closing_date if global_config else None,
                'opening_date': global_config.opening_date if global_config else None,
            },
            'school_info': {
                'name': global_config.school_name if global_config else "KIRIMA PRIMARY SCHOOL",
                'address': global_config.school_address if global_config else "P.O. BOX 123, KIRIMA",
                'phone': global_config.school_phone if global_config else "+254 123 456789",
                'email': global_config.school_email if global_config else "info@kirimaprimary.ac.ke",
                'website': global_config.school_website if global_config else "www.kirimaprimary.ac.ke",
                'footer': global_config.report_footer if global_config else "Powered by CbcTeachkit"
            },
            'staff_info': ReportConfigService._get_staff_info(global_config, class_config, class_teacher_id),
            'visibility': ReportConfigService._get_visibility_settings(global_config, class_config),
            'remarks': ReportConfigService._get_remarks_templates(class_config)
        }
        
        return report_data
    
    @staticmethod
    def _get_staff_info(global_config, class_config, class_teacher_id=None):
        """Get staff information with proper fallbacks."""
        staff_info = {}
        
        # Helper function to get teacher info
        def get_teacher_info(teacher):
            if not teacher:
                return {'name': 'Not Assigned', 'employee_id': '', 'qualification': ''}
            return {
                'name': getattr(teacher, 'full_name', teacher.username),
                'employee_id': getattr(teacher, 'employee_id', ''),
                'qualification': getattr(teacher, 'qualification', '')
            }
        
        # Class Teacher
        class_teacher = None
        if class_config and class_config.class_teacher_id:
            class_teacher = Teacher.query.get(class_config.class_teacher_id)
        elif class_teacher_id:
            class_teacher = Teacher.query.get(class_teacher_id)
        
        staff_info['class_teacher'] = get_teacher_info(class_teacher)
        
        # Headteacher
        headteacher = None
        if class_config and class_config.custom_headteacher_id:
            headteacher = Teacher.query.get(class_config.custom_headteacher_id)
        elif global_config and global_config.headteacher_id:
            headteacher = Teacher.query.get(global_config.headteacher_id)
        else:
            # Fallback to role-based lookup
            headteacher = Teacher.query.filter_by(role='headteacher').first()
        
        staff_info['headteacher'] = get_teacher_info(headteacher)
        
        # Deputy Headteacher
        deputy = None
        if class_config and class_config.custom_deputy_id:
            deputy = Teacher.query.get(class_config.custom_deputy_id)
        elif global_config and global_config.deputy_headteacher_id:
            deputy = Teacher.query.get(global_config.deputy_headteacher_id)
        else:
            # Fallback to role-based lookup or qualification
            deputy = Teacher.query.filter(
                or_(Teacher.role.like('%deputy%'), Teacher.qualification.like('%deputy%'))
            ).first()
        
        staff_info['deputy_headteacher'] = get_teacher_info(deputy)
        
        # Principal
        principal = None
        if class_config and class_config.custom_principal_id:
            principal = Teacher.query.get(class_config.custom_principal_id)
        elif global_config and global_config.principal_id:
            principal = Teacher.query.get(global_config.principal_id)
        else:
            # Fallback to role-based lookup
            principal = Teacher.query.filter(
                or_(Teacher.role.like('%principal%'), Teacher.qualification.like('%principal%'))
            ).first()
        
        staff_info['principal'] = get_teacher_info(principal)
        
        return staff_info
    
    @staticmethod
    def _get_visibility_settings(global_config, class_config):
        """Get visibility settings with class overrides."""
        visibility = {
            'show_class_teacher': True,
            'show_headteacher': True,
            'show_deputy_headteacher': True,
            'show_principal': False
        }
        
        # Apply global settings
        if global_config:
            visibility.update({
                'show_class_teacher': global_config.show_class_teacher,
                'show_headteacher': global_config.show_headteacher,
                'show_deputy_headteacher': global_config.show_deputy_headteacher,
                'show_principal': global_config.show_principal
            })
        
        # Apply class-specific overrides
        if class_config:
            for key in visibility.keys():
                class_value = getattr(class_config, key, None)
                if class_value is not None:
                    visibility[key] = class_value
        
        return visibility
    
    @staticmethod
    def _get_remarks_templates(class_config):
        """Get remarks templates for the class."""
        remarks = {
            'class_teacher_remarks': None,
            'headteacher_remarks': None
        }
        
        if class_config:
            remarks.update({
                'class_teacher_remarks': class_config.class_teacher_remarks,
                'headteacher_remarks': class_config.headteacher_remarks
            })
        
        return remarks
    
    @staticmethod
    def get_all_teachers_for_selection():
        """Get all teachers formatted for selection dropdowns."""
        try:
            teachers = Teacher.query.filter_by(is_active=True).all()
        except:
            # Fallback if is_active column doesn't exist
            teachers = Teacher.query.all()

        return [
            {
                'id': teacher.id,
                'name': getattr(teacher, 'full_name', teacher.username),
                'role': teacher.role,
                'qualification': getattr(teacher, 'qualification', ''),
                'employee_id': getattr(teacher, 'employee_id', '')
            }
            for teacher in teachers
        ]
