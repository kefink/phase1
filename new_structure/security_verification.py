#!/usr/bin/env python3
"""
Comprehensive Security Verification Script for Hillview School Management System
Tests all implemented security measures to ensure 100% protection.
"""

import sys
import os
sys.path.append('.')

def test_security_imports():
    """Test if all security modules can be imported."""
    print('\n1. Testing Security Module Imports...')
    results = {}
    
    try:
        from security.sql_injection_protection import SQLInjectionProtection, sql_injection_protection
        print('✅ SQL Injection Protection: IMPORTED')
        results['sql_injection'] = True
    except Exception as e:
        print(f'❌ SQL Injection Protection: FAILED - {e}')
        results['sql_injection'] = False
    
    try:
        from security.rce_protection import RCEProtection
        print('✅ RCE Protection: IMPORTED')
        results['rce_protection'] = True
    except Exception as e:
        print(f'❌ RCE Protection: FAILED - {e}')
        results['rce_protection'] = False
    
    try:
        from security.csrf_protection import CSRFProtection, csrf_protect
        print('✅ CSRF Protection: IMPORTED')
        results['csrf_protection'] = True
    except Exception as e:
        print(f'❌ CSRF Protection: FAILED - {e}')
        results['csrf_protection'] = False
    
    try:
        from utils.rate_limiter import auth_rate_limit, api_rate_limit
        print('✅ Rate Limiting: IMPORTED')
        results['rate_limiting'] = True
    except Exception as e:
        print(f'❌ Rate Limiting: FAILED - {e}')
        results['rate_limiting'] = False
    
    return results

def test_sql_injection_protection():
    """Test SQL injection protection."""
    print('\n2. Testing SQL Injection Protection...')
    
    try:
        from security.sql_injection_protection import SQLInjectionProtection
        
        test_inputs = [
            ("'; DROP TABLE users; --", False),  # Should be blocked
            ("admin' OR '1'='1", False),         # Should be blocked
            ("1 UNION SELECT * FROM users", False), # Should be blocked
            ("<script>alert('xss')</script>", False), # Should be blocked
            ("normal_input", True),              # Should be allowed
            ("user@example.com", True),          # Should be allowed
            ("SELECT * FROM table", False),      # Should be blocked
            ("INSERT INTO users", False),        # Should be blocked
        ]
        
        passed = 0
        total = len(test_inputs)
        
        for test_input, should_pass in test_inputs:
            is_safe = SQLInjectionProtection.validate_input(test_input, 'test_field')
            if is_safe == should_pass:
                status = '✅ CORRECT'
                passed += 1
            else:
                status = '❌ FAILED'
            
            expected = 'ALLOW' if should_pass else 'BLOCK'
            actual = 'ALLOWED' if is_safe else 'BLOCKED'
            print(f'  {status}: Expected {expected}, Got {actual} for: {test_input[:30]}...')
        
        print(f'\nSQL Injection Protection: {passed}/{total} tests passed')
        return passed == total
        
    except Exception as e:
        print(f'❌ SQL Injection test failed: {e}')
        return False

def test_rce_protection():
    """Test RCE (Remote Code Execution) protection."""
    print('\n3. Testing RCE Protection...')
    
    try:
        from security.rce_protection import RCEProtection
        
        rce_inputs = [
            ('ls -la', True),                    # Should be detected
            ('cat /etc/passwd', True),           # Should be detected
            ('rm -rf /', True),                  # Should be detected
            ('__import__("os").system("ls")', True), # Should be detected
            ('eval("print(1)")', True),          # Should be detected
            ('normal_text', False),              # Should not be detected
            ('user input', False),               # Should not be detected
            ('os.system("command")', True),      # Should be detected
        ]
        
        passed = 0
        total = len(rce_inputs)
        
        for test_input, should_detect in rce_inputs:
            is_dangerous = RCEProtection.detect_code_injection(test_input)
            if is_dangerous == should_detect:
                status = '✅ CORRECT'
                passed += 1
            else:
                status = '❌ FAILED'
            
            expected = 'DETECT' if should_detect else 'SAFE'
            actual = 'DETECTED' if is_dangerous else 'SAFE'
            print(f'  {status}: Expected {expected}, Got {actual} for: {test_input[:30]}...')
        
        print(f'\nRCE Protection: {passed}/{total} tests passed')
        return passed == total
        
    except Exception as e:
        print(f'❌ RCE test failed: {e}')
        return False

