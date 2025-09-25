#!/usr/bin/env python3
"""
WSGI entry point for Render deployment.
This file is used by Render to start the Flask application.
"""

import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables
def _load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = os.path.join(current_dir, '.env')
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
        except Exception:
            pass

_load_env_file()

# Set production environment if not set
if not os.environ.get('FLASK_ENV'):
    os.environ['FLASK_ENV'] = 'production'

# Create a simple Flask app for Render deployment
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging

def initialize_database_self_contained():
    """Self-contained database initialization without importing new_structure modules."""
    try:
        # Create SQLAlchemy instance
        db = SQLAlchemy()
        
        # Define models inline for database creation
        class Teacher(db.Model):
            __tablename__ = 'teachers'
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(80), unique=True, nullable=False)
            password_hash = db.Column(db.String(120), nullable=False)
            role = db.Column(db.String(20), nullable=False)
            first_name = db.Column(db.String(50), nullable=False)
            last_name = db.Column(db.String(50), nullable=False)
            employee_id = db.Column(db.String(20), unique=True)
            
            def set_password(self, password):
                # Simple hash for initialization (not secure for production)
                self.password_hash = str(hash(password))
        
        class Grade(db.Model):
            __tablename__ = 'grades'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(50), unique=True, nullable=False)
            education_level = db.Column(db.String(50), nullable=False)
        
        class Stream(db.Model):
            __tablename__ = 'streams'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(10), nullable=False)
            grade_id = db.Column(db.Integer, db.ForeignKey('grades.id'), nullable=False)
        
        class Subject(db.Model):
            __tablename__ = 'subjects'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(100), nullable=False)
            education_level = db.Column(db.String(50), nullable=False)
            is_composite = db.Column(db.Boolean, default=False)
        
        class Term(db.Model):
            __tablename__ = 'terms'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(50), nullable=False)
            academic_year = db.Column(db.String(10), nullable=False)
            is_current = db.Column(db.Boolean, default=False)
        
        class AssessmentType(db.Model):
            __tablename__ = 'assessment_types'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(100), nullable=False)
        
        class SchoolConfiguration(db.Model):
            __tablename__ = 'school_configurations'
            id = db.Column(db.Integer, primary_key=True)
            school_name = db.Column(db.String(200), nullable=False)
            school_motto = db.Column(db.String(200))
            current_academic_year = db.Column(db.String(10))
            current_term = db.Column(db.String(50))
            headteacher_name = db.Column(db.String(100))
        
        # Initialize database with app context
        from flask import current_app
        
        db.init_app(current_app)
        
        with current_app.app_context():
            # Create all tables
            db.create_all()
            
            # Check if data already exists
            if Teacher.query.first() is not None:
                return {"success": True, "message": "Database already initialized"}
            
            # Create default users
            default_users = [
                {"username": "headteacher", "password": "admin123", "role": "headteacher", 
                 "first_name": "Head", "last_name": "Teacher", "employee_id": "HT001"},
                {"username": "kevin", "password": "kev123", "role": "classteacher", 
                 "first_name": "Kevin", "last_name": "Teacher", "employee_id": "CT002"},
                {"username": "telvo", "password": "telvo123", "role": "teacher", 
                 "first_name": "Telvo", "last_name": "Subject Teacher", "employee_id": "ST001"},
            ]
            for data in default_users:
                pwd = data.pop("password")
                t = Teacher(**data)
                t.set_password(pwd)
                db.session.add(t)
            
            # Create grades and streams
            grade_configs = [
                ("PP1", "pre_primary"), ("PP2", "pre_primary"),
                ("Grade 1", "lower_primary"), ("Grade 2", "lower_primary"), ("Grade 3", "lower_primary"),
                ("Grade 4", "upper_primary"), ("Grade 5", "upper_primary"), ("Grade 6", "upper_primary"),
                ("Grade 7", "junior_secondary"), ("Grade 8", "junior_secondary"), ("Grade 9", "junior_secondary")
            ]
            
            grades = []
            for name, level in grade_configs:
                g = Grade(name=name, education_level=level)
                db.session.add(g)
                grades.append(g)
            
            db.session.flush()  # Get IDs
            
            # Create streams for each grade
            for g in grades:
                for stream_name in ("A", "B"):
                    db.session.add(Stream(name=stream_name, grade_id=g.id))
            
            # Create subjects
            subjects = [
                ("English", "lower_primary", True),
                ("Kiswahili", "lower_primary", True),
                ("Mathematics", "lower_primary", False),
                ("Environmental Activities", "lower_primary", False),
                ("English", "upper_primary", True),
                ("Kiswahili", "upper_primary", True),
                ("Mathematics", "upper_primary", False),
                ("Science & Technology", "upper_primary", False),
                ("English", "junior_secondary", True),
                ("Kiswahili", "junior_secondary", True),
                ("Mathematics", "junior_secondary", False),
                ("Integrated Science", "junior_secondary", False),
            ]
            for name, level, composite in subjects:
                db.session.add(Subject(name=name, education_level=level, is_composite=composite))
            
            # Create terms
            terms = [
                {"name": "Term 1", "academic_year": "2024", "is_current": True},
                {"name": "Term 2", "academic_year": "2024", "is_current": False},
                {"name": "Term 3", "academic_year": "2024", "is_current": False},
            ]
            for t in terms:
                db.session.add(Term(**t))
            
            # Create assessment types
            assessments = [
                {"name": "CAT 1"},
                {"name": "CAT 2"},
                {"name": "End Term Exam"},
                {"name": "Assignment"},
                {"name": "Project"},
            ]
            for a in assessments:
                db.session.add(AssessmentType(**a))
            
            # Create school configuration
            cfg = SchoolConfiguration(
                school_name="Hillview School",
                school_motto="Excellence in Education",
                current_academic_year="2024",
                current_term="Term 1",
                headteacher_name="Head Teacher",
            )
            db.session.add(cfg)
            
            # Commit all changes
            db.session.commit()
            
            return {"success": True, "message": "Database initialized successfully"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_simple_app():
    """Create a simplified Flask app for deployment."""
    app = Flask(__name__)
    
    # Simple configuration for deployment
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-deployment')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///fallback.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Try to initialize database on startup (one-time)
    with app.app_context():
        try:
            # Try the full initialization if modules are available
            from new_structure.utils.database_init import initialize_database_completely
            print("Attempting full database initialization...")
            result = initialize_database_completely()
            print(f"Full database initialization result: {result}")
        except Exception as e:
            print(f"Full database initialization skipped: {e}")
            # Try self-contained initialization
            try:
                result = initialize_database_self_contained()
                print(f"Self-contained database initialization result: {result}")
            except Exception as e2:
                print(f"Self-contained database initialization also failed: {e2}")
    
    # Simple routes
    @app.route('/')
    def index():
        return """
        <h1>🎉 Hillview School Management System</h1>
        <p><strong>Status:</strong> Successfully Deployed!</p>
        <p><strong>Environment:</strong> Production</p>
        <p>The application is running and ready to be initialized.</p>
        <hr>
        <p><a href="/health">Health Check</a></p>
        """
    
    @app.route('/health')
    def health():
        return {"status": "ok", "message": "Application is running"}
    
    @app.route('/init-database')
    def init_database():
        try:
            result = initialize_database_self_contained()
            if result.get('success'):
                return {
                    "status": "success", 
                    "message": "Database initialized successfully",
                    "result": str(result)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Database initialization failed: {result.get('error', 'Unknown error')}"
                }, 500
        except Exception as e:
            return {
                "status": "error",
                "message": f"Database initialization failed: {str(e)}"
            }, 500
    
    @app.route('/admin_login')
    def admin_login():
        return """
        <h1>🏫 Admin Login</h1>
        <p>Mobile-friendly admin login will be available after database initialization.</p>
        <p><a href="/">← Back to Home</a></p>
        """
    
    @app.route('/teacher_login')
    def teacher_login():
        return """
        <h1>👩‍🏫 Teacher Login</h1>
        <p>Mobile-friendly teacher login will be available after database initialization.</p>
        <p><a href="/">← Back to Home</a></p>
        """
    
    @app.route('/classteacher_login')
    def classteacher_login():
        return """
        <h1>👨‍🏫 Class Teacher Login</h1>
        <p>Mobile-friendly class teacher login will be available after database initialization.</p>
        <p><a href="/">← Back to Home</a></p>
        """
    
    return app

# Create the application
app = create_simple_app()

if __name__ == '__main__':
    # This won't be called in production, but useful for local testing
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)