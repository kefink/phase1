"""
Cross-Site Scripting (XSS) Protection Module
Comprehensive protection against XSS attacks.
"""

import re
import html
import logging
from functools import wraps
from flask import request, abort, make_response
from markupsafe import Markup, escape
import bleach

class XSSProtection:
    """Comprehensive XSS protection."""
    
    # Dangerous HTML tags that should be removed
    DANGEROUS_TAGS = [
        'script', 'iframe', 'object', 'embed', 'form', 'input', 'button',
        'textarea', 'select', 'option', 'meta', 'link', 'style', 'base',
        'applet', 'bgsound', 'blink', 'body', 'frame', 'frameset', 'head',
        'html', 'ilayer', 'layer', 'plaintext', 'xml', 'xmp'
    ]
    
    # Allowed HTML tags for rich content (if needed)
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'hr', 'div', 'span'
    ]
    
    # Allowed attributes for HTML tags
    ALLOWED_ATTRIBUTES = {
        '*': ['class', 'id'],
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'div': ['class', 'id'],
        'span': ['class', 'id']
    }
    
    # XSS patterns to detect
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'onfocus\s*=',
        r'onblur\s*=',
        r'onchange\s*=',
        r'onsubmit\s*=',
        r'onkeydown\s*=',
        r'onkeyup\s*=',
        r'onkeypress\s*=',
        r'onmousedown\s*=',
        r'onmouseup\s*=',
        r'onmousemove\s*=',
        r'onmouseout\s*=',
        r'oncontextmenu\s*=',
        r'ondblclick\s*=',
        r'ondrag\s*=',
        r'ondrop\s*=',
        r'onresize\s*=',
        r'onscroll\s*=',
        r'onselect\s*=',
        r'onunload\s*=',
        r'eval\s*\(',
        r'expression\s*\(',
        r'url\s*\(',
        r'@import',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<applet[^>]*>',
        r'<meta[^>]*>',
        r'<link[^>]*>',
        r'<style[^>]*>',
        r'<base[^>]*>',
        r'<form[^>]*>',
        r'<input[^>]*>',
        r'<button[^>]*>',
        r'<textarea[^>]*>',
        r'<select[^>]*>',
        r'data:text/html',
        r'data:application/',
        r'&#x[0-9a-fA-F]+;',
        r'&#[0-9]+;',
        r'%3C.*%3E',
        r'&lt;.*&gt;'
    ]
    
    @classmethod
    def detect_xss(cls, input_value):
        """
        Detect potential XSS attacks in input.
        
        Args:
            input_value: The input to check
            
        Returns:
            bool: True if XSS detected, False otherwise
        """
        if not input_value:
            return False
            
        input_str = str(input_value)
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
                
        return False
    
    @classmethod
    def sanitize_html(cls, input_value, allow_tags=False):
        """
        Sanitize HTML input to prevent XSS.
        
        Args:
            input_value: The input to sanitize
            allow_tags: Whether to allow safe HTML tags
            
        Returns:
            str: Sanitized input
        """
        if not input_value:
            return input_value
            
        input_str = str(input_value)
        
        if allow_tags:
            # Use bleach to clean HTML while preserving safe tags
            cleaned = bleach.clean(
                input_str,
                tags=cls.ALLOWED_TAGS,
                attributes=cls.ALLOWED_ATTRIBUTES,
                strip=True
            )
        else:
            # Escape all HTML
            cleaned = html.escape(input_str)
        
        return cleaned
    
    @classmethod
    def sanitize_javascript(cls, input_value):
        """
        Remove JavaScript from input.
        
        Args:
            input_value: The input to sanitize
            
        Returns:
            str: Sanitized input
        """
        if not input_value:
            return input_value
            
        input_str = str(input_value)
        
        # Remove script tags
        input_str = re.sub(r'<script[^>]*>.*?</script>', '', input_str, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove javascript: URLs
        input_str = re.sub(r'javascript:', '', input_str, flags=re.IGNORECASE)
        
        # Remove vbscript: URLs
        input_str = re.sub(r'vbscript:', '', input_str, flags=re.IGNORECASE)
        
        # Remove event handlers
        for pattern in cls.XSS_PATTERNS:
            if 'on' in pattern and '=' in pattern:
                input_str = re.sub(pattern, '', input_str, flags=re.IGNORECASE)
        
        return input_str
    
    @classmethod
    def validate_input(cls, input_value, field_name="input"):
        """
        Validate input for XSS attacks.
        
        Args:
            input_value: The input to validate
            field_name: Name of the field for logging
            
        Returns:
            bool: True if safe, False if potentially malicious
        """
        if cls.detect_xss(input_value):
            logging.warning(f"XSS attempt detected in {field_name}: {input_value}")
            return False
        return True
    
    @classmethod
    def sanitize_form_data(cls, form_data):
        """
        Sanitize all form data for XSS.
        
        Args:
            form_data: Flask request.form or similar
            
        Returns:
            dict: Sanitized form data
        """
        sanitized = {}
        for field_name, value in form_data.items():
            sanitized[field_name] = cls.sanitize_html(value)
        return sanitized
    
    @classmethod
    def get_csp_header(cls, strict=True):
        """
        Generate Content Security Policy header.
        
        Args:
            strict: Whether to use strict CSP
            
        Returns:
            str: CSP header value
        """
        if strict:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-src 'none'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none';"
            )
        else:
            csp = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "img-src 'self' data: https:; "
                "frame-src 'none'; "
                "object-src 'none';"
            )
        
        return csp

