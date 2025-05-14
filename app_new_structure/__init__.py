"""
Application factory for the Hillview School Management System.
This file initializes the Flask application and registers extensions and blueprints.
"""
from flask import Flask

def create_app(config_object=None):
    """Create and configure the Flask application.
    
    Args:
        config_object: Configuration object or string path to configuration file.
        
    Returns:
        Flask application instance.
    """
    app = Flask(__name__)
    
    # Default configuration
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    
    # Override with provided configuration if any
    if config_object:
        app.config.from_object(config_object)
    
    # We'll register extensions and blueprints in later steps
    
    # For now, just return a minimal app
    @app.route('/test')
    def test_route():
        return "New application structure is working!"
    
    return app
