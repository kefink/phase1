#!/usr/bin/env python3
"""
Comprehensive Security Testing Suite for Hillview School Management System
Tests all security features including authentication, authorization, input validation, and more.
"""

import sys
import os
import requests
import json
import time
from datetime import datetime
from urllib.parse import urljoin

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SecurityTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'authentication': [],
            'authorization': [],
            'input_validation': [],
            'csrf_protection': [],
            'security_headers': [],
            'file_upload': [],
            'path_traversal': []
        }
        self.test_credentials = {
            'headteacher': {'username': 'headteacher', 'password': 'admin123'},
            'invalid': {'username': 'invalid_user', 'password': 'wrong_password'}
        }
    
    def log_test(self, category, test_name, status, details=""):
        """Log test result"""
        result = {
            'test_name': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results[category].append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {category.upper()}: {test_name} - {status}")
        if details:
            print(f"   Details: {details}")
    
    def test_authentication_security(self):
        """Test authentication and session security"""
        print("\n🔐 TESTING AUTHENTICATION & SESSION SECURITY")
        print("=" * 60)
        
        # Test 1: Valid login
        try:
            response = self.session.post(
                urljoin(self.base_url, '/admin_login'),
                data=self.test_credentials['headteacher'],
                allow_redirects=False
            )
            if response.status_code in [200, 302]:
                self.log_test('authentication', 'Valid Login', 'PASS', 
                            f"Status: {response.status_code}")
            else:
                self.log_test('authentication', 'Valid Login', 'FAIL', 
                            f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test('authentication', 'Valid Login', 'ERROR', str(e))
        
        # Test 2: Invalid login
        try:
            response = self.session.post(
                urljoin(self.base_url, '/admin_login'),
                data=self.test_credentials['invalid'],
                allow_redirects=False
            )
            if response.status_code in [200, 401, 403]:
                self.log_test('authentication', 'Invalid Login Rejection', 'PASS',
                            f"Properly rejected with status: {response.status_code}")
            else:
                self.log_test('authentication', 'Invalid Login Rejection', 'FAIL',
                            f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test('authentication', 'Invalid Login Rejection', 'ERROR', str(e))
        
        # Test 3: SQL Injection in login
        try:
            sql_payloads = [
                "admin' OR '1'='1",
                "admin'; DROP TABLE teacher; --",
                "admin' UNION SELECT * FROM teacher --"
            ]
            for payload in sql_payloads:
                response = self.session.post(
                    urljoin(self.base_url, '/admin_login'),
                    data={'username': payload, 'password': 'test'},
                    allow_redirects=False
                )
                if response.status_code not in [200, 302]:
                    self.log_test('authentication', f'SQL Injection Protection ({payload[:20]}...)', 'PASS',
                                "SQL injection attempt blocked")
                else:
                    self.log_test('authentication', f'SQL Injection Protection ({payload[:20]}...)', 'FAIL',
                                "SQL injection may have succeeded")
        except Exception as e:
            self.log_test('authentication', 'SQL Injection Protection', 'ERROR', str(e))
        
        # Test 4: Session security headers
        try:
            response = self.session.get(urljoin(self.base_url, '/'))
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options', 
                'X-XSS-Protection',
                'Strict-Transport-Security',
                'Content-Security-Policy'
            ]
            
            missing_headers = []
            for header in security_headers:
                if header not in response.headers:
                    missing_headers.append(header)
            
            if not missing_headers:
                self.log_test('authentication', 'Security Headers Present', 'PASS',
                            "All security headers found")
            else:
                self.log_test('authentication', 'Security Headers Present', 'FAIL',
                            f"Missing headers: {', '.join(missing_headers)}")
        except Exception as e:
            self.log_test('authentication', 'Security Headers Present', 'ERROR', str(e))
    
    def test_authorization_security(self):
        """Test access control and authorization"""
        print("\n🛡️ TESTING ACCESS CONTROL & AUTHORIZATION")
        print("=" * 60)
        
        # First login as headteacher
        try:
            login_response = self.session.post(
                urljoin(self.base_url, '/admin_login'),
                data=self.test_credentials['headteacher']
            )
        except:
            pass
        
        # Test 1: Access to protected routes without authentication
        protected_routes = [
            '/headteacher/',
            '/classteacher/',
            '/teacher/',
            '/manage_students',
            '/manage_teachers'
        ]
        
        # Create new session without authentication
        unauth_session = requests.Session()
        
        for route in protected_routes:
            try:
                response = unauth_session.get(urljoin(self.base_url, route), allow_redirects=False)
                if response.status_code in [401, 403, 302]:
                    self.log_test('authorization', f'Unauthorized Access Block ({route})', 'PASS',
                                f"Access denied with status: {response.status_code}")
                else:
                    self.log_test('authorization', f'Unauthorized Access Block ({route})', 'FAIL',
                                f"Unexpected access granted: {response.status_code}")
            except Exception as e:
                self.log_test('authorization', f'Unauthorized Access Block ({route})', 'ERROR', str(e))
        
        # Test 2: Role-based access control
        try:
            # Test headteacher access to admin functions
            response = self.session.get(urljoin(self.base_url, '/headteacher/'))
            if response.status_code == 200:
                self.log_test('authorization', 'Headteacher Role Access', 'PASS',
                            "Headteacher can access admin functions")
            else:
                self.log_test('authorization', 'Headteacher Role Access', 'FAIL',
                            f"Headteacher access denied: {response.status_code}")
        except Exception as e:
            self.log_test('authorization', 'Headteacher Role Access', 'ERROR', str(e))
    
    def test_input_validation_security(self):
        """Test input validation and injection protection"""
        print("\n🔍 TESTING INPUT VALIDATION & INJECTION PROTECTION")
        print("=" * 60)
        
        # Login first
        try:
            self.session.post(
                urljoin(self.base_url, '/admin_login'),
                data=self.test_credentials['headteacher']
            )
        except:
            pass
        
        # Test 1: XSS Protection
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        for payload in xss_payloads:
            try:
                # Test in search or form fields
                response = self.session.get(
                    urljoin(self.base_url, '/manage_students'),
                    params={'search': payload}
                )
                
                # Check if payload is reflected without encoding
                if payload in response.text and '<script>' in response.text:
                    self.log_test('input_validation', f'XSS Protection ({payload[:20]}...)', 'FAIL',
                                "XSS payload may be reflected")
                else:
                    self.log_test('input_validation', f'XSS Protection ({payload[:20]}...)', 'PASS',
                                "XSS payload properly handled")
            except Exception as e:
                self.log_test('input_validation', f'XSS Protection ({payload[:20]}...)', 'ERROR', str(e))
        
        # Test 2: Path traversal protection
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd"
        ]
        
        for payload in path_traversal_payloads:
            try:
                response = self.session.get(
                    urljoin(self.base_url, f'/static/{payload}'),
                    allow_redirects=False
                )
                
                if response.status_code in [403, 404]:
                    self.log_test('input_validation', f'Path Traversal Protection ({payload[:20]}...)', 'PASS',
                                f"Path traversal blocked: {response.status_code}")
                else:
                    self.log_test('input_validation', f'Path Traversal Protection ({payload[:20]}...)', 'FAIL',
                                f"Unexpected response: {response.status_code}")
            except Exception as e:
                self.log_test('input_validation', f'Path Traversal Protection ({payload[:20]}...)', 'ERROR', str(e))
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        print("\n🔒 TESTING CSRF PROTECTION")
        print("=" * 60)
        
        # Login first
        try:
            self.session.post(
                urljoin(self.base_url, '/admin_login'),
                data=self.test_credentials['headteacher']
            )
        except:
            pass
        
        # Test 1: CSRF token presence in forms
        try:
            response = self.session.get(urljoin(self.base_url, '/manage_students'))
            if 'csrf_token' in response.text or 'csrf-token' in response.text:
                self.log_test('csrf_protection', 'CSRF Token Present', 'PASS',
                            "CSRF tokens found in forms")
            else:
                self.log_test('csrf_protection', 'CSRF Token Present', 'WARNING',
                            "CSRF tokens not clearly visible in forms")
        except Exception as e:
            self.log_test('csrf_protection', 'CSRF Token Present', 'ERROR', str(e))
        
        # Test 2: CSRF protection on state-changing operations
        try:
            # Attempt POST without CSRF token
            response = self.session.post(
                urljoin(self.base_url, '/manage_students'),
                data={'student_name': 'Test Student', 'admission_number': 'TEST001'},
                allow_redirects=False
            )
            
            if response.status_code in [403, 400]:
                self.log_test('csrf_protection', 'CSRF Protection Active', 'PASS',
                            f"POST without CSRF token blocked: {response.status_code}")
            else:
                self.log_test('csrf_protection', 'CSRF Protection Active', 'WARNING',
                            f"POST may have succeeded without CSRF: {response.status_code}")
        except Exception as e:
            self.log_test('csrf_protection', 'CSRF Protection Active', 'ERROR', str(e))
    
    def run_all_tests(self):
        """Run all security tests"""
        print("🛡️ HILLVIEW SECURITY TESTING SUITE")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all test categories
        self.test_authentication_security()
        self.test_authorization_security()
        self.test_input_validation_security()
        self.test_csrf_protection()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n📊 SECURITY TEST SUMMARY")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for category, tests in self.results.items():
            if tests:
                print(f"\n{category.upper().replace('_', ' ')}:")
                for test in tests:
                    status_icon = "✅" if test['status'] == "PASS" else "❌" if test['status'] == "FAIL" else "⚠️"
                    print(f"  {status_icon} {test['test_name']}")
                    
                    total_tests += 1
                    if test['status'] == 'PASS':
                        passed_tests += 1
                    elif test['status'] == 'FAIL':
                        failed_tests += 1
                    else:
                        error_tests += 1
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Errors: {error_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        # Save results to file
        with open('security_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: security_test_results.json")

if __name__ == "__main__":
    # Check if application is running
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print("✅ Application is running, starting security tests...")
    except:
        print("❌ Application not running. Please start with: python run.py")
        sys.exit(1)
    
    # Run security tests
    tester = SecurityTester()
    tester.run_all_tests()
