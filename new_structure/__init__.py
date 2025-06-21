"""
Application factory for the Hillview School Management System.
This file initializes the Flask application and registers extensions and blueprints.
"""
from flask import Flask
from .extensions import db, csrf
from .config import config
from .logging_config import setup_logging
from .middleware import MarkSanitizerMiddleware
# Temporarily disable security manager for debugging
# from .security.security_manager import security_manager

def create_app(config_name='default'):
    """Create and configure the Flask application.

    Args:
        config_name: Name of the configuration to use (default, development, testing, production)

    Returns:
        Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Set up logging
    setup_logging(app)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)

    # Initialize database with tables and default data
    with app.app_context():
        try:
            from .utils.database_init import initialize_database_completely, check_database_integrity

            # Check if database needs initialization
            status = check_database_integrity()

            if status['status'] != 'healthy':
                print("Database needs initialization...")
                result = initialize_database_completely()

                if result['success']:
                    print("Database initialized successfully!")
                    print(f"   Teachers: {result['status']['teacher_count']}")
                    print(f"   Subjects: {result['status']['subject_count']}")
                    print(f"   Grades: {result['status']['grade_count']}")
                    print(f"   Streams: {result['status']['stream_count']}")
                else:
                    print(f"Database initialization failed: {result.get('error', 'Unknown error')}")
            else:
                print("Database is healthy and ready!")

        except Exception as e:
            print(f"Database initialization error: {e}")
            print("   Application will continue but may have limited functionality")

    # Initialize comprehensive security (temporarily disabled for debugging)
    # security_manager.init_app(app)

    # Register blueprints with error handling
    try:
        from .views import blueprints
        for blueprint in blueprints:
            app.register_blueprint(blueprint)
            # Exempt parent portal from CSRF protection
            if hasattr(blueprint, 'name') and 'parent' in blueprint.name:
                csrf.exempt(blueprint)
        print(f"✅ Successfully registered {len(blueprints)} blueprints")
    except Exception as e:
        print(f"❌ Error importing blueprints: {e}")
        print("⚠️ Application will start with minimal functionality")

    # Register middleware
    MarkSanitizerMiddleware(app)

    # Register custom Jinja2 filters
    @app.template_filter('get_education_level')
    def get_education_level(grade):
        """Filter to determine the education level for a grade."""
        education_level_mapping = {
            'lower_primary': ['Grade 1', 'Grade 2', 'Grade 3'],
            'upper_primary': ['Grade 4', 'Grade 5', 'Grade 6'],
            'junior_secondary': ['Grade 7', 'Grade 8', 'Grade 9']
        }

        for level, grades in education_level_mapping.items():
            if grade in grades:
                return level
        return ''

    @app.template_filter('tojsonhtml')
    def tojsonhtml_filter(obj):
        """Convert object to JSON for safe use in HTML templates."""
        import json
        from markupsafe import Markup
        return Markup(json.dumps(obj))

    # Import the classteacher blueprint
    from .views.classteacher import classteacher_bp

    # Add a simple health check route
    @app.route('/health')
    def health_check():
        """Simple health check route"""
        try:
            from .utils.database_init import check_database_integrity
            status = check_database_integrity()

            if status['status'] == 'healthy':
                return f"""
                <h2>✅ System Health Check</h2>
                <p><strong>Status:</strong> <span style="color: green;">Healthy</span></p>
                <p><strong>Teachers:</strong> {status['teacher_count']}</p>
                <p><strong>Subjects:</strong> {status['subject_count']}</p>
                <p><strong>Grades:</strong> {status['grade_count']}</p>
                <p><strong>Streams:</strong> {status['stream_count']}</p>
                <p><a href="/">🏠 Go to Login Page</a></p>
                """
            else:
                return f"""
                <h2>⚠️ System Health Check</h2>
                <p><strong>Status:</strong> <span style="color: red;">{status['status']}</span></p>
                <p><a href="/debug/initialize_database" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🔄 Initialize Database</a></p>
                <p><a href="/">🏠 Go to Login Page</a></p>
                """
        except Exception as e:
            return f"""
            <h2>❌ System Health Check</h2>
            <p><strong>Status:</strong> <span style="color: red;">Error</span></p>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><a href="/debug/initialize_database" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🔄 Initialize Database</a></p>
            """

    # Register error handlers
    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"Internal Server Error: {str(e)}")
        # Check if it's a database error and provide helpful message
        error_str = str(e)
        if "no such table" in error_str.lower() or "database" in error_str.lower():
            return f"""
            <h2>🔧 Database Error Detected</h2>
            <p>It looks like there's a database issue. This usually means the database tables haven't been created yet.</p>
            <p><strong>Quick Fix:</strong></p>
            <p><a href="/debug/initialize_database" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🔄 Initialize Database</a></p>
            <p><a href="/debug/check_tables" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">📋 Check Database Tables</a></p>
            <hr>
            <p><strong>Error Details:</strong> {error_str}</p>
            """, 500
        return "Internal Server Error", 500

    # Temporary routes for debugging user issues
    @app.route('/debug/check_users')
    def debug_check_users():
        """Debug route to check all users."""
        try:
            from .models.user import Teacher

            teachers = Teacher.query.all()

            result = f"<h2>Users in Database ({len(teachers)} total):</h2><ul>"

            for teacher in teachers:
                result += f"<li><strong>{teacher.username}</strong> - Password: {teacher.password} - Role: {teacher.role}"
                if hasattr(teacher, 'full_name') and teacher.full_name:
                    result += f" - Full Name: {teacher.full_name}"
                result += "</li>"

            result += "</ul>"

            # Check for Kevin specifically
            kevin = Teacher.query.filter_by(username='kevin').first()
            if kevin:
                result += f"<p>✅ <strong>Kevin found!</strong> Username: {kevin.username}, Password: {kevin.password}</p>"
            else:
                result += f"<p>❌ <strong>Kevin NOT found</strong></p>"
                result += f'<p><a href="/debug/add_kevin">Click here to add Kevin</a></p>'

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    @app.route('/debug/add_kevin')
    def debug_add_kevin():
        """Debug route to add Kevin user."""
        try:
            from .models.user import Teacher

            # Check if Kevin exists
            kevin = Teacher.query.filter_by(username='kevin').first()

            if kevin:
                return f"Kevin already exists: {kevin.username}, role: {kevin.role}"

            # Add Kevin
            kevin = Teacher(
                username='kevin',
                password='kev123',
                role='classteacher'
            )

            # Add enhanced fields if they exist
            if hasattr(Teacher, 'full_name'):
                kevin.full_name = 'Kevin Teacher'
            if hasattr(Teacher, 'employee_id'):
                kevin.employee_id = 'EMP002'
            if hasattr(Teacher, 'is_active'):
                kevin.is_active = True

            db.session.add(kevin)
            db.session.commit()

            return "✅ Kevin added successfully! You can now login with kevin/kev123<br><a href='/debug/check_users'>Check users again</a>"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    @app.route('/debug/check_all_databases')
    def debug_check_all_databases():
        """Debug route to check all database files."""
        import glob
        import os

        def check_db_users(db_path):
            if not os.path.exists(db_path):
                return None
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher'")
                if not cursor.fetchone():
                    conn.close()
                    return "No teacher table"
                cursor.execute("SELECT id, username, password, role FROM teacher")
                users = cursor.fetchall()
                conn.close()
                return users
            except Exception as e:
                return f"Error: {e}"

        result = "<h2>🔍 All Database Files Check</h2>"

        # Check main databases
        db_files = ["../kirima_primary.db", "kirima_primary.db"]

        # Add backup files
        backup_files = glob.glob("kirima_primary.db.backup_*")
        backup_files.extend(glob.glob("../kirima_primary.db.backup_*"))

        all_files = db_files + backup_files

        for db_file in all_files:
            result += f"<h3>📁 {db_file}</h3>"
            result += f"<p>Exists: {os.path.exists(db_file)}</p>"

            if os.path.exists(db_file):
                size = os.path.getsize(db_file)
                result += f"<p>Size: {size:,} bytes</p>"

                users = check_db_users(db_file)

                if isinstance(users, list):
                    result += f"<p><strong>Users: {len(users)} found</strong></p><ul>"
                    for user in users:
                        result += f"<li>{user[1]} (password: {user[2]}, role: {user[3]})</li>"
                    result += "</ul>"

                    # Check for kevin
                    kevin_found = any(user[1] == 'kevin' for user in users)
                    if kevin_found:
                        result += f"<p style='color: green;'>✅ <strong>KEVIN FOUND in this database!</strong></p>"
                        result += f"<p><a href='/debug/restore_from_backup?file={db_file}'>Restore from this database</a></p>"
                else:
                    result += f"<p>Status: {users}</p>"

            result += "<hr>"

        return result

    @app.route('/debug/check_subjects')
    def debug_check_subjects():
        """Debug route to check all subjects in the database."""
        try:
            from .models.academic import Subject

            subjects = Subject.query.order_by(Subject.education_level, Subject.name).all()

            result = f"<h2>📚 Subjects in Database ({len(subjects)} total)</h2>"

            if not subjects:
                result += "<p style='color: red;'>❌ <strong>NO SUBJECTS FOUND!</strong></p>"
                result += "<p>This means the subject table is empty or doesn't exist.</p>"
                return result

            # Group by education level
            levels = {}
            for subject in subjects:
                level = subject.education_level
                if level not in levels:
                    levels[level] = []
                levels[level].append(subject)

            for level, level_subjects in levels.items():
                result += f"<h3>🎓 {level.replace('_', ' ').title()} ({len(level_subjects)} subjects)</h3>"
                result += "<ul>"
                for subject in level_subjects:
                    result += f"<li><strong>{subject.name}</strong>"
                    if hasattr(subject, 'is_standard'):
                        result += f" - Standard: {subject.is_standard}"
                    if hasattr(subject, 'is_composite'):
                        result += f" - Composite: {subject.is_composite}"
                    result += "</li>"
                result += "</ul>"

            return result

        except Exception as e:
            return f"❌ Error checking subjects: {str(e)}"

    @app.route('/debug/check_tables')
    def debug_check_tables():
        """Debug route to check what tables exist in the database."""
        try:
            import sqlite3
            from .config import config

            # Get the database path from config
            conf = config['development']()
            db_uri = conf.SQLALCHEMY_DATABASE_URI
            db_path = db_uri.replace('sqlite:///', '')

            result = f"<h2>🗃️ Database Tables Check</h2>"
            result += f"<p><strong>Database Path:</strong> {db_path}</p>"
            result += f"<p><strong>Database URI:</strong> {db_uri}</p>"

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]

            result += f"<h3>📋 Tables Found ({len(tables)} total):</h3><ul>"

            for table in sorted(tables):
                result += f"<li><strong>{table}</strong>"

                # Get row count for each table
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    result += f" - {count} records"
                except:
                    result += " - Error counting records"

                result += "</li>"

            result += "</ul>"

            # Check specific tables we care about
            important_tables = ['teacher', 'subject', 'grade', 'stream', 'student', 'term']
            missing_tables = [table for table in important_tables if table not in tables]

            if missing_tables:
                result += f"<h3 style='color: red;'>❌ Missing Important Tables:</h3><ul>"
                for table in missing_tables:
                    result += f"<li>{table}</li>"
                result += "</ul>"
            else:
                result += f"<h3 style='color: green;'>✅ All Important Tables Present</h3>"

            conn.close()
            return result

        except Exception as e:
            return f"❌ Error checking tables: {str(e)}"

    @app.route('/debug/find_real_database')
    def debug_find_real_database():
        """Search for the real database with telvo, kevin, and classteacher1."""
        import os
        import glob
        import sqlite3

        result = "<h2>🔍 Searching for Your Real Database</h2>"
        result += "<p>Looking for database with users: telvo, kevin, classteacher1</p><hr>"

        # Search patterns
        search_paths = [
            "*.db",
            "../*.db",
            "../../*.db",
            "**/kirima*.db",
            "**/school*.db",
            "**/*.db"
        ]

        found_databases = set()

        for pattern in search_paths:
            try:
                files = glob.glob(pattern, recursive=True)
                for file in files:
                    if os.path.exists(file):
                        found_databases.add(os.path.abspath(file))
            except:
                pass

        result += f"<h3>📁 Found {len(found_databases)} database files:</h3>"

        for db_path in sorted(found_databases):
            result += f"<h4>🗃️ {db_path}</h4>"

            try:
                # Get file info
                size = os.path.getsize(db_path)
                result += f"<p>Size: {size:,} bytes</p>"

                # Check users
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Check if teacher table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher'")
                if not cursor.fetchone():
                    result += "<p>❌ No teacher table</p>"
                    conn.close()
                    continue

                # Get all users
                cursor.execute("SELECT id, username, password, role FROM teacher")
                users = cursor.fetchall()

                result += f"<p><strong>Users ({len(users)}):</strong></p><ul>"

                # Check for your specific users
                telvo_found = False
                kevin_found = False
                classteacher1_found = False

                for user in users:
                    username = user[1].lower()
                    result += f"<li><strong>{user[1]}</strong> (password: {user[2]}, role: {user[3]})</li>"

                    if 'telvo' in username:
                        telvo_found = True
                    if 'kevin' in username:
                        kevin_found = True
                    if 'classteacher1' in username:
                        classteacher1_found = True

                result += "</ul>"

                # Check if this is the real database
                matches = sum([telvo_found, kevin_found, classteacher1_found])
                if matches >= 2:
                    result += f"<p style='color: green; font-size: 18px;'>🎯 <strong>POTENTIAL MATCH!</strong> Found {matches}/3 of your users!</p>"
                    result += f"<p><a href='/debug/use_database?path={db_path}' style='background: green; color: white; padding: 10px; text-decoration: none;'>USE THIS DATABASE</a></p>"

                # Also check subjects to see if they're your real subjects
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subject'")
                if cursor.fetchone():
                    cursor.execute("SELECT COUNT(*) FROM subject")
                    subject_count = cursor.fetchone()[0]
                    result += f"<p>📚 Subjects: {subject_count} found</p>"

                conn.close()

            except Exception as e:
                result += f"<p>❌ Error: {e}</p>"

            result += "<hr>"

        return result

    @app.route('/debug/use_database')
    def debug_use_database():
        """Switch to use a specific database."""
        import shutil
        import os
        from flask import request
        from datetime import datetime

        db_path = request.args.get('path')
        if not db_path or not os.path.exists(db_path):
            return "❌ Invalid database path"

        try:
            # Get the current database path
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            current_db_path = current_db_uri.replace('sqlite:///', '')

            # Create backup of current database
            backup_path = f"{current_db_path}.backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(current_db_path, backup_path)

            # Copy the real database to the current location
            shutil.copy2(db_path, current_db_path)

            return f"""
            <h2>✅ Database Restored!</h2>
            <p><strong>Copied from:</strong> {db_path}</p>
            <p><strong>To:</strong> {current_db_path}</p>
            <p><strong>Backup created:</strong> {backup_path}</p>
            <p><a href='/debug/check_users'>Check users now</a></p>
            <p><strong>You may need to restart the Flask app for changes to take effect.</strong></p>
            """

        except Exception as e:
            return f"❌ Error restoring database: {e}"

    @app.route('/debug/check_git_database')
    def debug_check_git_database():
        """Check the last committed database from Git."""
        import subprocess
        import os
        import sqlite3
        import tempfile

        result = "<h2>🔍 Checking Git for Original Database</h2>"

        try:
            # Check if we're in a git repository
            git_check = subprocess.run(['git', 'status'], capture_output=True, text=True, cwd='..')
            if git_check.returncode != 0:
                return result + "<p>❌ Not in a Git repository or Git not available</p>"

            result += "<p>✅ Git repository found</p>"

            # Get the last few commits
            commits = subprocess.run(['git', 'log', '--oneline', '-10'], capture_output=True, text=True, cwd='..')
            result += f"<h3>📋 Recent Commits:</h3><pre>{commits.stdout}</pre>"

            # Check if database file is tracked in git
            git_files = subprocess.run(['git', 'ls-files', '*.db'], capture_output=True, text=True, cwd='..')
            result += f"<h3>🗃️ Database files in Git:</h3><pre>{git_files.stdout}</pre>"

            # Try to get the database from the last commit
            db_files_in_git = git_files.stdout.strip().split('\n') if git_files.stdout.strip() else []

            for db_file in db_files_in_git:
                if db_file:
                    result += f"<h4>📁 Checking {db_file} from Git</h4>"

                    # Get the file from the last commit
                    try:
                        git_show = subprocess.run(['git', 'show', f'HEAD:{db_file}'], capture_output=True, cwd='..')

                        if git_show.returncode == 0:
                            # Save to temporary file
                            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
                                temp_db.write(git_show.stdout)
                                temp_db_path = temp_db.name

                            # Check users in this database
                            conn = sqlite3.connect(temp_db_path)
                            cursor = conn.cursor()

                            # Check if teacher table exists
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher'")
                            if cursor.fetchone():
                                cursor.execute("SELECT id, username, password, role FROM teacher")
                                users = cursor.fetchall()

                                result += f"<p><strong>Users in Git version ({len(users)}):</strong></p><ul>"

                                telvo_found = False
                                kevin_found = False
                                classteacher1_found = False

                                for user in users:
                                    username = user[1].lower()
                                    result += f"<li><strong>{user[1]}</strong> (password: {user[2]}, role: {user[3]})</li>"

                                    if 'telvo' in username:
                                        telvo_found = True
                                    if 'kevin' in username:
                                        kevin_found = True
                                    if 'classteacher1' in username:
                                        classteacher1_found = True

                                result += "</ul>"

                                matches = sum([telvo_found, kevin_found, classteacher1_found])
                                if matches >= 2:
                                    result += f"<p style='color: green; font-size: 18px;'>🎯 <strong>FOUND YOUR ORIGINAL DATABASE!</strong> Found {matches}/3 of your users!</p>"
                                    result += f"<p><a href='/debug/restore_git_database?file={db_file}' style='background: green; color: white; padding: 10px; text-decoration: none;'>RESTORE THIS DATABASE</a></p>"

                                # Check subjects
                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subject'")
                                if cursor.fetchone():
                                    cursor.execute("SELECT COUNT(*) FROM subject")
                                    subject_count = cursor.fetchone()[0]
                                    result += f"<p>📚 Subjects: {subject_count} found</p>"

                                    # Show some subjects
                                    cursor.execute("SELECT name FROM subject LIMIT 10")
                                    subjects = cursor.fetchall()
                                    result += "<p>Sample subjects: " + ", ".join([s[0] for s in subjects]) + "</p>"

                            conn.close()
                            os.unlink(temp_db_path)  # Clean up temp file

                        else:
                            result += f"<p>❌ Could not retrieve {db_file} from Git</p>"

                    except Exception as e:
                        result += f"<p>❌ Error checking {db_file}: {e}</p>"

            return result

        except Exception as e:
            return result + f"<p>❌ Error: {e}</p>"

    @app.route('/debug/restore_git_database')
    def debug_restore_git_database():
        """Restore database from Git."""
        import subprocess
        import os
        from flask import request
        from datetime import datetime

        db_file = request.args.get('file')
        if not db_file:
            return "❌ No database file specified"

        try:
            # Get the current database path
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            current_db_path = current_db_uri.replace('sqlite:///', '')

            # Create backup of current database
            backup_path = f"{current_db_path}.backup_before_git_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists(current_db_path):
                import shutil
                shutil.copy2(current_db_path, backup_path)

            # Get the database from Git and save it
            git_show = subprocess.run(['git', 'show', f'HEAD:{db_file}'], capture_output=True, cwd='..')

            if git_show.returncode == 0:
                with open(current_db_path, 'wb') as f:
                    f.write(git_show.stdout)

                return f"""
                <h2>✅ Database Restored from Git!</h2>
                <p><strong>Restored:</strong> {db_file} from Git HEAD</p>
                <p><strong>To:</strong> {current_db_path}</p>
                <p><strong>Backup created:</strong> {backup_path}</p>
                <p><a href='/debug/check_users'>Check users now</a></p>
                <p><strong>Please restart the Flask app for changes to take effect.</strong></p>
                <p><strong>You should now be able to login with your original credentials!</strong></p>
                """
            else:
                return f"❌ Could not retrieve {db_file} from Git"

        except Exception as e:
            return f"❌ Error restoring from Git: {e}"

    @app.route('/debug/enhance_restored_database')
    def debug_enhance_restored_database():
        """Add enhanced columns to the restored database."""
        import sqlite3
        import os
        from datetime import datetime

        result = "<h2>🔧 Enhancing Restored Database</h2>"

        try:
            # Get the current database path
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            current_db_path = current_db_uri.replace('sqlite:///', '')

            result += f"<p><strong>Database:</strong> {current_db_path}</p>"

            # Create backup before enhancement
            backup_path = f"{current_db_path}.backup_before_enhancement_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(current_db_path, backup_path)
            result += f"<p>✅ Backup created: {backup_path}</p>"

            conn = sqlite3.connect(current_db_path)
            cursor = conn.cursor()

            # Check current teacher table structure
            cursor.execute("PRAGMA table_info(teacher)")
            columns = [col[1] for col in cursor.fetchall()]
            result += f"<p><strong>Current columns:</strong> {', '.join(columns)}</p>"

            # Enhanced columns to add
            enhanced_columns = [
                ('full_name', 'TEXT'),
                ('employee_id', 'TEXT'),
                ('phone_number', 'TEXT'),
                ('email', 'TEXT'),
                ('qualification', 'TEXT'),
                ('specialization', 'TEXT'),
                ('is_active', 'BOOLEAN DEFAULT 1'),
                ('date_joined', 'DATE')
            ]

            # Add missing columns
            added_columns = []
            for col_name, col_type in enhanced_columns:
                if col_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE teacher ADD COLUMN {col_name} {col_type}")
                        added_columns.append(col_name)
                        result += f"<p>✅ Added column: {col_name}</p>"
                    except Exception as e:
                        result += f"<p>❌ Failed to add {col_name}: {e}</p>"

            # Update existing teachers with default enhanced values
            cursor.execute("SELECT id, username FROM teacher")
            teachers = cursor.fetchall()

            result += f"<p><strong>Updating {len(teachers)} teachers with enhanced data...</strong></p>"

            for teacher_id, username in teachers:
                updates = []

                # Set full_name to username if null
                if 'full_name' in added_columns:
                    updates.append(f"full_name = '{username}'")

                # Set employee_id if null
                if 'employee_id' in added_columns:
                    updates.append(f"employee_id = 'EMP{teacher_id:03d}'")

                # Set is_active to true if null
                if 'is_active' in added_columns:
                    updates.append("is_active = 1")

                if updates:
                    update_sql = f"UPDATE teacher SET {', '.join(updates)} WHERE id = ?"
                    cursor.execute(update_sql, (teacher_id,))
                    result += f"<p>✅ Updated {username}</p>"

            # Check if school_configuration table exists, create if missing
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='school_configuration'")
            if not cursor.fetchone():
                result += f"<p>⚠️ school_configuration table missing - creating it...</p>"
                cursor.execute("""
                    CREATE TABLE school_configuration (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        school_name TEXT NOT NULL DEFAULT 'Hillview School',
                        school_motto TEXT DEFAULT 'Excellence in Education',
                        school_address TEXT,
                        school_phone TEXT,
                        school_email TEXT,
                        school_website TEXT,
                        current_academic_year TEXT DEFAULT '2024',
                        current_term TEXT DEFAULT 'Term 1',
                        use_streams BOOLEAN DEFAULT 1,
                        grading_system TEXT DEFAULT 'percentage',
                        show_position BOOLEAN DEFAULT 1,
                        show_class_average BOOLEAN DEFAULT 1,
                        show_subject_teacher BOOLEAN DEFAULT 1,
                        logo_filename TEXT,
                        primary_color TEXT DEFAULT '#1f7d53',
                        secondary_color TEXT DEFAULT '#18230f',
                        headteacher_name TEXT DEFAULT 'Head Teacher',
                        deputy_headteacher_name TEXT DEFAULT 'Deputy Head Teacher',
                        max_raw_marks_default INTEGER DEFAULT 100,
                        pass_mark_percentage INTEGER DEFAULT 50,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        headteacher_id INTEGER,
                        deputy_headteacher_id INTEGER,
                        FOREIGN KEY (headteacher_id) REFERENCES teacher (id),
                        FOREIGN KEY (deputy_headteacher_id) REFERENCES teacher (id)
                    )
                """)

                # Insert default configuration
                cursor.execute("""
                    INSERT INTO school_configuration (
                        school_name, school_motto, current_academic_year, current_term,
                        headteacher_name, deputy_headteacher_name
                    ) VALUES (
                        'Hillview School', 'Excellence in Education', '2024', 'Term 1',
                        'Head Teacher', 'Deputy Head Teacher'
                    )
                """)
                result += f"<p>✅ Created school_configuration table with default data</p>"
            else:
                # Table exists, check and add enhanced columns
                cursor.execute("PRAGMA table_info(school_configuration)")
                config_columns = [col[1] for col in cursor.fetchall()]

                if 'headteacher_id' not in config_columns:
                    cursor.execute("ALTER TABLE school_configuration ADD COLUMN headteacher_id INTEGER")
                    result += f"<p>✅ Added headteacher_id to school_configuration</p>"

                if 'deputy_headteacher_id' not in config_columns:
                    cursor.execute("ALTER TABLE school_configuration ADD COLUMN deputy_headteacher_id INTEGER")
                    result += f"<p>✅ Added deputy_headteacher_id to school_configuration</p>"

            conn.commit()

            # Verify final structure
            cursor.execute("PRAGMA table_info(teacher)")
            final_columns = [col[1] for col in cursor.fetchall()]
            result += f"<p><strong>Final teacher columns:</strong> {', '.join(final_columns)}</p>"

            # Test query
            cursor.execute("SELECT id, username, full_name, employee_id FROM teacher LIMIT 3")
            test_teachers = cursor.fetchall()
            result += f"<p><strong>Sample enhanced teachers:</strong></p><ul>"
            for teacher in test_teachers:
                result += f"<li>{teacher[1]} - Full Name: {teacher[2]}, Employee ID: {teacher[3]}</li>"
            result += "</ul>"

            conn.close()

            result += f"<h3 style='color: green;'>✅ Database Enhancement Complete!</h3>"
            result += f"<p><strong>Your original data is preserved with enhanced features added.</strong></p>"
            result += f"<p><a href='/debug/check_users'>Check users now</a></p>"
            result += f"<p><strong>Please restart the Flask app to use the enhanced database.</strong></p>"

            return result

        except Exception as e:
            return f"❌ Error enhancing database: {e}"

    @app.route('/debug/complete_database_setup')
    def debug_complete_database_setup():
        """Add ALL missing tables to the restored database."""
        import sqlite3
        import os
        from datetime import datetime

        result = "<h2>🔧 Complete Database Setup</h2>"
        result += "<p>Adding all missing tables while preserving your original data...</p>"

        try:
            # Get the current database path
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            current_db_path = current_db_uri.replace('sqlite:///', '')

            result += f"<p><strong>Database:</strong> {current_db_path}</p>"

            # Create backup before setup
            backup_path = f"{current_db_path}.backup_before_complete_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(current_db_path, backup_path)
            result += f"<p>✅ Backup created: {backup_path}</p>"

            conn = sqlite3.connect(current_db_path)
            cursor = conn.cursor()

            # Check what tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [table[0] for table in cursor.fetchall()]
            result += f"<p><strong>Existing tables:</strong> {', '.join(existing_tables)}</p>"

            # Create grade table if missing
            if 'grade' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE grade (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        education_level TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Insert default grades
                grades_data = [
                    ('Grade 1', 'lower_primary'),
                    ('Grade 2', 'lower_primary'),
                    ('Grade 3', 'lower_primary'),
                    ('Grade 4', 'upper_primary'),
                    ('Grade 5', 'upper_primary'),
                    ('Grade 6', 'upper_primary'),
                    ('Grade 7', 'junior_secondary'),
                    ('Grade 8', 'junior_secondary'),
                    ('Grade 9', 'junior_secondary')
                ]

                for grade_name, education_level in grades_data:
                    cursor.execute("INSERT INTO grade (name, education_level) VALUES (?, ?)",
                                 (grade_name, education_level))

                result += f"<p>✅ Created grade table with {len(grades_data)} grades</p>"

            # Create stream table if missing
            if 'stream' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE stream (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        grade_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (grade_id) REFERENCES grade (id)
                    )
                """)

                # Insert default streams for each grade
                cursor.execute("SELECT id, name FROM grade")
                grade_records = cursor.fetchall()

                stream_count = 0
                for grade_id, grade_name in grade_records:
                    cursor.execute("INSERT INTO stream (name, grade_id) VALUES (?, ?)", ('A', grade_id))
                    cursor.execute("INSERT INTO stream (name, grade_id) VALUES (?, ?)", ('B', grade_id))
                    stream_count += 2

                result += f"<p>✅ Created stream table with {stream_count} streams</p>"

            # Create term table if missing
            if 'term' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE term (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        academic_year TEXT,
                        start_date DATE,
                        end_date DATE,
                        is_current BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Insert default terms
                cursor.execute("INSERT INTO term (name, academic_year, is_current) VALUES (?, ?, ?)",
                              ('Term 1', '2024', 1))
                cursor.execute("INSERT INTO term (name, academic_year, is_current) VALUES (?, ?, ?)",
                              ('Term 2', '2024', 0))
                cursor.execute("INSERT INTO term (name, academic_year, is_current) VALUES (?, ?, ?)",
                              ('Term 3', '2024', 0))

                result += f"<p>✅ Created term table with 3 terms</p>"

            # Create assessment_type table if missing
            if 'assessment_type' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE assessment_type (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        weight REAL DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Insert default assessment types
                cursor.execute("INSERT INTO assessment_type (name, description) VALUES (?, ?)",
                              ('End of Term Exam', 'Final examination for the term'))
                cursor.execute("INSERT INTO assessment_type (name, description) VALUES (?, ?)",
                              ('Mid Term Test', 'Mid-term assessment'))
                cursor.execute("INSERT INTO assessment_type (name, description) VALUES (?, ?)",
                              ('Continuous Assessment', 'Ongoing classroom assessment'))

                result += f"<p>✅ Created assessment_type table with 3 types</p>"

            # Create student table if missing
            if 'student' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE student (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        admission_number TEXT UNIQUE,
                        grade_id INTEGER NOT NULL,
                        stream_id INTEGER NOT NULL,
                        date_of_birth DATE,
                        gender TEXT,
                        parent_contact TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (grade_id) REFERENCES grade (id),
                        FOREIGN KEY (stream_id) REFERENCES stream (id)
                    )
                """)
                result += f"<p>✅ Created student table</p>"

            # Create marks table if missing
            if 'marks' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE marks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        subject_id INTEGER NOT NULL,
                        term_id INTEGER NOT NULL,
                        assessment_type_id INTEGER NOT NULL,
                        raw_mark REAL,
                        percentage REAL,
                        grade TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES student (id),
                        FOREIGN KEY (subject_id) REFERENCES subject (id),
                        FOREIGN KEY (term_id) REFERENCES term (id),
                        FOREIGN KEY (assessment_type_id) REFERENCES assessment_type (id)
                    )
                """)
                result += f"<p>✅ Created marks table</p>"

            # Create teacher_subjects table if missing
            if 'teacher_subjects' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE teacher_subjects (
                        teacher_id INTEGER NOT NULL,
                        subject_id INTEGER NOT NULL,
                        PRIMARY KEY (teacher_id, subject_id),
                        FOREIGN KEY (teacher_id) REFERENCES teacher (id),
                        FOREIGN KEY (subject_id) REFERENCES subject (id)
                    )
                """)
                result += f"<p>✅ Created teacher_subjects table</p>"

            # Create teacher_subject_assignment table if missing
            if 'teacher_subject_assignment' not in existing_tables:
                cursor.execute("""
                    CREATE TABLE teacher_subject_assignment (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        teacher_id INTEGER NOT NULL,
                        subject_id INTEGER NOT NULL,
                        grade_id INTEGER NOT NULL,
                        stream_id INTEGER NOT NULL,
                        is_class_teacher BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (teacher_id) REFERENCES teacher (id),
                        FOREIGN KEY (subject_id) REFERENCES subject (id),
                        FOREIGN KEY (grade_id) REFERENCES grade (id),
                        FOREIGN KEY (stream_id) REFERENCES stream (id)
                    )
                """)
                result += f"<p>✅ Created teacher_subject_assignment table</p>"

            conn.commit()

            # Final verification
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            final_tables = [table[0] for table in cursor.fetchall()]
            result += f"<p><strong>Final tables ({len(final_tables)}):</strong> {', '.join(sorted(final_tables))}</p>"

            # Check data counts
            for table in ['grade', 'stream', 'term', 'assessment_type']:
                if table in final_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    result += f"<p>  - {table}: {count} records</p>"

            conn.close()

            result += f"<h3 style='color: green;'>✅ Complete Database Setup Finished!</h3>"
            result += f"<p><strong>Your original data is preserved with all required tables added.</strong></p>"
            result += f"<p><a href='/debug/check_users'>Check users</a> | <a href='/debug/check_subjects'>Check subjects</a></p>"
            result += f"<p><strong>Please restart the Flask app to use the complete database.</strong></p>"

            return result

        except Exception as e:
            return f"❌ Error in complete database setup: {e}"

    @app.route('/debug/test_school_config')
    def debug_test_school_config():
        """Test the school configuration integration."""
        try:
            from .services.school_config_service import SchoolConfigService

            result = "<h2>🧪 School Configuration Integration Test</h2>"

            # Test get_school_name
            school_name = SchoolConfigService.get_school_name()
            result += f"<h3>📋 get_school_name():</h3>"
            result += f"<p><strong>{school_name}</strong></p>"

            # Test get_school_info_dict
            school_info = SchoolConfigService.get_school_info_dict()
            result += f"<h3>📋 get_school_info_dict():</h3>"
            result += "<ul>"
            for key, value in school_info.items():
                result += f"<li><strong>{key}:</strong> {value}</li>"
            result += "</ul>"

            # Check if using setup data
            from .models.school_setup import SchoolSetup
            setup = SchoolSetup.query.first()

            if setup and setup.setup_completed:
                result += f"<h3>✅ School Setup Status:</h3>"
                result += f"<p>Setup completed: <strong>Yes</strong></p>"
                result += f"<p>Setup school name: <strong>{setup.school_name}</strong></p>"
                result += f"<p>Service school name: <strong>{school_name}</strong></p>"

                if school_name.lower() == setup.school_name.lower():
                    result += f"<p style='color: green; font-size: 18px;'>🎯 <strong>SUCCESS!</strong> Service is using setup data!</p>"
                else:
                    result += f"<p style='color: red; font-size: 18px;'>❌ <strong>ISSUE!</strong> Service is not using setup data!</p>"
            else:
                result += f"<h3>❌ School Setup Status:</h3>"
                result += f"<p>Setup completed: <strong>No</strong></p>"

            return result

        except Exception as e:
            return f"❌ Error testing school config: {e}"

    @app.route('/debug/check_new_structure_databases')
    def debug_check_new_structure_databases():
        """Check for databases specifically in the new_structure directory."""
        import os
        import glob
        import sqlite3

        result = "<h2>🔍 Checking new_structure Directory for Databases</h2>"

        try:
            # Get current working directory
            current_dir = os.getcwd()
            result += f"<p><strong>Current working directory:</strong> {current_dir}</p>"

            # Check Flask app database configuration
            from .config import config
            conf = config['development']()
            db_uri = conf.SQLALCHEMY_DATABASE_URI
            configured_db_path = db_uri.replace('sqlite:///', '')
            result += f"<p><strong>Flask configured database:</strong> {configured_db_path}</p>"
            result += f"<p><strong>Configured DB exists:</strong> {os.path.exists(configured_db_path)}</p>"

            # Look for all .db files in current directory (new_structure)
            db_files_here = glob.glob("*.db")
            result += f"<h3>📁 Database files in new_structure directory ({len(db_files_here)}):</h3>"

            if not db_files_here:
                result += "<p>❌ No .db files found in new_structure directory</p>"
            else:
                for db_file in db_files_here:
                    result += f"<h4>🗃️ {db_file}</h4>"

                    try:
                        # Get file info
                        full_path = os.path.abspath(db_file)
                        size = os.path.getsize(db_file)
                        result += f"<p><strong>Full path:</strong> {full_path}</p>"
                        result += f"<p><strong>Size:</strong> {size:,} bytes</p>"

                        # Check if this is the configured database
                        if os.path.abspath(db_file) == os.path.abspath(configured_db_path):
                            result += f"<p style='color: green;'>✅ <strong>This is the Flask configured database!</strong></p>"

                        # Check users in this database
                        conn = sqlite3.connect(db_file)
                        cursor = conn.cursor()

                        # Check if teacher table exists
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher'")
                        if cursor.fetchone():
                            cursor.execute("SELECT id, username, password, role FROM teacher")
                            users = cursor.fetchall()

                            result += f"<p><strong>Users ({len(users)}):</strong></p><ul>"

                            telvo_found = False
                            kevin_found = False
                            classteacher1_found = False

                            for user in users:
                                username = user[1].lower()
                                result += f"<li><strong>{user[1]}</strong> (password: {user[2]}, role: {user[3]})</li>"

                                if 'telvo' in username:
                                    telvo_found = True
                                if 'kevin' in username:
                                    kevin_found = True
                                if 'classteacher1' in username:
                                    classteacher1_found = True

                            result += "</ul>"

                            matches = sum([telvo_found, kevin_found, classteacher1_found])
                            if matches >= 2:
                                result += f"<p style='color: green; font-size: 16px;'>🎯 <strong>CONTAINS YOUR ORIGINAL USERS!</strong> ({matches}/3 found)</p>"
                        else:
                            result += "<p>❌ No teacher table found</p>"

                        # Check what tables exist
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = [table[0] for table in cursor.fetchall()]
                        result += f"<p><strong>Tables ({len(tables)}):</strong> {', '.join(sorted(tables))}</p>"

                        # Check subjects if table exists
                        if 'subject' in tables:
                            cursor.execute("SELECT COUNT(*) FROM subject")
                            subject_count = cursor.fetchone()[0]
                            result += f"<p><strong>Subjects:</strong> {subject_count} found</p>"

                            if subject_count > 0:
                                cursor.execute("SELECT name FROM subject LIMIT 5")
                                sample_subjects = [s[0] for s in cursor.fetchall()]
                                result += f"<p><strong>Sample subjects:</strong> {', '.join(sample_subjects)}</p>"

                        conn.close()

                    except Exception as e:
                        result += f"<p>❌ Error checking {db_file}: {e}</p>"

                    result += "<hr>"

            # Also check parent directory
            parent_db_files = glob.glob("../*.db")
            result += f"<h3>📁 Database files in parent directory ({len(parent_db_files)}):</h3>"

            for db_file in parent_db_files:
                db_name = os.path.basename(db_file)
                result += f"<p>📄 {db_name}</p>"

            # Summary
            result += f"<h3>📋 Summary:</h3>"
            result += f"<p>• Flask is configured to use: <code>{configured_db_path}</code></p>"
            result += f"<p>• Database files in new_structure: {len(db_files_here)}</p>"
            result += f"<p>• Database files in parent: {len(parent_db_files)}</p>"

            return result

        except Exception as e:
            return f"❌ Error checking new_structure databases: {e}"

    @app.route('/debug/fix_grade_table')
    def debug_fix_grade_table():
        """Specifically fix the grade table issue."""
        import sqlite3
        import os
        from datetime import datetime

        result = "<h2>🔧 Fixing Grade Table</h2>"

        try:
            # Get the current database path
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            current_db_path = current_db_uri.replace('sqlite:///', '')

            result += f"<p><strong>Database:</strong> {current_db_path}</p>"

            # Create backup
            backup_path = f"{current_db_path}.backup_grade_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(current_db_path, backup_path)
            result += f"<p>✅ Backup created: {backup_path}</p>"

            conn = sqlite3.connect(current_db_path)
            cursor = conn.cursor()

            # Check if grade table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='grade'")
            grade_table_exists = cursor.fetchone()

            if grade_table_exists:
                result += f"<p>📋 Grade table exists - checking structure...</p>"

                # Check current structure
                cursor.execute("PRAGMA table_info(grade)")
                columns = cursor.fetchall()
                result += f"<p><strong>Current columns:</strong></p><ul>"
                for col in columns:
                    result += f"<li>{col[1]} ({col[2]})</li>"
                result += "</ul>"

                # Check if 'name' column exists
                column_names = [col[1] for col in columns]
                if 'name' not in column_names:
                    result += f"<p>❌ Missing 'name' column - adding it...</p>"

                    # Add name column
                    cursor.execute("ALTER TABLE grade ADD COLUMN name TEXT")

                    # If there's a 'level' column, copy its data to 'name'
                    if 'level' in column_names:
                        cursor.execute("UPDATE grade SET name = level")
                        result += f"<p>✅ Copied data from 'level' to 'name' column</p>"

                if 'education_level' not in column_names:
                    result += f"<p>❌ Missing 'education_level' column - adding it...</p>"
                    cursor.execute("ALTER TABLE grade ADD COLUMN education_level TEXT")

                    # Set default education levels based on grade names
                    cursor.execute("""
                        UPDATE grade SET education_level =
                        CASE
                            WHEN name IN ('Grade 1', 'Grade 2', 'Grade 3') THEN 'lower_primary'
                            WHEN name IN ('Grade 4', 'Grade 5', 'Grade 6') THEN 'upper_primary'
                            WHEN name IN ('Grade 7', 'Grade 8', 'Grade 9') THEN 'junior_secondary'
                            ELSE 'lower_primary'
                        END
                    """)
                    result += f"<p>✅ Added education_level column with default values</p>"

            else:
                result += f"<p>❌ Grade table doesn't exist - creating it...</p>"

                # Create grade table
                cursor.execute("""
                    CREATE TABLE grade (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        education_level TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Insert default grades
                grades_data = [
                    ('Grade 1', 'lower_primary'),
                    ('Grade 2', 'lower_primary'),
                    ('Grade 3', 'lower_primary'),
                    ('Grade 4', 'upper_primary'),
                    ('Grade 5', 'upper_primary'),
                    ('Grade 6', 'upper_primary'),
                    ('Grade 7', 'junior_secondary'),
                    ('Grade 8', 'junior_secondary'),
                    ('Grade 9', 'junior_secondary')
                ]

                for grade_name, education_level in grades_data:
                    cursor.execute("INSERT INTO grade (name, education_level) VALUES (?, ?)",
                                 (grade_name, education_level))

                result += f"<p>✅ Created grade table with {len(grades_data)} grades</p>"

            # Also create stream table if missing
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stream'")
            if not cursor.fetchone():
                result += f"<p>⚠️ Stream table missing - creating it...</p>"

                cursor.execute("""
                    CREATE TABLE stream (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        grade_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (grade_id) REFERENCES grade (id)
                    )
                """)

                # Insert default streams for each grade
                cursor.execute("SELECT id, name FROM grade")
                grade_records = cursor.fetchall()

                stream_count = 0
                for grade_id, grade_name in grade_records:
                    cursor.execute("INSERT INTO stream (name, grade_id) VALUES (?, ?)", ('A', grade_id))
                    cursor.execute("INSERT INTO stream (name, grade_id) VALUES (?, ?)", ('B', grade_id))
                    stream_count += 2

                result += f"<p>✅ Created stream table with {stream_count} streams</p>"

            conn.commit()

            # Verify the fix
            cursor.execute("PRAGMA table_info(grade)")
            final_columns = [col[1] for col in cursor.fetchall()]
            result += f"<p><strong>Final grade table columns:</strong> {', '.join(final_columns)}</p>"

            # Test the query that was failing
            cursor.execute("SELECT id, name, education_level FROM grade LIMIT 3")
            test_grades = cursor.fetchall()
            result += f"<p><strong>Test query results:</strong></p><ul>"
            for grade in test_grades:
                result += f"<li>ID: {grade[0]}, Name: {grade[1]}, Level: {grade[2]}</li>"
            result += "</ul>"

            conn.close()

            result += f"<h3 style='color: green;'>✅ Grade Table Fix Complete!</h3>"
            result += f"<p><strong>The grade table now has the correct structure.</strong></p>"
            result += f"<p><a href='/debug/check_users'>Check users</a> | <a href='/classteacher_login'>Try login</a></p>"
            result += f"<p><strong>Please restart the Flask app to use the fixed database.</strong></p>"

            return result

        except Exception as e:
            return f"❌ Error fixing grade table: {e}"

    @app.route('/debug/cleanup_databases')
    def debug_cleanup_databases():
        """Show which database files can be safely removed."""
        import os
        import glob
        from datetime import datetime

        result = "<h2>🧹 Database Cleanup Guide</h2>"
        result += "<p>Here's what database files exist and which ones you can safely remove:</p>"

        try:
            # Get the current active database
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            active_db_path = os.path.abspath(current_db_uri.replace('sqlite:///', ''))

            result += f"<h3>🎯 ACTIVE DATABASE (DO NOT DELETE):</h3>"
            result += f"<p style='color: green; font-weight: bold;'>{active_db_path}</p>"
            result += f"<p>This is the database your Flask app is currently using.</p>"

            # Find all database files
            search_patterns = [
                "*.db",
                "../*.db",
                "*.db.backup*",
                "../*.db.backup*"
            ]

            all_db_files = set()
            for pattern in search_patterns:
                files = glob.glob(pattern)
                for file in files:
                    all_db_files.add(os.path.abspath(file))

            # Remove the active database from the list
            cleanup_files = all_db_files - {active_db_path}

            if cleanup_files:
                result += f"<h3>🗑️ FILES SAFE TO DELETE ({len(cleanup_files)} files):</h3>"
                result += "<p>These are backup files and unused databases that can be safely removed:</p>"
                result += "<ul>"

                # Group files by type
                backups = []
                other_dbs = []

                for file_path in sorted(cleanup_files):
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

                    if 'backup' in file_name:
                        backups.append((file_path, file_name, file_size))
                    else:
                        other_dbs.append((file_path, file_name, file_size))

                # Show backup files
                if backups:
                    result += "<li><strong>📦 Backup Files:</strong><ul>"
                    for file_path, file_name, file_size in backups:
                        result += f"<li>{file_name} ({file_size:,} bytes)<br><small>{file_path}</small></li>"
                    result += "</ul></li>"

                # Show other database files
                if other_dbs:
                    result += "<li><strong>🗃️ Other Database Files:</strong><ul>"
                    for file_path, file_name, file_size in other_dbs:
                        result += f"<li>{file_name} ({file_size:,} bytes)<br><small>{file_path}</small></li>"
                    result += "</ul></li>"

                result += "</ul>"

                # Calculate total space that can be freed
                total_size = sum(file_size for _, _, file_size in backups + other_dbs)
                result += f"<p><strong>💾 Total space that can be freed: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)</strong></p>"

                # Provide cleanup commands
                result += f"<h3>🔧 How to Clean Up:</h3>"
                result += f"<p><strong>Option 1: Delete backup files only (recommended):</strong></p>"
                result += f"<pre>cd {os.path.dirname(active_db_path)}\n"
                for file_path, file_name, _ in backups:
                    if 'backup' in file_name:
                        result += f"del \"{file_name}\"\n"
                result += "</pre>"

                result += f"<p><strong>Option 2: Delete all unused databases:</strong></p>"
                result += f"<pre>cd {os.path.dirname(active_db_path)}\n"
                for file_path, file_name, _ in backups + other_dbs:
                    result += f"del \"{file_name}\"\n"
                result += "</pre>"

                result += f"<p><strong>⚠️ Safety Note:</strong> Keep at least one recent backup in case you need to restore.</p>"

            else:
                result += f"<h3>✅ NO CLEANUP NEEDED</h3>"
                result += f"<p>Only the active database exists. No unnecessary files found.</p>"

            # Show summary
            result += f"<h3>📋 Summary:</h3>"
            result += f"<ul>"
            result += f"<li><strong>Active database:</strong> {os.path.basename(active_db_path)}</li>"
            result += f"<li><strong>Backup files:</strong> {len(backups)}</li>"
            result += f"<li><strong>Other databases:</strong> {len(other_dbs)}</li>"
            result += f"<li><strong>Total files found:</strong> {len(all_db_files)}</li>"
            result += f"</ul>"

            return result

        except Exception as e:
            return f"❌ Error analyzing databases: {e}"

    @app.route('/debug/perform_cleanup')
    def debug_perform_cleanup():
        """Automatically clean up unnecessary database files."""
        import os
        import glob
        from datetime import datetime

        result = "<h2>🧹 Performing Database Cleanup</h2>"

        try:
            # Get the current active database
            from .config import config
            conf = config['development']()
            current_db_uri = conf.SQLALCHEMY_DATABASE_URI
            active_db_path = os.path.abspath(current_db_uri.replace('sqlite:///', ''))

            result += f"<p><strong>🎯 Active database (keeping):</strong> {os.path.basename(active_db_path)}</p>"

            # Find all database files
            search_patterns = [
                "*.db",
                "../*.db",
                "*.db.backup*",
                "../*.db.backup*"
            ]

            all_db_files = set()
            for pattern in search_patterns:
                files = glob.glob(pattern)
                for file in files:
                    all_db_files.add(os.path.abspath(file))

            # Remove the active database from cleanup list
            cleanup_files = all_db_files - {active_db_path}

            if not cleanup_files:
                result += "<p>✅ No files need cleanup. Your system is already clean!</p>"
                return result

            # Categorize files
            backup_files = []
            old_databases = []

            for file_path in cleanup_files:
                file_name = os.path.basename(file_path)
                if 'backup' in file_name:
                    backup_files.append(file_path)
                else:
                    old_databases.append(file_path)

            # Keep the most recent backup as safety
            if backup_files:
                # Sort by modification time, keep the newest
                backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                keep_backup = backup_files[0] if backup_files else None
                backup_files_to_delete = backup_files[1:] if len(backup_files) > 1 else []
            else:
                keep_backup = None
                backup_files_to_delete = []

            # Perform cleanup
            deleted_files = []
            total_space_freed = 0

            result += "<h3>🗑️ Cleanup Results:</h3>"

            # Delete old backup files (keep the newest one)
            if backup_files_to_delete:
                result += f"<p><strong>📦 Deleting old backup files:</strong></p><ul>"
                for file_path in backup_files_to_delete:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_files.append(os.path.basename(file_path))
                        total_space_freed += file_size
                        result += f"<li>✅ Deleted: {os.path.basename(file_path)} ({file_size:,} bytes)</li>"
                    except Exception as e:
                        result += f"<li>❌ Failed to delete {os.path.basename(file_path)}: {e}</li>"
                result += "</ul>"

            # Keep the newest backup
            if keep_backup:
                result += f"<p><strong>📦 Keeping newest backup:</strong> {os.path.basename(keep_backup)}</p>"

            # Handle other database files (be more cautious)
            if old_databases:
                result += f"<p><strong>🗃️ Other database files found:</strong></p><ul>"
                for file_path in old_databases:
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)

                    # Only delete if it's clearly a duplicate or test database
                    if file_name in ['kirima_primary.db'] and file_path != active_db_path:
                        # This is likely a duplicate in a different directory
                        try:
                            os.remove(file_path)
                            deleted_files.append(file_name)
                            total_space_freed += file_size
                            result += f"<li>✅ Deleted duplicate: {file_name} ({file_size:,} bytes)</li>"
                        except Exception as e:
                            result += f"<li>❌ Failed to delete {file_name}: {e}</li>"
                    else:
                        result += f"<li>⚠️ Kept (uncertain): {file_name} ({file_size:,} bytes)<br><small>{file_path}</small></li>"
                result += "</ul>"

            # Summary
            result += f"<h3>📋 Cleanup Summary:</h3>"
            result += f"<ul>"
            result += f"<li><strong>Files deleted:</strong> {len(deleted_files)}</li>"
            result += f"<li><strong>Space freed:</strong> {total_space_freed:,} bytes ({total_space_freed/1024/1024:.1f} MB)</li>"
            result += f"<li><strong>Active database:</strong> Preserved ✅</li>"
            result += f"<li><strong>Safety backup:</strong> {'Kept' if keep_backup else 'None needed'}</li>"
            result += f"</ul>"

            if deleted_files:
                result += f"<p><strong>🎉 Cleanup completed successfully!</strong></p>"
                result += f"<p>Deleted files: {', '.join(deleted_files)}</p>"
            else:
                result += f"<p><strong>ℹ️ No files were deleted.</strong> Your system was already clean or files were kept for safety.</p>"

            result += f"<p><a href='/debug/cleanup_databases'>View cleanup guide again</a></p>"

            return result

        except Exception as e:
            return f"❌ Error performing cleanup: {e}"

    @app.route('/debug/initialize_database')
    def debug_initialize_database():
        """Debug route to manually initialize the database."""
        try:
            from .utils.database_init import initialize_database_completely, check_database_integrity

            # Check current status
            current_status = check_database_integrity()

            result = "<h2>🔄 Database Initialization</h2>"
            result += f"<h3>📊 Current Status:</h3>"
            result += f"<ul>"
            result += f"<li>Tables Exist: {'✅' if current_status['tables_exist'] else '❌'}</li>"
            result += f"<li>Has Data: {'✅' if current_status['has_data'] else '❌'}</li>"
            result += f"<li>Teachers: {current_status.get('teacher_count', 0)}</li>"
            result += f"<li>Subjects: {current_status.get('subject_count', 0)}</li>"
            result += f"<li>Grades: {current_status.get('grade_count', 0)}</li>"
            result += f"<li>Streams: {current_status.get('stream_count', 0)}</li>"
            result += f"<li>Status: {current_status['status']}</li>"
            result += f"</ul>"

            if current_status['status'] != 'healthy':
                result += f"<h3>🔧 Initializing Database...</h3>"

                init_result = initialize_database_completely()

                if init_result['success']:
                    result += f"<p style='color: green;'>✅ <strong>Database initialized successfully!</strong></p>"
                    result += f"<ul>"
                    result += f"<li>Teachers: {init_result['status']['teacher_count']}</li>"
                    result += f"<li>Subjects: {init_result['status']['subject_count']}</li>"
                    result += f"<li>Grades: {init_result['status']['grade_count']}</li>"
                    result += f"<li>Streams: {init_result['status']['stream_count']}</li>"
                    result += f"</ul>"
                    result += f"<p><strong>Default Users Created:</strong></p>"
                    result += f"<ul>"
                    result += f"<li><strong>headteacher</strong> / admin123 (Headteacher)</li>"
                    result += f"<li><strong>classteacher1</strong> / class123 (Class Teacher)</li>"
                    result += f"<li><strong>kevin</strong> / kev123 (Class Teacher)</li>"
                    result += f"<li><strong>telvo</strong> / telvo123 (Subject Teacher)</li>"
                    result += f"</ul>"
                    result += f"<p><a href='/'>🏠 Go to Login Page</a></p>"
                else:
                    result += f"<p style='color: red;'>❌ <strong>Database initialization failed:</strong> {init_result.get('error', 'Unknown error')}</p>"
            else:
                result += f"<p style='color: green;'>✅ <strong>Database is already healthy!</strong></p>"
                result += f"<p><a href='/debug/check_users'>👥 Check Users</a></p>"
                result += f"<p><a href='/'>🏠 Go to Login Page</a></p>"

            return result

        except Exception as e:
            return f"❌ Error during database initialization: {str(e)}"

    @app.route('/debug/repair_database')
    def debug_repair_database():
        """Debug route to repair the database."""
        try:
            from .utils.database_init import repair_database

            result = "<h2>🔧 Database Repair</h2>"

            repair_result = repair_database()

            if repair_result['success']:
                result += f"<p style='color: green;'>✅ <strong>Database repaired successfully!</strong></p>"
                result += f"<h3>📊 Before Repair:</h3><ul>"
                before = repair_result['before']
                result += f"<li>Tables Exist: {'✅' if before['tables_exist'] else '❌'}</li>"
                result += f"<li>Has Data: {'✅' if before['has_data'] else '❌'}</li>"
                result += f"<li>Status: {before['status']}</li>"
                result += f"</ul>"

                result += f"<h3>📊 After Repair:</h3><ul>"
                after = repair_result['after']
                result += f"<li>Tables Exist: {'✅' if after['tables_exist'] else '❌'}</li>"
                result += f"<li>Has Data: {'✅' if after['has_data'] else '❌'}</li>"
                result += f"<li>Teachers: {after.get('teacher_count', 0)}</li>"
                result += f"<li>Subjects: {after.get('subject_count', 0)}</li>"
                result += f"<li>Status: {after['status']}</li>"
                result += f"</ul>"

                result += f"<p><a href='/'>🏠 Go to Login Page</a></p>"
            else:
                result += f"<p style='color: red;'>❌ <strong>Database repair failed:</strong> {repair_result.get('error', 'Unknown error')}</p>"

            return result

        except Exception as e:
            return f"❌ Error during database repair: {str(e)}"

    @app.route('/debug/test_login')
    def debug_test_login():
        """Debug route to test login functionality."""
        try:
            from .services.auth_service import authenticate_teacher
            from .models.user import Teacher

            result = "<h2>🔍 Login Test</h2>"

            # Test database connection
            try:
                teacher_count = Teacher.query.count()
                result += f"<p>✅ Database connection: OK ({teacher_count} teachers found)</p>"
            except Exception as e:
                result += f"<p>❌ Database connection: FAILED - {e}</p>"
                return result

            # Test authentication for each default user
            test_users = [
                ('headteacher', 'admin123', 'headteacher'),
                ('classteacher1', 'class123', 'classteacher'),
                ('kevin', 'kev123', 'classteacher'),
                ('telvo', 'telvo123', 'teacher')
            ]

            result += "<h3>🧪 Authentication Tests:</h3><ul>"

            for username, password, role in test_users:
                try:
                    teacher = authenticate_teacher(username, password, role)
                    if teacher:
                        result += f"<li>✅ <strong>{username}</strong> / {password} ({role}) - SUCCESS</li>"
                    else:
                        result += f"<li>❌ <strong>{username}</strong> / {password} ({role}) - FAILED</li>"
                except Exception as e:
                    result += f"<li>❌ <strong>{username}</strong> / {password} ({role}) - ERROR: {e}</li>"

            result += "</ul>"

            # Test session functionality
            result += "<h3>🔧 Session Test:</h3>"
            try:
                from flask import session
                session['test_key'] = 'test_value'
                if session.get('test_key') == 'test_value':
                    result += "<p>✅ Session functionality: OK</p>"
                else:
                    result += "<p>❌ Session functionality: FAILED</p>"
            except Exception as e:
                result += f"<p>❌ Session functionality: ERROR - {e}</p>"

            # Test URL generation
            result += "<h3>🔗 URL Generation Test:</h3>"
            try:
                from flask import url_for
                admin_url = url_for('admin.dashboard')
                classteacher_url = url_for('classteacher.dashboard')
                result += f"<p>✅ Admin dashboard URL: {admin_url}</p>"
                result += f"<p>✅ Classteacher dashboard URL: {classteacher_url}</p>"
            except Exception as e:
                result += f"<p>❌ URL generation: ERROR - {e}</p>"

            result += f"<p><a href='/'>🏠 Go to Login Page</a></p>"
            return result

        except Exception as e:
            return f"❌ Error during login test: {str(e)}"

    # Log application startup
    app.logger.info("Application initialized")

    return app