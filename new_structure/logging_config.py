"""
Logging configuration for the application.
"""
import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """
    Set up logging for the application.
    
    Args:
        app: Flask application instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Configure root logger - minimal console output
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # Only show warnings and errors in console

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create console handler with minimal output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler for general logs
    general_log_file = os.path.join(logs_dir, 'app.log')
    file_handler = RotatingFileHandler(general_log_file, maxBytes=10485760, backupCount=10)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Create file handler for mark validation logs
    mark_validation_log_file = os.path.join(logs_dir, 'mark_validation.log')
    mark_validation_handler = RotatingFileHandler(mark_validation_log_file, maxBytes=10485760, backupCount=10)
    mark_validation_handler.setLevel(logging.INFO)
    mark_validation_handler.setFormatter(formatter)
    
    # Create mark validation logger
    mark_validation_logger = logging.getLogger('mark_validation')
    mark_validation_logger.setLevel(logging.INFO)
    mark_validation_logger.addHandler(mark_validation_handler)
    
    # Log startup message only for the main process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        app.logger.info('Application logging configured')
