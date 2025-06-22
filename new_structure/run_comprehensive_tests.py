"""
Comprehensive Testing Runner for Hillview School Management System
This script runs all types of tests and generates comprehensive reports.

USAGE:
    python run_comprehensive_tests.py --all
    python run_comprehensive_tests.py --security
    python run_comprehensive_tests.py --api
    python run_comprehensive_tests.py --e2e
    python run_comprehensive_tests.py --performance
"""

import subprocess
import sys
import argparse
import time
from datetime import datetime
from pathlib import Path

class ComprehensiveTestRunner:
    """Run comprehensive tests for Hillview School Management System."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {}
        self.start_time = datetime.now()
    
    def run_security_tests(self):
        """Run comprehensive security tests."""
        print("\n🔒 RUNNING SECURITY TESTS")
        print("=" * 50)
        
        try:
            # Run our custom security testing framework
            result = subprocess.run([
                sys.executable, 'security_testing/comprehensive_security_test.py'
            ], cwd=self.project_root, capture_output=True, text=True, timeout=600)
            
            self.test_results['security'] = {
                'status': 'PASSED' if result.returncode == 0 else 'FAILED',
                'output': result.stdout,
                'errors': result.stderr,
                'duration': time.time()
            }
            
            if result.returncode == 0:
                print("✅ Security tests PASSED")
            else:
                print("❌ Security tests FAILED")
                print(f"Error: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ Security tests TIMEOUT")
            self.test_results['security'] = {'status': 'TIMEOUT'}
            return False
        except Exception as e:
            print(f"❌ Security tests ERROR: {e}")
            self.test_results['security'] = {'status': 'ERROR', 'error': str(e)}
            return False
    
    def run_api_tests(self):
        """Run API integration tests."""
        print("\n🔧 RUNNING API TESTS")
        print("=" * 50)
        
        try:
            # Run pytest for API tests
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                'testing_framework/api_tests/',
                '-v', '--tb=short',
                '--cov=new_structure',
                '--cov-report=html:testing_framework/reports/api_coverage',
                '--html=testing_framework/reports/api_report.html',
                '--self-contained-html'
            ], cwd=self.project_root, capture_output=True, text=True, timeout=300)
            
            self.test_results['api'] = {
                'status': 'PASSED' if result.returncode == 0 else 'FAILED',
                'output': result.stdout,
                'errors': result.stderr
            }
            
            if result.returncode == 0:
                print("✅ API tests PASSED")
            else:
                print("❌ API tests FAILED")
                print(f"Output: {result.stdout}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ API tests TIMEOUT")
            self.test_results['api'] = {'status': 'TIMEOUT'}
            return False
        except Exception as e:
            print(f"❌ API tests ERROR: {e}")
            self.test_results['api'] = {'status': 'ERROR', 'error': str(e)}
            return False
    
    def run_e2e_tests(self):
        """Run end-to-end tests."""
        print("\n🎭 RUNNING E2E TESTS")
        print("=" * 50)
        
        try:
            # Check if application is running
            health_check = subprocess.run([
                'curl', '-s', 'http://localhost:5000/health'
            ], capture_output=True, text=True, timeout=5)
            
            if health_check.returncode != 0:
                print("⚠️ Application not running, starting it...")
                # Start application in background
                app_process = subprocess.Popen([
                    sys.executable, 'run.py'
                ], cwd=self.project_root)
                time.sleep(5)  # Wait for app to start
            
            # Run E2E tests
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                'testing_framework/e2e_tests/',
                '-v', '--tb=short',
                '--html=testing_framework/reports/e2e_report.html',
                '--self-contained-html'
            ], cwd=self.project_root, capture_output=True, text=True, timeout=600)
            
            self.test_results['e2e'] = {
                'status': 'PASSED' if result.returncode == 0 else 'FAILED',
                'output': result.stdout,
                'errors': result.stderr
            }
            
            if result.returncode == 0:
                print("✅ E2E tests PASSED")
            else:
                print("❌ E2E tests FAILED")
                print(f"Output: {result.stdout}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ E2E tests TIMEOUT")
            self.test_results['e2e'] = {'status': 'TIMEOUT'}
            return False
        except Exception as e:
            print(f"❌ E2E tests ERROR: {e}")
            self.test_results['e2e'] = {'status': 'ERROR', 'error': str(e)}
            return False
    
    def run_performance_tests(self):
        """Run performance tests."""
        print("\n⚡ RUNNING PERFORMANCE TESTS")
        print("=" * 50)
        
        try:
            # Simple performance test using curl
            print("🔍 Testing response times...")
            
            endpoints = [
                '/',
                '/health',
                '/admin_login',
                '/classteacher_login',
                '/teacher_login'
            ]
            
            performance_results = {}
            
            for endpoint in endpoints:
                start_time = time.time()
                result = subprocess.run([
                    'curl', '-s', '-w', '%{time_total}',
                    f'http://localhost:5000{endpoint}'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    response_time = float(result.stderr.strip()) if result.stderr.strip() else 0
                    performance_results[endpoint] = response_time
                    print(f"  {endpoint}: {response_time:.3f}s")
                else:
                    performance_results[endpoint] = 'FAILED'
                    print(f"  {endpoint}: FAILED")
            
            # Check if all response times are under 2 seconds
            all_passed = all(
                isinstance(time, float) and time < 2.0 
                for time in performance_results.values()
            )
            
            self.test_results['performance'] = {
                'status': 'PASSED' if all_passed else 'FAILED',
                'results': performance_results
            }
            
            if all_passed:
                print("✅ Performance tests PASSED")
            else:
                print("❌ Performance tests FAILED")
            
            return all_passed
            
        except Exception as e:
            print(f"❌ Performance tests ERROR: {e}")
            self.test_results['performance'] = {'status': 'ERROR', 'error': str(e)}
            return False
    
    def run_database_tests(self):
        """Run database tests."""
        print("\n🗄️ RUNNING DATABASE TESTS")
        print("=" * 50)
        
        try:
            # Run pytest for database tests
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                'testing_framework/database_tests/',
                '-v', '--tb=short',
                '--html=testing_framework/reports/database_report.html',
                '--self-contained-html'
            ], cwd=self.project_root, capture_output=True, text=True, timeout=300)
            
            self.test_results['database'] = {
                'status': 'PASSED' if result.returncode == 0 else 'FAILED',
                'output': result.stdout,
                'errors': result.stderr
            }
            
            if result.returncode == 0:
                print("✅ Database tests PASSED")
            else:
                print("❌ Database tests FAILED")
                print(f"Output: {result.stdout}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ Database tests TIMEOUT")
            self.test_results['database'] = {'status': 'TIMEOUT'}
            return False
        except Exception as e:
            print(f"❌ Database tests ERROR: {e}")
            self.test_results['database'] = {'status': 'ERROR', 'error': str(e)}
            return False
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report."""
        print("\n📊 GENERATING COMPREHENSIVE REPORT")
        print("=" * 50)
        
        end_time = datetime.now()
        total_duration = end_time - self.start_time
        
        # Count results
        passed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'PASSED')
        failed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'FAILED')
        error_tests = sum(1 for result in self.test_results.values() if result.get('status') in ['ERROR', 'TIMEOUT'])
        total_tests = len(self.test_results)
        
        # Generate report
        report = f"""
# 🧪 HILLVIEW COMPREHENSIVE TEST REPORT

**Date:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
**Duration:** {total_duration}
**Total Test Suites:** {total_tests}

## 📊 TEST RESULTS SUMMARY

| Test Suite | Status | Details |
|------------|--------|---------|
"""
        
        for test_name, result in self.test_results.items():
            status = result.get('status', 'UNKNOWN')
            emoji = '✅' if status == 'PASSED' else '❌' if status == 'FAILED' else '⚠️'
            report += f"| {test_name.title()} | {emoji} {status} | - |\n"
        
        report += f"""
## 🎯 OVERALL RESULTS

- ✅ **Passed:** {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)
- ❌ **Failed:** {failed_tests}/{total_tests} ({(failed_tests/total_tests)*100:.1f}%)
- ⚠️ **Errors:** {error_tests}/{total_tests} ({(error_tests/total_tests)*100:.1f}%)

## 📋 DETAILED REPORTS

- 🔒 **Security Report:** `security_testing/security_report_*.json`
- 🔧 **API Report:** `testing_framework/reports/api_report.html`
- 🎭 **E2E Report:** `testing_framework/reports/e2e_report.html`
- 🗄️ **Database Report:** `testing_framework/reports/database_report.html`
- 📊 **Coverage Report:** `testing_framework/reports/api_coverage/index.html`

## 🚀 NEXT STEPS

"""
        
        if passed_tests == total_tests:
            report += "🎉 **ALL TESTS PASSED!** Your system is ready for production.\n"
        else:
            report += f"🔧 **{failed_tests + error_tests} test suites need attention.** Review the detailed reports above.\n"
        
        # Save report
        report_file = self.project_root / 'testing_framework' / 'reports' / f'comprehensive_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report, encoding='utf-8')
        
        print(f"📄 Report saved to: {report_file}")
        print(report)
        
        return passed_tests == total_tests
    
    def run_all_tests(self):
        """Run all test suites."""
        print("🚀 RUNNING COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print(f"Start time: {self.start_time}")
        
        test_suites = [
            ("Security Tests", self.run_security_tests),
            ("API Tests", self.run_api_tests),
            ("Database Tests", self.run_database_tests),
            ("E2E Tests", self.run_e2e_tests),
            ("Performance Tests", self.run_performance_tests)
        ]
        
        all_passed = True
        
        for suite_name, test_func in test_suites:
            print(f"\n🔄 Running {suite_name}...")
            try:
                result = test_func()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ {suite_name} failed with error: {e}")
                all_passed = False
        
        # Generate comprehensive report
        self.generate_comprehensive_report()
        
        return all_passed

def main():
    """Main function to run tests based on command line arguments."""
    parser = argparse.ArgumentParser(description='Run comprehensive tests for Hillview School Management System')
    parser.add_argument('--all', action='store_true', help='Run all test suites')
    parser.add_argument('--security', action='store_true', help='Run security tests only')
    parser.add_argument('--api', action='store_true', help='Run API tests only')
    parser.add_argument('--e2e', action='store_true', help='Run E2E tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--database', action='store_true', help='Run database tests only')
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    if args.all or not any([args.security, args.api, args.e2e, args.performance, args.database]):
        success = runner.run_all_tests()
    else:
        success = True
        if args.security:
            success &= runner.run_security_tests()
        if args.api:
            success &= runner.run_api_tests()
        if args.database:
            success &= runner.run_database_tests()
        if args.e2e:
            success &= runner.run_e2e_tests()
        if args.performance:
            success &= runner.run_performance_tests()
        
        runner.generate_comprehensive_report()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
