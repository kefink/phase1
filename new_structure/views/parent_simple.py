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
from ..models.parent import Parent, ParentStudent, ParentEmailLog
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
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '').strip()
            
            if not email or not password:
                flash('Email and password are required.', 'error')
                return render_template('parent_login.html')
            
            # Find parent by email
            parent = Parent.query.filter_by(email=email).first()
            
            if not parent:
                flash('Invalid email or password.', 'error')
                return render_template('parent_login.html')
            
            # Check if account is locked
            if parent.is_locked():
                flash('Account is temporarily locked due to multiple failed login attempts. Please try again later.', 'error')
                return render_template('parent_login.html')
            
            # Check password
            if not parent.check_password(password):
                parent.lock_account()
                db.session.commit()
                flash('Invalid email or password.', 'error')
                return render_template('parent_login.html')
            
            # Check if account is active
            if not parent.is_active:
                flash('Your account has been deactivated. Please contact the school.', 'error')
                return render_template('parent_login.html')
            
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
    
    return render_template('parent_login.html')

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
        ).join(Student).join(Grade).join(Stream).filter(
            ParentStudent.parent_id == parent.id
        ).order_by(Grade.name, Stream.name, Student.name)
        
        children = children_query.all()
        
        # Get recent email notifications
        recent_emails = ParentEmailLog.query.filter_by(
            parent_id=parent.id
        ).order_by(ParentEmailLog.created_at.desc()).limit(5).all()
        
        return render_template('parent_dashboard.html',
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
        ).join(Student).join(Grade).join(Stream).filter(
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
