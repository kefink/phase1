"""
Application factory for the Hillview School Management System.
This file initializes the Flask application and registers extensions and blueprints.
"""
from flask import Flask
from .extensions import db, csrf
from .config import config

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
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    
    # Register blueprints
    from .views import blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    
    return app