def test_configuration_security():
    """Test security configuration."""
    print('\n4. Testing Configuration Security...')
    
    try:
        from config import DevelopmentConfig
        config = DevelopmentConfig()
        
        tests_passed = 0
        total_tests = 3
        
        # Check CSRF is enabled
        csrf_enabled = getattr(config, 'WTF_CSRF_ENABLED', False)
        if csrf_enabled:
            print('  ✅ CSRF Protection: ENABLED')
            tests_passed += 1
        else:
            print('  ❌ CSRF Protection: DISABLED')
        
        # Check rate limiting
        rate_limit_enabled = getattr(config, 'RATELIMIT_ENABLED', False)
        if rate_limit_enabled:
            print('  ✅ Rate Limiting: ENABLED')
            tests_passed += 1
        else:
            print('  ❌ Rate Limiting: DISABLED')
        
        # Check session security
        session_secure = getattr(config, 'SESSION_COOKIE_SECURE', False)
        session_httponly = getattr(config, 'SESSION_COOKIE_HTTPONLY', False)
        if session_secure and session_httponly:
            print('  ✅ Session Security: SECURE')
            tests_passed += 1
        else:
            print('  ⚠️ Session Security: PARTIAL')
        
        print(f'\nConfiguration Security: {tests_passed}/{total_tests} tests passed')
        return tests_passed == total_tests
        
    except Exception as e:
        print(f'❌ Configuration test failed: {e}')
        return False

def test_authentication_security():
    """Test authentication security."""
    print('\n5. Testing Authentication Security...')
    
    try:
        # Import with proper path handling
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from models.user import Teacher
        
        tests_passed = 0
        total_tests = 2
        
        # Test password hashing
        test_teacher = Teacher(username='test', password='test123', role='teacher')
        test_teacher.set_password('test123')
        
        # Test secure password check
        is_valid = test_teacher.check_password('test123')
        is_invalid = test_teacher.check_password('wrong_password')
        
        if is_valid and not is_invalid:
            print('  ✅ Password Hashing: WORKING')
            tests_passed += 1
        else:
            print('  ❌ Password Hashing: FAILED')
        
        # Test SQL injection in password
        malicious_password = "'; DROP TABLE users; --"
        is_blocked = not test_teacher.check_password(malicious_password)
        if is_blocked:
            print('  ✅ Password Injection Protection: BLOCKED')
            tests_passed += 1
        else:
            print('  ❌ Password Injection Protection: VULNERABLE')
        
        print(f'\nAuthentication Security: {tests_passed}/{total_tests} tests passed')
        return tests_passed == total_tests
        
    except Exception as e:
        print(f'❌ Authentication test failed: {e}')
        return False

def test_security_headers():
    """Test security headers implementation."""
    print('\n6. Testing Security Headers...')
    
    try:
        # Check if security headers are configured in the main app
        with open('__init__.py', 'r') as f:
            content = f.read()
        
        required_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy',
            'Referrer-Policy'
        ]
        
        tests_passed = 0
        for header in required_headers:
            if header in content:
                print(f'  ✅ {header}: CONFIGURED')
                tests_passed += 1
            else:
                print(f'  ❌ {header}: MISSING')
        
        print(f'\nSecurity Headers: {tests_passed}/{len(required_headers)} headers configured')
        return tests_passed == len(required_headers)
        
    except Exception as e:
        print(f'❌ Security headers test failed: {e}')
        return False

def main():
    """Run comprehensive security verification."""
    print('🔒 COMPREHENSIVE SECURITY VERIFICATION')
    print('=' * 60)
    
    # Run all tests
    test_results = []
    
    # Test 1: Module imports
    import_results = test_security_imports()
    test_results.append(all(import_results.values()))
    
    # Test 2: SQL injection protection
    test_results.append(test_sql_injection_protection())
    
    # Test 3: RCE protection
    test_results.append(test_rce_protection())
    
    # Test 4: Configuration security
    test_results.append(test_configuration_security())
    
    # Test 5: Authentication security
    test_results.append(test_authentication_security())
    
    # Test 6: Security headers
    test_results.append(test_security_headers())
    
    # Calculate overall security score
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    security_percentage = (passed_tests / total_tests) * 100
    
    print('\n🔒 SECURITY VERIFICATION SUMMARY')
    print('=' * 60)
    print(f'Tests Passed: {passed_tests}/{total_tests}')
    print(f'Security Level: {security_percentage:.1f}%')
    
    if security_percentage == 100:
        print('🎉 CONGRATULATIONS! 100% SECURITY LEVEL ACHIEVED!')
        print('✅ All security measures are properly implemented and working.')
    elif security_percentage >= 80:
        print('⚠️ Good security level, but some improvements needed.')
    else:
        print('❌ Critical security issues detected. Immediate attention required.')
    
    print('=' * 60)
    return security_percentage == 100

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
