"""
Parent Portal views for the Hillview School Management System.
This module handles parent authentication and dashboard functionality.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from datetime import datetime
import secrets
import string

from ..models import db
# ParentEmailLog may not exist yet; import defensively
try:
    from ..models.parent import Parent, ParentStudent, ParentEmailLog
except ImportError:
    from ..models.parent import Parent, ParentStudent
    ParentEmailLog = None  # Optional feature not yet available
from ..models.academic import Student, Grade, Stream
from ..services.parent_email_service import ParentEmailService

# Create blueprint for parent portal
parent_simple_bp = Blueprint('parent', __name__, url_prefix='/parent')

def parent_required(f):
    """Decorator to require parent authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'parent_id' not in session:
            return redirect(url_for('parent.login'))
        
        # Check if parent account is active
        parent = Parent.query.get(session['parent_id'])
        if not parent or not parent.is_active:
            session.clear()
            flash('Your account has been deactivated. Please contact the school.', 'error')
            return redirect(url_for('parent.login'))
        
        return f(*args, **kwargs)
    return decorated_function

@parent_simple_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Parent login page."""
    
    def get_context():
        """Get template context variables."""
        try:
            from ..services.school_config_service import SchoolConfigService
            school_info = SchoolConfigService.get_school_info_dict()
            return {'school_info': school_info}
        except:
            # Fallback to hardcoded values if service fails
            return {
                'school_info': {
                    'school_name': 'Hillview School',
                    'logo_url': '/static/uploads/logos/optimized_school_logo_1750595986_hvs.jpg'
                }
            }
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '').strip()
            
            if not email or not password:
                flash('Email and password are required.', 'error')
                return render_template('parent_login.html', **get_context())
            
            # Find parent by email
            parent = Parent.query.filter_by(email=email).first()
            
            if not parent:
                flash('Invalid email or password.', 'error')
                return render_template('parent_login.html', **get_context())
            
            # Check if account is locked
            if parent.is_locked():
                flash('Account is temporarily locked due to multiple failed login attempts. Please try again later.', 'error')
                return render_template('parent_login.html', **get_context())
            
            # Check password
            if not parent.check_password(password):
                parent.lock_account()
                db.session.commit()
                flash('Invalid email or password.', 'error')
                return render_template('parent_login.html', **get_context())
            
            # Check if account is active
            if not parent.is_active:
                flash('Your account has been deactivated. Please contact the school.', 'error')
                return render_template('parent_login.html', **get_context())
            
            # Successful login
            parent.unlock_account()
            parent.last_login = datetime.utcnow()
            db.session.commit()
            
            session['parent_id'] = parent.id
            session['parent_email'] = parent.email
            session.permanent = True
            
            flash(f'Welcome back, {parent.get_full_name()}!', 'success')
            return redirect(url_for('parent.dashboard'))
        
        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')
    
    # Provide context for template
    return render_template('parent_login.html', **get_context())

@parent_simple_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Parent registration page."""
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            # Validation
            if not all([first_name, last_name, email, password, confirm_password]):
                flash('All fields except phone are required.', 'error')
                return render_template('parent_register.html')
            
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('parent_register.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
                return render_template('parent_register.html')
            
            # Check if email already exists
            existing_parent = Parent.query.filter_by(email=email).first()
            if existing_parent:
                flash('An account with this email already exists.', 'error')
                return render_template('parent_register.html')
            
            # Create parent account
            parent = Parent(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                is_verified=False,
                is_active=True
            )
            parent.set_password(password)
            
            db.session.add(parent)
            db.session.commit()
            
            # Send verification email
            success, message = ParentEmailService.send_verification_email(parent)
            if success:
                flash('Account created successfully! Please check your email to verify your account.', 'success')
                flash('You will need to contact the school to link your children to your account.', 'info')
            else:
                flash('Account created, but verification email could not be sent. Please contact the school.', 'warning')
            
            return redirect(url_for('parent.login'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Registration error: {str(e)}', 'error')
    
    return render_template('parent_register.html')

@parent_simple_bp.route('/dashboard')
@parent_required
def dashboard():
    """Parent dashboard."""
    try:
        parent = Parent.query.get(session['parent_id'])
        
        # Get linked children with their class information
        children_query = db.session.query(
            ParentStudent, Student, Grade, Stream
        ).join(
            Student, ParentStudent.student_id == Student.id
        ).join(
            Grade, Student.grade_id == Grade.id
        ).join(
            Stream, Student.stream_id == Stream.id
        ).filter(
            ParentStudent.parent_id == parent.id
        ).order_by(Grade.name, Stream.name, Student.name)
        
        children = children_query.all()
        
        # Get recent email notifications (if model available)
        if ParentEmailLog:
            recent_emails = ParentEmailLog.query.filter_by(
                parent_id=parent.id
            ).order_by(ParentEmailLog.created_at.desc()).limit(5).all()
        else:
            recent_emails = []
        
        return render_template('parent_management_dashboard_enhanced.html',
                             parent=parent,
                             children=children,
                             recent_emails=recent_emails)
    
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('parent.login'))

@parent_simple_bp.route('/profile')
@parent_required
def profile():
    """Parent profile page."""
    try:
        parent = Parent.query.get(session['parent_id'])
        return render_template('parent_profile.html', parent=parent)
    
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'error')
        return redirect(url_for('parent.dashboard'))

@parent_simple_bp.route('/children')
@parent_required
def children():
    """View children and their academic information."""
    try:
        parent = Parent.query.get(session['parent_id'])
        
        # Get linked children with detailed information
        children_query = db.session.query(
            ParentStudent, Student, Grade, Stream
        ).join(
            Student, ParentStudent.student_id == Student.id
        ).join(
            Grade, Student.grade_id == Grade.id
        ).join(
            Stream, Student.stream_id == Stream.id
        ).filter(
            ParentStudent.parent_id == parent.id
        ).order_by(Grade.name, Stream.name, Student.name)
        
        children = children_query.all()
        
        return render_template('parent_children.html',
                             parent=parent,
                             children=children)
    
    except Exception as e:
        flash(f'Error loading children information: {str(e)}', 'error')
        return redirect(url_for('parent.dashboard'))

@parent_simple_bp.route('/verify/<token>')
def verify_email(token):
    """Verify parent email address."""
    try:
        parent = Parent.query.filter_by(verification_token=token).first()
        
        if not parent:
            flash('Invalid verification link.', 'error')
            return redirect(url_for('parent.login'))
        
        # Check if token is still valid (24 hours)
        if parent.verification_sent_at:
            time_diff = datetime.utcnow() - parent.verification_sent_at
            if time_diff.total_seconds() > 86400:  # 24 hours
                flash('Verification link has expired. Please contact the school.', 'error')
                return redirect(url_for('parent.login'))
        
        # Verify the account
        parent.is_verified = True
        parent.verification_token = None
        parent.verification_sent_at = None
        db.session.commit()
        
        flash('Email verified successfully! You can now log in.', 'success')
        return redirect(url_for('parent.login'))
    
    except Exception as e:
        flash(f'Verification error: {str(e)}', 'error')
        return redirect(url_for('parent.login'))

@parent_simple_bp.route('/logout')
def logout():
    """Parent logout."""
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('parent.login'))

