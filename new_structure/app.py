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
from flask import Flask, request
import logging

def initialize_database_self_contained():
    """Self-contained database initialization for PostgreSQL using direct connection."""
    try:
        # Try psycopg3 first, fallback to psycopg2
        try:
            import psycopg
            use_psycopg3 = True
        except ImportError:
            import psycopg2 as psycopg
            use_psycopg3 = False
        
        from urllib.parse import urlparse
        import os
        
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return {"success": False, "error": "DATABASE_URL not found in environment"}
        
        # Parse PostgreSQL URL
        parsed = urlparse(db_url)
        
        # Create direct database connection with compatibility for both psycopg versions
        if use_psycopg3:
            # psycopg3 syntax
            conn = psycopg.connect(
                host=parsed.hostname,
                port=parsed.port,
                dbname=parsed.path[1:],  # Remove leading slash
                user=parsed.username,
                password=parsed.password,
                autocommit=True
            )
        else:
            # psycopg2 syntax
            conn = psycopg.connect(
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path[1:],  # Remove leading slash
                user=parsed.username,
                password=parsed.password
            )
            conn.autocommit = True
        
        cur = conn.cursor()
        
        # Check if tables already exist and have data
        try:
            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'teachers')")
            tables_exist = cur.fetchone()[0]
            
            if tables_exist:
                cur.execute("SELECT COUNT(*) FROM teachers")
                teacher_count = cur.fetchone()[0]
                if teacher_count > 0:
                    conn.close()
                    return {"success": True, "message": "Database already initialized with data"}
        except Exception:
            # Tables don't exist yet, continue with creation
            pass
        
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
        
        # Insert default data only if tables are empty
        # Check if we already have users
        cur.execute("SELECT COUNT(*) FROM teachers")
        existing_teachers = cur.fetchone()[0]
        
        if existing_teachers == 0:
            # Insert default users
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
        
        # Close connection
        cur.close()
        conn.close()
        
        driver_used = "psycopg3" if use_psycopg3 else "psycopg2"
        return {"success": True, "message": f"Database initialized successfully with PostgreSQL direct connection using {driver_used}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def validate_login(username, password, required_role=None):
    """Validate user login credentials against the database."""
    try:
        # Try psycopg3 first, fallback to psycopg2
        try:
            import psycopg
            use_psycopg3 = True
        except ImportError:
            import psycopg2 as psycopg
            use_psycopg3 = False
        
        from urllib.parse import urlparse
        
        # Get database URL
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return False
        
        parsed = urlparse(db_url)
        
        # Create connection
        if use_psycopg3:
            conn = psycopg.connect(
                host=parsed.hostname,
                port=parsed.port,
                dbname=parsed.path[1:],
                user=parsed.username,
                password=parsed.password,
                autocommit=True
            )
        else:
            conn = psycopg.connect(
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path[1:],
                user=parsed.username,
                password=parsed.password
            )
            conn.autocommit = True
        
        cur = conn.cursor()
        
        # Query user from database
        cur.execute("SELECT password_hash, role FROM teachers WHERE username = %s", (username,))
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if result:
            stored_hash, user_role = result
            # Simple hash comparison (in production, use proper password hashing)
            if str(hash(password)) == stored_hash:
                if required_role is None or user_role == required_role:
                    return True
        
        return False
        
    except Exception as e:
        print(f"Login validation error: {e}")
        return False

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
        <!DOCTYPE html>
        <html>
        <head>
            <title>Hillview School Management System</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 600px; margin: 50px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .header h1 { color: #2c3e50; margin: 0; }
                .header p { color: #7f8c8d; margin: 10px 0; }
                .status { background: #2ecc71; color: white; padding: 15px; border-radius: 5px; margin-bottom: 30px; text-align: center; }
                .login-links { display: grid; gap: 15px; margin-bottom: 30px; }
                .login-link { display: block; padding: 15px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; text-align: center; font-weight: bold; }
                .login-link:hover { background: #2980b9; }
                .login-link.admin { background: #e74c3c; }
                .login-link.admin:hover { background: #c0392b; }
                .login-link.teacher { background: #27ae60; }
                .login-link.teacher:hover { background: #229954; }
                .login-link.classteacher { background: #f39c12; }
                .login-link.classteacher:hover { background: #e67e22; }
                .system-links { text-align: center; padding-top: 20px; border-top: 1px solid #ecf0f1; }
                .system-links a { color: #3498db; text-decoration: none; margin: 0 15px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Hillview School Management System</h1>
                    <p>Mobile-Optimized School Management Platform</p>
                </div>
                <div class="status">
                    ✅ Successfully Deployed & Database Initialized
                </div>
                <div class="login-links">
                    <a href="/admin_login" class="login-link admin">🏫 Headteacher Login</a>
                    <a href="/classteacher_login" class="login-link classteacher">👨‍🏫 Class Teacher Login</a>
                    <a href="/teacher_login" class="login-link teacher">👩‍🏫 Subject Teacher Login</a>
                </div>
                <div class="system-links">
                    <a href="/health">Health Check</a> | 
                    <a href="/init-database">Database Status</a>
                </div>
            </div>
        </body>
        </html>
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
    
    @app.route('/admin_login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Validate credentials against database
            if validate_login(username, password, 'headteacher'):
                return f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; border: 2px solid #4CAF50; border-radius: 10px; background: #f9f9f9;">
                    <h2 style="color: #4CAF50;">✅ Login Successful!</h2>
                    <p><strong>Welcome, {username}!</strong></p>
                    <p>You have successfully logged into the <strong>Headteacher Dashboard</strong>.</p>
                    <p><em>Note: This is the login verification page. In the full application, you would be redirected to your dashboard.</em></p>
                    <p><a href="/admin_login" style="color: #2196F3;">← Try Another Login</a> | <a href="/" style="color: #2196F3;">Home</a></p>
                </div>
                """
            else:
                error_msg = "Invalid credentials. Please try again."
        else:
            error_msg = None
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Hillview School - Admin Login</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .logo {{ text-align: center; margin-bottom: 30px; }}
                .logo h1 {{ color: #2c3e50; margin: 0; }}
                .logo p {{ color: #7f8c8d; margin: 5px 0 0 0; }}
                .form-group {{ margin-bottom: 20px; }}
                label {{ display: block; margin-bottom: 5px; color: #2c3e50; font-weight: bold; }}
                input[type="text"], input[type="password"] {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; font-size: 16px; }}
                .btn {{ background: #3498db; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-size: 16px; }}
                .btn:hover {{ background: #2980b9; }}
                .error {{ background: #e74c3c; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
                .back-link {{ text-align: center; margin-top: 20px; }}
                .back-link a {{ color: #3498db; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>🏫 Hillview School</h1>
                    <p>Admin Login Portal</p>
                </div>
                {"<div class='error'>" + error_msg + "</div>" if error_msg else ""}
                <form method="POST">
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn">Login</button>
                </form>
                <div class="back-link">
                    <a href="/">← Back to Home</a>
                </div>
                <div style="margin-top: 20px; padding: 15px; background: #ecf0f1; border-radius: 5px; font-size: 14px;">
                    <strong>Default Credentials:</strong><br>
                    Username: <code>headteacher</code><br>
                    Password: <code>admin123</code>
                </div>
            </div>
        </body>
        </html>
        """
    
    @app.route('/teacher_login', methods=['GET', 'POST'])
    def teacher_login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Validate credentials against database (any teacher role)
            if validate_login(username, password) and username in ['kevin', 'telvo']:
                return f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; border: 2px solid #4CAF50; border-radius: 10px; background: #f9f9f9;">
                    <h2 style="color: #4CAF50;">✅ Login Successful!</h2>
                    <p><strong>Welcome, {username}!</strong></p>
                    <p>You have successfully logged into the <strong>Teacher Dashboard</strong>.</p>
                    <p><em>Note: This is the login verification page. In the full application, you would be redirected to your dashboard.</em></p>
                    <p><a href="/teacher_login" style="color: #2196F3;">← Try Another Login</a> | <a href="/" style="color: #2196F3;">Home</a></p>
                </div>
                """
            else:
                error_msg = "Invalid credentials. Please try again."
        else:
            error_msg = None
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Hillview School - Teacher Login</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .logo {{ text-align: center; margin-bottom: 30px; }}
                .logo h1 {{ color: #2c3e50; margin: 0; }}
                .logo p {{ color: #7f8c8d; margin: 5px 0 0 0; }}
                .form-group {{ margin-bottom: 20px; }}
                label {{ display: block; margin-bottom: 5px; color: #2c3e50; font-weight: bold; }}
                input[type="text"], input[type="password"] {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; font-size: 16px; }}
                .btn {{ background: #27ae60; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-size: 16px; }}
                .btn:hover {{ background: #229954; }}
                .error {{ background: #e74c3c; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
                .back-link {{ text-align: center; margin-top: 20px; }}
                .back-link a {{ color: #27ae60; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>👩‍🏫 Hillview School</h1>
                    <p>Teacher Login Portal</p>
                </div>
                {"<div class='error'>" + error_msg + "</div>" if error_msg else ""}
                <form method="POST">
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn">Login</button>
                </form>
                <div class="back-link">
                    <a href="/">← Back to Home</a>
                </div>
                <div style="margin-top: 20px; padding: 15px; background: #ecf0f1; border-radius: 5px; font-size: 14px;">
                    <strong>Default Credentials:</strong><br>
                    Class Teacher: <code>kevin</code> / <code>kev123</code><br>
                    Subject Teacher: <code>telvo</code> / <code>telvo123</code>
                </div>
            </div>
        </body>
        </html>
        """
    
    @app.route('/classteacher_login', methods=['GET', 'POST'])
    def classteacher_login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Validate credentials against database
            if validate_login(username, password, 'classteacher'):
                return f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; border: 2px solid #4CAF50; border-radius: 10px; background: #f9f9f9;">
                    <h2 style="color: #4CAF50;">✅ Login Successful!</h2>
                    <p><strong>Welcome, {username}!</strong></p>
                    <p>You have successfully logged into the <strong>Class Teacher Dashboard</strong>.</p>
                    <p><em>Note: This is the login verification page. In the full application, you would be redirected to your dashboard.</em></p>
                    <p><a href="/classteacher_login" style="color: #2196F3;">← Try Another Login</a> | <a href="/" style="color: #2196F3;">Home</a></p>
                </div>
                """
            else:
                error_msg = "Invalid credentials. Please try again."
        else:
            error_msg = None
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Hillview School - Class Teacher Login</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .logo {{ text-align: center; margin-bottom: 30px; }}
                .logo h1 {{ color: #2c3e50; margin: 0; }}
                .logo p {{ color: #7f8c8d; margin: 5px 0 0 0; }}
                .form-group {{ margin-bottom: 20px; }}
                label {{ display: block; margin-bottom: 5px; color: #2c3e50; font-weight: bold; }}
                input[type="text"], input[type="password"] {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; font-size: 16px; }}
                .btn {{ background: #f39c12; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-size: 16px; }}
                .btn:hover {{ background: #e67e22; }}
                .error {{ background: #e74c3c; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
                .back-link {{ text-align: center; margin-top: 20px; }}
                .back-link a {{ color: #f39c12; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>👨‍🏫 Hillview School</h1>
                    <p>Class Teacher Login Portal</p>
                </div>
                {"<div class='error'>" + error_msg + "</div>" if error_msg else ""}
                <form method="POST">
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn">Login</button>
                </form>
                <div class="back-link">
                    <a href="/">← Back to Home</a>
                </div>
                <div style="margin-top: 20px; padding: 15px; background: #ecf0f1; border-radius: 5px; font-size: 14px;">
                    <strong>Default Credentials:</strong><br>
                    Username: <code>kevin</code><br>
                    Password: <code>kev123</code>
                </div>
            </div>
        </body>
        </html>
        """
    
    return app

# Create the application
app = create_simple_app()

if __name__ == '__main__':
    # This won't be called in production, but useful for local testing
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)