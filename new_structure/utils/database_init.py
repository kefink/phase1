"""
Database Initialization for Hillview School Management System
Comprehensive solution to create all required tables and initial data
"""

import os
import sqlite3
import logging
from datetime import datetime, date
from flask import current_app
from ..extensions import db

logger = logging.getLogger(__name__)

def create_all_tables():
    """
    Create all database tables using SQLAlchemy models
    """
    try:
        # Import all models to ensure they're registered
        from ..models.user import Teacher
        from ..models.academic import (
            SchoolConfiguration, Subject, Grade, Stream, Term,
            AssessmentType, Student, Mark
        )
        from ..models.assignment import TeacherSubjectAssignment
        # Note: Import permission models to register them with SQLAlchemy
        try:
            from ..models.permission import ClassTeacherPermission, PermissionRequest
        except ImportError:
            pass  # Permission models are optional
        try:
            from ..models.function_permission import FunctionPermission
        except ImportError:
            pass  # Function permission models are optional
        from ..models.parent import Parent, ParentStudent
        from ..models.report_config import ReportConfiguration
        from ..models.school_setup import SchoolSetup
        
        # Create all tables
        db.create_all()
        logger.info("All database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False

def initialize_default_data():
    """
    Initialize the database with default data
    """
    try:
        # Check if data already exists
        from ..models.user import Teacher
        if Teacher.query.first():
            logger.info("Database already has data, skipping initialization")
            return True
        
        # Create default users
        create_default_users()
        
        # Create default academic structure
        create_default_academic_structure()
        
        # Create default subjects
        create_default_subjects()
        
        # Create default school configuration
        create_default_school_config()
        
        db.session.commit()
        logger.info("Default data initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing default data: {e}")
        db.session.rollback()
        return False

def create_default_users():
    """Create default users for the system"""
    from ..models.user import Teacher
    
    default_users = [
        {
            'username': 'headteacher',
            'password': 'admin123',
            'role': 'headteacher',
            'first_name': 'Head',
            'last_name': 'Teacher',
            'email': 'headteacher@school.com',
            'employee_id': 'HT001',
            'qualification': 'DEGREE',
            'is_active': True
        },
        {
            'username': 'classteacher1',
            'password': 'class123',
            'role': 'classteacher',
            'first_name': 'Class',
            'last_name': 'Teacher One',
            'email': 'classteacher1@school.com',
            'employee_id': 'CT001',
            'qualification': 'DIPLOMA',
            'is_active': True
        },
        {
            'username': 'kevin',
            'password': 'kev123',
            'role': 'classteacher',
            'first_name': 'Kevin',
            'last_name': 'Teacher',
            'email': 'kevin@school.com',
            'employee_id': 'CT002',
            'qualification': 'DEGREE',
            'is_active': True
        },
        {
            'username': 'telvo',
            'password': 'telvo123',
            'role': 'teacher',
            'first_name': 'Telvo',
            'last_name': 'Subject Teacher',
            'email': 'telvo@school.com',
            'employee_id': 'ST001',
            'qualification': 'DIPLOMA',
            'is_active': True
        }
    ]
    
    for user_data in default_users:
        teacher = Teacher(**user_data)
        db.session.add(teacher)
    
    logger.info("Default users created")

def create_default_academic_structure():
    """Create default grades, streams, terms, and assessment types"""
    from ..models.academic import Grade, Stream, Term, AssessmentType
    
    # Create grades
    grades = ['Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5', 'Grade 6', 'Grade 7', 'Grade 8', 'Grade 9']
    for grade_name in grades:
        grade = Grade(name=grade_name)
        db.session.add(grade)
    
    # Create streams
    streams = ['A', 'B', 'C']
    for stream_name in streams:
        stream = Stream(name=stream_name)
        db.session.add(stream)
    
    # Create terms
    terms = [
        {'name': 'Term 1', 'academic_year': '2024', 'is_current': True},
        {'name': 'Term 2', 'academic_year': '2024', 'is_current': False},
        {'name': 'Term 3', 'academic_year': '2024', 'is_current': False}
    ]
    for term_data in terms:
        term = Term(**term_data)
        db.session.add(term)
    
    # Create assessment types
    assessments = [
        {'name': 'CAT 1', 'description': 'Continuous Assessment Test 1'},
        {'name': 'CAT 2', 'description': 'Continuous Assessment Test 2'},
        {'name': 'End Term Exam', 'description': 'End of Term Examination'},
        {'name': 'Assignment', 'description': 'Class Assignment'},
        {'name': 'Project', 'description': 'Project Work'}
    ]
    for assessment_data in assessments:
        assessment = AssessmentType(**assessment_data)
        db.session.add(assessment)
    
    logger.info("Default academic structure created")

def create_default_subjects():
    """Create default subjects for all education levels"""
    from ..models.academic import Subject
    
    subjects_data = [
        # Lower Primary (Grades 1-3)
        {'name': 'English', 'education_level': 'lower_primary', 'is_standard': True, 'is_composite': True},
        {'name': 'Kiswahili', 'education_level': 'lower_primary', 'is_standard': True, 'is_composite': True},
        {'name': 'Mathematics', 'education_level': 'lower_primary', 'is_standard': True, 'is_composite': False},
        {'name': 'Environmental Activities', 'education_level': 'lower_primary', 'is_standard': True, 'is_composite': False},
        {'name': 'Creative Arts', 'education_level': 'lower_primary', 'is_standard': True, 'is_composite': False},
        {'name': 'Physical Education', 'education_level': 'lower_primary', 'is_standard': True, 'is_composite': False},
        
        # Upper Primary (Grades 4-6)
        {'name': 'English', 'education_level': 'upper_primary', 'is_standard': True, 'is_composite': True},
        {'name': 'Kiswahili', 'education_level': 'upper_primary', 'is_standard': True, 'is_composite': True},
        {'name': 'Mathematics', 'education_level': 'upper_primary', 'is_standard': True, 'is_composite': False},
        {'name': 'Science & Technology', 'education_level': 'upper_primary', 'is_standard': True, 'is_composite': False},
        {'name': 'Social Studies', 'education_level': 'upper_primary', 'is_standard': True, 'is_composite': False},
        {'name': 'Creative Arts & Sports', 'education_level': 'upper_primary', 'is_standard': True, 'is_composite': False},
        {'name': 'Religious Education', 'education_level': 'upper_primary', 'is_standard': True, 'is_composite': False},
        
        # Junior Secondary (Grades 7-9)
        {'name': 'English', 'education_level': 'junior_secondary', 'is_standard': True, 'is_composite': True},
        {'name': 'Kiswahili', 'education_level': 'junior_secondary', 'is_standard': True, 'is_composite': True},
        {'name': 'Mathematics', 'education_level': 'junior_secondary', 'is_standard': True, 'is_composite': False},
        {'name': 'Integrated Science', 'education_level': 'junior_secondary', 'is_standard': True, 'is_composite': False},
        {'name': 'Social Studies', 'education_level': 'junior_secondary', 'is_standard': True, 'is_composite': False},
        {'name': 'Creative Arts & Sports', 'education_level': 'junior_secondary', 'is_standard': True, 'is_composite': False},
        {'name': 'Religious Education', 'education_level': 'junior_secondary', 'is_standard': True, 'is_composite': False},
        {'name': 'Pre-Technical Studies', 'education_level': 'junior_secondary', 'is_standard': True, 'is_composite': False}
    ]
    
    for subject_data in subjects_data:
        subject = Subject(**subject_data)
        db.session.add(subject)
    
    logger.info("Default subjects created")

def create_default_school_config():
    """Create default school configuration"""
    from ..models.academic import SchoolConfiguration
    from ..models.school_setup import SchoolSetup
    
    # Create SchoolConfiguration
    school_config = SchoolConfiguration(
        school_name='Hillview School',
        school_address='123 Education Street, Learning City',
        school_phone='+254-700-000-000',
        school_email='info@hillviewschool.ac.ke',
        school_motto='Excellence in Education',
        current_term='Term 1',
        current_year=2024
    )
    db.session.add(school_config)
    
    # Create SchoolSetup
    school_setup = SchoolSetup(
        school_name='Hillview School',
        school_address='123 Education Street, Learning City',
        school_email='info@hillviewschool.ac.ke',
        school_phone='+254-700-000-000',
        school_motto='Excellence in Education',
        school_logo_path=None,
        is_configured=True
    )
    db.session.add(school_setup)
    
    logger.info("✅ Default school configuration created")

def check_database_integrity():
    """
    Check database integrity and return status
    """
    try:
        from ..models.user import Teacher
        from ..models.academic import Subject, Grade, Stream
        
        # Check if essential tables exist and have data
        teacher_count = Teacher.query.count()
        subject_count = Subject.query.count()
        grade_count = Grade.query.count()
        stream_count = Stream.query.count()
        
        status = {
            'tables_exist': True,
            'has_data': teacher_count > 0 and subject_count > 0,
            'teacher_count': teacher_count,
            'subject_count': subject_count,
            'grade_count': grade_count,
            'stream_count': stream_count,
            'status': 'healthy' if teacher_count > 0 and subject_count > 0 else 'needs_initialization'
        }
        
        return status
        
    except Exception as e:
        return {
            'tables_exist': False,
            'has_data': False,
            'error': str(e),
            'status': 'error'
        }

def initialize_database_completely():
    """
    Complete database initialization - creates tables and populates with default data
    """
    logger.info("Starting complete database initialization...")

    try:
        # Step 1: Create all tables
        logger.info("Creating database tables...")
        if not create_all_tables():
            return {'success': False, 'error': 'Failed to create tables'}
        
        # Step 2: Initialize default data
        logger.info("Initializing default data...")
        if not initialize_default_data():
            return {'success': False, 'error': 'Failed to initialize default data'}
        
        # Step 3: Check integrity
        logger.info("Checking database integrity...")
        status = check_database_integrity()
        
        if status['status'] == 'healthy':
            logger.info("Database initialization completed successfully!")
            return {
                'success': True,
                'message': 'Database initialized successfully',
                'status': status
            }
        else:
            return {
                'success': False,
                'error': 'Database initialization completed but integrity check failed',
                'status': status
            }
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def repair_database():
    """
    Repair database by recreating missing tables and data
    """
    logger.info("🔧 Starting database repair...")
    
    try:
        # Check current status
        status = check_database_integrity()
        
        if not status['tables_exist']:
            logger.info("📋 Tables missing, creating all tables...")
            create_all_tables()
        
        if not status['has_data']:
            logger.info("📝 Data missing, initializing default data...")
            initialize_default_data()
        
        # Verify repair
        new_status = check_database_integrity()
        
        if new_status['status'] == 'healthy':
            logger.info("✅ Database repair completed successfully!")
            return {
                'success': True,
                'message': 'Database repaired successfully',
                'before': status,
                'after': new_status
            }
        else:
            return {
                'success': False,
                'error': 'Database repair failed',
                'status': new_status
            }
            
    except Exception as e:
        logger.error(f"❌ Database repair failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    # Test database initialization
    print("Testing database initialization...")
    
    # Check current status
    status = check_database_integrity()
    print(f"Current status: {status}")
    
    if status['status'] != 'healthy':
        print("Initializing database...")
        result = initialize_database_completely()
        print(f"Initialization result: {result}")
    else:
        print("Database is already healthy!")