@parent_simple_bp.route('/resend-verification')
@parent_required
def resend_verification():
    """Resend email verification."""
    try:
        parent = Parent.query.get(session['parent_id'])
        
        if parent.is_verified:
            flash('Your email is already verified.', 'info')
            return redirect(url_for('parent.profile'))
        
        # Send verification email
        success, message = ParentEmailService.send_verification_email(parent)
        if success:
            flash('Verification email sent! Please check your inbox.', 'success')
        else:
            flash('Failed to send verification email. Please try again.', 'error')
        
        return redirect(url_for('parent.profile'))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('parent.profile'))

@parent_simple_bp.route('/child/<int:child_id>/grades')
@parent_required
def child_grades(child_id):
    """View child's grades and academic performance."""
    try:
        parent = Parent.query.get(session['parent_id'])
        
        # Verify this child belongs to this parent
        child_link = ParentStudent.query.filter_by(
            parent_id=parent.id, 
            student_id=child_id
        ).first()
        
        if not child_link:
            flash('You do not have access to this child\'s records.', 'error')
            return redirect(url_for('parent.dashboard'))
        
        # Get child information
        child_query = db.session.query(Student, Grade, Stream)\
            .join(Grade, Student.grade_id == Grade.id)\
            .join(Stream, Student.stream_id == Stream.id)\
            .filter(Student.id == child_id).first()
        
        if not child_query:
            flash('Child not found.', 'error')
            return redirect(url_for('parent.dashboard'))
        
        child, grade, stream = child_query
        
        # For now, return mock data since we don't have marks table integration yet
        # TODO: Integrate with actual marks/assessment tables when available
        grades_data = [
            {
                'term': 'term_1',
                'average': 85.5,
                'subjects': [
                    {'name': 'Mathematics', 'entrance': 88, 'mid_term': 85, 'end_term': 87, 'average': 86.7, 'remarks': 'Excellent work'},
                    {'name': 'English', 'entrance': 82, 'mid_term': 84, 'end_term': 86, 'average': 84.0, 'remarks': 'Good progress'},
                    {'name': 'Science', 'entrance': 90, 'mid_term': 88, 'end_term': 89, 'average': 89.0, 'remarks': 'Outstanding performance'},
                ]
            }
        ]
        
        child_info = {
            'id': child.id,
            'name': child.name,
            'admission_number': child.admission_number,
            'grade': grade.name,
            'stream': stream.name
        }
        
        return render_template('parent_child_grades.html',
                             child=child_info,
                             grades_data=grades_data,
                             parent=parent)
    
    except Exception as e:
        flash(f'Error loading grades: {str(e)}', 'error')
        return redirect(url_for('parent.dashboard'))

