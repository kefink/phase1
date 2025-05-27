"""
Application factory for the Hillview School Management System.
This file initializes the Flask application and registers extensions and blueprints.
"""
from flask import Flask
from .extensions import db, csrf
from .config import config
from .logging_config import setup_logging
from .middleware import MarkSanitizerMiddleware

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

    # Register blueprints
    from .views import blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

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

    # Import the classteacher blueprint
    from .views.classteacher import classteacher_bp

    # Register error handlers
    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"Internal Server Error: {str(e)}")
        return "Internal Server Error", 500

    # Log application startup
    app.logger.info("Application initialized")

    return app