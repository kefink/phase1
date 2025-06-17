#!/usr/bin/env python3
"""
Simple run script for the Hillview School Management System.
This script creates and runs the Flask application without relative imports.
"""

import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set up Flask app
from flask import Flask
from extensions import db, csrf
from config import config
from logging_config import setup_logging
from middleware import MarkSanitizerMiddleware

def create_simple_app(config_name='development'):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Set up logging
    setup_logging(app)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from views import blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
        # Exempt parent portal from CSRF protection
        if hasattr(blueprint, 'name') and 'parent' in blueprint.name:
            csrf.exempt(blueprint)

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

    # Register error handlers
    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"Internal Server Error: {str(e)}")
        return "Internal Server Error", 500

    return app

if __name__ == '__main__':
    try:
        print("🔄 Starting Hillview School Management System...")
        print("📍 Current directory:", os.getcwd())
        
        # Create the Flask application
        app = create_simple_app('development')
        print("✅ Successfully created Flask app")
        
        # Test database connection
        with app.app_context():
            from models.parent import Parent
            parent_count = Parent.query.count()
            print(f"✅ Database connection successful - {parent_count} parents found")
        
        print("🚀 Starting server on http://localhost:5000")
        print("📋 Parent Management: http://localhost:5000/headteacher/parent_management")
        print("🔐 Parent Portal: http://localhost:5000/parent/login")
        
        # Run the application
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
