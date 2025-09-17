"""
Logging configuration for the application.
"""
import os
import logging
import json
from logging.handlers import RotatingFileHandler
from flask import has_request_context, g, request


class RequestContextFilter(logging.Filter):
    """Inject request-scoped correlation data into log records."""
    def filter(self, record):  # noqa: D401
        if has_request_context():
            record.request_id = getattr(g, 'request_id', 'n/a')
            record.remote_addr = request.remote_addr or 'n/a'
            record.path = request.path
            record.method = request.method
        else:
            record.request_id = 'n/a'
            record.remote_addr = 'n/a'
            record.path = ''
            record.method = ''
        return True

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

    class SafeEncodingFilter(logging.Filter):
        """Ensure log messages with emoji/wide Unicode don't break narrow encodings (Windows cp1252)."""
        def filter(self, record):  # noqa: D401
            try:
                # Attempt encode to console encoding; replace if fails
                target_enc = getattr(getattr(os, 'sys', None), 'stdout', None)
                _ = record.getMessage().encode('cp1252', errors='strict')  # may raise
            except Exception:
                try:
                    record.msg = record.getMessage().encode('cp1252', errors='replace').decode('cp1252')
                except Exception:
                    pass
            return True

    # Determine formatter (text vs JSON)
    enable_json = bool(os.environ.get('ENABLE_JSON_LOGS'))
    if enable_json:
        class JsonFormatter(logging.Formatter):
            def format(self, record):  # noqa: D401
                base = {
                    'ts': self.formatTime(record, datefmt='%Y-%m-%dT%H:%M:%S'),
                    'level': record.levelname,
                    'logger': record.name,
                    'request_id': getattr(record, 'request_id', 'n/a'),
                    'method': getattr(record, 'method', ''),
                    'path': getattr(record, 'path', ''),
                    'remote_addr': getattr(record, 'remote_addr', ''),
                    'msg': record.getMessage(),
                }
                if record.exc_info:
                    base['exc_info'] = self.formatException(record.exc_info)
                return json.dumps(base, ensure_ascii=False)
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(request_id)s - %(name)s - %(method)s %(path)s - %(message)s')

    # Create console handler with minimal output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    console_handler.addFilter(SafeEncodingFilter())
    console_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(console_handler)
    
    # Create file handler for general logs
    general_log_file = os.path.join(logs_dir, 'app.log')
    file_handler = RotatingFileHandler(general_log_file, maxBytes=10485760, backupCount=10)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(SensitiveDataFilter())
    file_handler.addFilter(SafeEncodingFilter())
    file_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(file_handler)
    
    # Create file handler for audit logs
    audit_log_file = os.path.join(logs_dir, 'audit.log')
    audit_handler = RotatingFileHandler(audit_log_file, maxBytes=10485760, backupCount=10)
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(formatter)
    audit_handler.addFilter(SensitiveDataFilter())
    audit_handler.addFilter(SafeEncodingFilter())
    audit_handler.addFilter(RequestContextFilter())
    audit_logger = logging.getLogger('audit')
    audit_logger.setLevel(logging.INFO)
    audit_logger.addHandler(audit_handler)

    # Create file handler for mark validation logs
    mark_validation_log_file = os.path.join(logs_dir, 'mark_validation.log')
    mark_validation_handler = RotatingFileHandler(mark_validation_log_file, maxBytes=10485760, backupCount=10)
    mark_validation_handler.setLevel(logging.INFO)
    mark_validation_handler.setFormatter(formatter)
    
    # Create mark validation logger
    mark_validation_logger = logging.getLogger('mark_validation')
    mark_validation_logger.setLevel(logging.INFO)
    mark_validation_handler.addFilter(SensitiveDataFilter())
    mark_validation_handler.addFilter(SafeEncodingFilter())
    mark_validation_logger.addHandler(mark_validation_handler)
    mark_validation_logger.addFilter(RequestContextFilter())
    
    # Log startup message only for the main process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        app.logger.info('Application logging configured (json=%s)', enable_json)
