#!/usr/bin/env python3
"""
Quick Security Check for 100% Rating Target
"""
import os
from pathlib import Path

def check_security_100():
    """Quick check of implemented security measures."""
    print("🔐 Security Check - Targeting 100% Rating")
    print("=" * 50)
    
    score = 100.0
    checks_passed = 0
    total_checks = 0
    
    # Check 1: Security Headers
    print("🛡️ Checking Security Headers...")
    init_path = Path('__init__.py')
    if init_path.exists():
        try:
            with open(init_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            headers = ['X-Frame-Options', 'X-Content-Type-Options', 'X-XSS-Protection', 
                      'Strict-Transport-Security', 'Referrer-Policy', 'Permissions-Policy',
                      'Content-Security-Policy']
            
            for header in headers:
                total_checks += 1
                if header in content:
                    print(f"  ✅ {header} implemented")
                    checks_passed += 1
                else:
                    print(f"  ❌ {header} missing")
                    score -= 3
        except:
            print("  ❌ Could not read __init__.py")
            score -= 10
    
    # Check 2: Error Handlers
    print("\n⚠️ Checking Error Handlers...")
    error_codes = ['400', '401', '403', '404', '405', '429', '500']
    for code in error_codes:
        total_checks += 1
        if f"@app.errorhandler({code})" in content:
            print(f"  ✅ Error handler {code} implemented")
            checks_passed += 1
        else:
            print(f"  ❌ Error handler {code} missing")
            score -= 2
    
    # Check 3: PDF Security
    print("\n📄 Checking PDF Security...")
    classteacher_path = Path('views/classteacher.py')
    if classteacher_path.exists():
        try:
            with open(classteacher_path, 'r', encoding='utf-8', errors='ignore') as f:
                pdf_content = f.read()
            
            pdf_checks = ['sanitize_html_for_pdf', 'secure_pdf_generation']
            for check in pdf_checks:
                total_checks += 1
                if check in pdf_content:
                    print(f"  ✅ {check} implemented")
                    checks_passed += 1
                else:
                    print(f"  ❌ {check} missing")
                    score -= 5
        except:
            print("  ❌ Could not read classteacher.py")
            score -= 5
    
    # Check 4: File Upload Security
    print("\n📁 Checking File Upload Security...")
    upload_security_path = Path('security/file_upload_security.py')
    if upload_security_path.exists():
        try:
            with open(upload_security_path, 'r', encoding='utf-8', errors='ignore') as f:
                upload_content = f.read()
            
            upload_checks = ['DANGEROUS_SIGNATURES', 'MALICIOUS_PATTERNS']
            for check in upload_checks:
                total_checks += 1
                if check in upload_content:
                    print(f"  ✅ {check} implemented")
                    checks_passed += 1
                else:
                    print(f"  ❌ {check} missing")
                    score -= 5
        except:
            print("  ❌ Could not read file_upload_security.py")
            score -= 5
    
    # Check 5: Security Logging
    print("\n📋 Checking Security Logging...")
    logging_path = Path('logging_config.py')
    if logging_path.exists():
        try:
            with open(logging_path, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()
            
            log_checks = ['security.log', 'SensitiveDataFilter']
            for check in log_checks:
                total_checks += 1
                if check in log_content:
                    print(f"  ✅ {check} implemented")
                    checks_passed += 1
                else:
                    print(f"  ❌ {check} missing")
                    score -= 3
        except:
            print("  ❌ Could not read logging_config.py")
            score -= 3
    
    # Check 6: Debug Route Protection
    print("\n🐛 Checking Debug Route Protection...")
    total_checks += 1
    if "config_name in ['development', 'testing']" in content:
        print("  ✅ Debug routes properly restricted")
        checks_passed += 1
    else:
        print("  ❌ Debug routes not properly restricted")
        score -= 5
    
    # Final Results
    score = max(0, score)
    if score >= 95:
        grade = 'A+'
        status = "🏆 TARGET ACHIEVED!"
    elif score >= 90:
        grade = 'A'
        status = "⭐ EXCELLENT!"
    elif score >= 85:
        grade = 'B+'
        status = "👍 VERY GOOD"
    else:
        grade = 'B'
        status = "📈 GOOD PROGRESS"
    
    print(f"\n🎯 SECURITY RATING: {score:.1f}/100 (Grade: {grade})")
    print(f"Checks Passed: {checks_passed}/{total_checks}")
    print(f"Status: {status}")
    
    return score >= 95

if __name__ == '__main__':
    success = check_security_100()
    exit(0 if success else 1)