#!/usr/bin/env python3
"""
Schema Migration Script - Convert SQLite schema to MySQL
This script creates MySQL tables equivalent to the current SQLite schema.
"""

import mysql.connector
from mysql.connector import Error
import json
import os
import sys

class SchemaMigration:
    def __init__(self, credentials_file="mysql_credentials.json"):
        """Initialize with MySQL credentials."""
        self.credentials = self.load_credentials(credentials_file)
        self.connection = None
        
    def load_credentials(self, credentials_file):
        """Load MySQL credentials from file."""
        try:
            with open(credentials_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Credentials file not found: {credentials_file}")
            print("Please run mysql_setup.py first")
            sys.exit(1)
    
    def connect(self):
        """Connect to MySQL tenant database."""
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                database=self.credentials['database_name'],
                user=self.credentials['username'],
                password=self.credentials['password'],
                autocommit=True
            )
            print(f"✅ Connected to database: {self.credentials['database_name']}")
            return True
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            return False
    
    def create_academic_tables(self):
        """Create academic structure tables."""
        cursor = self.connection.cursor()
        
        # Grade table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grade (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                education_level VARCHAR(50) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_education_level (education_level)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created grade table")
        
        # Stream table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stream (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                grade_id INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (grade_id) REFERENCES grade(id) ON DELETE CASCADE,
                INDEX idx_grade_id (grade_id)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created stream table")
        
        # Term table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS term (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                academic_year VARCHAR(20) NOT NULL,
                start_date DATE,
                end_date DATE,
                is_current BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_academic_year (academic_year),
                INDEX idx_is_current (is_current)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created term table")
        
        # Assessment type table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessment_type (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                weight DECIMAL(5,2) DEFAULT 100.00,
                group_name VARCHAR(100),
                show_on_reports BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_group_name (group_name)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created assessment_type table")
        
        # Subject table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subject (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                education_level VARCHAR(50) NOT NULL,
                is_composite BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_education_level (education_level),
                INDEX idx_is_composite (is_composite)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created subject table")
        
        # Subject component table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subject_component (
                id INT AUTO_INCREMENT PRIMARY KEY,
                subject_id INT NOT NULL,
                name VARCHAR(100) NOT NULL,
                weight DECIMAL(5,2) DEFAULT 100.00,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE,
                INDEX idx_subject_id (subject_id)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created subject_component table")
        
        cursor.close()
    
    def create_user_tables(self):
        """Create user management tables."""
        cursor = self.connection.cursor()
        
        # Teacher table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'teacher',
                stream_id INT,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                email VARCHAR(120),
                phone VARCHAR(20),
                specialization VARCHAR(200),
                qualification VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (stream_id) REFERENCES stream(id) ON SET NULL,
                INDEX idx_username (username),
                INDEX idx_role (role),
                INDEX idx_stream_id (stream_id)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created teacher table")
        
        # Student table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                admission_number VARCHAR(50) UNIQUE,
                stream_id INT,
                grade_id INT,
                gender VARCHAR(20) DEFAULT 'Unknown',
                date_of_birth DATE,
                parent_contact VARCHAR(20),
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (stream_id) REFERENCES stream(id) ON SET NULL,
                FOREIGN KEY (grade_id) REFERENCES grade(id) ON SET NULL,
                INDEX idx_admission_number (admission_number),
                INDEX idx_stream_id (stream_id),
                INDEX idx_grade_id (grade_id),
                INDEX idx_name (name)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created student table")
        
        # Parent table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parent (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                is_verified BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                failed_login_attempts INT DEFAULT 0,
                locked_until DATETIME,
                verification_token VARCHAR(255),
                reset_token VARCHAR(255),
                reset_token_expires DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_verification_token (verification_token),
                INDEX idx_reset_token (reset_token)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created parent table")
        
        cursor.close()
    
    def create_relationship_tables(self):
        """Create relationship and junction tables."""
        cursor = self.connection.cursor()
        
        # Teacher subjects many-to-many
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_subjects (
                teacher_id INT NOT NULL,
                subject_id INT NOT NULL,
                PRIMARY KEY (teacher_id, subject_id),
                FOREIGN KEY (teacher_id) REFERENCES teacher(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created teacher_subjects table")
        
        # Teacher subject assignments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_subject_assignment (
                id INT AUTO_INCREMENT PRIMARY KEY,
                teacher_id INT NOT NULL,
                subject_id INT NOT NULL,
                grade_id INT NOT NULL,
                stream_id INT,
                assigned_by INT,
                assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (teacher_id) REFERENCES teacher(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE,
                FOREIGN KEY (grade_id) REFERENCES grade(id) ON DELETE CASCADE,
                FOREIGN KEY (stream_id) REFERENCES stream(id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_by) REFERENCES teacher(id) ON SET NULL,
                INDEX idx_teacher_subject (teacher_id, subject_id),
                INDEX idx_grade_stream (grade_id, stream_id)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created teacher_subject_assignment table")
        
        # Parent student relationships
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parent_student (
                id INT AUTO_INCREMENT PRIMARY KEY,
                parent_id INT NOT NULL,
                student_id INT NOT NULL,
                relationship VARCHAR(50) DEFAULT 'parent',
                is_primary_contact BOOLEAN DEFAULT FALSE,
                can_receive_reports BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES parent(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
                UNIQUE KEY unique_parent_student (parent_id, student_id),
                INDEX idx_parent_id (parent_id),
                INDEX idx_student_id (student_id)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created parent_student table")
        
        cursor.close()
    
    def create_marks_table(self):
        """Create marks table with proper indexing."""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mark (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                subject_id INT NOT NULL,
                term_id INT NOT NULL,
                assessment_type_id INT NOT NULL,
                grade_id INT NOT NULL,
                stream_id INT,
                marks DECIMAL(6,2),
                component_marks JSON,
                total_marks DECIMAL(6,2),
                percentage DECIMAL(5,2),
                grade_letter VARCHAR(5),
                remarks TEXT,
                is_uploaded BOOLEAN DEFAULT FALSE,
                uploaded_by_teacher_id INT,
                upload_date DATETIME,
                last_modified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE,
                FOREIGN KEY (term_id) REFERENCES term(id) ON DELETE CASCADE,
                FOREIGN KEY (assessment_type_id) REFERENCES assessment_type(id) ON DELETE CASCADE,
                FOREIGN KEY (grade_id) REFERENCES grade(id) ON DELETE CASCADE,
                FOREIGN KEY (stream_id) REFERENCES stream(id) ON DELETE CASCADE,
                FOREIGN KEY (uploaded_by_teacher_id) REFERENCES teacher(id) ON SET NULL,
                UNIQUE KEY unique_mark (student_id, subject_id, term_id, assessment_type_id),
                INDEX idx_student_term (student_id, term_id),
                INDEX idx_subject_assessment (subject_id, assessment_type_id),
                INDEX idx_grade_stream (grade_id, stream_id),
                INDEX idx_upload_status (is_uploaded, upload_date)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print("✅ Created mark table")
        
        cursor.close()
    
    def migrate_schema(self):
        """Run complete schema migration."""
        print("🔄 Starting schema migration...")
        
        if not self.connect():
            return False
        
        try:
            self.create_academic_tables()
            self.create_user_tables()
            self.create_relationship_tables()
            self.create_marks_table()
            
            print("✅ Schema migration completed successfully!")
            return True
            
        except Error as e:
            print(f"❌ Error during schema migration: {e}")
            return False
        finally:
            if self.connection:
                self.connection.close()

def main():
    """Main migration function."""
    print("🔄 MySQL Schema Migration for Hillview School Management System")
    print("=" * 70)
    
    migration = SchemaMigration()
    success = migration.migrate_schema()
    
    if success:
        print("\n🎉 Schema migration completed!")
        print("\n🔄 Next step: Run data migration")
        print("Command: python data_migration.py")
    else:
        print("\n❌ Schema migration failed!")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
