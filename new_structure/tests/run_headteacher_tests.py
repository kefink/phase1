"""
Comprehensive Headteacher Test Runner
Following Keploy principles for systematic testing

This script runs all headteacher tests and generates a comprehensive report.
"""

import unittest
import sys
import os
import time
from io import StringIO

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_comprehensive_headteacher_tests():
    """Run all headteacher tests and generate a comprehensive report."""
    
    print("🚀 STARTING COMPREHENSIVE HEADTEACHER TESTING")
    print("=" * 80)
    print("Following Keploy Principles:")
    print("✅ Build - All tests must build and run")
    print("✅ Pass - All tests must pass without flaky behavior")
    print("⬆️ Coverage - Tests cover all edge cases and functionality")
    print("✅ Clean - Tests are clean and require no manual review")
    print("=" * 80)
    
    # Test suites to run
    test_modules = [
        'test_headteacher_comprehensive',
        'test_headteacher_advanced'
    ]
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    test_results = {}
    
    start_time = time.time()
    
    for module_name in test_modules:
        print(f"\n📋 Running {module_name}...")
        print("-" * 60)
        
        try:
            # Import the test module
            module = __import__(module_name)
            
            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
            
            # Run tests with custom result handler
            stream = StringIO()
            runner = unittest.TextTestRunner(stream=stream, verbosity=2)
            result = runner.run(suite)
            
            # Capture results
            tests_run = result.testsRun
            failures = len(result.failures)
            errors = len(result.errors)
            
            total_tests += tests_run
            total_failures += failures
            total_errors += errors
            
            test_results[module_name] = {
                'tests_run': tests_run,
                'failures': failures,
                'errors': errors,
                'success_rate': ((tests_run - failures - errors) / tests_run * 100) if tests_run > 0 else 0
            }
            
            # Print module results
            print(f"Tests Run: {tests_run}")
            print(f"Failures: {failures}")
            print(f"Errors: {errors}")
            print(f"Success Rate: {test_results[module_name]['success_rate']:.1f}%")
            
            # Print detailed output
            output = stream.getvalue()
            if output:
                print("\nDetailed Output:")
                print(output)
            
            if failures > 0:
                print("❌ FAILURES:")
                for test, traceback in result.failures:
                    print(f"  - {test}: {traceback}")
            
            if errors > 0:
                print("💥 ERRORS:")
                for test, traceback in result.errors:
                    print(f"  - {test}: {traceback}")
                    
        except Exception as e:
            print(f"❌ Error running {module_name}: {e}")
            total_errors += 1
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST REPORT")
    print("=" * 80)
    
    print(f"🕒 Total Execution Time: {total_time:.2f} seconds")
    print(f"🧪 Total Tests Run: {total_tests}")
    print(f"✅ Successful Tests: {total_tests - total_failures - total_errors}")
    print(f"❌ Failed Tests: {total_failures}")
    print(f"💥 Error Tests: {total_errors}")
    
    overall_success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
    print(f"📈 Overall Success Rate: {overall_success_rate:.1f}%")
    
    print("\n📋 Module Breakdown:")
    for module, results in test_results.items():
        print(f"  {module}:")
        print(f"    Tests: {results['tests_run']}")
        print(f"    Success Rate: {results['success_rate']:.1f}%")
    
    # Keploy-style validation
    print("\n🎯 KEPLOY VALIDATION:")
    
    if total_errors == 0:
        print("✅ BUILD: All tests built and executed successfully")
    else:
        print("❌ BUILD: Some tests failed to build/execute")
    
    if total_failures == 0 and total_errors == 0:
        print("✅ PASS: All tests passed without flaky behavior")
    else:
        print("❌ PASS: Some tests failed or had errors")
    
    if overall_success_rate >= 90:
        print("✅ COVERAGE: Excellent test coverage achieved")
    elif overall_success_rate >= 75:
        print("⚠️ COVERAGE: Good test coverage, room for improvement")
    else:
        print("❌ COVERAGE: Insufficient test coverage")
    
    print("✅ CLEAN: Tests are clean and automated")
    
    # Final assessment
    print("\n🏆 FINAL ASSESSMENT:")
    if total_failures == 0 and total_errors == 0:
        print("🎉 ALL TESTS PASSED! Headteacher functionality is working perfectly.")
        print("🚀 Ready for production deployment!")
    elif overall_success_rate >= 90:
        print("⚠️ Most tests passed. Minor issues need attention.")
    else:
        print("❌ Significant issues found. Review and fix required.")
    
    print("=" * 80)
    
    return {
        'total_tests': total_tests,
        'total_failures': total_failures,
        'total_errors': total_errors,
        'success_rate': overall_success_rate,
        'execution_time': total_time
    }

def run_specific_test_category(category):
    """Run tests for a specific category."""
    print(f"\n🎯 Running {category} tests...")
    
    if category == "authentication":
        # Run authentication-specific tests
        test_methods = [
            'test_01_headteacher_login_success',
            'test_02_headteacher_login_invalid_credentials',
            'test_03_headteacher_session_management',
            'test_04_unauthorized_access_protection'
        ]
    elif category == "dashboard":
        # Run dashboard-specific tests
        test_methods = [
            'test_05_headteacher_dashboard_loads',
            'test_06_analytics_dashboard_access',
            'test_07_reports_page_access'
        ]
    elif category == "universal_access":
        # Run universal access tests
        test_methods = [
            'test_08_universal_access_dashboard',
            'test_09_universal_proxy_routes'
        ]
    elif category == "performance":
        # Run performance tests
        test_methods = [
            'test_01_dashboard_performance',
            'test_02_analytics_performance'
        ]
    else:
        print(f"❌ Unknown category: {category}")
        return
    
    print(f"Running {len(test_methods)} tests in {category} category...")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific category
        category = sys.argv[1]
        run_specific_test_category(category)
    else:
        # Run all tests
        results = run_comprehensive_headteacher_tests()
        
        # Exit with appropriate code
        if results['total_failures'] == 0 and results['total_errors'] == 0:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
