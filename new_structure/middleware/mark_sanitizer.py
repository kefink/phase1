"""
Middleware for sanitizing mark data in requests.
"""
import re
import logging
from flask import request
try:
    from ..services.mark_conversion_service import MarkConversionService
except ImportError:
    try:
        from services.mark_conversion_service import MarkConversionService
    except ImportError:
        # Mock service for testing
        class MarkConversionService:
            @staticmethod
            def sanitize_raw_mark(raw_mark, max_raw_mark):
                return float(raw_mark), float(max_raw_mark)

logger = logging.getLogger('mark_validation')

class MarkSanitizerMiddleware:
    """Middleware to sanitize mark data in incoming requests."""
    
    def __init__(self, app):
        """Initialize the middleware with the Flask app."""
        self.app = app
        self.app.before_request(self.sanitize_mark_data)
        logger.info("Mark sanitizer middleware initialized")
    
    def sanitize_mark_data(self):
        """Sanitize mark data in the request before it's processed by the view function."""
        if request.method == 'POST' and request.form:
            # Check if this is a mark-related request
            if self._is_mark_related_request():
                logger.info(f"Sanitizing mark data for request: {request.path}")
                self._sanitize_form_data()
    
    def _is_mark_related_request(self):
        """Check if the request is related to marks based on the URL and form data."""
        # Check URL patterns
        mark_related_urls = [
            '/upload_class_marks',
            '/update_class_marks',
            '/edit_class_marks',
            '/bulk_upload_marks'
        ]
        
        for url in mark_related_urls:
            if url in request.path:
                return True
        
        # Check for mark-related form fields
        mark_field_patterns = [
            r'^mark_\d+_\d+$',  # mark_student_subject
            r'^total_marks_\d+$',  # total_marks_subject
            r'^raw_mark_\d+_\d+$',  # raw_mark_student_subject
            r'^max_raw_mark_\d+$'  # max_raw_mark_subject
        ]
        
        for pattern in mark_field_patterns:
            for key in request.form.keys():
                if re.match(pattern, key):
                    return True
        
        return False
    
    def _sanitize_form_data(self):
        """Sanitize mark-related form data."""
        # Find and sanitize mark/total_marks pairs
        mark_keys = [k for k in request.form.keys() if k.startswith('mark_') and '_' in k]
        
        for mark_key in mark_keys:
            # Extract student_id and subject_id from the key
            parts = mark_key.split('_')
            if len(parts) >= 3:
                student_id = parts[1]
                subject_id = parts[2]
                
                # Find corresponding total_marks key
                total_marks_key = f'total_marks_{subject_id}'
                
                if total_marks_key in request.form:
                    try:
                        # Get values
                        raw_mark = request.form[mark_key]
                        max_raw_mark = request.form[total_marks_key]
                        
                        # Skip empty values
                        if not raw_mark or not max_raw_mark:
                            continue
                        
                        # Sanitize values
                        sanitized_raw_mark, sanitized_max_raw_mark = MarkConversionService.sanitize_raw_mark(
                            raw_mark, max_raw_mark
                        )
                        
                        # If values were changed, log it
                        if float(raw_mark) != sanitized_raw_mark or float(max_raw_mark) != sanitized_max_raw_mark:
                            logger.warning(
                                f"Sanitized mark data: {mark_key}={raw_mark}->{sanitized_raw_mark}, "
                                f"{total_marks_key}={max_raw_mark}->{sanitized_max_raw_mark}"
                            )
                            
                            # Update request.form (this is a bit hacky since request.form is immutable)
                            # We're using a private attribute, which is not ideal but necessary
                            if hasattr(request, '_cached_form'):
                                request._cached_form = request.form.copy()
                                request._cached_form[mark_key] = str(sanitized_raw_mark)
                                request._cached_form[total_marks_key] = str(sanitized_max_raw_mark)
                                
                    except (ValueError, TypeError) as e:
                        logger.error(f"Error sanitizing mark data: {e}")
