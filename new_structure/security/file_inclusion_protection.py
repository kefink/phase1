"""
File Inclusion (LFI/RFI) Protection Module
Comprehensive protection against Local and Remote File Inclusion attacks.
"""

import os
import re
import logging
from functools import wraps
from flask import request, abort, current_app
from urllib.parse import urlparse

class FileInclusionProtection:
    """Comprehensive file inclusion protection."""
    
    # Local File Inclusion patterns
    LFI_PATTERNS = [
        r'\.\./+',  # Directory traversal
        r'\.\.\\+',  # Windows directory traversal
        r'/etc/passwd',  # Unix password file
        r'/etc/shadow',  # Unix shadow file
        r'/etc/hosts',  # Unix hosts file
        r'/proc/self/environ',  # Process environment
        r'/proc/version',  # System version
        r'/proc/cmdline',  # Command line
        r'C:\\Windows\\System32\\',  # Windows system directory
        r'C:\\boot\.ini',  # Windows boot file
        r'C:\\Windows\\win\.ini',  # Windows configuration
        r'%SYSTEMROOT%',  # Windows environment variable
        r'%WINDIR%',  # Windows directory variable
        r'/var/log/',  # Log files
        r'/var/www/',  # Web directory
        r'/home/',  # Home directories
        r'/root/',  # Root directory
        r'/tmp/',  # Temporary directory
        r'file://',  # File protocol
        r'php://filter',  # PHP filter
        r'php://input',  # PHP input
        r'data://',  # Data protocol
        r'expect://',  # Expect protocol
        r'zip://',  # ZIP protocol
    ]
    
    # Remote File Inclusion patterns
    RFI_PATTERNS = [
        r'https?://',  # HTTP/HTTPS URLs
        r'ftps?://',  # FTP URLs
        r'smb://',  # SMB protocol
        r'ldap://',  # LDAP protocol
        r'gopher://',  # Gopher protocol
        r'dict://',  # Dictionary protocol
        r'jar://',  # JAR protocol
        r'netdoc://',  # NetDoc protocol
        r'mailto:',  # Email protocol
        r'news:',  # News protocol
        r'javascript:',  # JavaScript protocol
        r'vbscript:',  # VBScript protocol
    ]
    
    # Dangerous file extensions for inclusion
    DANGEROUS_INCLUDE_EXTENSIONS = [
        '.php', '.asp', '.aspx', '.jsp', '.py', '.pl', '.rb', '.sh',
        '.exe', '.bat', '.cmd', '.com', '.scr', '.vbs', '.js',
        '.htaccess', '.htpasswd', '.ini', '.conf', '.cfg'
    ]
    
    # Allowed file extensions for safe inclusion
    SAFE_INCLUDE_EXTENSIONS = [
        '.txt', '.log', '.csv', '.json', '.xml', '.html', '.htm',
        '.md', '.rst', '.pdf'
    ]
    
    # Allowed directories for file inclusion
    ALLOWED_INCLUDE_DIRS = [
        'templates',
        'static',
        'uploads',
        'data',
        'logs'
    ]
    
    @classmethod
    def detect_lfi_attempt(cls, input_value):
        """
        Detect Local File Inclusion attempts.
        
        Args:
            input_value: Input to check
            
        Returns:
            bool: True if LFI detected
        """
        if not input_value:
            return False
        
        input_str = str(input_value)
        
        for pattern in cls.LFI_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def detect_rfi_attempt(cls, input_value):
        """
        Detect Remote File Inclusion attempts.
        
        Args:
            input_value: Input to check
            
        Returns:
            bool: True if RFI detected
        """
        if not input_value:
            return False
        
        input_str = str(input_value)
        
        for pattern in cls.RFI_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def validate_file_path(cls, file_path):
        """
        Validate file path for inclusion safety.
        
        Args:
            file_path: File path to validate
            
        Returns:
            bool: True if path is safe
        """
        if not file_path:
            return False
        
        # Check for LFI/RFI patterns
        if cls.detect_lfi_attempt(file_path) or cls.detect_rfi_attempt(file_path):
            return False
        
        try:
            # Normalize path
            normalized_path = os.path.normpath(file_path)
            
            # Check for directory traversal
            if '..' in normalized_path:
                return False
            
            # Check if path is absolute (should be relative)
            if os.path.isabs(normalized_path):
                return False
            
            # Check file extension
            _, ext = os.path.splitext(normalized_path.lower())
            if ext in cls.DANGEROUS_INCLUDE_EXTENSIONS:
                return False
            
            # Check if extension is in safe list
            if ext and ext not in cls.SAFE_INCLUDE_EXTENSIONS:
                return False
            
            # Check if path starts with allowed directory
            path_parts = normalized_path.split(os.sep)
            if path_parts and path_parts[0] not in cls.ALLOWED_INCLUDE_DIRS:
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Path validation error: {e}")
            return False
    
    @classmethod
    def sanitize_include_path(cls, file_path):
        """
        Sanitize file path for safe inclusion.
        
        Args:
            file_path: Original file path
            
        Returns:
            str: Sanitized file path or None if unsafe
        """
        if not file_path:
            return None
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"|?*]', '', str(file_path))
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Normalize path
        sanitized = os.path.normpath(sanitized)
        
        # Remove leading slashes
        sanitized = sanitized.lstrip('/')
        sanitized = sanitized.lstrip('\\')
        
        # Validate sanitized path
        if cls.validate_file_path(sanitized):
            return sanitized
        
        return None
    
    @classmethod
    def safe_file_include(cls, file_path, base_dir=None):
        """
        Safely include/read a file.
        
        Args:
            file_path: Path to file
            base_dir: Base directory for file operations
            
        Returns:
            str: File content or None if error
        """
        # Sanitize path
        safe_path = cls.sanitize_include_path(file_path)
        if not safe_path:
            logging.warning(f"Unsafe file inclusion blocked: {file_path}")
            return None
        
        try:
            # Construct full path
            if base_dir:
                full_path = os.path.join(base_dir, safe_path)
            else:
                full_path = safe_path
            
            # Resolve absolute path
            abs_path = os.path.abspath(full_path)
            
            # Check if file exists and is readable
            if not os.path.isfile(abs_path):
                logging.warning(f"File not found: {abs_path}")
                return None
            
            # Additional security check - ensure file is within allowed directory
            if base_dir:
                base_abs = os.path.abspath(base_dir)
                if not abs_path.startswith(base_abs):
                    logging.warning(f"File outside allowed directory: {abs_path}")
                    return None
            
            # Read file content
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Limit file size
            max_size = 1024 * 1024  # 1MB
            if len(content) > max_size:
                logging.warning(f"File too large for inclusion: {abs_path}")
                return None
            
            return content
            
        except Exception as e:
            logging.error(f"File inclusion error: {e}")
            return None
    
    @classmethod
    def validate_url_inclusion(cls, url):
        """
        Validate URL for remote inclusion safety.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is safe
        """
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            
            # Only allow HTTPS
            if parsed.scheme != 'https':
                return False
            
            # Check for suspicious domains
            suspicious_domains = [
                'localhost',
                '127.0.0.1',
                '0.0.0.0',
                '10.',
                '172.',
                '192.168.',
                'metadata.google.internal',
                'instance-data'
            ]
            
            for domain in suspicious_domains:
                if domain in parsed.netloc:
                    return False
            
            # Check for suspicious paths
            if cls.detect_lfi_attempt(parsed.path):
                return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def validate_template_inclusion(cls, template_name):
        """
        Validate template name for safe inclusion.
        
        Args:
            template_name: Template name to validate
            
        Returns:
            bool: True if template name is safe
        """
        if not template_name:
            return False
        
        # Check for path traversal
        if '..' in template_name or '/' in template_name or '\\' in template_name:
            return False
        
        # Check for dangerous extensions
        _, ext = os.path.splitext(template_name.lower())
        if ext in cls.DANGEROUS_INCLUDE_EXTENSIONS:
            return False
        
        # Template names should only contain alphanumeric, underscore, hyphen, and dot
        if not re.match(r'^[a-zA-Z0-9_.-]+$', template_name):
            return False
        
        return True

