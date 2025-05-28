"""
Setup wizard for first-time school configuration.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import SchoolConfiguration, Teacher, Grade, Stream, Subject, Term, AssessmentType
from ..services.school_config_service import SchoolConfigService
from ..extensions import db
from werkzeug.security import generate_password_hash

# Create a blueprint for setup routes
setup_bp = Blueprint('setup', __name__, url_prefix='/setup')

def is_setup_complete():
    """Check if the initial setup has been completed."""
    config = SchoolConfiguration.query.first()
    if not config:
        return False
    
    # Check if school name has been customized (not default)
    if config.school_name == "School Name" or config.school_name == "Your School Name":
        return False
    
    # Check if there's at least one teacher
    if Teacher.query.count() == 0:
        return False
    
    return True

@setup_bp.route('/')
def index():
    """Setup wizard main page."""
    if is_setup_complete():
        return redirect(url_for('auth.index'))
    
    return render_template('setup_wizard.html')

@setup_bp.route('/step1', methods=['GET', 'POST'])
def step1_school_info():
    """Step 1: School Information."""
    if is_setup_complete():
        return redirect(url_for('auth.index'))
    
    error_message = None
    
    if request.method == 'POST':
        try:
            # Get form data
            school_name = request.form.get('school_name', '').strip()
            school_motto = request.form.get('school_motto', '').strip()
            school_address = request.form.get('school_address', '').strip()
            school_phone = request.form.get('school_phone', '').strip()
            school_email = request.form.get('school_email', '').strip()
            headteacher_name = request.form.get('headteacher_name', '').strip()
            
            # Validate required fields
            if not school_name:
                error_message = "School name is required."
            else:
                # Update configuration
                config_data = {
                    'school_name': school_name,
                    'school_motto': school_motto,
                    'school_address': school_address,
                    'school_phone': school_phone,
                    'school_email': school_email,
                    'headteacher_name': headteacher_name
                }
                
                SchoolConfigService.update_school_config(**config_data)
                return redirect(url_for('setup.step2_admin_account'))
                
        except Exception as e:
            error_message = f"Error saving school information: {str(e)}"
    
    # Get current configuration
    config = SchoolConfigService.get_school_config()
    
    return render_template('setup_step1.html', 
                         config=config,
                         error_message=error_message)

@setup_bp.route('/step2', methods=['GET', 'POST'])
def step2_admin_account():
    """Step 2: Create Admin Account."""
    if is_setup_complete():
        return redirect(url_for('auth.index'))
    
    error_message = None
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            # Validate input
            if not username or not password:
                error_message = "Username and password are required."
            elif len(password) < 6:
                error_message = "Password must be at least 6 characters long."
            elif password != confirm_password:
                error_message = "Passwords do not match."
            else:
                # Check if admin already exists
                existing_admin = Teacher.query.filter_by(role='headteacher').first()
                if existing_admin:
                    # Update existing admin
                    existing_admin.username = username
                    existing_admin.password = password  # Note: In production, use proper hashing
                else:
                    # Create new admin
                    admin = Teacher(
                        username=username,
                        password=password,  # Note: In production, use proper hashing
                        role='headteacher'
                    )
                    db.session.add(admin)
                
                db.session.commit()
                return redirect(url_for('setup.step3_basic_data'))
                
        except Exception as e:
            error_message = f"Error creating admin account: {str(e)}"
    
    return render_template('setup_step2.html', error_message=error_message)

@setup_bp.route('/step3', methods=['GET', 'POST'])
def step3_basic_data():
    """Step 3: Set up basic academic data."""
    if is_setup_complete():
        return redirect(url_for('auth.index'))
    
    error_message = None
    success_message = None
    
    if request.method == 'POST':
        try:
            # Get form data
            academic_year = request.form.get('academic_year', '').strip()
            current_term = request.form.get('current_term', '').strip()
            use_streams = request.form.get('use_streams') == 'on'
            grades_data = request.form.get('grades', '').strip()
            
            if not academic_year or not current_term:
                error_message = "Academic year and current term are required."
            else:
                # Update school configuration
                SchoolConfigService.update_school_config(
                    current_academic_year=academic_year,
                    current_term=current_term,
                    use_streams=use_streams
                )
                
                # Create basic grades if provided
                if grades_data:
                    grade_names = [g.strip() for g in grades_data.split(',') if g.strip()]
                    for grade_name in grade_names:
                        if not Grade.query.filter_by(level=grade_name).first():
                            grade = Grade(level=grade_name)
                            db.session.add(grade)
                            
                            # If using streams, create default streams
                            if use_streams:
                                for stream_name in ['A', 'B']:
                                    stream = Stream(name=stream_name, grade=grade)
                                    db.session.add(stream)
                            else:
                                # Create a single default stream
                                stream = Stream(name='Main', grade=grade)
                                db.session.add(stream)
                
                # Create basic terms if they don't exist
                term_names = ['Term 1', 'Term 2', 'Term 3']
                for term_name in term_names:
                    if not Term.query.filter_by(name=term_name).first():
                        term = Term(
                            name=term_name,
                            academic_year=academic_year,
                            is_current=(term_name == current_term)
                        )
                        db.session.add(term)
                
                # Create basic assessment types
                assessment_types = [
                    {'name': 'Mid Term', 'weight': 30},
                    {'name': 'End Term', 'weight': 70}
                ]
                for assessment_data in assessment_types:
                    if not AssessmentType.query.filter_by(name=assessment_data['name']).first():
                        assessment = AssessmentType(
                            name=assessment_data['name'],
                            weight=assessment_data['weight']
                        )
                        db.session.add(assessment)
                
                db.session.commit()
                return redirect(url_for('setup.complete'))
                
        except Exception as e:
            error_message = f"Error setting up basic data: {str(e)}"
    
    return render_template('setup_step3.html', error_message=error_message)

@setup_bp.route('/complete')
def complete():
    """Setup completion page."""
    if not is_setup_complete():
        return redirect(url_for('setup.index'))
    
    config = SchoolConfigService.get_school_config()
    return render_template('setup_complete.html', config=config)
