#!/usr/bin/env python3
"""
Quick setup for email verification templates
"""
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

# Create app and setup database
from __init__ import create_app
from extensions import db

app = create_app()

with app.app_context():
    # Check if EmailTemplate table exists
    try:
        from models.parent import EmailTemplate
        
        # Create verification email template if it doesn't exist
        verification_template = EmailTemplate.query.filter_by(template_type='verification').first()
        
        if not verification_template:
            verification_template = EmailTemplate(
                template_type='verification',
                subject='Verify Your Hillview School Parent Portal Email',
                html_content='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Email Verification - Hillview School</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f4f4f4;">
    <div style="background: linear-gradient(135deg, #14522f, #17eeca); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Hillview School</h1>
        <p style="color: white; margin: 10px 0; font-size: 16px;">Parent Portal Email Verification</p>
    </div>
    
    <div style="background: white; padding: 40px; margin: 0;">
        <h2 style="color: #14522f; margin-bottom: 20px;">Hello {{parent_name}},</h2>
        
        <p style="font-size: 16px; line-height: 1.6; color: #333;">
            Welcome to the Hillview School Parent Portal! To complete your registration and access your children's academic information, please verify your email address.
        </p>
        
        <div style="text-align: center; margin: 40px 0;">
            <a href="{{verification_url}}" 
               style="background: #14522f; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-size: 16px; font-weight: bold;">
                Verify Email Address
            </a>
        </div>
        
        <p style="color: #666; font-size: 14px; line-height: 1.6;">
            If the button doesn't work, copy and paste this link into your browser:<br>
            <a href="{{verification_url}}" style="color: #14522f;">{{verification_url}}</a>
        </p>
        
        <p style="color: #666; font-size: 14px;">
            This verification link will expire in 24 hours.
        </p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        
        <div style="color: #666; font-size: 12px; text-align: center;">
            <p><strong>Hillview School</strong><br>
            Kiambu Road, Runda Estate, Nairobi, Kenya<br>
            Phone: +254705204870 | Email: info@hillviewschool.ac.ke</p>
            
            <p style="margin-top: 20px;">
                If you didn't register for the parent portal, please ignore this email.
            </p>
        </div>
    </div>
</body>
</html>
                ''',
                text_content='''Hello {{parent_name}},

Welcome to the Hillview School Parent Portal!

To complete your registration and access your children's academic information, please verify your email address by clicking this link:

{{verification_url}}

This verification link will expire in 24 hours.

If you didn't register for the parent portal, please ignore this email.

Best regards,
Hillview School Administration
Phone: +254705204870
Email: info@hillviewschool.ac.ke
                '''
            )
            
            db.session.add(verification_template)
            db.session.commit()
            print("✅ Email verification template created successfully!")
        else:
            print("✅ Email verification template already exists!")
            
        print("🚀 Email verification system is ready!")
        
    except Exception as e:
        print(f"❌ Error setting up email templates: {e}")
        print("📝 Note: Make sure the database is initialized and EmailTemplate model exists")
