"""
Comprehensive Security Module for Hillview School Management System
Protects against all major web vulnerabilities including:
- SQL Injection (SQLi)
- Cross Site Scripting (XSS) 
- Broken Access Control
- Cross Site Request Forgery (CSRF)
- Security Misconfigurations
- Insecure Direct Object References (IDOR)
- Remote Code Execution (RCE)
- File Upload Vulnerabilities
- File Inclusion (LFI/RFI)
- Server-Side Request Forgery (SSRF)
"""

from .sql_injection_protection import SQLInjectionProtection
from .xss_protection import XSSProtection
from .access_control import AccessControlProtection
from .csrf_protection import CSRFProtection
from .security_config import SecurityConfiguration
from .idor_protection import IDORProtection
from .rce_protection import RCEProtection
from .file_upload_security import FileUploadSecurity
from .file_inclusion_protection import FileInclusionProtection
from .ssrf_protection import SSRFProtection

__all__ = [
    'SQLInjectionProtection',
    'XSSProtection', 
    'AccessControlProtection',
    'CSRFProtection',
    'SecurityConfiguration',
    'IDORProtection',
    'RCEProtection',
    'FileUploadSecurity',
    'FileInclusionProtection',
    'SSRFProtection'
]
