"""
Setup script to create default email templates for the parent portal.
Run this once to initialize the email verification system.
"""
from extensions import db
from models.parent import EmailTemplate

def create_verification_template():
    """Create default email verification template."""
    
    verification_template = EmailTemplate(
        name="Parent Email Verification",
        template_type="verification",
        subject_template="Verify Your {{ school_name }} Parent Portal Email",
        html_template="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Verification - {{ school_name }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .email-container {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #14522f, #17eeca);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: bold;
        }
        .header p {
            margin: 5px 0 0 0;
            opacity: 0.9;
            font-size: 16px;
        }
        .content {
            padding: 40px 30px;
        }
        .greeting {
            font-size: 18px;
            color: #14522f;
            margin-bottom: 20px;
            font-weight: 600;
        }
        .message {
            font-size: 16px;
            line-height: 1.8;
            margin-bottom: 30px;
            color: #555;
        }
        .verify-button {
            text-align: center;
            margin: 40px 0;
        }
        .verify-button a {
            background: linear-gradient(135deg, #14522f, #17eeca);
            color: white;
            padding: 15px 40px;
            text-decoration: none;
            border-radius: 50px;
            font-size: 18px;
            font-weight: 600;
            display: inline-block;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(20, 82, 47, 0.3);
        }
        .verify-button a:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(20, 82, 47, 0.4);
        }
        .alternative-link {
            background: #f8f9fa;
            border-left: 4px solid #17eeca;
            padding: 20px;
            margin: 30px 0;
            border-radius: 0 8px 8px 0;
        }
        .alternative-link p {
            margin: 0;
            font-size: 14px;
            color: #666;
        }
        .alternative-link a {
            color: #14522f;
            word-break: break-all;
        }
        .footer {
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #eee;
        }
        .footer p {
            margin: 0;
            font-size: 13px;
            color: #888;
            line-height: 1.5;
        }
        .school-info {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
        .expiry-notice {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            color: #856404;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>{{ school_name }}</h1>
            <p>Parent Portal Email Verification</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {{ parent_name }},</div>
            
            <div class="message">
                <p>Welcome to the {{ school_name }} Parent Portal! We're excited to have you join our digital community.</p>
                
                <p>To complete your registration and gain full access to your children's academic information, reports, and school updates, please verify your email address by clicking the button below:</p>
            </div>
            
            <div class="verify-button">
                <a href="{{ verification_link }}">Verify Email Address</a>
            </div>
            
            <div class="expiry-notice">
                <strong>⏰ Important:</strong> This verification link will expire in 24 hours for security reasons.
            </div>
            
            <div class="alternative-link">
                <p><strong>Button not working?</strong> Copy and paste this link into your browser:</p>
                <p><a href="{{ verification_link }}">{{ verification_link }}</a></p>
            </div>
            
            <div class="message">
                <p>Once your email is verified, you'll be able to:</p>
                <ul style="color: #555; margin-left: 20px;">
                    <li>Access your children's academic reports</li>
                    <li>View grades and progress updates</li>
                    <li>Receive important school notifications</li>
                    <li>Download and print reports</li>
                </ul>
                
                <p><strong>Next Steps:</strong> After verification, please contact the school administration to link your children to your parent account.</p>
            </div>
        </div>
        
        <div class="footer">
            <p>This email was sent by {{ school_name }} Parent Portal System.</p>
            <p>If you didn't register for the parent portal, please ignore this email.</p>
            
            <div class="school-info">
                <p><strong>{{ school_name }}</strong></p>
                {% if school_address %}<p>{{ school_address }}</p>{% endif %}
                {% if school_phone %}<p>Phone: {{ school_phone }}</p>{% endif %}
                {% if school_email %}<p>Email: {{ school_email }}</p>{% endif %}
                {% if school_motto %}<p><em>"{{ school_motto }}"</em></p>{% endif %}
            </div>
        </div>
    </div>
</body>
</html>
        """,
        text_template="""
{{ school_name }} - Email Verification

Hello {{ parent_name }},

Welcome to the {{ school_name }} Parent Portal!

To complete your registration and access your children's academic information, please verify your email address by visiting this link:

{{ verification_link }}

This verification link will expire in 24 hours.

Once verified, you'll be able to:
- Access your children's academic reports
- View grades and progress updates  
- Receive important school notifications
- Download and print reports

Next Steps: After verification, please contact the school administration to link your children to your parent account.

If you didn't register for the parent portal, please ignore this email.

---
{{ school_name }}
{% if school_address %}{{ school_address }}{% endif %}
{% if school_phone %}Phone: {{ school_phone }}{% endif %}
{% if school_email %}Email: {{ school_email }}{% endif %}
{% if school_motto %}"{{ school_motto }}"{% endif %}
        """,
        available_variables='{"school_name": "School name", "parent_name": "Parent full name", "verification_link": "Email verification URL", "school_address": "School address", "school_phone": "School phone", "school_email": "School email", "school_motto": "School motto"}',
        is_active=True,
        is_default=True
    )
    
    return verification_template

def create_password_reset_template():
    """Create default password reset template."""
    
    reset_template = EmailTemplate(
        name="Parent Password Reset",
        template_type="reset",
        subject_template="Reset Your {{ school_name }} Parent Portal Password",
        html_template="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset - {{ school_name }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .email-container {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #14522f, #17eeca);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: bold;
        }
        .header p {
            margin: 5px 0 0 0;
            opacity: 0.9;
            font-size: 16px;
        }
        .content {
            padding: 40px 30px;
        }
        .greeting {
            font-size: 18px;
            color: #14522f;
            margin-bottom: 20px;
            font-weight: 600;
        }
        .message {
            font-size: 16px;
            line-height: 1.8;
            margin-bottom: 30px;
            color: #555;
        }
        .reset-button {
            text-align: center;
            margin: 40px 0;
        }
        .reset-button a {
            background: linear-gradient(135deg, #14522f, #17eeca);
            color: white;
            padding: 15px 40px;
            text-decoration: none;
            border-radius: 50px;
            font-size: 18px;
            font-weight: 600;
            display: inline-block;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(20, 82, 47, 0.3);
        }
        .reset-button a:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(20, 82, 47, 0.4);
        }
        .alternative-link {
            background: #f8f9fa;
            border-left: 4px solid #17eeca;
            padding: 20px;
            margin: 30px 0;
            border-radius: 0 8px 8px 0;
        }
        .alternative-link p {
            margin: 0;
            font-size: 14px;
            color: #666;
        }
        .alternative-link a {
            color: #14522f;
            word-break: break-all;
        }
        .footer {
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #eee;
        }
        .footer p {
            margin: 0;
            font-size: 13px;
            color: #888;
            line-height: 1.5;
        }
        .security-notice {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            color: #856404;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>{{ school_name }}</h1>
            <p>Password Reset Request</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {{ parent_name }},</div>
            
            <div class="message">
                <p>We received a request to reset your password for the {{ school_name }} Parent Portal.</p>
                
                <p>If you requested this password reset, please click the button below to create a new password:</p>
            </div>
            
            <div class="reset-button">
                <a href="{{ reset_link }}">Reset Password</a>
            </div>
            
            <div class="security-notice">
                <strong>⏰ Security Notice:</strong> This password reset link will expire in 1 hour for your security.
            </div>
            
            <div class="alternative-link">
                <p><strong>Button not working?</strong> Copy and paste this link into your browser:</p>
                <p><a href="{{ reset_link }}">{{ reset_link }}</a></p>
            </div>
            
            <div class="message">
                <p><strong>Didn't request this?</strong> If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                
                <p>For security reasons, we recommend that you:</p>
                <ul style="color: #555; margin-left: 20px;">
                    <li>Use a strong, unique password</li>
                    <li>Don't share your login credentials</li>
                    <li>Contact the school if you notice any suspicious activity</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>This email was sent by {{ school_name }} Parent Portal System.</p>
            <p>For technical support, please contact the school administration.</p>
        </div>
    </div>
</body>
</html>
        """,
        text_template="""
{{ school_name }} - Password Reset

Hello {{ parent_name }},

We received a request to reset your password for the {{ school_name }} Parent Portal.

If you requested this password reset, please visit this link to create a new password:

{{ reset_link }}

This password reset link will expire in 1 hour for your security.

Didn't request this? If you didn't request a password reset, please ignore this email. Your password will remain unchanged.

For security reasons, we recommend that you:
- Use a strong, unique password
- Don't share your login credentials  
- Contact the school if you notice any suspicious activity

---
{{ school_name }}
Parent Portal System
        """,
        available_variables='{"school_name": "School name", "parent_name": "Parent full name", "reset_link": "Password reset URL"}',
        is_active=True,
        is_default=True
    )
    
    return reset_template

def setup_email_templates():
    """Setup all default email templates."""
    try:
        print("Setting up email templates...")
        
        # Check if verification template already exists
        verification_exists = EmailTemplate.query.filter_by(
            template_type='verification',
            is_default=True
        ).first()
        
        if not verification_exists:
            verification_template = create_verification_template()
            db.session.add(verification_template)
            print("✅ Created email verification template")
        else:
            print("ℹ️  Email verification template already exists")
        
        # Check if reset template already exists
        reset_exists = EmailTemplate.query.filter_by(
            template_type='reset',
            is_default=True
        ).first()
        
        if not reset_exists:
            reset_template = create_password_reset_template()
            db.session.add(reset_template)
            print("✅ Created password reset template")
        else:
            print("ℹ️  Password reset template already exists")
        
        db.session.commit()
        print("🎉 Email templates setup completed successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error setting up email templates: {e}")
        raise

if __name__ == "__main__":
    # This can be run directly to setup templates
    setup_email_templates()