@parent_simple_bp.route('/child/<int:child_id>/progress')
@parent_required
def child_progress(child_id):
    """View child's academic progress and trends."""
    try:
        parent = Parent.query.get(session['parent_id'])
        
        # Verify this child belongs to this parent
        child_link = ParentStudent.query.filter_by(
            parent_id=parent.id, 
            student_id=child_id
        ).first()
        
        if not child_link:
            flash('You do not have access to this child\'s records.', 'error')
            return redirect(url_for('parent.dashboard'))
        
        # Get child information
        child_query = db.session.query(Student, Grade, Stream)\
            .join(Grade, Student.grade_id == Grade.id)\
            .join(Stream, Student.stream_id == Stream.id)\
            .filter(Student.id == child_id).first()
        
        if not child_query:
            flash('Child not found.', 'error')
            return redirect(url_for('parent.dashboard'))
        
        child, grade, stream = child_query
        
        # Mock progress data - TODO: Replace with real data from marks tables
        progress_data = {
            'overall_average': 85.5,
            'class_rank': 5,
            'attendance_rate': 95.2,
            'total_subjects': 8,
            'subjects_progress': [
                {'name': 'Mathematics', 'current_score': 87, 'trend': 'up', 'trend_text': '+3% from last term'},
                {'name': 'English', 'current_score': 84, 'trend': 'stable', 'trend_text': 'No change'},
                {'name': 'Science', 'current_score': 89, 'trend': 'up', 'trend_text': '+5% from last term'},
            ],
            'total_attendance': 95.2,
            'days_present': 190,
            'days_absent': 10,
            'school_days': 200,
            'recommendations': [
                {'area': 'Mathematics', 'suggestion': 'Focus on algebra concepts and practice more word problems'},
                {'area': 'Study Habits', 'suggestion': 'Maintain consistent daily study schedule'}
            ],
            'teacher_comments': [
                {'subject': 'Mathematics', 'teacher': 'Mr. Smith', 'comment': 'Shows great improvement in problem-solving', 'date': '2025-01-15'},
                {'subject': 'English', 'teacher': 'Ms. Johnson', 'comment': 'Excellent reading comprehension skills', 'date': '2025-01-14'}
            ]
        }
        
        child_info = {
            'id': child.id,
            'name': child.name,
            'admission_number': child.admission_number,
            'grade': grade.name,
            'stream': stream.name
        }
        
        return render_template('parent_child_progress.html',
                             child=child_info,
                             parent=parent,
                             **progress_data)
    
    except Exception as e:
        flash(f'Error loading progress: {str(e)}', 'error')
        return redirect(url_for('parent.dashboard'))

