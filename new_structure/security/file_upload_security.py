"""
File Upload Security Module
Comprehensive protection against file upload vulnerabilities.
"""

import os
import magic
import hashlib
import logging
from functools import wraps
from flask import request, abort, current_app
from werkzeug.utils import secure_filename
from PIL import Image
import zipfile
import tempfile

class FileUploadSecurity:
    """Comprehensive file upload security."""
    
    # Allowed file extensions and their MIME types
    ALLOWED_EXTENSIONS = {
        # Documents
        '.pdf': ['application/pdf'],
        '.doc': ['application/msword'],
        '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        '.xls': ['application/vnd.ms-excel'],
        '.xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        '.ppt': ['application/vnd.ms-powerpoint'],
        '.pptx': ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
        '.txt': ['text/plain'],
        '.rtf': ['application/rtf'],
        
        # Images
        '.jpg': ['image/jpeg'],
        '.jpeg': ['image/jpeg'],
        '.png': ['image/png'],
        '.gif': ['image/gif'],
        '.bmp': ['image/bmp'],
        '.webp': ['image/webp'],
        
        # Archives (with restrictions)
        '.zip': ['application/zip'],
        '.rar': ['application/x-rar-compressed'],
        
        # Audio/Video (if needed)
        '.mp3': ['audio/mpeg'],
        '.mp4': ['video/mp4'],
        '.avi': ['video/x-msvideo'],
        '.mov': ['video/quicktime']
    }
    
    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.php', '.asp', '.aspx', '.jsp', '.py', '.pl', '.rb', '.sh', '.ps1',
        '.msi', '.deb', '.rpm', '.dmg', '.app', '.ipa', '.apk',
        '.dll', '.so', '.dylib', '.sys', '.drv',
        '.html', '.htm', '.xml', '.svg', '.swf'
    ]
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        'image': 5 * 1024 * 1024,      # 5MB for images
        'document': 10 * 1024 * 1024,  # 10MB for documents
        'archive': 50 * 1024 * 1024,   # 50MB for archives
        'media': 100 * 1024 * 1024,    # 100MB for media files
        'default': 16 * 1024 * 1024    # 16MB default
    }
    
    # Virus signatures (simple patterns)
    VIRUS_SIGNATURES = [
        b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*',  # EICAR test
        b'MZ',  # PE executable header
        b'\x7fELF',  # ELF executable header
        b'\xca\xfe\xba\xbe',  # Java class file
        b'PK\x03\x04',  # ZIP file (needs additional validation)
    ]
    
    @classmethod
    def validate_file_extension(cls, filename):
        """
        Validate file extension.
        
        Args:
            filename: Name of the file
            
        Returns:
            bool: True if extension is allowed
        """
        if not filename:
            return False
        
        # Get file extension
        _, ext = os.path.splitext(filename.lower())
        
        # Check if extension is dangerous
        if ext in cls.DANGEROUS_EXTENSIONS:
            logging.warning(f"Dangerous file extension blocked: {ext}")
            return False
        
        # Check if extension is allowed
        if ext not in cls.ALLOWED_EXTENSIONS:
            logging.warning(f"File extension not allowed: {ext}")
            return False
        
        return True
    
    @classmethod
    def validate_mime_type(cls, file_obj, filename):
        """
        Validate MIME type using python-magic.
        
        Args:
            file_obj: File object
            filename: Name of the file
            
        Returns:
            bool: True if MIME type is valid
        """
        try:
            # Get file extension
            _, ext = os.path.splitext(filename.lower())
            
            # Read file header
            file_obj.seek(0)
            file_header = file_obj.read(1024)
            file_obj.seek(0)
            
            # Get MIME type using magic
            mime_type = magic.from_buffer(file_header, mime=True)
            
            # Check if MIME type matches extension
            allowed_mimes = cls.ALLOWED_EXTENSIONS.get(ext, [])
            if mime_type not in allowed_mimes:
                logging.warning(f"MIME type mismatch: {mime_type} for extension {ext}")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"MIME type validation error: {e}")
            return False
    
    @classmethod
    def validate_file_size(cls, file_obj, filename):
        """
        Validate file size.
        
        Args:
            file_obj: File object
            filename: Name of the file
            
        Returns:
            bool: True if file size is acceptable
        """
        try:
            # Get file size
            file_obj.seek(0, os.SEEK_END)
            file_size = file_obj.tell()
            file_obj.seek(0)
            
            # Determine file category
            _, ext = os.path.splitext(filename.lower())
            
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                category = 'image'
            elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf']:
                category = 'document'
            elif ext in ['.zip', '.rar']:
                category = 'archive'
            elif ext in ['.mp3', '.mp4', '.avi', '.mov']:
                category = 'media'
            else:
                category = 'default'
            
            max_size = cls.MAX_FILE_SIZES.get(category, cls.MAX_FILE_SIZES['default'])
            
            if file_size > max_size:
                logging.warning(f"File too large: {file_size} bytes (max: {max_size})")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"File size validation error: {e}")
            return False
    
    @classmethod
    def scan_for_malware(cls, file_obj):
        """
        Simple malware scanning using signatures.
        
        Args:
            file_obj: File object
            
        Returns:
            bool: True if file appears clean
        """
        try:
            file_obj.seek(0)
            file_content = file_obj.read()
            file_obj.seek(0)
            
            # Check for virus signatures
            for signature in cls.VIRUS_SIGNATURES:
                if signature in file_content:
                    logging.warning("Malware signature detected in uploaded file")
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Malware scanning error: {e}")
            return False
    
    @classmethod
    def validate_image_file(cls, file_obj):
        """
        Additional validation for image files.
        
        Args:
            file_obj: File object
            
        Returns:
            bool: True if image is valid
        """
        try:
            file_obj.seek(0)
            
            # Try to open with PIL
            with Image.open(file_obj) as img:
                # Verify image
                img.verify()
                
                # Check image dimensions (prevent zip bombs)
                if img.size[0] > 10000 or img.size[1] > 10000:
                    logging.warning("Image dimensions too large")
                    return False
                
                # Check for suspicious formats
                if img.format not in ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP']:
                    logging.warning(f"Suspicious image format: {img.format}")
                    return False
            
            file_obj.seek(0)
            return True
            
        except Exception as e:
            logging.warning(f"Image validation failed: {e}")
            return False
    
    @classmethod
    def validate_archive_file(cls, file_obj, filename):
        """
        Additional validation for archive files.
        
        Args:
            file_obj: File object
            filename: Name of the file
            
        Returns:
            bool: True if archive is safe
        """
        try:
            _, ext = os.path.splitext(filename.lower())
            
            if ext == '.zip':
                return cls.validate_zip_file(file_obj)
            elif ext == '.rar':
                # Basic RAR validation (limited without rarfile library)
                return cls.validate_rar_file(file_obj)
            
            return True
            
        except Exception as e:
            logging.warning(f"Archive validation failed: {e}")
            return False
    
    @classmethod
    def validate_zip_file(cls, file_obj):
        """
        Validate ZIP file for zip bombs and malicious content.
        
        Args:
            file_obj: File object
            
        Returns:
            bool: True if ZIP is safe
        """
        try:
            file_obj.seek(0)
            
            with zipfile.ZipFile(file_obj, 'r') as zip_file:
                # Check for zip bomb (compression ratio)
                total_compressed = 0
                total_uncompressed = 0
                
                for info in zip_file.infolist():
                    total_compressed += info.compress_size
                    total_uncompressed += info.file_size
                    
                    # Check individual file size
                    if info.file_size > 100 * 1024 * 1024:  # 100MB per file
                        logging.warning("ZIP contains file too large")
                        return False
                    
                    # Check for directory traversal
                    if '..' in info.filename or info.filename.startswith('/'):
                        logging.warning("ZIP contains path traversal")
                        return False
                    
                    # Check for dangerous file extensions
                    _, ext = os.path.splitext(info.filename.lower())
                    if ext in cls.DANGEROUS_EXTENSIONS:
                        logging.warning(f"ZIP contains dangerous file: {info.filename}")
                        return False
                
                # Check compression ratio (zip bomb detection)
                if total_compressed > 0:
                    ratio = total_uncompressed / total_compressed
                    if ratio > 100:  # Suspicious compression ratio
                        logging.warning("Suspicious compression ratio in ZIP")
                        return False
                
                # Check total uncompressed size
                if total_uncompressed > 500 * 1024 * 1024:  # 500MB total
                    logging.warning("ZIP uncompressed size too large")
                    return False
            
            file_obj.seek(0)
            return True
            
        except Exception as e:
            logging.warning(f"ZIP validation failed: {e}")
            return False
    
    @classmethod
    def validate_rar_file(cls, file_obj):
        """
        Basic RAR file validation.
        
        Args:
            file_obj: File object
            
        Returns:
            bool: True if RAR appears safe
        """
        try:
            file_obj.seek(0)
            header = file_obj.read(7)
            file_obj.seek(0)
            
            # Check RAR signature
            if header[:4] != b'Rar!':
                logging.warning("Invalid RAR signature")
                return False
            
            return True
            
        except Exception as e:
            logging.warning(f"RAR validation failed: {e}")
            return False
    
    @classmethod
    def generate_safe_filename(cls, original_filename):
        """
        Generate a safe filename.
        
        Args:
            original_filename: Original filename
            
        Returns:
            str: Safe filename
        """
        if not original_filename:
            return 'unnamed_file'
        
        # Use werkzeug's secure_filename
        safe_name = secure_filename(original_filename)
        
        # Add timestamp to prevent conflicts
        import time
        timestamp = str(int(time.time()))
        
        name, ext = os.path.splitext(safe_name)
        safe_name = f"{name}_{timestamp}{ext}"
        
        return safe_name
    
    @classmethod
    def create_file_hash(cls, file_obj):
        """
        Create hash of file content.
        
        Args:
            file_obj: File object
            
        Returns:
            str: SHA256 hash of file
        """
        try:
            file_obj.seek(0)
            file_hash = hashlib.sha256()
            
            for chunk in iter(lambda: file_obj.read(4096), b""):
                file_hash.update(chunk)
            
            file_obj.seek(0)
            return file_hash.hexdigest()
            
        except Exception as e:
            logging.error(f"File hashing error: {e}")
            return None
    
    @classmethod
    def validate_uploaded_file(cls, file_obj, filename):
        """
        Comprehensive file validation.
        
        Args:
            file_obj: File object
            filename: Original filename
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check if file exists
        if not file_obj or not filename:
            return False, "No file provided"
        
        # Validate file extension
        if not cls.validate_file_extension(filename):
            return False, "File type not allowed"
        
        # Validate file size
        if not cls.validate_file_size(file_obj, filename):
            return False, "File size too large"
        
        # Validate MIME type
        if not cls.validate_mime_type(file_obj, filename):
            return False, "Invalid file format"
        
        # Scan for malware
        if not cls.scan_for_malware(file_obj):
            return False, "File failed security scan"
        
        # Additional validation based on file type
        _, ext = os.path.splitext(filename.lower())
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            if not cls.validate_image_file(file_obj):
                return False, "Invalid image file"
        
        if ext in ['.zip', '.rar']:
            if not cls.validate_archive_file(file_obj, filename):
                return False, "Invalid or dangerous archive file"
        
        return True, "File is valid"

def secure_file_upload(allowed_extensions=None, max_size=None):
    """
    Decorator for secure file upload handling.
    
    Args:
        allowed_extensions: List of allowed extensions (optional)
        max_size: Maximum file size in bytes (optional)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.files:
                return f(*args, **kwargs)
            
            for file_key, file in request.files.items():
                if file.filename:
                    # Validate file
                    is_valid, error_msg = FileUploadSecurity.validate_uploaded_file(file, file.filename)
                    
                    if not is_valid:
                        logging.warning(f"File upload blocked: {error_msg} for file {file.filename}")
                        abort(400, f"File upload error: {error_msg}")
                    
                    # Additional custom validation
                    if allowed_extensions:
                        _, ext = os.path.splitext(file.filename.lower())
                        if ext not in allowed_extensions:
                            abort(400, f"File extension {ext} not allowed for this upload")
                    
                    if max_size:
                        file.seek(0, os.SEEK_END)
                        file_size = file.tell()
                        file.seek(0)
                        if file_size > max_size:
                            abort(400, "File size exceeds limit for this upload")
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
