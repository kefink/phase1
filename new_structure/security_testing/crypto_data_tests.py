"""
Cryptographic Failures and Data Protection Testing (OWASP A02)
Testing for weak cryptography, data exposure, and privacy violations
"""

import requests
import re
import base64
import hashlib
from urllib.parse import urljoin

class CryptoDataTester:
    """Test for cryptographic failures and data protection issues."""
    
    def __init__(self, base_url, session):
        self.base_url = base_url
        self.session = session
        self.vulnerabilities = []
    
    def log_vulnerability(self, severity, title, description, evidence="", remediation=""):
        """Log cryptographic/data protection vulnerability."""
        vuln = {
            'category': 'A02 - Cryptographic Failures',
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
    
    def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure in responses."""
        print("\n🔍 TESTING SENSITIVE DATA EXPOSURE")
        print("-" * 50)
        
        # Test various endpoints for sensitive data
        test_endpoints = [
            '/',
            '/admin_login',
            '/teacher_login', 
            '/classteacher_login',
            '/api/config',
            '/api/users',
            '/api/students',
            '/api/teachers',
            '/debug',
            '/status',
            '/info'
        ]
        
        # Patterns for sensitive data
        sensitive_patterns = {
            'passwords': [
                r'password["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'pwd["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'pass["\']?\s*[:=]\s*["\']([^"\']+)["\']'
            ],
            'api_keys': [
                r'api[_-]?key["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'secret[_-]?key["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'access[_-]?token["\']?\s*[:=]\s*["\']([^"\']+)["\']'
            ],
            'database_info': [
                r'database[_-]?url["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'db[_-]?host["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'mysql[_-]?password["\']?\s*[:=]\s*["\']([^"\']+)["\']'
            ],
            'personal_data': [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'  # Credit card pattern
            ]
        }
        
        for endpoint in test_endpoints:
            try:
                response = self.session.get(urljoin(self.base_url, endpoint), timeout=5)
                
                if response.status_code == 200:
                    response_text = response.text
                    
                    # Check for sensitive data patterns
                    for data_type, patterns in sensitive_patterns.items():
                        for pattern in patterns:
                            matches = re.findall(pattern, response_text, re.IGNORECASE)
                            if matches:
                                severity = 'CRITICAL' if data_type in ['passwords', 'api_keys'] else 'HIGH'
                                self.log_vulnerability(
                                    severity,
                                    f'Sensitive {data_type.title()} Exposed',
                                    f'Sensitive {data_type} found in response from {endpoint}',
                                    f'Endpoint: {endpoint}, Pattern: {pattern}, Matches: {len(matches)}',
                                    f'Remove sensitive {data_type} from responses and implement proper data handling'
                                )
            
            except Exception:
                continue
    
    def test_weak_password_storage(self):
        """Test for weak password storage mechanisms."""
        print("\n🔍 TESTING PASSWORD STORAGE SECURITY")
        print("-" * 50)
        
        # Test login with known credentials to analyze response
        test_logins = [
            {'endpoint': '/admin_login', 'username': 'headteacher', 'password': 'admin123'},
            {'endpoint': '/teacher_login', 'username': 'telvo', 'password': 'telvo123'},
            {'endpoint': '/classteacher_login', 'username': 'kevin', 'password': 'kev123'}
        ]
        
        for login in test_logins:
            try:
                response = self.session.post(
                    urljoin(self.base_url, login['endpoint']),
                    data={
                        'username': login['username'],
                        'password': login['password']
                    },
                    timeout=5
                )
                
                # Check if password is echoed back in any form
                if login['password'] in response.text:
                    self.log_vulnerability(
                        'HIGH',
                        'Password Echoed in Response',
                        f'Password appears in response from {login["endpoint"]}',
                        f'Endpoint: {login["endpoint"]}, Password found in response',
                        'Never include passwords in responses'
                    )
                
                # Check for weak password hashing indicators
                weak_hash_patterns = [
                    r'md5\([^)]+\)',
                    r'sha1\([^)]+\)',
                    r'base64\([^)]+\)',
                    login['password'].encode().hex(),  # Plain hex
                    base64.b64encode(login['password'].encode()).decode()  # Base64
                ]
                
                for pattern in weak_hash_patterns:
                    if re.search(str(pattern), response.text, re.IGNORECASE):
                        self.log_vulnerability(
                            'HIGH',
                            'Weak Password Hashing Detected',
                            f'Weak password hashing method detected in {login["endpoint"]}',
                            f'Pattern: {pattern}',
                            'Use strong password hashing algorithms like bcrypt, scrypt, or Argon2'
                        )
            
            except Exception:
                continue
    
    def test_session_token_security(self):
        """Test session token security and randomness."""
        print("\n🔍 TESTING SESSION TOKEN SECURITY")
        print("-" * 50)
        
        # Collect multiple session tokens to analyze
        session_tokens = []
        
        for i in range(5):
            try:
                test_session = requests.Session()
                response = test_session.get(urljoin(self.base_url, '/admin_login'))
                
                # Extract session cookies
                for cookie in test_session.cookies:
                    if 'session' in cookie.name.lower():
                        session_tokens.append(cookie.value)
                        
                        # Check token length
                        if len(cookie.value) < 16:
                            self.log_vulnerability(
                                'MEDIUM',
                                'Short Session Token',
                                'Session token is too short and may be predictable',
                                f'Token length: {len(cookie.value)} characters',
                                'Use longer, cryptographically secure session tokens'
                            )
                        
                        # Check for obvious patterns
                        if cookie.value.isdigit():
                            self.log_vulnerability(
                                'HIGH',
                                'Predictable Session Token',
                                'Session token contains only digits',
                                f'Token: {cookie.value}',
                                'Use cryptographically secure random token generation'
                            )
                        
                        # Check for base64 encoding (might indicate weak entropy)
                        try:
                            decoded = base64.b64decode(cookie.value)
                            if len(decoded) < 16:
                                self.log_vulnerability(
                                    'MEDIUM',
                                    'Weak Session Token Entropy',
                                    'Session token has low entropy when decoded',
                                    f'Decoded length: {len(decoded)} bytes',
                                    'Increase session token entropy'
                                )
                        except:
                            pass  # Not base64, which is fine
            
            except Exception:
                continue
        
        # Check for token reuse
        if len(set(session_tokens)) < len(session_tokens):
            self.log_vulnerability(
                'HIGH',
                'Session Token Reuse',
                'Same session token used multiple times',
                f'Unique tokens: {len(set(session_tokens))}, Total tokens: {len(session_tokens)}',
                'Ensure each session gets a unique token'
            )
    
    def test_data_transmission_security(self):
        """Test data transmission security."""
        print("\n🔍 TESTING DATA TRANSMISSION SECURITY")
        print("-" * 50)
        
        # Check if sensitive operations use HTTPS
        if not self.base_url.startswith('https://'):
            self.log_vulnerability(
                'HIGH',
                'Insecure Data Transmission',
                'Application uses HTTP instead of HTTPS',
                f'URL: {self.base_url}',
                'Implement HTTPS for all communications'
            )
        
        # Test if login forms submit over HTTP
        login_endpoints = ['/admin_login', '/teacher_login', '/classteacher_login']
        
        for endpoint in login_endpoints:
            try:
                response = self.session.get(urljoin(self.base_url, endpoint))
                
                if response.status_code == 200:
                    # Check form action
                    form_actions = re.findall(r'<form[^>]*action=["\']([^"\']*)["\']', response.text, re.IGNORECASE)
                    
                    for action in form_actions:
                        if action.startswith('http://'):
                            self.log_vulnerability(
                                'HIGH',
                                'Login Form Submits Over HTTP',
                                f'Login form in {endpoint} submits to HTTP URL',
                                f'Form action: {action}',
                                'Ensure all login forms submit over HTTPS'
                            )
            
            except Exception:
                continue
    
    def test_encryption_implementation(self):
        """Test encryption implementation quality."""
        print("\n🔍 TESTING ENCRYPTION IMPLEMENTATION")
        print("-" * 50)
        
        # Test for common encryption mistakes
        test_endpoints = [
            '/api/encrypt',
            '/api/decrypt', 
            '/crypto',
            '/hash',
            '/token'
        ]
        
        for endpoint in test_endpoints:
            try:
                response = self.session.get(urljoin(self.base_url, endpoint))
                
                if response.status_code == 200:
                    # Check for weak encryption indicators
                    weak_crypto_patterns = [
                        r'DES\(',
                        r'3DES\(',
                        r'RC4\(',
                        r'MD5\(',
                        r'SHA1\(',
                        r'ECB',
                        r'CBC.*null',
                        r'key.*=.*["\'][0-9a-f]{16,32}["\']'  # Hardcoded keys
                    ]
                    
                    for pattern in weak_crypto_patterns:
                        if re.search(pattern, response.text, re.IGNORECASE):
                            self.log_vulnerability(
                                'HIGH',
                                'Weak Cryptographic Implementation',
                                f'Weak cryptographic method detected in {endpoint}',
                                f'Pattern: {pattern}',
                                'Use strong, modern cryptographic algorithms (AES-256, SHA-256+)'
                            )
            
            except Exception:
                continue
    
    def test_pii_data_handling(self):
        """Test Personally Identifiable Information (PII) handling."""
        print("\n🔍 TESTING PII DATA HANDLING")
        print("-" * 50)
        
        # Test endpoints that might expose PII
        pii_endpoints = [
            '/api/students',
            '/api/teachers',
            '/api/parents',
            '/reports',
            '/export',
            '/download'
        ]
        
        # PII patterns to look for
        pii_patterns = {
            'phone_numbers': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'id_numbers': r'\b\d{8,12}\b',
            'addresses': r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr)',
            'dates_of_birth': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b'
        }
        
        for endpoint in pii_endpoints:
            try:
                response = self.session.get(urljoin(self.base_url, endpoint))
                
                if response.status_code == 200:
                    for pii_type, pattern in pii_patterns.items():
                        matches = re.findall(pattern, response.text)
                        if matches:
                            self.log_vulnerability(
                                'MEDIUM',
                                f'PII Exposure: {pii_type.title()}',
                                f'{pii_type.title()} found in response from {endpoint}',
                                f'Endpoint: {endpoint}, Matches: {len(matches)}',
                                'Implement proper data masking and access controls for PII'
                            )
            
            except Exception:
                continue
    
    def run_all_crypto_data_tests(self):
        """Run all cryptographic and data protection tests."""
        print("🔍 STARTING CRYPTOGRAPHIC & DATA PROTECTION TESTING")
        print("=" * 60)
        
        self.test_sensitive_data_exposure()
        self.test_weak_password_storage()
        self.test_session_token_security()
        self.test_data_transmission_security()
        self.test_encryption_implementation()
        self.test_pii_data_handling()
        
        print(f"\n📊 CRYPTOGRAPHIC & DATA PROTECTION TESTING COMPLETE")
        print(f"Vulnerabilities found: {len(self.vulnerabilities)}")
        
        return self.vulnerabilities