@parent_simple_bp.route('/child/<int:child_id>/reports')
@parent_required
def child_reports(child_id):
    """View all reports for a specific child."""
    try:
        parent = Parent.query.get(session['parent_id'])
        
        # Verify this child belongs to this parent
        child_link = ParentStudent.query.filter_by(
            parent_id=parent.id, 
            student_id=child_id
        ).first()
        
        if not child_link:
            flash('You do not have access to this child\'s records.', 'error')
            return redirect(url_for('parent.dashboard'))
        
        # Get child information
        child_query = db.session.query(Student, Grade, Stream)\
            .join(Grade, Student.grade_id == Grade.id)\
            .join(Stream, Student.stream_id == Stream.id)\
            .filter(Student.id == child_id).first()
        
        if not child_query:
            flash('Child not found.', 'error')
            return redirect(url_for('parent.dashboard'))
        
        child, grade, stream = child_query
        
        # Get filter parameters
        selected_year = request.args.get('year', '')
        selected_term = request.args.get('term', '')
        selected_assessment = request.args.get('assessment', '')
        
        # Mock reports data - TODO: Replace with real report data
        available_years = ['2024', '2025']
        reports = [
            {
                'id': 1,
                'title': 'Term 1 Mid-Term Report',
                'term': 'term_1',
                'assessment_type': 'mid_term',
                'status': 'available',
                'generated_date': datetime(2025, 1, 15),
                'overall_average': 85.5,
                'class_rank': 5
            },
            {
                'id': 2,
                'title': 'Term 1 End-Term Report',
                'term': 'term_1',
                'assessment_type': 'end_term',
                'status': 'processing',
                'generated_date': None,
                'overall_average': None,
                'class_rank': None
            }
        ]
        
        child_info = {
            'id': child.id,
            'name': child.name,
            'admission_number': child.admission_number,
            'grade': grade.name,
            'stream': stream.name
        }
        
        return render_template('parent_child_reports.html',
                             child=child_info,
                             reports=reports,
                             available_years=available_years,
                             selected_year=selected_year,
                             selected_term=selected_term,
                             selected_assessment=selected_assessment,
                             parent=parent)
    
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'error')
        return redirect(url_for('parent.dashboard'))

