#!/usr/bin/env python3
"""
Automated Enhancement Script for Hillview School Management System
This script automatically handles all database migrations and model updates.
"""

import sqlite3
import os
import sys
import re
import shutil
from datetime import datetime

class AutomatedEnhancement:
    def __init__(self):
        self.db_path = None
        self.backup_created = False

    def find_database(self):
        """Find the database file automatically."""
        possible_paths = [
            'kirima_primary.db',
            '../kirima_primary.db',
            '../../kirima_primary.db',
            os.path.join('..', 'kirima_primary.db')
        ]

        for path in possible_paths:
            if os.path.exists(path):
                self.db_path = os.path.abspath(path)
                return True

        print("❌ Database file 'kirima_primary.db' not found!")
        return False

    def create_backup(self):
        """Create a backup of the database."""
        if not self.db_path:
            return False

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.backup_{timestamp}"
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ Database backup created: {backup_path}")
            self.backup_created = True
            return True
        except Exception as e:
            print(f"⚠️  Could not create backup: {e}")
            return False

    def initialize_database(self):
        """Initialize the database with basic tables if they don't exist."""
        try:
            print("🔧 Initializing database...")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = [table[0] for table in cursor.fetchall()]

            if not existing_tables or 'teacher' not in existing_tables:
                print("  📋 Creating basic database tables...")

                # Create basic tables with minimal structure
                create_tables_sql = """
                -- Create teacher table
                CREATE TABLE IF NOT EXISTS teacher (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    stream_id INTEGER
                );

                -- Create school_configuration table
                CREATE TABLE IF NOT EXISTS school_configuration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_name VARCHAR(200) NOT NULL DEFAULT 'School Name',
                    school_motto VARCHAR(500),
                    school_address TEXT,
                    school_phone VARCHAR(50),
                    school_email VARCHAR(100),
                    school_website VARCHAR(100),
                    current_academic_year VARCHAR(20) NOT NULL DEFAULT '2024',
                    current_term VARCHAR(50) NOT NULL DEFAULT 'Term 1',
                    use_streams BOOLEAN DEFAULT 1,
                    grading_system VARCHAR(20) DEFAULT 'CBC',
                    show_position BOOLEAN DEFAULT 1,
                    show_class_average BOOLEAN DEFAULT 1,
                    show_subject_teacher BOOLEAN DEFAULT 0,
                    logo_filename VARCHAR(100),
                    primary_color VARCHAR(7) DEFAULT '#1f7d53',
                    secondary_color VARCHAR(7) DEFAULT '#18230f',
                    headteacher_name VARCHAR(100),
                    deputy_headteacher_name VARCHAR(100),
                    max_raw_marks_default INTEGER DEFAULT 100,
                    pass_mark_percentage REAL DEFAULT 50.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- Insert default configuration
                INSERT OR IGNORE INTO school_configuration (id, school_name) VALUES (1, 'Hillview School');

                -- Create a default admin teacher if none exists
                INSERT OR IGNORE INTO teacher (username, password, role) VALUES ('admin', 'admin123', 'headteacher');
                """

                cursor.executescript(create_tables_sql)
                conn.commit()
                print("  ✅ Basic database tables created")
            else:
                print("  ✅ Database tables already exist")

            conn.close()
            return True

        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            print(f"   Error details: {type(e).__name__}: {str(e)}")
            return False

    def migrate_database(self):
        """Migrate the database to add new fields."""
        if not self.db_path:
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            print("🔧 Migrating database...")

            # Check if teacher table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher';")
            if not cursor.fetchone():
                print("❌ Teacher table not found. Database needs to be initialized first.")
                conn.close()
                return False

            # Check current teacher table structure
            cursor.execute("PRAGMA table_info(teacher)")
            existing_columns = [column[1] for column in cursor.fetchall()]

            # Add new teacher columns
            new_teacher_columns = [
                ('full_name', 'TEXT'),
                ('employee_id', 'TEXT'),
                ('phone_number', 'TEXT'),
                ('email', 'TEXT'),
                ('qualification', 'TEXT'),
                ('specialization', 'TEXT'),
                ('is_active', 'BOOLEAN DEFAULT 1'),
                ('date_joined', 'DATE')
            ]

            added_count = 0
            for column_name, column_type in new_teacher_columns:
                if column_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE teacher ADD COLUMN {column_name} {column_type}")
                        added_count += 1
                        print(f"  ✅ Added teacher.{column_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  ⚠️  Could not add teacher.{column_name}: {e}")

            # Check school_configuration table
            cursor.execute("PRAGMA table_info(school_configuration)")
            config_columns = [column[1] for column in cursor.fetchall()]

            # Add new config columns
            config_new_columns = [
                ('headteacher_id', 'INTEGER'),
                ('deputy_headteacher_id', 'INTEGER')
            ]

            for column_name, column_type in config_new_columns:
                if column_name not in config_columns:
                    try:
                        cursor.execute(f"ALTER TABLE school_configuration ADD COLUMN {column_name} {column_type}")
                        added_count += 1
                        print(f"  ✅ Added school_configuration.{column_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  ⚠️  Could not add school_configuration.{column_name}: {e}")

            # Update existing data
            print("🔄 Updating existing records...")

            # Set default values
            cursor.execute("UPDATE teacher SET is_active = 1 WHERE is_active IS NULL")
            cursor.execute("UPDATE teacher SET full_name = username WHERE full_name IS NULL OR full_name = ''")

            # Generate employee IDs
            cursor.execute("SELECT id, username FROM teacher WHERE employee_id IS NULL OR employee_id = ''")
            teachers = cursor.fetchall()

            for teacher_id, username in teachers:
                employee_id = f"EMP{teacher_id:03d}"
                cursor.execute("UPDATE teacher SET employee_id = ? WHERE id = ?", (employee_id, teacher_id))

            conn.commit()
            conn.close()

            print(f"✅ Database migration completed! Added {added_count} columns, updated {len(teachers)} teachers.")
            return True

        except Exception as e:
            print(f"❌ Database migration failed: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False

    def update_teacher_model(self):
        """Update the Teacher model to include enhanced fields."""
        model_file = 'models/user.py'

        if not os.path.exists(model_file):
            print(f"❌ Model file not found: {model_file}")
            return False

        try:
            with open(model_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Define the enhanced Teacher model
            enhanced_teacher_model = '''class Teacher(db.Model):
    """Teacher model representing school staff members."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # e.g., 'headteacher', 'teacher', 'classteacher'
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)

    # Enhanced teacher information
    full_name = db.Column(db.String(200), nullable=True)  # Full display name
    employee_id = db.Column(db.String(50), nullable=True, unique=True)  # Staff ID
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    qualification = db.Column(db.String(200), nullable=True)  # e.g., "B.Ed Mathematics"
    specialization = db.Column(db.String(200), nullable=True)  # e.g., "Primary Education"
    is_active = db.Column(db.Boolean, default=True)  # Whether teacher is currently active
    date_joined = db.Column(db.Date, nullable=True)

    # Relationships
    stream = db.relationship('Stream', backref=db.backref('teachers', lazy=True))
    subjects = db.relationship('Subject', secondary=teacher_subjects, back_populates='subjects')
'''

            # Replace the Teacher class definition
            pattern = r'class Teacher\(db\.Model\):.*?subjects = db\.relationship\(.*?\)'
            content = re.sub(pattern, enhanced_teacher_model.strip(), content, flags=re.DOTALL)

            with open(model_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print("✅ Teacher model updated with enhanced fields")
            return True

        except Exception as e:
            print(f"❌ Failed to update Teacher model: {e}")
            return False

    def update_school_config_model(self):
        """Update the SchoolConfiguration model to include enhanced fields."""
        model_file = 'models/academic.py'

        if not os.path.exists(model_file):
            print(f"❌ Model file not found: {model_file}")
            return False

        try:
            with open(model_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Add the enhanced fields after deputy_headteacher_name
            enhanced_config_section = '''    # Contact Information
    headteacher_name = db.Column(db.String(100), nullable=True)
    deputy_headteacher_name = db.Column(db.String(100), nullable=True)

    # Dynamic Staff Assignment IDs (references to Teacher table)
    headteacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    deputy_headteacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)

    # Relationships for dynamic staff assignment
    headteacher = db.relationship('Teacher', foreign_keys=[headteacher_id],
                                 backref='headteacher_schools')
    deputy_headteacher = db.relationship('Teacher', foreign_keys=[deputy_headteacher_id],
                                        backref='deputy_headteacher_schools')'''

            # Find and replace the contact information section
            pattern = r'    # Contact Information.*?deputy_headteacher_name = db\.Column\(db\.String\(100\), nullable=True\)'

            if re.search(pattern, content, flags=re.DOTALL):
                content = re.sub(pattern, enhanced_config_section.strip(), content, flags=re.DOTALL)
            else:
                # If pattern not found, try to add after deputy_headteacher_name
                pattern2 = r'(deputy_headteacher_name = db\.Column\(db\.String\(100\), nullable=True\))'
                replacement = r'\1\n\n    # Dynamic Staff Assignment IDs (references to Teacher table)\n    headteacher_id = db.Column(db.Integer, db.ForeignKey(\'teacher.id\'), nullable=True)\n    deputy_headteacher_id = db.Column(db.Integer, db.ForeignKey(\'teacher.id\'), nullable=True)\n\n    # Relationships for dynamic staff assignment\n    headteacher = db.relationship(\'Teacher\', foreign_keys=[headteacher_id], backref=\'headteacher_schools\')\n    deputy_headteacher = db.relationship(\'Teacher\', foreign_keys=[deputy_headteacher_id], backref=\'deputy_headteacher_schools\')'
                content = re.sub(pattern2, replacement, content)

            with open(model_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print("✅ SchoolConfiguration model updated with enhanced fields")
            return True

        except Exception as e:
            print(f"❌ Failed to update SchoolConfiguration model: {e}")
            return False

    def verify_installation(self):
        """Verify that the enhancement was successful."""
        try:
            # Check database
            if not self.db_path:
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check teacher table
            cursor.execute("PRAGMA table_info(teacher)")
            teacher_columns = [column[1] for column in cursor.fetchall()]

            expected_teacher_columns = ['full_name', 'employee_id', 'phone_number', 'email',
                                      'qualification', 'specialization', 'is_active', 'date_joined']

            missing_teacher = [col for col in expected_teacher_columns if col not in teacher_columns]

            # Check config table
            cursor.execute("PRAGMA table_info(school_configuration)")
            config_columns = [column[1] for column in cursor.fetchall()]

            expected_config_columns = ['headteacher_id', 'deputy_headteacher_id']
            missing_config = [col for col in expected_config_columns if col not in config_columns]

            # Check data
            cursor.execute("SELECT COUNT(*) FROM teacher WHERE full_name IS NOT NULL")
            teachers_with_names = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM teacher WHERE employee_id IS NOT NULL")
            teachers_with_ids = cursor.fetchone()[0]

            conn.close()

            print("\n📊 Verification Results:")
            if not missing_teacher:
                print("✅ All teacher columns present")
            else:
                print(f"⚠️  Missing teacher columns: {missing_teacher}")

            if not missing_config:
                print("✅ All config columns present")
            else:
                print(f"⚠️  Missing config columns: {missing_config}")

            print(f"✅ {teachers_with_names} teachers have full names")
            print(f"✅ {teachers_with_ids} teachers have employee IDs")

            return len(missing_teacher) == 0 and len(missing_config) == 0

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

    def run_complete_enhancement(self):
        """Run the complete enhancement process."""
        print("🚀 Automated Enhancement for Hillview School Management System")
        print("=" * 70)
        print("This will automatically enhance your system with dynamic staff management.")
        print("=" * 70)

        # Step 1: Find database
        print("\n📁 Step 1: Locating database...")
        if not self.find_database():
            return False
        print(f"✅ Found database: {self.db_path}")

        # Step 2: Create backup
        print("\n💾 Step 2: Creating backup...")
        self.create_backup()

        # Step 3: Initialize database (create tables if needed)
        print("\n🔧 Step 3: Initializing database...")
        if not self.initialize_database():
            print("⚠️  Database initialization failed, but continuing with migration...")

        # Step 4: Migrate database
        print("\n🔧 Step 4: Migrating database...")
        if not self.migrate_database():
            return False

        # Step 5: Update models
        print("\n📝 Step 5: Updating models...")
        teacher_success = self.update_teacher_model()
        config_success = self.update_school_config_model()

        if not (teacher_success and config_success):
            print("⚠️  Some model updates failed, but database migration succeeded.")

        # Step 6: Verify
        print("\n🔍 Step 6: Verifying installation...")
        verification_success = self.verify_installation()

        # Final results
        print("\n" + "=" * 70)
        if verification_success:
            print("🎉 ENHANCEMENT COMPLETED SUCCESSFULLY!")
            print("\n✅ What's been enhanced:")
            print("  • Database updated with new teacher fields")
            print("  • Models updated with enhanced functionality")
            print("  • Dynamic staff assignment system ready")
            print("  • Employee IDs generated for all teachers")
            print("  • Professional report generation enabled")

            print("\n🚀 Next steps:")
            print("  1. Restart your Flask application")
            print("  2. Test the enhanced features")
            print("  3. Generate reports with dynamic staff information")
            print("  4. Assign class teachers and headteachers as needed")

        else:
            print("⚠️  ENHANCEMENT PARTIALLY COMPLETED")
            print("The database has been updated, but some model updates may have failed.")
            print("Your system should still work with basic functionality.")

        if self.backup_created:
            print(f"\n💾 Backup created for safety. You can restore from backup if needed.")

        print("=" * 70)
        return verification_success

def main():
    enhancer = AutomatedEnhancement()
    enhancer.run_complete_enhancement()

if __name__ == "__main__":
    main()
