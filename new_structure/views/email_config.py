"""
Email Configuration views for the Hillview School Management System.
This module handles email configuration and template management for parent notifications.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import os
from ..services.auth_service import is_authenticated, get_role
from ..services.parent_email_service import ParentEmailService
from ..models import db
from ..models.parent import EmailTemplate
from ..models.user import Teacher

# Create blueprint for email configuration
email_config_bp = Blueprint('email_config', __name__, url_prefix='/email_config')

def headteacher_required(f):
    """Decorator to require headteacher authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session) or get_role(session) != 'headteacher':
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@email_config_bp.route('/dashboard')
@headteacher_required
def dashboard():
    """Email configuration dashboard."""
    try:
        # Get current SMTP configuration status
        config = ParentEmailService.get_smtp_config()
        smtp_configured = bool(config['smtp_username'] and config['smtp_password'])
        
        # Get email templates
        templates = EmailTemplate.query.order_by(EmailTemplate.template_type, EmailTemplate.name).all()
        
        # Get email statistics (if needed)
        from ..models.parent import ParentEmailLog
        total_emails = ParentEmailLog.query.count()
        sent_emails = ParentEmailLog.query.filter_by(status='sent').count()
        failed_emails = ParentEmailLog.query.filter_by(status='failed').count()
        
        return render_template('email_config_dashboard.html',
                             smtp_configured=smtp_configured,
                             smtp_server=config['smtp_server'],
                             smtp_port=config['smtp_port'],
                             smtp_username=config['smtp_username'],
                             templates=templates,
                             total_emails=total_emails,
                             sent_emails=sent_emails,
                             failed_emails=failed_emails)
    
    except Exception as e:
        flash(f'Error loading email configuration: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@email_config_bp.route('/smtp_settings', methods=['GET', 'POST'])
@headteacher_required
def smtp_settings():
    """Configure SMTP settings."""
    if request.method == 'POST':
        try:
            # This would typically save to a configuration file or database
            # For now, we'll show how to set environment variables
            smtp_server = request.form.get('smtp_server', '').strip()
            smtp_port = request.form.get('smtp_port', '').strip()
            smtp_username = request.form.get('smtp_username', '').strip()
            smtp_password = request.form.get('smtp_password', '').strip()
            use_tls = request.form.get('use_tls') == 'on'
            
            # Validation
            if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
                flash('All SMTP fields are required.', 'error')
                return render_template('smtp_settings.html')
            
            try:
                smtp_port = int(smtp_port)
                if smtp_port <= 0 or smtp_port > 65535:
                    raise ValueError("Invalid port range")
            except ValueError:
                flash('SMTP port must be a valid number between 1 and 65535.', 'error')
                return render_template('smtp_settings.html')
            
            # Create environment configuration instructions
            env_config = f"""
# Add these environment variables to your system or .env file:
SMTP_SERVER={smtp_server}
SMTP_PORT={smtp_port}
SMTP_USERNAME={smtp_username}
SMTP_PASSWORD={smtp_password}
SMTP_USE_TLS={'true' if use_tls else 'false'}
BASE_URL=http://localhost:5000
"""
            
            flash('SMTP configuration saved! Please add the environment variables to your system.', 'success')
            flash('Environment configuration has been generated. Please set these variables and restart the application.', 'info')
            
            # Store in session temporarily for display
            session['env_config'] = env_config
            
            return redirect(url_for('email_config.dashboard'))
        
        except Exception as e:
            flash(f'Error saving SMTP configuration: {str(e)}', 'error')
    
    # Get current configuration
    config = ParentEmailService.get_smtp_config()
    return render_template('smtp_settings.html', config=config)

@email_config_bp.route('/test_email')
@headteacher_required
def test_email():
    """Test email configuration."""
    try:
        success, message = ParentEmailService.test_email_configuration()
        
        if success:
            flash('Test email sent successfully! Check your inbox.', 'success')
        else:
            flash(f'Test email failed: {message}', 'error')
    
    except Exception as e:
        flash(f'Error testing email configuration: {str(e)}', 'error')
    
    return redirect(url_for('email_config.dashboard'))

@email_config_bp.route('/templates')
@headteacher_required
def templates():
    """Manage email templates."""
    try:
        templates = EmailTemplate.query.order_by(EmailTemplate.template_type, EmailTemplate.name).all()
        return render_template('email_templates.html', templates=templates)
    
    except Exception as e:
        flash(f'Error loading email templates: {str(e)}', 'error')
        return redirect(url_for('email_config.dashboard'))

@email_config_bp.route('/template/<int:template_id>')
@headteacher_required
def view_template(template_id):
    """View email template details."""
    try:
        template = EmailTemplate.query.get_or_404(template_id)
        return render_template('view_email_template.html', template=template)
    
    except Exception as e:
        flash(f'Error loading email template: {str(e)}', 'error')
        return redirect(url_for('email_config.templates'))

@email_config_bp.route('/template/<int:template_id>/edit', methods=['GET', 'POST'])
@headteacher_required
def edit_template(template_id):
    """Edit email template."""
    template = EmailTemplate.query.get_or_404(template_id)
    
    if request.method == 'POST':
        try:
            # Update template
            template.subject_template = request.form.get('subject_template', '').strip()
            template.html_template = request.form.get('html_template', '').strip()
            template.text_template = request.form.get('text_template', '').strip()
            template.is_active = request.form.get('is_active') == 'on'
            
            # Validation
            if not template.subject_template or not template.html_template:
                flash('Subject and HTML content are required.', 'error')
                return render_template('edit_email_template.html', template=template)
            
            db.session.commit()
            flash('Email template updated successfully!', 'success')
            return redirect(url_for('email_config.view_template', template_id=template.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating email template: {str(e)}', 'error')
    
    return render_template('edit_email_template.html', template=template)

@email_config_bp.route('/template/<int:template_id>/preview')
@headteacher_required
def preview_template(template_id):
    """Preview email template with sample data."""
    try:
        template = EmailTemplate.query.get_or_404(template_id)
        
        # Sample context data
        school_context = ParentEmailService.get_school_context()
        sample_context = {
            **school_context,
            'parent_name': 'John Doe',
            'student_name': 'Jane Doe',
            'admission_number': 'ADM001',
            'grade_name': 'Grade 5',
            'stream_name': 'Blue',
            'term_name': 'Term 1',
            'assessment_type': 'End of Term Exam',
            'verification_link': '#verification-link',
            'reset_link': '#reset-link',
            'portal_link': '#portal-link'
        }
        
        # Render template
        subject, html_content = ParentEmailService.render_template(template, sample_context)
        
        return render_template('preview_email_template.html', 
                             template=template,
                             subject=subject,
                             html_content=html_content,
                             sample_context=sample_context)
    
    except Exception as e:
        flash(f'Error previewing email template: {str(e)}', 'error')
        return redirect(url_for('email_config.view_template', template_id=template_id))

@email_config_bp.route('/logs')
@headteacher_required
def email_logs():
    """View email logs."""
    try:
        from ..models.parent import ParentEmailLog
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status', '')
        email_type_filter = request.args.get('email_type', '')
        
        # Build query
        query = ParentEmailLog.query
        
        if status_filter:
            query = query.filter(ParentEmailLog.status == status_filter)
        
        if email_type_filter:
            query = query.filter(ParentEmailLog.email_type == email_type_filter)
        
        # Order by most recent first
        query = query.order_by(ParentEmailLog.created_at.desc())
        
        # Paginate
        logs = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Get filter options
        statuses = db.session.query(ParentEmailLog.status).distinct().all()
        email_types = db.session.query(ParentEmailLog.email_type).distinct().all()
        
        return render_template('email_logs.html',
                             logs=logs,
                             statuses=[s[0] for s in statuses],
                             email_types=[t[0] for t in email_types],
                             current_status=status_filter,
                             current_email_type=email_type_filter)
    
    except Exception as e:
        flash(f'Error loading email logs: {str(e)}', 'error')
        return redirect(url_for('email_config.dashboard'))

@email_config_bp.route('/setup_guide')
@headteacher_required
def setup_guide():
    """Email setup guide for administrators."""
    return render_template('email_setup_guide.html')