@parent_simple_bp.route('/student/<int:student_id>/report/<int:report_id>')
@parent_required
def view_individual_report(student_id, report_id):
    """View individual student report."""
    try:
        parent = Parent.query.get(session['parent_id'])
        
        # Verify this child belongs to this parent
        child_link = ParentStudent.query.filter_by(
            parent_id=parent.id, 
            student_id=student_id
        ).first()
        
        if not child_link:
            flash('You do not have access to this student\'s records.', 'error')
            return redirect(url_for('parent.dashboard'))
        
        # Get student information
        student_query = db.session.query(Student, Grade, Stream)\
            .join(Grade, Student.grade_id == Grade.id)\
            .join(Stream, Student.stream_id == Stream.id)\
            .filter(Student.id == student_id).first()
        
        if not student_query:
            flash('Student not found.', 'error')
            return redirect(url_for('parent.dashboard'))
        
        student, grade, stream = student_query
        
        # Mock report data - TODO: Replace with real report data from marks tables
        report_data = {
            'student_name': student.name,
            'admission_no': student.admission_number,
            'grade': grade.name,
            'stream': stream.name,
            'term': 'term_1',
            'assessment_type': 'mid_term',
            'academic_year': '2025',
            'avg_percentage': 85.5,
            'total': 683,
            'total_possible_marks': 800,
            'mean_points': 7.2,
            'table_data': [
                {
                    'subject': 'Mathematics',
                    'entrance': 88, 'mid_term': 85, 'end_term': 87, 'avg': 87,
                    'current_assessment': 85,
                    'grade': 'ME1',
                    'remarks': 'Good performance'
                },
                {
                    'subject': 'English',
                    'entrance': 82, 'mid_term': 84, 'end_term': 86, 'avg': 84,
                    'current_assessment': 84,
                    'grade': 'ME1',
                    'remarks': 'Steady progress'
                },
                {
                    'subject': 'Science',
                    'entrance': 90, 'mid_term': 88, 'end_term': 89, 'avg': 89,
                    'current_assessment': 88,
                    'grade': 'EE2',
                    'remarks': 'Excellent work'
                }
            ],
            'subject_teachers': {
                'Mathematics': {'full_name': 'Mr. John Smith', 'username': 'j.smith'},
                'English': {'full_name': 'Ms. Jane Johnson', 'username': 'j.johnson'},
                'Science': {'full_name': 'Dr. Mary Wilson', 'username': 'm.wilson'}
            },
            'class_teacher_comment': 'Shows consistent effort and improvement across all subjects.',
            'headteacher_comment': 'Keep up the excellent work!',
            'general_remarks': 'A dedicated student with great potential.',
            'term_info': {'next_term_opening_date': '2025-02-15'},
            'school_info': {
                'school_name': 'Hillview School',
                'address': '123 Education Street',
                'phone': '+254-123-456789',
                'email': 'info@hillviewschool.ac.ke',
                'logo': None
            }
        }
        
        return render_template('parent_individual_report.html',
                             student_id=student_id,
                             report_id=report_id,
                             **report_data)
    
    except Exception as e:
        flash(f'Error loading report: {str(e)}', 'error')
        return redirect(url_for('parent.dashboard'))

