#!/usr/bin/env python3
"""
Database migration script to create parent portal tables.
Run this script to add parent portal functionality to your existing database.
"""

import sqlite3
import os
from datetime import datetime

def create_parent_portal_tables():
    """Create all parent portal related tables."""
    
    # Database path
    db_path = 'kirima_primary.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🚀 Creating Parent Portal tables...")
        
        # 1. Create parent table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                phone VARCHAR(20),
                is_verified BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until DATETIME,
                email_notifications BOOLEAN DEFAULT 1,
                notification_frequency VARCHAR(20) DEFAULT 'immediate',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                verification_token VARCHAR(100),
                verification_sent_at DATETIME,
                reset_token VARCHAR(100),
                reset_token_expires DATETIME
            )
        ''')
        
        # Create index on email for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_parent_email ON parent(email)')
        
        print("✅ Created parent table")
        
        # 2. Create parent_student association table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parent_student (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                relationship_type VARCHAR(20) DEFAULT 'parent',
                is_primary_contact BOOLEAN DEFAULT 0,
                can_receive_reports BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (parent_id) REFERENCES parent(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES teacher(id),
                UNIQUE(parent_id, student_id)
            )
        ''')
        
        print("✅ Created parent_student table")
        
        # 3. Create parent_email_log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parent_email_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL,
                student_id INTEGER,
                email_type VARCHAR(50) NOT NULL,
                subject VARCHAR(200) NOT NULL,
                recipient_email VARCHAR(120) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                sent_at DATETIME,
                error_message TEXT,
                template_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES parent(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE SET NULL,
                FOREIGN KEY (template_id) REFERENCES email_template(id)
            )
        ''')
        
        print("✅ Created parent_email_log table")
        
        # 4. Create email_template table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_template (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                template_type VARCHAR(50) NOT NULL,
                subject_template VARCHAR(200) NOT NULL,
                html_template TEXT NOT NULL,
                text_template TEXT,
                available_variables TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_default BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES teacher(id)
            )
        ''')
        
        print("✅ Created email_template table")
        
        # 5. Insert default email templates
        default_templates = [
            {
                'name': 'Email Verification',
                'template_type': 'verification',
                'subject_template': 'Verify Your Parent Portal Account - {{school_name}}',
                'html_template': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c3e50;">Welcome to {{school_name}} Parent Portal</h2>
                    <p>Dear {{parent_name}},</p>
                    <p>Thank you for registering for the {{school_name}} Parent Portal. To complete your registration, please verify your email address by clicking the link below:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{verification_link}}" style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Verify Email Address</a>
                    </div>
                    <p>If you cannot click the link, copy and paste this URL into your browser:</p>
                    <p style="word-break: break-all; color: #7f8c8d;">{{verification_link}}</p>
                    <p>This verification link will expire in 24 hours.</p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ecf0f1;">
                    <p style="color: #7f8c8d; font-size: 12px;">
                        If you did not create this account, please ignore this email.<br>
                        {{school_name}}<br>
                        {{school_address}}
                    </p>
                </div>
                ''',
                'available_variables': '{"school_name": "School name", "parent_name": "Parent full name", "verification_link": "Email verification URL", "school_address": "School address"}'
            },
            {
                'name': 'Password Reset',
                'template_type': 'reset',
                'subject_template': 'Reset Your Password - {{school_name}} Parent Portal',
                'html_template': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c3e50;">Password Reset Request</h2>
                    <p>Dear {{parent_name}},</p>
                    <p>We received a request to reset your password for the {{school_name}} Parent Portal.</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{reset_link}}" style="background-color: #e74c3c; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Reset Password</a>
                    </div>
                    <p>If you cannot click the link, copy and paste this URL into your browser:</p>
                    <p style="word-break: break-all; color: #7f8c8d;">{{reset_link}}</p>
                    <p>This reset link will expire in 1 hour.</p>
                    <p><strong>If you did not request this password reset, please ignore this email and your password will remain unchanged.</strong></p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ecf0f1;">
                    <p style="color: #7f8c8d; font-size: 12px;">
                        {{school_name}}<br>
                        {{school_address}}
                    </p>
                </div>
                ''',
                'available_variables': '{"school_name": "School name", "parent_name": "Parent full name", "reset_link": "Password reset URL", "school_address": "School address"}'
            },
            {
                'name': 'Result Notification',
                'template_type': 'result_notification',
                'subject_template': 'New Results Available for {{student_name}} - {{school_name}}',
                'html_template': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c3e50;">New Results Available</h2>
                    <p>Dear {{parent_name}},</p>
                    <p>New academic results are now available for your child <strong>{{student_name}}</strong> ({{admission_number}}).</p>
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #2c3e50;">Result Details:</h3>
                        <p><strong>Student:</strong> {{student_name}}</p>
                        <p><strong>Class:</strong> {{grade_name}} {{stream_name}}</p>
                        <p><strong>Term:</strong> {{term_name}}</p>
                        <p><strong>Assessment:</strong> {{assessment_type}}</p>
                    </div>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{portal_link}}" style="background-color: #27ae60; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">View Results</a>
                    </div>
                    <p>You can log in to the Parent Portal to view detailed results and download report cards.</p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ecf0f1;">
                    <p style="color: #7f8c8d; font-size: 12px;">
                        {{school_name}}<br>
                        {{school_address}}<br>
                        Email: {{school_email}}
                    </p>
                </div>
                ''',
                'available_variables': '{"school_name": "School name", "parent_name": "Parent full name", "student_name": "Student name", "admission_number": "Student admission number", "grade_name": "Grade/class name", "stream_name": "Stream name", "term_name": "Term name", "assessment_type": "Assessment type", "portal_link": "Parent portal login URL", "school_address": "School address", "school_email": "School email"}'
            }
        ]
        
        for template in default_templates:
            cursor.execute('''
                INSERT OR IGNORE INTO email_template 
                (name, template_type, subject_template, html_template, available_variables, is_default)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (
                template['name'],
                template['template_type'], 
                template['subject_template'],
                template['html_template'],
                template['available_variables']
            ))
        
        print("✅ Inserted default email templates")
        
        # Commit all changes
        conn.commit()
        
        print("\n🎉 Parent Portal tables created successfully!")
        print("\nNext steps:")
        print("1. Configure Gmail SMTP settings")
        print("2. Set up parent management interface")
        print("3. Test parent registration and login")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("🔧 Parent Portal Database Migration")
    print("=" * 40)
    success = create_parent_portal_tables()
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
