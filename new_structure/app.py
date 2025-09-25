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

def create_simple_app():
    """Create a simplified Flask app for deployment."""
    app = Flask(__name__)
    
    # Simple configuration for deployment
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-deployment')
    app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///fallback.db')
    
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