def xss_protection(strict_csp=True):
    """
    Decorator to protect routes from XSS attacks.
    
    Args:
        strict_csp: Whether to use strict Content Security Policy
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Validate form data
            if request.form:
                for field_name, value in request.form.items():
                    if not XSSProtection.validate_input(value, field_name):
                        logging.warning(f"XSS attempt blocked on route: {request.endpoint}")
                        abort(400, "Potentially malicious input detected")
            
            # Validate query parameters
            if request.args:
                for param_name, value in request.args.items():
                    if not XSSProtection.validate_input(value, f"query_param_{param_name}"):
                        logging.warning(f"XSS attempt blocked on route: {request.endpoint}")
                        abort(400, "Potentially malicious query parameters detected")
            
            # Validate JSON data
            if request.is_json and request.json:
                for key, value in request.json.items():
                    if isinstance(value, str) and not XSSProtection.validate_input(value, f"json_{key}"):
                        logging.warning(f"XSS attempt blocked on route: {request.endpoint}")
                        abort(400, "Potentially malicious JSON data detected")
            
            # Execute the route function
            response = make_response(f(*args, **kwargs))
            
            # Add security headers
            response.headers['Content-Security-Policy'] = XSSProtection.get_csp_header(strict_csp)
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            return response
        
        return decorated_function
    return decorator

class SafeTemplateRenderer:
    """
    Helper class for safe template rendering.
    """
    
    @staticmethod
    def safe_render(template_string, **context):
        """
        Safely render a template with XSS protection.
        
        Args:
            template_string: Template string
            **context: Template context variables
            
        Returns:
            str: Safely rendered template
        """
        # Sanitize all context variables
        safe_context = {}
        for key, value in context.items():
            if isinstance(value, str):
                safe_context[key] = XSSProtection.sanitize_html(value)
            else:
                safe_context[key] = value
        
        # Render template (this would integrate with Flask's template engine)
        return template_string.format(**safe_context)
    
    @staticmethod
    def escape_for_js(value):
        """
        Escape value for safe inclusion in JavaScript.
        
        Args:
            value: Value to escape
            
        Returns:
            str: JavaScript-safe value
        """
        if not value:
            return value
            
        # Escape for JavaScript context
        escaped = str(value).replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
        escaped = escaped.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        escaped = escaped.replace('<', '\\u003c').replace('>', '\\u003e')
        
        return escaped
    
    @staticmethod
    def escape_for_css(value):
        """
        Escape value for safe inclusion in CSS.
        
        Args:
            value: Value to escape
            
        Returns:
            str: CSS-safe value
        """
        if not value:
            return value
            
        # Remove potentially dangerous CSS
        escaped = re.sub(r'[<>"\']', '', str(value))
        escaped = re.sub(r'javascript:', '', escaped, flags=re.IGNORECASE)
        escaped = re.sub(r'expression\s*\(', '', escaped, flags=re.IGNORECASE)
        escaped = re.sub(r'@import', '', escaped, flags=re.IGNORECASE)
        
        return escaped
