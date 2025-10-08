"""
Parent Portal views for the Hillview School Management System.
This module handles parent authentication and dashboard functionality.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from datetime import datetime, timedelta
import secrets
import string
import time

from ..models import db
# ParentEmailLog may not exist yet; import defensively
try:
    from ..models.parent import Parent, ParentStudent, ParentEmailLog
except ImportError:
    from ..models.parent import Parent, ParentStudent
    ParentEmailLog = None  # Optional feature not yet available
from ..models.academic import Student, Grade, Stream
from ..services.parent_email_service import ParentEmailService
from ..security.security_manager import comprehensive_security
from ..security.csrf_protection import csrf_protect
from ..extensions import limiter

# Create blueprint for parent portal
parent_simple_bp = Blueprint('parent', __name__, url_prefix='/parent')

def parent_required(f):
    """Enhanced decorator with maximum security for parent authentication."""
    @wraps(f)
    @limiter.limit("60 per minute")  # Rate limiting
    @comprehensive_security()  # Full security stack
    def decorated_function(*args, **kwargs):
        # Session validation
        if 'parent_id' not in session:
            flash('Please log in to access your dashboard.', 'info')
            return redirect(url_for('parent.login'))
        
        # Check if parent account exists and is active
        parent = Parent.query.get(session['parent_id'])
        if not parent or not parent.is_active:
            session.clear()
            flash('Your account has been deactivated. Please contact the school.', 'error')
            return redirect(url_for('parent.login'))
        
        # Enhanced session security checks
        current_time = time.time()
        
        # Session timeout (2 hours)
        last_activity = session.get('last_activity', 0)
        if current_time - last_activity > 7200:  # 2 hours
            session.clear()
            flash('Your session has expired. Please log in again.', 'info')
            return redirect(url_for('parent.login'))
        
        # IP binding for security
        if 'ip_address' not in session:
            session['ip_address'] = request.remote_addr
        elif session['ip_address'] != request.remote_addr:
            # IP changed - potential security violation
            session.clear()
            flash('Security violation detected. Please log in again.', 'error')
            return redirect(url_for('parent.login'))
        
        # User agent consistency check
        if 'user_agent' not in session:
            session['user_agent'] = request.headers.get('User-Agent', '')
        elif session['user_agent'] != request.headers.get('User-Agent', ''):
            # User agent changed - potential security risk
            session.clear()
            flash('Security violation detected. Please log in again.', 'error')
            return redirect(url_for('parent.login'))
        
        # Update session activity
        session['last_activity'] = current_time
        session.permanent = True
        
        return f(*args, **kwargs)
    return decorated_function

# Internal helper: normalize term and assessment names to exact DB values (case-insensitive)
def _normalize_term_and_assessment(term_candidate: str, assessment_candidate: str):
    try:
        from ..models.academic import Term as TermModel, AssessmentType as ATModel
        term_obj = TermModel.query.filter(db.func.lower(TermModel.name) == (term_candidate or '').strip().lower()).first()
        at_obj = ATModel.query.filter(db.func.lower(ATModel.name) == (assessment_candidate or '').strip().lower()).first()
        norm_term = term_obj.name if term_obj else term_candidate
        norm_assessment = at_obj.name if at_obj else assessment_candidate
        return norm_term, norm_assessment
    except Exception:
        return term_candidate, assessment_candidate

# Normalize various shapes returned by get_class_report_data to a consistent dict
def _coerce_class_report_result(result):
    """Coerce legacy return types from get_class_report_data into a dict.

    - dict -> returned as-is
    - list -> {"class_data": list, "subjects": [], "total_marks": 100}
    - tuple(len=2/3) -> map to (class_data, subjects, total)
    - other -> error shaped dict
    """
    try:
        if result is None:
            return {"class_data": [], "subjects": [], "total_marks": 100, "error": "No data"}
        if isinstance(result, dict):
            return result
        if isinstance(result, list):
            return {"class_data": result, "subjects": [], "total_marks": 100}
        if isinstance(result, tuple):
            if len(result) == 2 and isinstance(result[0], list):
                return {"class_data": result[0], "subjects": result[1] or [], "total_marks": 100}
            if len(result) == 3 and isinstance(result[0], list):
                return {"class_data": result[0], "subjects": result[1] or [], "total_marks": result[2] or 100}
        return {"class_data": [], "subjects": [], "total_marks": 100, "error": f"Unexpected type: {type(result).__name__}"}
    except Exception as e:
        return {"class_data": [], "subjects": [], "total_marks": 100, "error": str(e)}

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
    """Parent dashboard showing aggregated children and recent notifications."""
    try:
        parent = Parent.query.get(session['parent_id'])

        # Get school info for header/branding
        try:
            from ..services.school_config_service import SchoolConfigService
            school_info = SchoolConfigService.get_school_info_dict()
        except Exception:
            school_info = {
                'school_name': 'Hillview School',
                'logo_url': '/static/uploads/logos/optimized_school_logo_1750595986_hvs.jpg'
            }

        # Get linked children with their class information (include unassigned class via outer joins)
        children_query = db.session.query(
            ParentStudent, Student, Grade, Stream
        ).join(
            Student, ParentStudent.student_id == Student.id
        ).outerjoin(
            Grade, Student.grade_id == Grade.id
        ).outerjoin(
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

        return render_template(
            'parent_dashboard.html',
            parent=parent,
            children=children,
            recent_emails=recent_emails,
            school_info=school_info
        )

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
        
        # Get linked children with detailed information (outer joins to include unassigned)
        children_query = db.session.query(
            ParentStudent, Student, Grade, Stream
        ).join(
            Student, ParentStudent.student_id == Student.id
        ).outerjoin(
            Grade, Student.grade_id == Grade.id
        ).outerjoin(
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
    """Redirect to the student's latest available individual report in the exact class-teacher format."""
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
        child_query = db.session.query(Student, Grade, Stream) \
            .outerjoin(Grade, Student.grade_id == Grade.id) \
            .outerjoin(Stream, Student.stream_id == Stream.id) \
            .filter(Student.id == child_id).first()

        if not child_query:
            flash('Child not found.', 'error')
            return redirect(url_for('parent.dashboard'))

        student, grade, stream = child_query

        # Find the latest reportable term + assessment for this student from marks
        from new_structure.models.academic import Mark, Term, AssessmentType
        from sqlalchemy import desc

        latest = db.session.query(Term.name.label('term_name'),
                                   Term.academic_year.label('academic_year'),
                                   AssessmentType.name.label('assessment_name')) \
            .join(Mark, Term.id == Mark.term_id) \
            .join(AssessmentType, Mark.assessment_type_id == AssessmentType.id) \
            .filter(Mark.student_id == student.id) \
            .order_by(desc(Term.academic_year), desc(Term.name), desc(AssessmentType.name)) \
            .first()

        if not latest:
            flash(f'No marks have been entered for {student.name} yet.', 'info')
            return redirect(url_for('parent.child_reports', child_id=student.id))

        term_name, assessment_name = _normalize_term_and_assessment(latest.term_name, latest.assessment_name)

        # Build a robust report_id that our parser can understand (with explicit "Stream")
        grade_name = (grade.name if grade else 'Grade')
        stream_letter = (stream.name if stream else 'A')

        # Tokenize term name (e.g., "Term 3" -> ["Term", "3"]) preserving original case
        term_tokens = term_name.split()
        if len(term_tokens) >= 2:
            term_part = f"{term_tokens[0]}_{term_tokens[1]}"
        else:
            # Fallback
            term_part = term_name.replace(' ', '_')

        assessment_part = assessment_name.replace(' ', '_')
        grade_part = grade_name.replace(' ', '_')

        report_id = f"{grade_part}_Stream_{stream_letter}_{term_part}_{assessment_part}"

        # Reuse the parent individual report renderer (exact template as class teacher)
        return redirect(url_for('parent.view_individual_report', student_id=student.id, report_id=report_id))

    except Exception as e:
        flash(f'Error loading latest report: {str(e)}', 'error')
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
            .outerjoin(Grade, Student.grade_id == Grade.id)\
            .outerjoin(Stream, Student.stream_id == Stream.id)\
            .filter(Student.id == child_id).first()
        
        if not child_query:
            flash('Child not found.', 'error')
            return redirect(url_for('parent.dashboard'))
        
        child, grade, stream = child_query
        
        # Get real progress data from marks tables
        from new_structure.models.academic import Mark, Subject, Term, AssessmentType
        
        try:
            # Get all terms and calculate overall progress
            student_marks = db.session.query(Mark, Subject, Term, AssessmentType)\
                .join(Subject, Mark.subject_id == Subject.id)\
                .join(Term, Mark.term_id == Term.id)\
                .join(AssessmentType, Mark.assessment_type_id == AssessmentType.id)\
                .filter(Mark.student_id == child.id)\
                .order_by(Term.academic_year.desc(), Term.name.desc(), Subject.name)\
                .all()
            
            if not student_marks:
                progress_data = {
                    'overall_average': 0,
                    'class_rank': None,
                    'attendance_rate': 0,
                    'total_subjects': 0,
                    'subjects_progress': [],
                    'total_attendance': 0,
                    'days_present': 0,
                    'days_absent': 0,
                    'school_days': 0,
                    'recommendations': [
                        {'area': 'General', 'suggestion': 'No marks available yet. Speak with teachers about assessment schedule.'}
                    ],
                    'teacher_comments': [],
                    'message': f'No academic data available for {child.name} yet.'
                }
            else:
                # Calculate overall average across all marks
                total_percentage = sum(mark.percentage or 0 for mark, _, _, _ in student_marks if mark.percentage)
                marks_count = sum(1 for mark, _, _, _ in student_marks if mark.percentage is not None)
                overall_average = (total_percentage / marks_count) if marks_count > 0 else 0
                
                # Get unique subjects for progress tracking
                subjects_dict = {}
                terms_list = []
                
                for mark, subject, term, assessment_type in student_marks:
                    if subject.name not in subjects_dict:
                        subjects_dict[subject.name] = []
                    
                    subjects_dict[subject.name].append({
                        'term': term.name,
                        'term_order': f"{term.academic_year}_{term.name}",
                        'assessment': assessment_type.name,
                        'percentage': mark.percentage or 0
                    })
                    
                    if term.name not in terms_list:
                        terms_list.append(term.name)
                
                # Calculate subject progress (trend analysis)
                subjects_progress = []
                for subject_name, subject_marks in subjects_dict.items():
                    if len(subject_marks) >= 2:
                        # Compare latest two assessments to determine trend
                        sorted_marks = sorted(subject_marks, key=lambda x: x['term_order'], reverse=True)
                        current_score = sorted_marks[0]['percentage']
                        previous_score = sorted_marks[1]['percentage']
                        
                        diff = current_score - previous_score
                        if diff > 2:
                            trend = 'up'
                            trend_text = f'+{diff:.1f}% improvement'
                        elif diff < -2:
                            trend = 'down'
                            trend_text = f'{diff:.1f}% decline'
                        else:
                            trend = 'stable'
                            trend_text = 'Stable performance'
                        
                        subjects_progress.append({
                            'name': subject_name,
                            'current_score': round(current_score, 1),
                            'trend': trend,
                            'trend_text': trend_text
                        })
                    elif len(subject_marks) == 1:
                        subjects_progress.append({
                            'name': subject_name,
                            'current_score': round(subject_marks[0]['percentage'], 1),
                            'trend': 'new',
                            'trend_text': 'First assessment'
                        })
                
                # Generate recommendations based on performance
                recommendations = []
                low_performing_subjects = [s for s in subjects_progress if s['current_score'] < 60]
                if low_performing_subjects:
                    for subject in low_performing_subjects[:2]:  # Limit to 2 recommendations
                        recommendations.append({
                            'area': subject['name'],
                            'suggestion': f'Focus on improving {subject["name"]} - current score {subject["current_score"]}%'
                        })
                else:
                    recommendations.append({
                        'area': 'General',
                        'suggestion': 'Maintain excellent performance across all subjects'
                    })
                
                progress_data = {
                    'overall_average': round(overall_average, 1),
                    'class_rank': None,  # Would require class-wide comparison
                    'attendance_rate': 95.0,  # Placeholder - would need attendance tracking
                    'total_subjects': len(subjects_dict),
                    'subjects_progress': subjects_progress,
                    'total_attendance': 95.0,
                    'days_present': 190,  # Placeholder values
                    'days_absent': 10,
                    'school_days': 200,
                    'recommendations': recommendations,
                    'teacher_comments': [
                        {
                            'subject': 'General',
                            'teacher': 'Class Teacher',
                            'comment': f'Overall academic performance: {overall_average:.1f}%',
                            'date': datetime.utcnow().strftime('%Y-%m-%d')
                        }
                    ]
                }
        
        except Exception as e:
            progress_data = {
                'overall_average': 0,
                'class_rank': None,
                'attendance_rate': 0,
                'total_subjects': 0,
                'subjects_progress': [],
                'total_attendance': 0,
                'days_present': 0,
                'days_absent': 0,
                'school_days': 0,
                'recommendations': [
                    {'area': 'System', 'suggestion': f'Error loading progress data: {str(e)}'}
                ],
                'teacher_comments': [],
                'error': str(e)
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

        # Branding/config used by template
        try:
            from ..services.school_config_service import SchoolConfigService
            school_info = SchoolConfigService.get_school_info_dict()
        except Exception:
            school_info = {
                'school_name': 'Hillview School',
                'logo_url': '/static/uploads/logos/optimized_school_logo_1750595986_hvs.jpg'
            }
        
        # Get filter parameters
        selected_year = request.args.get('year', '')
        selected_term = request.args.get('term', '')
        selected_assessment = request.args.get('assessment', '')
        
        # Get real reports data using classteacher report service
        available_years = []
        reports = []
        
        try:
            from new_structure.services import get_class_report_data
            from new_structure.models.academic import Mark, Term, AssessmentType
            
            # Get available years from terms
            terms = Term.query.distinct(Term.academic_year).all()
            available_years = [term.academic_year for term in terms]
            if not available_years:
                available_years = ['2024', '2025']  # Fallback
            
            # Determine latest term/assessment for this child for UI highlighting
            from sqlalchemy import desc
            latest_pair = db.session.query(
                Term.name.label('term_name'),
                AssessmentType.name.label('assessment_name')
            ).join(Mark, Term.id == Mark.term_id) \
             .join(AssessmentType, Mark.assessment_type_id == AssessmentType.id) \
             .filter(Mark.student_id == child.id) \
             .order_by(desc(Term.academic_year), desc(Term.name), desc(AssessmentType.name)) \
             .first()
            current_term_name = latest_pair.term_name if latest_pair else ''
            current_assessment_name = latest_pair.assessment_name if latest_pair else ''

            # Find reports where this child appears in the real report data
            # Get all unique grade/stream/term/assessment combinations that have marks
            from sqlalchemy import func
            unique_reports = db.session.query(
                Grade.name.label('grade_name'),
                Stream.name.label('stream_name'), 
                Term.name.label('term_name'),
                Term.academic_year.label('academic_year'),
                AssessmentType.name.label('assessment_name'),
                func.count(Mark.id).label('marks_count')
            ).select_from(Mark)\
             .join(Student, Mark.student_id == Student.id)\
             .join(Stream, Student.stream_id == Stream.id)\
             .join(Grade, Student.grade_id == Grade.id)\
             .join(Term, Mark.term_id == Term.id)\
             .join(AssessmentType, Mark.assessment_type_id == AssessmentType.id)\
             .filter(Mark.student_id == child.id)\
             .group_by(Grade.name, Stream.name, Term.name, Term.academic_year, AssessmentType.name)\
             .order_by(Term.academic_year.desc(), Term.name.desc(), AssessmentType.name)\
             .all()
            
            # Apply filters if provided
            if selected_year:
                unique_reports = [r for r in unique_reports if r.academic_year == selected_year]
            if selected_term:
                unique_reports = [r for r in unique_reports if r.term_name == selected_term]
            if selected_assessment:
                unique_reports = [r for r in unique_reports if r.assessment_name == selected_assessment]
            
            # Convert to reports format using real classteacher report structure
            for idx, report in enumerate(unique_reports, start=1):
                if report.marks_count > 0:
                    # Get the actual report data to calculate averages
                    grade_str = report.grade_name
                    stream_str = f"Stream {report.stream_name}"
                    
                    try:
                        # Normalize names to exact DB values and fetch report data
                        _term_norm, _assess_norm = _normalize_term_and_assessment(report.term_name, report.assessment_name)
                        class_data_result = _coerce_class_report_result(
                            get_class_report_data(
                                grade_str, stream_str, _term_norm, _assess_norm
                            )
                        )
                        
                        # Find this child's data in the class report (case-insensitive match)
                        def _name_eq(a, b):
                            return (a or "").strip().lower() == (b or "").strip().lower()

                        child_avg = None
                        if class_data_result and not class_data_result.get("error"):
                            for student_data in class_data_result.get("class_data", []):
                                if _name_eq(student_data.get("student"), child.name):
                                    child_avg = student_data.get("average_percentage")
                                    break

                        # Build robust report id including 'Stream'
                        _report_id = f"{report.grade_name.replace(' ', '_')}_Stream_{report.stream_name}_{_term_norm.replace(' ', '_')}_{_assess_norm.replace(' ', '_')}"

                        reports.append({
                            'id': idx,  # keep numeric id for templates that cast to int
                            'report_key': _report_id,  # string key containing full identifier
                            'title': f'{report.term_name} {report.assessment_name} Report - {report.grade_name} {report.stream_name}',
                            'term': report.term_name,
                            'assessment_type': report.assessment_name,
                            'grade': report.grade_name,
                            'stream': report.stream_name,
                            'status': 'available',
                            'generated_date': datetime.utcnow(),
                            'overall_average': round(child_avg, 1) if child_avg else None,
                            'class_rank': None,  # Could be calculated from class_data_result
                            'marks_count': report.marks_count,
                            'academic_year': report.academic_year,
                            'is_latest': (report.term_name == current_term_name and report.assessment_name == current_assessment_name),
                            'parent_report_url': url_for('parent.view_individual_report', student_id=child.id, report_id=_report_id)
                        })
                        
                    except Exception as report_error:
                        print(f"Error getting report data: {report_error}")
                        # Still add the report entry even if we can't get detailed data
                        _report_id = f"{report.grade_name.replace(' ', '_')}_Stream_{report.stream_name}_{_term_norm.replace(' ', '_')}_{_assess_norm.replace(' ', '_')}"
                        reports.append({
                            'id': idx,
                            'report_key': _report_id,
                            'title': f'{report.term_name} {report.assessment_name} Report - {report.grade_name} {report.stream_name}',
                            'term': report.term_name,
                            'assessment_type': report.assessment_name,
                            'grade': report.grade_name,
                            'stream': report.stream_name,
                            'status': 'available',
                            'generated_date': datetime.utcnow(),
                            'overall_average': None,
                            'class_rank': None,
                            'marks_count': report.marks_count,
                            'academic_year': report.academic_year,
                            'is_latest': (report.term_name == current_term_name and report.assessment_name == current_assessment_name),
                            'error': str(report_error)
                        })
            
            # If no real data, provide helpful message
            if not reports:
                reports = [{
                    'id': 'no_data',
                    'title': 'No Reports Available',
                    'term': '',
                    'assessment_type': '',
                    'status': 'unavailable',
                    'generated_date': None,
                    'overall_average': None,
                    'class_rank': None,
                    'message': f'No marks have been entered for {child.name} yet. Check if they are enrolled in the correct grade and stream.'
                }]
                
        except Exception as e:
            # Fallback to error message
            available_years = ['2024', '2025']
            reports = [{
                'id': 'error',
                'title': 'Error Loading Reports',
                'term': '',
                'assessment_type': '',
                'status': 'error',
                'generated_date': None,
                'overall_average': None,
                'class_rank': None,
                'message': f'Error loading reports: {str(e)}'
            }]
        
        child_info = {
            'id': child.id,
            'name': child.name,
            'admission_number': child.admission_number,
            'grade': grade.name,
            'stream': stream.name
        }

        return render_template(
            'parent_child_reports.html',
            child=child_info,
            reports=reports,
            available_years=available_years,
            selected_year=selected_year,
            selected_term=selected_term,
            selected_assessment=selected_assessment,
            current_term=current_term_name,
            current_assessment=current_assessment_name,
            parent=parent,
            school_info=school_info
        )
    
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'error')
        return redirect(url_for('parent.dashboard'))

