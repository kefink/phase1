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
import logging

def initialize_database_self_contained():
    """Self-contained database initialization using direct SQL commands."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return {"success": False, "error": "DATABASE_URL not found"}
        
        # Parse the URL
        url = urlparse(database_url)
        
        # Connect directly to PostgreSQL
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],  # Remove leading slash
            user=url.username,
            password=url.password
        )
        cur = conn.cursor()
        
        # Check if tables already exist
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'teachers'")
        if cur.fetchone()[0] > 0:
            # Check if data exists
            cur.execute("SELECT COUNT(*) FROM teachers")
            teacher_count = cur.fetchone()[0]
            cur.close()
            conn.close()
            if teacher_count > 0:
                return {"success": True, "message": "Database already initialized"}
        
        # Create tables using direct SQL
        sql_commands = [
            # Teachers table
            """
            CREATE TABLE IF NOT EXISTS teachers (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(120) NOT NULL,
                role VARCHAR(20) NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                employee_id VARCHAR(20) UNIQUE
            )
            """,
            
            # Grades table
            """
            CREATE TABLE IF NOT EXISTS grades (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                education_level VARCHAR(50) NOT NULL
            )
            """,
            
            # Streams table
            """
            CREATE TABLE IF NOT EXISTS streams (
                id SERIAL PRIMARY KEY,
                name VARCHAR(10) NOT NULL,
                grade_id INTEGER REFERENCES grades(id)
            )
            """,
            
            # Subjects table
            """
            CREATE TABLE IF NOT EXISTS subjects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                education_level VARCHAR(50) NOT NULL,
                is_composite BOOLEAN DEFAULT FALSE
            )
            """,
            
            # Terms table
            """
            CREATE TABLE IF NOT EXISTS terms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                academic_year VARCHAR(10) NOT NULL,
                is_current BOOLEAN DEFAULT FALSE
            )
            """,
            
            # Assessment types table
            """
            CREATE TABLE IF NOT EXISTS assessment_types (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL
            )
            """,
            
            # School configurations table
            """
            CREATE TABLE IF NOT EXISTS school_configurations (
                id SERIAL PRIMARY KEY,
                school_name VARCHAR(200) NOT NULL,
                school_motto VARCHAR(200),
                current_academic_year VARCHAR(10),
                current_term VARCHAR(50),
                headteacher_name VARCHAR(100)
            )
            """
        ]
        
        # Execute table creation
        for sql in sql_commands:
            cur.execute(sql)
        
        # Insert default data
        # Users (simple hash for demo - not production secure)
        users = [
            ('headteacher', str(hash('admin123')), 'headteacher', 'Head', 'Teacher', 'HT001'),
            ('kevin', str(hash('kev123')), 'classteacher', 'Kevin', 'Teacher', 'CT002'),
            ('telvo', str(hash('telvo123')), 'teacher', 'Telvo', 'Subject Teacher', 'ST001')
        ]
        
        for user in users:
            cur.execute(
                "INSERT INTO teachers (username, password_hash, role, first_name, last_name, employee_id) VALUES (%s, %s, %s, %s, %s, %s)",
                user
            )
        
        # Grades
        grades = [
            ('PP1', 'pre_primary'), ('PP2', 'pre_primary'),
            ('Grade 1', 'lower_primary'), ('Grade 2', 'lower_primary'), ('Grade 3', 'lower_primary'),
            ('Grade 4', 'upper_primary'), ('Grade 5', 'upper_primary'), ('Grade 6', 'upper_primary'),
            ('Grade 7', 'junior_secondary'), ('Grade 8', 'junior_secondary'), ('Grade 9', 'junior_secondary')
        ]
        
        grade_ids = []
        for name, level in grades:
            cur.execute("INSERT INTO grades (name, education_level) VALUES (%s, %s) RETURNING id", (name, level))
            grade_ids.append(cur.fetchone()[0])
        
        # Streams (A and B for each grade)
        for grade_id in grade_ids:
            cur.execute("INSERT INTO streams (name, grade_id) VALUES (%s, %s)", ('A', grade_id))
            cur.execute("INSERT INTO streams (name, grade_id) VALUES (%s, %s)", ('B', grade_id))
        
        # Subjects
        subjects = [
            ('English', 'lower_primary', True),
            ('Kiswahili', 'lower_primary', True),
            ('Mathematics', 'lower_primary', False),
            ('Environmental Activities', 'lower_primary', False),
            ('English', 'upper_primary', True),
            ('Kiswahili', 'upper_primary', True),
            ('Mathematics', 'upper_primary', False),
            ('Science & Technology', 'upper_primary', False),
            ('English', 'junior_secondary', True),
            ('Kiswahili', 'junior_secondary', True),
            ('Mathematics', 'junior_secondary', False),
            ('Integrated Science', 'junior_secondary', False)
        ]
        
        for name, level, composite in subjects:
            cur.execute("INSERT INTO subjects (name, education_level, is_composite) VALUES (%s, %s, %s)", (name, level, composite))
        
        # Terms
        terms = [
            ('Term 1', '2024', True),
            ('Term 2', '2024', False),
            ('Term 3', '2024', False)
        ]
        
        for name, year, current in terms:
            cur.execute("INSERT INTO terms (name, academic_year, is_current) VALUES (%s, %s, %s)", (name, year, current))
        
        # Assessment types
        assessments = ['CAT 1', 'CAT 2', 'End Term Exam', 'Assignment', 'Project']
        for assessment in assessments:
            cur.execute("INSERT INTO assessment_types (name) VALUES (%s)", (assessment,))
        
        # School configuration
        cur.execute(
            "INSERT INTO school_configurations (school_name, school_motto, current_academic_year, current_term, headteacher_name) VALUES (%s, %s, %s, %s, %s)",
            ('Hillview School', 'Excellence in Education', '2024', 'Term 1', 'Head Teacher')
        )
        
        # Commit all changes
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Database initialized successfully with direct SQL"}
        
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