def file_inclusion_protection(f):
    """
    Decorator to protect routes from file inclusion attacks.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check form data
        if request.form:
            for field_name, value in request.form.items():
                if FileInclusionProtection.detect_lfi_attempt(value):
                    logging.warning(f"LFI attempt blocked in form field {field_name}: {value}")
                    abort(400, "Local file inclusion attempt detected")
                
                if FileInclusionProtection.detect_rfi_attempt(value):
                    logging.warning(f"RFI attempt blocked in form field {field_name}: {value}")
                    abort(400, "Remote file inclusion attempt detected")
        
        # Check query parameters
        if request.args:
            for param_name, value in request.args.items():
                if FileInclusionProtection.detect_lfi_attempt(value):
                    logging.warning(f"LFI attempt blocked in query param {param_name}: {value}")
                    abort(400, "Local file inclusion attempt detected")
                
                if FileInclusionProtection.detect_rfi_attempt(value):
                    logging.warning(f"RFI attempt blocked in query param {param_name}: {value}")
                    abort(400, "Remote file inclusion attempt detected")
        
        # Check JSON data
        if request.is_json and request.json:
            for key, value in request.json.items():
                if isinstance(value, str):
                    if FileInclusionProtection.detect_lfi_attempt(value):
                        logging.warning(f"LFI attempt blocked in JSON field {key}: {value}")
                        abort(400, "Local file inclusion attempt detected")
                    
                    if FileInclusionProtection.detect_rfi_attempt(value):
                        logging.warning(f"RFI attempt blocked in JSON field {key}: {value}")
                        abort(400, "Remote file inclusion attempt detected")
        
        return f(*args, **kwargs)
    
    return decorated_function

class SecureTemplateLoader:
    """
    Secure template loader with file inclusion protection.
    """
    
    @staticmethod
    def safe_load_template(template_name, template_dir='templates'):
        """
        Safely load template file.
        
        Args:
            template_name: Name of template
            template_dir: Template directory
            
        Returns:
            str: Template content or None if error
        """
        if not FileInclusionProtection.validate_template_inclusion(template_name):
            logging.warning(f"Unsafe template inclusion blocked: {template_name}")
            return None
        
        return FileInclusionProtection.safe_file_include(template_name, template_dir)
    
    @staticmethod
    def safe_include_partial(partial_name, template_dir='templates/partials'):
        """
        Safely include template partial.
        
        Args:
            partial_name: Name of partial template
            template_dir: Partial template directory
            
        Returns:
            str: Partial content or None if error
        """
        if not FileInclusionProtection.validate_template_inclusion(partial_name):
            logging.warning(f"Unsafe partial inclusion blocked: {partial_name}")
            return None
        
        return FileInclusionProtection.safe_file_include(partial_name, template_dir)

class SecureConfigLoader:
    """
    Secure configuration file loader.
    """
    
    @staticmethod
    def safe_load_config(config_name, config_dir='config'):
        """
        Safely load configuration file.
        
        Args:
            config_name: Name of config file
            config_dir: Configuration directory
            
        Returns:
            str: Config content or None if error
        """
        # Additional validation for config files
        if not config_name.endswith(('.json', '.yaml', '.yml', '.ini', '.cfg')):
            logging.warning(f"Invalid config file extension: {config_name}")
            return None
        
        if not FileInclusionProtection.validate_file_path(config_name):
            logging.warning(f"Unsafe config inclusion blocked: {config_name}")
            return None
        
        return FileInclusionProtection.safe_file_include(config_name, config_dir)
