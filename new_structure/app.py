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
import config

def create_simple_app():
    """Create a simplified Flask app for deployment."""
    app = Flask(__name__)
    
    # Load configuration
    config_name = 'production'
    app.config.from_object(config.config[config_name])
    
    # Initialize database
    from extensions import db
    db.init_app(app)
    
    # Simple route for testing
    @app.route('/')
    def index():
        return "Hillview School Management System - Loading..."
    
    @app.route('/health')
    def health():
        return {"status": "ok", "message": "Application is running"}
    
    return app

# Create the application
app = create_simple_app()

if __name__ == '__main__':
    # This won't be called in production, but useful for local testing
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)