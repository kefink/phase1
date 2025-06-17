"""
Parent Email Service for the Hillview School Management System.
Handles all email communications with parents including notifications, verification, and password resets.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from jinja2 import Template

from ..models import db
from ..models.parent import Parent, ParentStudent, ParentEmailLog, EmailTemplate
from ..models.academic import Student, Grade, Stream
from ..models.school_setup import SchoolSetup


class ParentEmailService:
    """Service for handling parent email communications."""
    
    @staticmethod
    def get_smtp_config():
        """Get SMTP configuration from environment variables."""
        return {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_username': os.getenv('SMTP_USERNAME', ''),
            'smtp_password': os.getenv('SMTP_PASSWORD', ''),
            'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        }
    
    @staticmethod
    def get_school_context():
        """Get school information for email templates."""
        school_setup = SchoolSetup.query.first()
        if school_setup:
            return {
                'school_name': school_setup.school_name,
                'school_address': school_setup.school_address,
                'school_email': school_setup.school_email,
                'school_phone': school_setup.school_phone,
                'school_motto': school_setup.school_motto
            }
        else:
            return {
                'school_name': 'Hillview School',
                'school_address': 'School Address',
                'school_email': 'info@hillviewschool.com',
                'school_phone': 'School Phone',
                'school_motto': 'Excellence in Education'
            }
    
    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str, text_content: str = None) -> tuple[bool, str]:
        """
        Send an email using SMTP configuration.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            config = ParentEmailService.get_smtp_config()
            
            # Validate SMTP configuration
            if not config['smtp_username'] or not config['smtp_password']:
                return False, "SMTP configuration not set. Please configure email settings."
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = config['smtp_username']
            msg['To'] = to_email
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                if config['use_tls']:
                    server.starttls(context=context)
                server.login(config['smtp_username'], config['smtp_password'])
                server.send_message(msg)
            
            return True, "Email sent successfully"
            
        except smtplib.SMTPAuthenticationError:
            return False, "SMTP authentication failed. Please check email credentials."
        except smtplib.SMTPRecipientsRefused:
            return False, f"Invalid recipient email address: {to_email}"
        except smtplib.SMTPServerDisconnected:
            return False, "SMTP server connection failed. Please check server settings."
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    @staticmethod
    def render_template(template: EmailTemplate, context: Dict[str, Any]) -> tuple[str, str]:
        """
        Render email template with context variables.
        
        Args:
            template: EmailTemplate instance
            context: Dictionary of template variables
            
        Returns:
            Tuple of (subject, html_content)
        """
        try:
            # Render subject
            subject_template = Template(template.subject_template)
            subject = subject_template.render(**context)
            
            # Render HTML content
            html_template = Template(template.html_template)
            html_content = html_template.render(**context)
            
            return subject, html_content
            
        except Exception as e:
            raise Exception(f"Template rendering failed: {str(e)}")
    
    @staticmethod
    def send_verification_email(parent: Parent) -> tuple[bool, str]:
        """
        Send email verification to a parent.
        
        Args:
            parent: Parent instance
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Generate verification token
            verification_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
            parent.verification_token = verification_token
            parent.verification_sent_at = datetime.utcnow()
            
            # Get email template
            template = EmailTemplate.query.filter_by(
                template_type='verification',
                is_active=True,
                is_default=True
            ).first()
            
            if not template:
                return False, "Email verification template not found"
            
            # Prepare context
            school_context = ParentEmailService.get_school_context()
            context = {
                **school_context,
                'parent_name': parent.get_full_name(),
                'verification_link': f"{os.getenv('BASE_URL', 'http://localhost:5000')}/parent/verify/{verification_token}"
            }
            
            # Render template
            subject, html_content = ParentEmailService.render_template(template, context)
            
            # Send email
            success, message = ParentEmailService.send_email(parent.email, subject, html_content)
            
            # Log email attempt
            email_log = ParentEmailLog(
                parent_id=parent.id,
                email_type='verification',
                subject=subject,
                recipient_email=parent.email,
                template_id=template.id,
                status='sent' if success else 'failed',
                sent_at=datetime.utcnow() if success else None,
                error_message=None if success else message
            )
            db.session.add(email_log)
            
            if success:
                db.session.commit()
            else:
                db.session.rollback()
            
            return success, message
            
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to send verification email: {str(e)}"
    
    @staticmethod
    def send_password_reset_email(parent: Parent) -> tuple[bool, str]:
        """
        Send password reset email to a parent.
        
        Args:
            parent: Parent instance
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Generate reset token
            reset_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
            parent.reset_token = reset_token
            parent.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            
            # Get email template
            template = EmailTemplate.query.filter_by(
                template_type='reset',
                is_active=True,
                is_default=True
            ).first()
            
            if not template:
                return False, "Password reset template not found"
            
            # Prepare context
            school_context = ParentEmailService.get_school_context()
            context = {
                **school_context,
                'parent_name': parent.get_full_name(),
                'reset_link': f"{os.getenv('BASE_URL', 'http://localhost:5000')}/parent/reset-password/{reset_token}"
            }
            
            # Render template
            subject, html_content = ParentEmailService.render_template(template, context)
            
            # Send email
            success, message = ParentEmailService.send_email(parent.email, subject, html_content)
            
            # Log email attempt
            email_log = ParentEmailLog(
                parent_id=parent.id,
                email_type='reset',
                subject=subject,
                recipient_email=parent.email,
                template_id=template.id,
                status='sent' if success else 'failed',
                sent_at=datetime.utcnow() if success else None,
                error_message=None if success else message
            )
            db.session.add(email_log)
            
            if success:
                db.session.commit()
            else:
                db.session.rollback()
            
            return success, message
            
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to send password reset email: {str(e)}"

    @staticmethod
    def send_result_notification(parent: Parent, student: Student, assessment_info: Dict[str, Any]) -> tuple[bool, str]:
        """
        Send result notification email to a parent.

        Args:
            parent: Parent instance
            student: Student instance
            assessment_info: Dictionary containing assessment details

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get email template
            template = EmailTemplate.query.filter_by(
                template_type='result_notification',
                is_active=True,
                is_default=True
            ).first()

            if not template:
                return False, "Result notification template not found"

            # Get student's class information
            grade = Grade.query.get(student.grade_id)
            stream = Stream.query.get(student.stream_id)

            # Prepare context
            school_context = ParentEmailService.get_school_context()
            context = {
                **school_context,
                'parent_name': parent.get_full_name(),
                'student_name': student.name,
                'admission_number': student.admission_number,
                'grade_name': grade.name if grade else 'Unknown',
                'stream_name': stream.name if stream else 'Unknown',
                'term_name': assessment_info.get('term_name', 'Current Term'),
                'assessment_type': assessment_info.get('assessment_type', 'Assessment'),
                'portal_link': f"{os.getenv('BASE_URL', 'http://localhost:5000')}/parent/login"
            }

            # Render template
            subject, html_content = ParentEmailService.render_template(template, context)

            # Send email
            success, message = ParentEmailService.send_email(parent.email, subject, html_content)

            # Log email attempt
            email_log = ParentEmailLog(
                parent_id=parent.id,
                student_id=student.id,
                email_type='result_notification',
                subject=subject,
                recipient_email=parent.email,
                template_id=template.id,
                status='sent' if success else 'failed',
                sent_at=datetime.utcnow() if success else None,
                error_message=None if success else message
            )
            db.session.add(email_log)

            if success:
                db.session.commit()
            else:
                db.session.rollback()

            return success, message

        except Exception as e:
            db.session.rollback()
            return False, f"Failed to send result notification: {str(e)}"

    @staticmethod
    def notify_parents_of_results(student_id: int, assessment_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Notify all parents of a student about new results.

        Args:
            student_id: Student ID
            assessment_info: Dictionary containing assessment details

        Returns:
            List of notification results
        """
        try:
            student = Student.query.get(student_id)
            if not student:
                return [{'success': False, 'message': 'Student not found'}]

            # Get all parents linked to this student
            parent_links = ParentStudent.query.filter_by(
                student_id=student_id,
                can_receive_reports=True
            ).all()

            if not parent_links:
                return [{'success': False, 'message': 'No parents linked to this student'}]

            results = []
            for link in parent_links:
                parent = Parent.query.get(link.parent_id)
                if parent and parent.is_active and parent.email_notifications:
                    success, message = ParentEmailService.send_result_notification(
                        parent, student, assessment_info
                    )
                    results.append({
                        'parent_id': parent.id,
                        'parent_name': parent.get_full_name(),
                        'parent_email': parent.email,
                        'success': success,
                        'message': message
                    })
                else:
                    results.append({
                        'parent_id': link.parent_id,
                        'parent_name': parent.get_full_name() if parent else 'Unknown',
                        'parent_email': parent.email if parent else 'Unknown',
                        'success': False,
                        'message': 'Parent inactive or notifications disabled'
                    })

            return results

        except Exception as e:
            return [{'success': False, 'message': f'Error notifying parents: {str(e)}'}]

    @staticmethod
    def test_email_configuration() -> tuple[bool, str]:
        """
        Test email configuration by sending a test email.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            config = ParentEmailService.get_smtp_config()

            if not config['smtp_username'] or not config['smtp_password']:
                return False, "SMTP configuration not complete"

            # Test email content
            school_context = ParentEmailService.get_school_context()
            subject = f"Test Email - {school_context['school_name']} Parent Portal"
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Email Configuration Test</h2>
                <p>This is a test email to verify that the parent portal email system is working correctly.</p>
                <p><strong>School:</strong> {school_context['school_name']}</p>
                <p><strong>Test Time:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                <p>If you receive this email, the configuration is working properly!</p>
            </div>
            """

            # Send test email to the configured SMTP username
            success, message = ParentEmailService.send_email(
                config['smtp_username'],
                subject,
                html_content
            )

            return success, message

        except Exception as e:
            return False, f"Email configuration test failed: {str(e)}"
