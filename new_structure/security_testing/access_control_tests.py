"""
Access Control and Authorization Testing (OWASP A01)
Testing for broken access control, privilege escalation, and authorization flaws
"""

import requests
import time
from urllib.parse import urljoin

class AccessControlTester:
    """Test for access control and authorization vulnerabilities."""
    
    def __init__(self, base_url, session):
        self.base_url = base_url
        self.session = session
        self.vulnerabilities = []
        self.user_sessions = {}
    
    def log_vulnerability(self, severity, title, description, evidence="", remediation=""):
        """Log access control vulnerability."""
        vuln = {
            'category': 'A01 - Broken Access Control',
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
    
    def create_user_sessions(self):
        """Create sessions for different user roles."""
        print("\n🔍 CREATING USER SESSIONS FOR ACCESS CONTROL TESTING")
        print("-" * 60)
        
        # Test users with different roles
        test_users = [
            {'username': 'headteacher', 'password': 'admin123', 'role': 'headteacher'},
            {'username': 'kevin', 'password': 'kev123', 'role': 'classteacher'},
            {'username': 'telvo', 'password': 'telvo123', 'role': 'teacher'}
        ]
        
        for user in test_users:
            session = requests.Session()
            
            # Determine login endpoint based on role
            if user['role'] == 'headteacher':
                login_url = '/admin_login'
            elif user['role'] == 'classteacher':
                login_url = '/classteacher_login'
            else:
                login_url = '/teacher_login'
            
            try:
                response = session.post(
                    urljoin(self.base_url, login_url),
                    data={
                        'username': user['username'],
                        'password': user['password']
                    },
                    allow_redirects=False,
                    timeout=10
                )
                
                if response.status_code == 302:
                    self.user_sessions[user['role']] = session
                    print(f"✅ Created session for {user['role']}")
                else:
                    print(f"❌ Failed to create session for {user['role']}")
            
            except Exception as e:
                print(f"❌ Error creating session for {user['role']}: {e}")
    
    def test_horizontal_privilege_escalation(self):
        """Test for horizontal privilege escalation."""
        print("\n🔍 TESTING HORIZONTAL PRIVILEGE ESCALATION")
        print("-" * 50)
        
        # Test if users can access other users' data
        test_endpoints = [
            # User-specific endpoints that might be vulnerable
            '/teacher/profile/1',
            '/teacher/profile/2',
            '/classteacher/assignments/1',
            '/classteacher/assignments/2',
            '/api/user/1',
            '/api/user/2',
            '/student/1/marks',
            '/student/2/marks'
        ]
        
        for role, session in self.user_sessions.items():
            for endpoint in test_endpoints:
                self.test_endpoint_access(session, role, endpoint, 'horizontal')
    
    def test_vertical_privilege_escalation(self):
        """Test for vertical privilege escalation."""
        print("\n🔍 TESTING VERTICAL PRIVILEGE ESCALATION")
        print("-" * 50)
        
        # Admin-only endpoints that lower-privilege users shouldn't access
        admin_endpoints = [
            '/headteacher/',
            '/headteacher/manage_teachers',
            '/headteacher/analytics',
            '/headteacher/reports',
            '/admin/',
            '/admin/users',
            '/admin/settings',
            '/universal/dashboard'
        ]
        
        # Test if non-admin users can access admin endpoints
        for role, session in self.user_sessions.items():
            if role != 'headteacher':  # Test non-admin users
                for endpoint in admin_endpoints:
                    self.test_endpoint_access(session, role, endpoint, 'vertical')
    
    def test_unauthenticated_access(self):
        """Test for unauthenticated access to protected resources."""
        print("\n🔍 TESTING UNAUTHENTICATED ACCESS")
        print("-" * 50)
        
        # Create unauthenticated session
        unauth_session = requests.Session()
        
        protected_endpoints = [
            '/headteacher/',
            '/classteacher/',
            '/teacher/',
            '/api/students',
            '/api/teachers',
            '/api/marks',
            '/reports/',
            '/analytics/',
            '/upload/',
            '/download/'
        ]
        
        for endpoint in protected_endpoints:
            self.test_endpoint_access(unauth_session, 'unauthenticated', endpoint, 'authentication')
    
    def test_endpoint_access(self, session, user_role, endpoint, test_type):
        """Test access to a specific endpoint."""
        try:
            response = session.get(
                urljoin(self.base_url, endpoint),
                allow_redirects=False,
                timeout=10
            )
            
            # Analyze response for access control issues
            if response.status_code == 200:
                # Check if sensitive data is exposed
                sensitive_indicators = [
                    'password', 'secret', 'token', 'api_key',
                    'admin', 'database', 'config', 'private'
                ]
                
                response_text = response.text.lower()
                for indicator in sensitive_indicators:
                    if indicator in response_text:
                        severity = 'CRITICAL' if test_type == 'authentication' else 'HIGH'
                        self.log_vulnerability(
                            severity,
                            f'{test_type.title()} Access Control Bypass',
                            f'{user_role} user can access {endpoint}',
                            f'Endpoint: {endpoint}, Status: {response.status_code}, Contains: {indicator}',
                            'Implement proper access control checks'
                        )
                        return
                
                # If endpoint returns 200 but shouldn't be accessible
                if test_type == 'authentication' or (test_type == 'vertical' and 'admin' in endpoint):
                    self.log_vulnerability(
                        'HIGH',
                        f'{test_type.title()} Access Control Bypass',
                        f'{user_role} user can access protected endpoint {endpoint}',
                        f'Endpoint: {endpoint}, Status: {response.status_code}',
                        'Implement proper authentication and authorization checks'
                    )
            
            elif response.status_code == 302:
                # Check if redirect is to login (good) or to accessible content (bad)
                location = response.headers.get('Location', '')
                if 'login' not in location.lower() and test_type == 'authentication':
                    self.log_vulnerability(
                        'MEDIUM',
                        'Improper Access Control Redirect',
                        f'Unauthenticated access to {endpoint} redirects to {location}',
                        f'Endpoint: {endpoint}, Redirect: {location}',
                        'Ensure unauthenticated users are redirected to login'
                    )
            
            elif response.status_code == 403:
                # This is expected for proper access control
                pass
            
            elif response.status_code == 404:
                # Endpoint doesn't exist, which is fine
                pass
        
        except Exception as e:
            # Network errors are expected for non-existent endpoints
            pass
    
    def test_direct_object_references(self):
        """Test for Insecure Direct Object References (IDOR)."""
        print("\n🔍 TESTING INSECURE DIRECT OBJECT REFERENCES")
        print("-" * 50)
        
        # Test endpoints with object IDs
        idor_endpoints = [
            '/student/{id}',
            '/teacher/{id}',
            '/report/{id}',
            '/mark/{id}',
            '/api/student/{id}',
            '/api/teacher/{id}',
            '/download/report/{id}',
            '/view/marks/{id}'
        ]
        
        # Test with different ID values
        test_ids = [1, 2, 3, 999, -1, 0, 'admin', '../', '../../etc/passwd']
        
        for role, session in self.user_sessions.items():
            for endpoint_template in idor_endpoints:
                for test_id in test_ids:
                    endpoint = endpoint_template.replace('{id}', str(test_id))
                    self.test_idor_endpoint(session, role, endpoint, test_id)
    
    def test_idor_endpoint(self, session, user_role, endpoint, test_id):
        """Test specific endpoint for IDOR vulnerability."""
        try:
            response = session.get(
                urljoin(self.base_url, endpoint),
                timeout=10
            )
            
            if response.status_code == 200:
                # Check if response contains data that user shouldn't access
                sensitive_patterns = [
                    r'password.*:',
                    r'secret.*:',
                    r'token.*:',
                    r'admin.*:',
                    r'root:',
                    r'uid=\d+'
                ]
                
                import re
                for pattern in sensitive_patterns:
                    if re.search(pattern, response.text, re.IGNORECASE):
                        self.log_vulnerability(
                            'HIGH',
                            f'Insecure Direct Object Reference in {endpoint}',
                            f'{user_role} can access sensitive data via object ID {test_id}',
                            f'Endpoint: {endpoint}, Pattern: {pattern}',
                            'Implement proper authorization checks for object access'
                        )
                        return
                
                # Check for path traversal success
                if test_id in ['../', '../../etc/passwd'] and ('root:' in response.text or 'bin:' in response.text):
                    self.log_vulnerability(
                        'CRITICAL',
                        f'Path Traversal via IDOR in {endpoint}',
                        f'Path traversal successful with ID {test_id}',
                        f'Endpoint: {endpoint}, ID: {test_id}',
                        'Implement input validation and proper file access controls'
                    )
        
        except Exception as e:
            pass
    
    def test_session_fixation(self):
        """Test for session fixation vulnerabilities."""
        print("\n🔍 TESTING SESSION FIXATION")
        print("-" * 50)
        
        # Create a session and get initial session ID
        test_session = requests.Session()
        
        try:
            # Get initial session
            response = test_session.get(urljoin(self.base_url, '/admin_login'))
            initial_cookies = dict(test_session.cookies)
            
            # Login
            login_response = test_session.post(
                urljoin(self.base_url, '/admin_login'),
                data={'username': 'headteacher', 'password': 'admin123'}
            )
            
            # Check if session ID changed after login
            post_login_cookies = dict(test_session.cookies)
            
            session_changed = False
            for cookie_name in initial_cookies:
                if cookie_name in post_login_cookies:
                    if initial_cookies[cookie_name] != post_login_cookies[cookie_name]:
                        session_changed = True
                        break
            
            if not session_changed:
                self.log_vulnerability(
                    'MEDIUM',
                    'Session Fixation Vulnerability',
                    'Session ID does not change after successful authentication',
                    'Session ID remains the same before and after login',
                    'Regenerate session ID after successful authentication'
                )
        
        except Exception as e:
            print(f"Session fixation test error: {e}")
    
    def run_all_access_control_tests(self):
        """Run all access control tests."""
        print("🔍 STARTING ACCESS CONTROL TESTING")
        print("=" * 60)
        
        self.create_user_sessions()
        
        if self.user_sessions:
            self.test_unauthenticated_access()
            self.test_horizontal_privilege_escalation()
            self.test_vertical_privilege_escalation()
            self.test_direct_object_references()
            self.test_session_fixation()
        else:
            print("❌ No user sessions created, skipping access control tests")
        
        print(f"\n📊 ACCESS CONTROL TESTING COMPLETE")
        print(f"Vulnerabilities found: {len(self.vulnerabilities)}")
        
        return self.vulnerabilities