@parent_simple_bp.route('/reports/archive')
@parent_required
def reports_archive():
    """View all reports archive for all children."""
    try:
        parent = Parent.query.get(session['parent_id'])
        
        # Get all children for this parent
        children_query = db.session.query(Student, Grade, Stream)\
            .join(ParentStudent, Student.id == ParentStudent.student_id)\
            .join(Grade, Student.grade_id == Grade.id)\
            .join(Stream, Student.stream_id == Stream.id)\
            .filter(ParentStudent.parent_id == parent.id)\
            .order_by(Grade.name, Stream.name, Student.name)
        
        children = children_query.all()
        
        # Get filter parameters
        selected_year = request.args.get('year', '')
        selected_term = request.args.get('term', '')
        selected_assessment = request.args.get('assessment', '')
        selected_child = request.args.get('child', '')
        search_query = request.args.get('search', '')
        
        # Mock archive data - TODO: Replace with real data
        available_years = ['2023', '2024', '2025']
        
        # Group reports by year
        reports_by_year = {
            '2025': [
                {
                    'id': 1,
                    'child_name': children[0][0].name if children else 'John Doe',
                    'student_id': children[0][0].id if children else 1,
                    'grade': 'Grade 5',
                    'stream': 'A',
                    'term': 'term_1',
                    'assessment_type': 'mid_term',
                    'generated_date': datetime(2025, 1, 15),
                    'overall_average': 85.5,
                    'performance_level': 'excellent'
                }
            ] if children else [],
            '2024': [
                {
                    'id': 2,
                    'child_name': children[0][0].name if children else 'John Doe',
                    'student_id': children[0][0].id if children else 1,
                    'grade': 'Grade 4',
                    'stream': 'A',
                    'term': 'term_3',
                    'assessment_type': 'end_term',
                    'generated_date': datetime(2024, 11, 30),
                    'overall_average': 82.0,
                    'performance_level': 'good'
                }
            ] if children else []
        }
        
        archive_stats = {
            'total_reports': sum(len(reports) for reports in reports_by_year.values()),
            'total_children': len(children),
            'academic_years_count': len(available_years),
            'total_downloads': 45  # Mock data
        }
        
        children_info = []
        for student, grade, stream in children:
            children_info.append({
                'id': student.id,
                'name': student.name,
                'admission_number': student.admission_number,
                'grade': grade.name,
                'stream': stream.name
            })
        
        return render_template('parent_reports_archive.html',
                             children=children_info,
                             reports_by_year=reports_by_year,
                             available_years=available_years,
                             selected_year=selected_year,
                             selected_term=selected_term,
                             selected_assessment=selected_assessment,
                             selected_child=selected_child,
                             search_query=search_query,
                             **archive_stats)
    
    except Exception as e:
        flash(f'Error loading reports archive: {str(e)}', 'error')
        return redirect(url_for('parent.dashboard'))

@parent_simple_bp.route('/download/report/<int:student_id>/<int:report_id>')
@parent_required
def download_report(student_id, report_id):
    """Download individual report as PDF."""
    try:
        parent = Parent.query.get(session['parent_id'])
        
        # Verify this child belongs to this parent
        child_link = ParentStudent.query.filter_by(
            parent_id=parent.id, 
            student_id=student_id
        ).first()
        
        if not child_link:
            flash('You do not have access to this student\'s records.', 'error')
            return redirect(url_for('parent.dashboard'))
        
        # TODO: Implement actual PDF generation and download
        flash('PDF download feature will be implemented soon.', 'info')
        return redirect(url_for('parent.view_individual_report', 
                              student_id=student_id, 
                              report_id=report_id))
    
    except Exception as e:
        flash(f'Error downloading report: {str(e)}', 'error')
        return redirect(url_for('parent.dashboard'))

@parent_simple_bp.route('/download/multiple', methods=['POST'])
@parent_required
def download_multiple_reports():
    """Download multiple reports as ZIP file."""
    try:
        report_ids = request.form.getlist('report_ids[]')
        
        if not report_ids:
            flash('No reports selected for download.', 'error')
            return redirect(url_for('parent.reports_archive'))
        
        # TODO: Implement bulk download functionality
        flash(f'Bulk download of {len(report_ids)} reports will be implemented soon.', 'info')
        return redirect(url_for('parent.reports_archive'))
    
    except Exception as e:
        flash(f'Error downloading reports: {str(e)}', 'error')
        return redirect(url_for('parent.reports_archive'))

@parent_simple_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page."""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            
            if not email:
                flash('Email address is required.', 'error')
                return render_template('parent_forgot_password.html')
            
            parent = Parent.query.filter_by(email=email).first()
            
            if parent and parent.is_active:
                success, message = ParentEmailService.send_password_reset_email(parent)
                if success:
                    flash('Password reset instructions have been sent to your email.', 'success')
                else:
                    flash('Could not send password reset email. Please contact the school.', 'error')
            else:
                # Don't reveal if email exists or not for security
                flash('If an account with this email exists, password reset instructions have been sent.', 'info')
            
            return redirect(url_for('parent.login'))
        
        except Exception as e:
            flash(f'Error processing request: {str(e)}', 'error')
    
    return render_template('parent_forgot_password.html')
