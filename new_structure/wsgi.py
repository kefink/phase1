#!/usr/bin/env python3
"""
WSGI Application Entry Point for Production Deployment
====================================================

This module provides the WSGI application interface for production deployment
servers like Gunicorn, uWSGI, or mod_wsgi. 

Production Usage:
    gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:application
    uwsgi --http :8000 --wsgi-file wsgi.py --callable application
"""

import os
import sys
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Import the Flask application factory
from __init__ import create_app

# Create the application instance for production
application = create_app('production')

# Ensure proper logging configuration for production
if application.config.get('ENV') == 'production':
    import logging
    from logging.handlers import RotatingFileHandler
    
    # Configure file logging for production
    if not application.debug and not application.testing:
        file_handler = RotatingFileHandler(
            'logs/twik.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        application.logger.addHandler(file_handler)
        application.logger.setLevel(logging.INFO)
        application.logger.info('Twik application startup')

if __name__ == "__main__":
    # This should not be used in production - use a proper WSGI server
    print("WARNING: This is the WSGI entry point. Use a production WSGI server.")
    print("Example: gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:application")
    application.run(host='0.0.0.0', port=8000, debug=False)