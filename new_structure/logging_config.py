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

    class SensitiveDataFilter(logging.Filter):
        """Redact obvious sensitive data patterns (emails, phone-like digit sequences)."""
        import re
        EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+')
        PHONE_RE = re.compile(r'\b\+?\d[\d\-() ]{6,}\b')
        def filter(self, record):  # noqa: D401
            msg = record.getMessage()
            try:
                redacted = self.EMAIL_RE.sub('[REDACTED-EMAIL]', msg)
                redacted = self.PHONE_RE.sub('[REDACTED-PHONE]', redacted)
                if redacted != msg:
                    record.msg = redacted
            except Exception:
                pass
            return True

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create console handler with minimal output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    root_logger.addHandler(console_handler)
    
    # Create file handler for general logs
    general_log_file = os.path.join(logs_dir, 'app.log')
    file_handler = RotatingFileHandler(general_log_file, maxBytes=10485760, backupCount=10)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(SensitiveDataFilter())
    root_logger.addHandler(file_handler)
    
    # Create file handler for mark validation logs
    mark_validation_log_file = os.path.join(logs_dir, 'mark_validation.log')
    mark_validation_handler = RotatingFileHandler(mark_validation_log_file, maxBytes=10485760, backupCount=10)
    mark_validation_handler.setLevel(logging.INFO)
    mark_validation_handler.setFormatter(formatter)
    
    # Create mark validation logger
    mark_validation_logger = logging.getLogger('mark_validation')
    mark_validation_logger.setLevel(logging.INFO)
    mark_validation_handler.addFilter(SensitiveDataFilter())
    mark_validation_logger.addHandler(mark_validation_handler)
    
    # Log startup message only for the main process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        app.logger.info('Application logging configured')