@parent_simple_bp.route('/preview_individual_report/<grade>/<stream>/<term>/<assessment_type>/<student_name>')
@parent_required
def preview_individual_report_direct(grade, stream, term, assessment_type, student_name):
    """Direct access to individual report using classteacher-style URL pattern."""
    try:
        parent = Parent.query.get(session['parent_id'])
        
        # Find the student by name and verify parent has access
        from ..models.academic import Stream as StreamModel, Grade as GradeModel
        
        # Extract stream letter from "Stream X" format
        stream_letter = stream.split()[-1] if 'Stream' in stream else stream[-1]
        
        # Find the student
        student_query = db.session.query(Student, GradeModel, StreamModel)\
            .join(GradeModel, Student.grade_id == GradeModel.id)\
            .join(StreamModel, Student.stream_id == StreamModel.id)\
            .filter(Student.name == student_name)\
            .filter(GradeModel.name == grade)\
            .filter(StreamModel.name == stream_letter)\
            .first()
        
        if not student_query:
            flash(f'Student {student_name} not found in {grade} {stream}', 'error')
            return redirect(url_for('parent.dashboard'))
        
        student, grade_obj, stream_obj = student_query
        
        # Verify this child belongs to this parent
        child_link = ParentStudent.query.filter_by(
            parent_id=parent.id, 
            student_id=student.id
        ).first()
        
        if not child_link:
            flash('You do not have access to this student\'s records.', 'error')
            return redirect(url_for('parent.dashboard'))

        # Create report_id in the expected format for the existing function (include explicit 'Stream')
        report_id = f"{grade.replace(' ', '_')}_Stream_{stream_letter}_{term.replace(' ', '_')}_{assessment_type.replace(' ', '_')}"

        # Call the existing view_individual_report function
        return view_individual_report(student.id, report_id)
        
    except Exception as e:
        flash(f'Error accessing report: {str(e)}', 'error')
        return redirect(url_for('parent.dashboard'))

