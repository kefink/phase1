"""
Enhanced School Setup views for plug-and-play deployment.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask import session
from werkzeug.utils import secure_filename
from ..models.school_setup import SchoolSetup, SchoolBranding, SchoolCustomization
from ..services.school_config_service import EnhancedSchoolSetupService
from datetime import datetime
from ..services import is_authenticated, get_role
from functools import wraps
import os

# Create blueprint
school_setup_bp = Blueprint('school_setup', __name__, url_prefix='/school-setup')

def headteacher_required(f):
    """Decorator to require headteacher authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session as flask_session
        if not is_authenticated(flask_session):
            return redirect(url_for('auth.admin_login'))

        role = get_role(flask_session)
        if role != 'headteacher':
            flash('Access denied. This feature is only available to headteachers.', 'error')
            return redirect(url_for('auth.admin_login'))

        return f(*args, **kwargs)
    return decorated_function

@school_setup_bp.route('/')
@headteacher_required
def setup_dashboard():
    """School setup dashboard - main entry point."""
    setup = EnhancedSchoolSetupService.get_school_setup()
    progress = EnhancedSchoolSetupService.get_setup_progress()
    
    return render_template('school_setup/dashboard.html',
                         setup=setup,
                         progress=progress,
                         is_completed=setup.setup_completed)

@school_setup_bp.route('/basic-info', methods=['GET', 'POST'])
@headteacher_required
def basic_info():
    """Step 1: Basic school information."""
    if request.method == 'POST':
        try:
            # Get form data
            data = {
                'school_name': request.form.get('school_name'),
                'school_motto': request.form.get('school_motto'),
                'school_vision': request.form.get('school_vision'),
                'school_mission': request.form.get('school_mission'),
                'school_address': request.form.get('school_address'),
                'postal_address': request.form.get('postal_address'),
                'school_phone': request.form.get('school_phone'),
                'school_mobile': request.form.get('school_mobile'),
                'school_email': request.form.get('school_email'),
                'school_website': request.form.get('school_website')
            }
            
            # Validate required fields
            if not data['school_name']:
                flash('School name is required.', 'error')
                return render_template('school_setup/basic_info.html', 
                                     setup=EnhancedSchoolSetupService.get_school_setup())
            
            # Update setup
            EnhancedSchoolSetupService.update_school_setup(step=2, **data)
            flash('Basic information saved successfully!', 'success')
            
            return redirect(url_for('school_setup.registration_info'))
            
        except Exception as e:
            flash(f'Error saving information: {str(e)}', 'error')
    
    setup = EnhancedSchoolSetupService.get_school_setup()
    return render_template('school_setup/basic_info.html', setup=setup)

@school_setup_bp.route('/registration-info', methods=['GET', 'POST'])
@headteacher_required
def registration_info():
    """Step 2: Registration and legal information."""
    if request.method == 'POST':
        try:
            data = {
                'registration_number': request.form.get('registration_number'),
                'ministry_code': request.form.get('ministry_code'),
                'county': request.form.get('county'),
                'sub_county': request.form.get('sub_county'),
                'ward': request.form.get('ward'),
                'constituency': request.form.get('constituency'),
                'school_type': request.form.get('school_type'),
                'school_category': request.form.get('school_category'),
                'education_system': request.form.get('education_system')
            }
            
            EnhancedSchoolSetupService.update_school_setup(step=3, **data)
            flash('Registration information saved successfully!', 'success')
            
            return redirect(url_for('school_setup.academic_config'))
            
        except Exception as e:
            flash(f'Error saving information: {str(e)}', 'error')
    
    setup = EnhancedSchoolSetupService.get_school_setup()
    return render_template('school_setup/registration_info.html', setup=setup)

@school_setup_bp.route('/academic-config', methods=['GET', 'POST'])
@headteacher_required
def academic_config():
    """Step 3: Academic configuration."""
    if request.method == 'POST':
        try:
            data = {
                'current_academic_year': request.form.get('current_academic_year'),
                'current_term': request.form.get('current_term'),
                'total_terms_per_year': int(request.form.get('total_terms_per_year', 3)),
                'uses_streams': 'uses_streams' in request.form,
                'lowest_grade': request.form.get('lowest_grade'),
                'highest_grade': request.form.get('highest_grade'),
                'grading_system': request.form.get('grading_system'),
                'max_raw_marks_default': int(request.form.get('max_raw_marks_default', 100)),
                'pass_mark_percentage': float(request.form.get('pass_mark_percentage', 50.0))
            }

            # Store secondary grading systems in session for now
            secondary_systems = request.form.getlist('secondary_grading_systems')
            show_multiple_grades = 'show_multiple_grades' in request.form

            session['secondary_grading_systems'] = secondary_systems
            session['show_multiple_grades'] = show_multiple_grades

            EnhancedSchoolSetupService.update_school_setup(step=4, **data)
            flash('Academic configuration saved successfully!', 'success')

            return redirect(url_for('school_setup.branding'))

        except Exception as e:
            flash(f'Error saving configuration: {str(e)}', 'error')

    setup = EnhancedSchoolSetupService.get_school_setup()

    # Get secondary grading systems from session for now
    secondary_systems = session.get('secondary_grading_systems', [])
    show_multiple_grades = session.get('show_multiple_grades', False)

    return render_template('school_setup/academic_config.html',
                         setup=setup,
                         secondary_systems=secondary_systems,
                         show_multiple_grades_session=show_multiple_grades)

