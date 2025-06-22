"""
Security Configuration Testing (OWASP A05)
Testing for security misconfigurations, insecure defaults, and hardening issues
"""

import requests
import ssl
import socket
from urllib.parse import urljoin, urlparse
import re

class SecurityConfigTester:
    """Test for security misconfigurations and hardening issues."""
    
    def __init__(self, base_url, session):
        self.base_url = base_url
        self.session = session
        self.vulnerabilities = []
        self.parsed_url = urlparse(base_url)
    
    def log_vulnerability(self, severity, title, description, evidence="", remediation=""):
        """Log security configuration vulnerability."""
        vuln = {
            'category': 'A05 - Security Misconfiguration',
            'severity': severity,
            'title': title,
            'description': description,
            'evidence': evidence,
            'remediation': remediation
        }
        self.vulnerabilities.append(vuln)
        print(f"🚨 {severity}: {title}")
        print(f"   Evidence: {evidence}")
        print()
    
    def test_http_security_headers(self):
        """Test for missing or misconfigured HTTP security headers."""
        print("\n🔍 TESTING HTTP SECURITY HEADERS")
        print("-" * 50)
        
        try:
            response = self.session.get(urljoin(self.base_url, '/'), timeout=10)
            headers = response.headers
            
            # Required security headers
            security_headers = {
                'X-Content-Type-Options': {
                    'expected': 'nosniff',
                    'severity': 'MEDIUM',
                    'description': 'Prevents MIME type sniffing attacks'
                },
                'X-Frame-Options': {
                    'expected': ['DENY', 'SAMEORIGIN'],
                    'severity': 'MEDIUM',
                    'description': 'Prevents clickjacking attacks'
                },
                'X-XSS-Protection': {
                    'expected': '1; mode=block',
                    'severity': 'LOW',
                    'description': 'Enables XSS filtering in browsers'
                },
                'Strict-Transport-Security': {
                    'expected': None,  # Any value is good for HTTPS
                    'severity': 'HIGH',
                    'description': 'Enforces HTTPS connections'
                },
                'Content-Security-Policy': {
                    'expected': None,  # Any CSP is better than none
                    'severity': 'HIGH',
                    'description': 'Prevents XSS and data injection attacks'
                },
                'Referrer-Policy': {
                    'expected': ['strict-origin-when-cross-origin', 'strict-origin', 'no-referrer'],
                    'severity': 'LOW',
                    'description': 'Controls referrer information'
                },
                'Permissions-Policy': {
                    'expected': None,
                    'severity': 'LOW',
                    'description': 'Controls browser features'
                }
            }
            
            for header_name, config in security_headers.items():
                if header_name not in headers:
                    self.log_vulnerability(
                        config['severity'],
                        f'Missing Security Header: {header_name}',
                        f'Security header {header_name} is missing',
                        f'Header: {header_name} not found in response',
                        f'Add {header_name} header. {config["description"]}'
                    )
                else:
                    header_value = headers[header_name]
                    if config['expected']:
                        if isinstance(config['expected'], list):
                            if header_value not in config['expected']:
                                self.log_vulnerability(
                                    'LOW',
                                    f'Weak Security Header: {header_name}',
                                    f'Security header {header_name} has weak configuration',
                                    f'Header: {header_name}: {header_value}',
                                    f'Use recommended values: {config["expected"]}'
                                )
                        elif header_value != config['expected']:
                            self.log_vulnerability(
                                'LOW',
                                f'Weak Security Header: {header_name}',
                                f'Security header {header_name} has weak configuration',
                                f'Header: {header_name}: {header_value}',
                                f'Use recommended value: {config["expected"]}'
                            )
            
            # Check for information disclosure headers
            disclosure_headers = [
                'Server', 'X-Powered-By', 'X-AspNet-Version', 
                'X-AspNetMvc-Version', 'X-Generator'
            ]
            
            for header in disclosure_headers:
                if header in headers:
                    self.log_vulnerability(
                        'LOW',
                        f'Information Disclosure Header: {header}',
                        f'Server information disclosed in {header} header',
                        f'Header: {header}: {headers[header]}',
                        f'Remove or obfuscate {header} header'
                    )
        
        except Exception as e:
            print(f"Error testing security headers: {e}")
    
    def test_ssl_tls_configuration(self):
        """Test SSL/TLS configuration if HTTPS is used."""
        print("\n🔍 TESTING SSL/TLS CONFIGURATION")
        print("-" * 50)
        
        if self.parsed_url.scheme != 'https':
            self.log_vulnerability(
                'HIGH',
                'HTTP Used Instead of HTTPS',
                'Application is not using HTTPS encryption',
                f'URL scheme: {self.parsed_url.scheme}',
                'Implement HTTPS with proper SSL/TLS configuration'
            )
            return
        
        try:
            # Test SSL/TLS configuration
            hostname = self.parsed_url.hostname
            port = self.parsed_url.port or 443
            
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Get SSL certificate info
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()
                    
                    # Check SSL/TLS version
                    weak_versions = ['SSLv2', 'SSLv3', 'TLSv1', 'TLSv1.1']
                    if version in weak_versions:
                        self.log_vulnerability(
                            'HIGH',
                            f'Weak SSL/TLS Version: {version}',
                            f'Server supports weak SSL/TLS version {version}',
                            f'SSL Version: {version}',
                            'Use TLS 1.2 or higher'
                        )
                    
                    # Check cipher strength
                    if cipher:
                        cipher_name = cipher[0]
                        key_length = cipher[2]
                        
                        if key_length < 128:
                            self.log_vulnerability(
                                'HIGH',
                                f'Weak Cipher: {cipher_name}',
                                f'Server uses weak cipher with {key_length}-bit key',
                                f'Cipher: {cipher_name}, Key length: {key_length}',
                                'Use strong ciphers with at least 128-bit keys'
                            )
                    
                    print(f"✅ SSL/TLS Version: {version}")
                    print(f"✅ Cipher: {cipher[0] if cipher else 'Unknown'}")
        
        except Exception as e:
            print(f"SSL/TLS testing error: {e}")
    
    def test_directory_listing(self):
        """Test for directory listing vulnerabilities."""
        print("\n🔍 TESTING DIRECTORY LISTING")
        print("-" * 50)
        
        # Common directories that might have listing enabled
        test_directories = [
            '/static/',
            '/assets/',
            '/uploads/',
            '/files/',
            '/images/',
            '/css/',
            '/js/',
            '/admin/',
            '/backup/',
            '/logs/',
            '/temp/',
            '/cache/'
        ]
        
        for directory in test_directories:
            try:
                response = self.session.get(urljoin(self.base_url, directory), timeout=5)
                
                if response.status_code == 200:
                    # Check for directory listing indicators
                    listing_indicators = [
                        'Index of',
                        'Directory listing',
                        'Parent Directory',
                        '<title>Index of',
                        'apache.*directory',
                        'nginx.*directory'
                    ]
                    
                    response_text = response.text.lower()
                    for indicator in listing_indicators:
                        if re.search(indicator, response_text, re.IGNORECASE):
                            self.log_vulnerability(
                                'MEDIUM',
                                f'Directory Listing Enabled: {directory}',
                                f'Directory listing is enabled for {directory}',
                                f'Directory: {directory}, Indicator: {indicator}',
                                'Disable directory listing in web server configuration'
                            )
                            break
            
            except Exception:
                continue
    
    def test_sensitive_file_exposure(self):
        """Test for exposure of sensitive files."""
        print("\n🔍 TESTING SENSITIVE FILE EXPOSURE")
        print("-" * 50)
        
        # Common sensitive files
        sensitive_files = [
            # Configuration files
            '/.env',
            '/config.py',
            '/settings.py',
            '/database.yml',
            '/config.yml',
            '/app.config',
            
            # Backup files
            '/backup.sql',
            '/database.sql',
            '/dump.sql',
            '/backup.zip',
            '/backup.tar.gz',
            
            # Version control
            '/.git/config',
            '/.git/HEAD',
            '/.svn/entries',
            
            # Log files
            '/error.log',
            '/access.log',
            '/debug.log',
            '/app.log',
            
            # System files
            '/etc/passwd',
            '/etc/shadow',
            '/proc/version',
            '/proc/self/environ',
            
            # Application files
            '/requirements.txt',
            '/package.json',
            '/composer.json',
            '/web.config',
            '/.htaccess',
            '/robots.txt',
            '/sitemap.xml'
        ]
        
        for file_path in sensitive_files:
            try:
                response = self.session.get(urljoin(self.base_url, file_path), timeout=5)
                
                if response.status_code == 200:
                    # Check if it's actually a sensitive file (not a 404 page)
                    if len(response.text) > 0 and not ('404' in response.text or 'not found' in response.text.lower()):
                        severity = 'CRITICAL' if any(x in file_path for x in ['.env', 'passwd', 'shadow', 'config']) else 'HIGH'
                        
                        self.log_vulnerability(
                            severity,
                            f'Sensitive File Exposed: {file_path}',
                            f'Sensitive file {file_path} is accessible',
                            f'File: {file_path}, Size: {len(response.text)} bytes',
                            f'Remove or restrict access to {file_path}'
                        )
            
            except Exception:
                continue
    
    def test_error_handling(self):
        """Test error handling and information disclosure."""
        print("\n🔍 TESTING ERROR HANDLING")
        print("-" * 50)
        
        # Test various error conditions
        error_tests = [
            {'url': '/nonexistent', 'expected_status': 404},
            {'url': '/admin/nonexistent', 'expected_status': 404},
            {'url': '/api/nonexistent', 'expected_status': 404},
        ]
        
        for test in error_tests:
            try:
                response = self.session.get(urljoin(self.base_url, test['url']), timeout=5)
                
                # Check for information disclosure in error messages
                disclosure_patterns = [
                    r'traceback',
                    r'stack trace',
                    r'exception',
                    r'error.*line \d+',
                    r'file.*\.py',
                    r'mysql.*error',
                    r'postgresql.*error',
                    r'sqlite.*error',
                    r'database.*error',
                    r'internal server error.*details'
                ]
                
                response_text = response.text.lower()
                for pattern in disclosure_patterns:
                    if re.search(pattern, response_text, re.IGNORECASE):
                        self.log_vulnerability(
                            'MEDIUM',
                            f'Information Disclosure in Error Page',
                            f'Error page reveals sensitive information',
                            f'URL: {test["url"]}, Pattern: {pattern}',
                            'Implement custom error pages without sensitive information'
                        )
                        break
            
            except Exception:
                continue
    
    def test_default_credentials(self):
        """Test for default or weak credentials."""
        print("\n🔍 TESTING DEFAULT CREDENTIALS")
        print("-" * 50)
        
        # Common default credentials
        default_creds = [
            {'username': 'admin', 'password': 'admin'},
            {'username': 'admin', 'password': 'password'},
            {'username': 'admin', 'password': '123456'},
            {'username': 'administrator', 'password': 'administrator'},
            {'username': 'root', 'password': 'root'},
            {'username': 'test', 'password': 'test'},
            {'username': 'guest', 'password': 'guest'},
            {'username': 'demo', 'password': 'demo'}
        ]
        
        login_endpoints = ['/admin_login', '/teacher_login', '/classteacher_login']
        
        for endpoint in login_endpoints:
            for creds in default_creds:
                try:
                    response = self.session.post(
                        urljoin(self.base_url, endpoint),
                        data=creds,
                        allow_redirects=False,
                        timeout=5
                    )
                    
                    # Check if login was successful
                    if response.status_code == 302:
                        location = response.headers.get('Location', '')
                        if 'dashboard' in location or 'admin' in location:
                            self.log_vulnerability(
                                'CRITICAL',
                                f'Default Credentials Found',
                                f'Default credentials work on {endpoint}',
                                f'Username: {creds["username"]}, Password: {creds["password"]}',
                                'Change default credentials immediately'
                            )
                
                except Exception:
                    continue
    
    def run_all_config_tests(self):
        """Run all security configuration tests."""
        print("🔍 STARTING SECURITY CONFIGURATION TESTING")
        print("=" * 60)
        
        self.test_http_security_headers()
        self.test_ssl_tls_configuration()
        self.test_directory_listing()
        self.test_sensitive_file_exposure()
        self.test_error_handling()
        self.test_default_credentials()
        
        print(f"\n📊 SECURITY CONFIGURATION TESTING COMPLETE")
        print(f"Vulnerabilities found: {len(self.vulnerabilities)}")
        
        return self.vulnerabilities