@parent_simple_bp.route('/student/<int:student_id>/report/<string:report_id>')
@parent_required
def view_individual_report(student_id, report_id):
    """View individual student report within parent context."""
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

        # Parse report_id to get grade, stream, term and assessment type
        try:
            # Accept both formats:
            #  A) Grade_9_Stream_B_Term_3_Midterm_3_2025
            #  B) Grade_9_B_Term_3_Midterm_3_2025 (legacy without the literal 'Stream')
            parts = report_id.split('_') if '_' in report_id else []
            if parts and len(parts) >= 5:
                # Determine indices by locating tokens
                def _idx(token: str):
                    try:
                        return parts.index(token)
                    except ValueError:
                        return -1

                grade_name = None
                stream_letter = None
                term_name = None
                assessment_name = None

                # Grade always assumed as first two tokens e.g., ["Grade", "9"]
                if len(parts) >= 2 and parts[0].lower() == 'grade':
                    grade_name = f"{parts[0]} {parts[1]}"

                stream_idx = _idx('Stream')
                if stream_idx != -1 and stream_idx + 1 < len(parts):
                    stream_letter = parts[stream_idx + 1]
                    after_stream = parts[stream_idx + 2:]
                else:
                    # Legacy: next token after grade number is the stream letter
                    stream_letter = parts[2] if len(parts) > 2 else None
                    after_stream = parts[3:]

                # Expect term as two tokens like ["Term", "3"]
                term_idx = None
                for i in range(len(after_stream) - 1):
                    if after_stream[i].lower() == 'term':
                        term_idx = i
                        break
                if term_idx is not None:
                    term_name = f"{after_stream[term_idx]} {after_stream[term_idx + 1]}"
                    assessment_tokens = after_stream[term_idx + 2:]
                else:
                    # Fallback: use remaining; this may fail later if invalid
                    term_name = ' '.join(after_stream[:2]) if len(after_stream) >= 2 else (after_stream[0] if after_stream else '')
                    assessment_tokens = after_stream[2:] if len(after_stream) >= 3 else []

                assessment_name = ' '.join(assessment_tokens) if assessment_tokens else ''
                
                # Get report data using the same service as classteacher but within parent context
                from new_structure.services import get_class_report_data

                # Normalize names to exact DB values (case-insensitive)
                term_name, assessment_name = _normalize_term_and_assessment(term_name, assessment_name)

                # Attempt 1: use the same service as classteacher
                class_data_result = None
                try:
                    class_data_result = _coerce_class_report_result(
                        get_class_report_data(
                            grade_name, f"Stream {stream_letter}", term_name, assessment_name
                        )
                    )
                except Exception:
                    class_data_result = None

                def _name_eq(a, b):
                    return (a or "").strip().lower() == (b or "").strip().lower()

                student_row = None
                subject_names = []
                composite_structure = {}

                # Attempt 2: if service is present, locate this student in class data
                if class_data_result and not class_data_result.get('error'):
                    for sd in class_data_result.get('class_data', []) or []:
                        if _name_eq(sd.get('student'), student.name):
                            student_row = sd
                            break
                    subject_names = class_data_result.get('subjects', []) or []

                # If we have a row but no subjects provided, try to derive from keys
                if student_row and not subject_names:
                    try:
                        subject_names = sorted(list((student_row.get('filtered_marks') or student_row.get('marks') or {}).keys()))
                    except Exception:
                        subject_names = []

                # Attempt 3: build from Mark table directly if needed (no row or no marks)
                def _build_from_db_marks():
                    from new_structure.models.academic import Mark, Subject, Term, AssessmentType
                    marks = db.session.query(Mark, Subject) \
                        .join(Subject, Mark.subject_id == Subject.id) \
                        .join(Term, Mark.term_id == Term.id) \
                        .join(AssessmentType, Mark.assessment_type_id == AssessmentType.id) \
                        .filter(Mark.student_id == student.id) \
                        .filter(db.func.lower(Term.name) == term_name.strip().lower()) \
                        .filter(db.func.lower(AssessmentType.name) == assessment_name.strip().lower()) \
                        .all()
                    filtered = {}
                    local_subjects = []
                    for mk, subj in marks:
                        if mk.percentage is not None:
                            filtered[subj.name] = float(mk.percentage)
                            if subj.name not in local_subjects:
                                local_subjects.append(subj.name)
                    if filtered:
                        return {
                            'student': student.name,
                            'filtered_marks': filtered,
                            'average_percentage': sum(filtered.values()) / max(1, len(filtered))
                        }, local_subjects
                    return None, []

                if not student_row:
                    student_row, derived_subjects = _build_from_db_marks()
                    subject_names = subject_names or derived_subjects
                else:
                    # If row exists but has no marks, build from DB
                    if not (student_row.get('filtered_marks') or student_row.get('marks')):
                        rebuilt, derived_subjects = _build_from_db_marks()
                        if rebuilt:
                            student_row = rebuilt
                            subject_names = subject_names or derived_subjects

                if not student_row:
                    # As a last resort, render an empty yet valid report shell so the page doesn't just refresh
                    student_row = {
                        'student': student.name,
                        'filtered_marks': {},
                        'average_percentage': 0
                    }
                    subject_names = subject_names or []

                # Compute metrics and table from available source
                from new_structure.utils import get_grade_and_points

                # Education level based on grade
                education_level = ""
                try:
                    grade_num = int(grade.name.split()[1]) if len(grade.name.split()) > 1 else int(grade.name)
                    if 1 <= grade_num <= 3:
                        education_level = "lower primary"
                    elif 4 <= grade_num <= 6:
                        education_level = "upper primary"
                    elif 7 <= grade_num <= 9:
                        education_level = "junior secondary"
                except:
                    education_level = "primary"

                # Prefer filtered_marks; fall back to 'marks' structure from service
                filtered_marks = (student_row or {}).get('filtered_marks') or (student_row or {}).get('marks') or {}
                avg_percentage = student_row.get('average_percentage', 0)

                table_data = []
                total_marks = 0
                total_possible_marks = 0
                total_points = 0

                for subject_name in subject_names:
                    mark_val = filtered_marks.get(subject_name)
                    if mark_val is None:
                        continue
                    mark_disp = int(round(mark_val)) if mark_val == int(mark_val) else round(mark_val, 1)
                    subject_grade, subject_points = get_grade_and_points(mark_val)
                    row = {
                        'subject': subject_name,
                        'grade': subject_grade,
                        'points': subject_points,
                        'remarks': None
                    }
                    # Fill columns according to template expectations
                    if assessment_name.lower() in ('end term', 'endterm', 'end_term'):
                        # Query other assessments to populate entrance/midterm if available
                        try:
                            from new_structure.models.academic import Mark as Mk, Subject as Subj, Term as Tm, AssessmentType as AT
                            def _get_mark_for(bucket):
                                at = db.session.query(AT).filter(db.func.lower(AT.name).like(f"%{bucket}%")).first()
                                if not at:
                                    return 0
                                m = db.session.query(Mk) \
                                    .join(Subj, Mk.subject_id == Subj.id) \
                                    .join(Tm, Mk.term_id == Tm.id) \
                                    .filter(Mk.student_id == student.id) \
                                    .filter(db.func.lower(Tm.name) == term_name.strip().lower()) \
                                    .filter(Mk.assessment_type_id == at.id) \
                                    .filter(db.func.lower(Subj.name) == subject_name.strip().lower()) \
                                    .first()
                                return float(m.percentage) if m and m.percentage is not None else 0
                            entrance_m = _get_mark_for('entrance')
                            mid_m = _get_mark_for('mid')
                            end_m = mark_val
                            avg_m = round((entrance_m + mid_m + end_m) / max(1, (1 if entrance_m else 0) + (1 if mid_m else 0) + (1 if end_m else 0)), 1)
                            row.update({
                                'entrance': entrance_m,
                                'mid_term': mid_m,
                                'end_term': end_m,
                                'avg': avg_m
                            })
                        except Exception:
                            row.update({'entrance': 0, 'mid_term': 0, 'end_term': mark_val, 'avg': mark_val})
                    else:
                        row['current_assessment'] = mark_disp

                    table_data.append(row)
                    total_marks += mark_val
                    total_possible_marks += 100
                    total_points += subject_points

                # Composite rows if any (none when building from raw marks)
                composite_data = {}
                for comp_name, _ in (composite_structure or {}).items():
                    comp_mark = filtered_marks.get(comp_name)
                    if comp_mark is not None:
                        comp_grade, comp_points = get_grade_and_points(comp_mark)
                        composite_data[comp_name] = {
                            'name': comp_name,
                            'mark': comp_mark,
                            'grade': comp_grade,
                            'points': comp_points,
                            'components': {}
                        }

                # School info
                try:
                    from new_structure.services.school_config_service import SchoolConfigService
                    school_info = SchoolConfigService.get_school_info_dict()
                except Exception:
                    school_info = {
                        'school_name': 'Hillview School',
                        'address': '123 Education Street',
                        'phone': '+254-123-456789',
                        'email': 'info@hillviewschool.ac.ke'
                    }

                from datetime import datetime
                current_date = datetime.now().strftime('%B %d, %Y')
                academic_year = '2025'
                admission_no = getattr(student, 'admission_number', 'N/A')
                staff_info = {'class_teacher': 'N/A', 'head_teacher': 'N/A'}
                term_info = {
                    'next_term_opening_date': 'TBA',
                    'current_term': term_name,
                    'academic_year': academic_year
                }
                logo_url = '/static/images/school_logo.png'
                subject_teachers = {}

                return render_template(
                    'preview_individual_report.html',
                    student=student,
                    student_data=student_row,
                    grade=grade.name,
                    stream=f"Stream {stream.name}",
                    term=term_name,
                    assessment_type=assessment_name,
                    education_level=education_level,
                    current_date=current_date,
                    table_data=table_data,
                    composite_data=composite_data,
                    total=total_marks,
                    avg_percentage=avg_percentage,
                    mean_grade=get_grade_and_points(avg_percentage)[0] if avg_percentage is not None else '-',
                    mean_points=get_grade_and_points(avg_percentage)[1] if avg_percentage is not None else 0,
                    total_possible_marks=total_possible_marks,
                    total_points=total_points,
                    admission_no=admission_no,
                    academic_year=academic_year,
                    print_mode=False,
                    school_info=school_info,
                    logo_url=logo_url,
                    staff_info=staff_info,
                    term_info=term_info,
                    subject_teachers=subject_teachers,
                    calculator_legends=None,
                    back_url=url_for('parent.child_reports', child_id=student_id)
                )
                
            else:
                flash('Invalid report ID format.', 'error')
                return redirect(url_for('parent.child_reports', child_id=student_id))
                
        except (ValueError, TypeError, IndexError) as e:
            flash(f'Invalid report ID: {str(e)}', 'error')
            return redirect(url_for('parent.child_reports', child_id=student_id))
    
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

@parent_simple_bp.route('/download/report/<int:student_id>/<path:report_id>')
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
@csrf_protect
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
@csrf_protect
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

@parent_simple_bp.route('/debug-links')
@parent_required
def debug_links():
    """Debug endpoint to inspect the logged-in parent's linked children."""
    try:
        pid = session.get('parent_id')
        parent = Parent.query.get(pid)
        links = ParentStudent.query.filter_by(parent_id=pid).all()
        students = []
        for link in links:
            stu = Student.query.get(link.student_id)
            students.append({
                'student_id': link.student_id,
                'student_name': stu.name if stu else None,
                'relationship_type': link.relationship_type,
                'is_primary_contact': link.is_primary_contact
            })
        return jsonify({
            'parent_id': pid,
            'parent_email': parent.email if parent else None,
            'link_count': len(links),
            'students': students
        })
    except Exception as e:
        return jsonify({'error': str(e)})