@school_setup_bp.route('/branding', methods=['GET', 'POST'])
@headteacher_required
def branding():
    """Step 4: School branding and visual identity."""
    if request.method == 'POST':
        try:
            # Handle logo upload
            logo_filename = None
            if 'logo_file' in request.files:
                logo_file = request.files['logo_file']
                if logo_file and logo_file.filename:
                    logo_filename = EnhancedSchoolSetupService.save_school_logo(logo_file)
            
            # Update branding data
            branding_data = {
                'primary_color': request.form.get('primary_color', '#1f7d53'),
                'secondary_color': request.form.get('secondary_color', '#18230f'),
                'accent_color': request.form.get('accent_color', '#4ade80')
            }
            
            if logo_filename:
                branding_data['logo_filename'] = logo_filename
            
            # Update school setup
            EnhancedSchoolSetupService.update_school_setup(step=5, **branding_data)
            
            # Update branding table
            branding = EnhancedSchoolSetupService.get_school_branding()
            for key, value in branding_data.items():
                setattr(branding, key, value)
            from ..extensions import db
            db.session.commit()
            
            flash('Branding configuration saved successfully!', 'success')
            return redirect(url_for('school_setup.features'))
            
        except Exception as e:
            flash(f'Error saving branding: {str(e)}', 'error')
    
    setup = EnhancedSchoolSetupService.get_school_setup()
    branding = EnhancedSchoolSetupService.get_school_branding()
    return render_template('school_setup/branding.html', setup=setup, branding=branding)

@school_setup_bp.route('/features', methods=['GET', 'POST'])
@headteacher_required
def features():
    """Step 5: Feature configuration and customization."""
    if request.method == 'POST':
        try:
            # Update feature settings
            customization = EnhancedSchoolSetupService.get_school_customization()
            
            customization.enable_analytics = 'enable_analytics' in request.form
            customization.enable_parent_portal = 'enable_parent_portal' in request.form
            customization.enable_sms_notifications = 'enable_sms_notifications' in request.form
            customization.enable_email_notifications = 'enable_email_notifications' in request.form
            customization.enable_mobile_app = 'enable_mobile_app' in request.form
            
            # Additional settings
            customization.timezone = request.form.get('timezone', 'Africa/Nairobi')
            customization.language = request.form.get('language', 'en')
            customization.currency = request.form.get('currency', 'KES')
            
            # Report settings
            setup_data = {
                'show_position': 'show_position' in request.form,
                'show_class_average': 'show_class_average' in request.form,
                'show_subject_teacher': 'show_subject_teacher' in request.form,
                'report_footer': request.form.get('report_footer', 'Powered by CbcTeachkit')
            }
            
            EnhancedSchoolSetupService.update_school_setup(step=6, **setup_data)
            from ..extensions import db
            db.session.commit()
            
            flash('Feature configuration saved successfully!', 'success')
            return redirect(url_for('school_setup.review'))
            
        except Exception as e:
            flash(f'Error saving features: {str(e)}', 'error')
    
    setup = EnhancedSchoolSetupService.get_school_setup()
    customization = EnhancedSchoolSetupService.get_school_customization()
    return render_template('school_setup/features.html', setup=setup, customization=customization)

@school_setup_bp.route('/review')
@headteacher_required
def review():
    """Step 6: Review and complete setup."""
    setup = EnhancedSchoolSetupService.get_school_setup()
    branding = EnhancedSchoolSetupService.get_school_branding()
    customization = EnhancedSchoolSetupService.get_school_customization()
    progress = EnhancedSchoolSetupService.get_setup_progress()
    
    return render_template('school_setup/review.html',
                         setup=setup,
                         branding=branding,
                         customization=customization,
                         progress=progress)

@school_setup_bp.route('/complete', methods=['POST'])
@headteacher_required
def complete_setup():
    """Complete the school setup process."""
    try:
        teacher_id = session.get('teacher_id')
        EnhancedSchoolSetupService.complete_setup(teacher_id)
        
        flash('School setup completed successfully! Your system is ready to use.', 'success')
        return redirect(url_for('admin.dashboard'))
        
    except Exception as e:
        flash(f'Error completing setup: {str(e)}', 'error')
        return redirect(url_for('school_setup.review'))

@school_setup_bp.route('/api/upload-logo', methods=['POST'])
@headteacher_required
def api_upload_logo():
    """API endpoint for logo upload."""
    try:
        if 'logo' not in request.files:
            return jsonify({'success': False, 'message': 'No logo file provided'})
        
        logo_file = request.files['logo']
        if not logo_file.filename:
            return jsonify({'success': False, 'message': 'No file selected'})
        
        filename = EnhancedSchoolSetupService.save_school_logo(logo_file)
        if filename:
            return jsonify({
                'success': True,
                'message': 'Logo uploaded successfully',
                'filename': filename,
                'url': f'/static/uploads/logos/{filename}'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to upload logo'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@school_setup_bp.route('/api/progress')
@headteacher_required
def api_progress():
    """API endpoint to get setup progress."""
    try:
        progress = EnhancedSchoolSetupService.get_setup_progress()
        setup = EnhancedSchoolSetupService.get_school_setup()
        
        return jsonify({
            'success': True,
            'progress': progress,
            'current_step': setup.setup_step,
            'completed': setup.setup_completed
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
