#!/usr/bin/env python3
"""
Comprehensive Test Runner for Student Promotion System
=====================================================

This script runs all tests for the student promotion system and generates
a comprehensive test report covering:
1. Security tests
2. Functionality tests  
3. Integration tests
4. Performance tests
5. Database migration tests

Usage:
    python run_promotion_tests.py [--verbose] [--coverage] [--html-report]
"""

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime
import json

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PromotionTestRunner:
    """Comprehensive test runner for student promotion system."""
    
    def __init__(self, verbose=False, coverage=False, html_report=False):
        self.verbose = verbose
        self.coverage = coverage
        self.html_report = html_report
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_command(self, command, description):
        """Run a command and capture output."""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {command}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if self.verbose or result.returncode != 0:
                print(f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    print(f"STDERR:\n{result.stderr}")
            
            success = result.returncode == 0
            print(f"Result: {'PASSED' if success else 'FAILED'} (Duration: {duration:.2f}s)")
            
            return {
                'success': success,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT: Command exceeded 5 minute limit")
            return {
                'success': False,
                'duration': 300,
                'stdout': '',
                'stderr': 'Command timed out',
                'return_code': -1
            }
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return {
                'success': False,
                'duration': 0,
                'stdout': '',
                'stderr': str(e),
                'return_code': -1
            }
    
    def run_database_migration_test(self):
        """Test database migration script."""
        print(f"\n{'#'*80}")
        print("PHASE 1: DATABASE MIGRATION TESTING")
        print(f"{'#'*80}")
        
        # Test migration script
        migration_command = "python migrations/add_student_promotion_system.py"
        result = self.run_command(
            migration_command,
            "Database Migration Test"
        )
        
        self.test_results['database_migration'] = result
        return result['success']
    
    def run_security_tests(self):
        """Run security-focused tests."""
        print(f"\n{'#'*80}")
        print("PHASE 2: SECURITY TESTING")
        print(f"{'#'*80}")
        
        test_command = "python -m pytest tests/test_student_promotion_security.py -v"
        if self.coverage:
            test_command += " --cov=services.student_promotion_service --cov=views.admin"
        
        result = self.run_command(
            test_command,
            "Security Tests (CSRF, Input Validation, RBAC, Rate Limiting)"
        )
        
        self.test_results['security_tests'] = result
        return result['success']
    
    def run_functionality_tests(self):
        """Run functionality tests."""
        print(f"\n{'#'*80}")
        print("PHASE 3: FUNCTIONALITY TESTING")
        print(f"{'#'*80}")
        
        test_command = "python -m pytest tests/test_student_promotion_functionality.py -v"
        if self.coverage:
            test_command += " --cov=services.student_promotion_service"
        
        result = self.run_command(
            test_command,
            "Functionality Tests (Promotion Logic, History, Statistics)"
        )
        
        self.test_results['functionality_tests'] = result
        return result['success']
    
    def run_integration_tests(self):
        """Run integration tests."""
        print(f"\n{'#'*80}")
        print("PHASE 4: INTEGRATION TESTING")
        print(f"{'#'*80}")
        
        test_command = "python -m pytest tests/test_student_promotion_integration.py -v"
        if self.coverage:
            test_command += " --cov=views.admin"
        
        result = self.run_command(
            test_command,
            "Integration Tests (End-to-End, UI/UX, Database Consistency)"
        )
        
        self.test_results['integration_tests'] = result
        return result['success']
    
    def run_performance_tests(self):
        """Run performance tests with larger datasets."""
        print(f"\n{'#'*80}")
        print("PHASE 5: PERFORMANCE TESTING")
        print(f"{'#'*80}")
        
        # Create performance test script
        perf_test_script = """
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, Student, Grade, Stream
from services.student_promotion_service import StudentPromotionService
from __init__ import create_app

def test_large_dataset_performance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        
        # Create large dataset
        print("Creating large test dataset...")
        grades = []
        for i in range(1, 10):
            grade = Grade(name=f'Grade {i}')
            db.session.add(grade)
            grades.append(grade)
        
        streams = []
        for grade in grades:
            for stream_name in ['A', 'B', 'C', 'D']:
                stream = Stream(name=stream_name, grade=grade)
                db.session.add(stream)
                streams.append(stream)
        
        # Create 1000 students
        students = []
        for i in range(1000):
            grade_idx = i % len(grades)
            stream_idx = i % len(streams)
            student = Student(
                name=f'Student {i}',
                admission_number=f'ADM{i:04d}',
                grade=grades[grade_idx],
                stream=streams[stream_idx % 4 + grade_idx * 4],
                academic_year='2024',
                promotion_status='active'
            )
            db.session.add(student)
            students.append(student)
        
        db.session.commit()
        print(f"Created {len(students)} students across {len(grades)} grades")
        
        # Test preview data generation performance
        print("Testing preview data generation...")
        start_time = time.time()
        preview_data = StudentPromotionService.get_promotion_preview_data()
        preview_time = time.time() - start_time
        print(f"Preview data generation: {preview_time:.2f}s")
        
        # Test bulk promotion performance
        print("Testing bulk promotion performance...")
        promotion_data = {
            'academic_year_to': '2025',
            'students': []
        }
        
        # Promote first 100 students
        for student in students[:100]:
            promotion_data['students'].append({
                'student_id': student.id,
                'action': 'promote',
                'to_grade_id': min(student.grade_id + 1, 9),
                'to_stream_id': student.stream_id,
                'notes': 'Performance test'
            })
        
        start_time = time.time()
        result = StudentPromotionService.process_bulk_promotion(promotion_data, 1)
        bulk_time = time.time() - start_time
        print(f"Bulk promotion (100 students): {bulk_time:.2f}s")
        
        # Test statistics generation performance
        print("Testing statistics generation...")
        start_time = time.time()
        stats = StudentPromotionService.get_promotion_statistics('2025')
        stats_time = time.time() - start_time
        print(f"Statistics generation: {stats_time:.2f}s")
        
        # Performance thresholds
        assert preview_time < 10.0, f"Preview generation too slow: {preview_time:.2f}s"
        assert bulk_time < 30.0, f"Bulk promotion too slow: {bulk_time:.2f}s"
        assert stats_time < 5.0, f"Statistics generation too slow: {stats_time:.2f}s"
        
        print("All performance tests passed!")
        return True

if __name__ == '__main__':
    try:
        test_large_dataset_performance()
        print("PERFORMANCE TESTS: PASSED")
    except Exception as e:
        print(f"PERFORMANCE TESTS: FAILED - {e}")
        sys.exit(1)
"""
        
        # Write and run performance test
        with open('temp_performance_test.py', 'w') as f:
            f.write(perf_test_script)
        
        try:
            result = self.run_command(
                "python temp_performance_test.py",
                "Performance Tests (Large Dataset Handling)"
            )
        finally:
            # Clean up
            if os.path.exists('temp_performance_test.py'):
                os.remove('temp_performance_test.py')
        
        self.test_results['performance_tests'] = result
        return result['success']
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print(f"\n{'#'*80}")
        print("COMPREHENSIVE TEST REPORT")
        print(f"{'#'*80}")
        
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        print(f"Test Run Started: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Run Completed: {datetime.fromtimestamp(self.end_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"\n{'='*60}")
        print("TEST PHASE RESULTS:")
        print(f"{'='*60}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        
        for phase, result in self.test_results.items():
            status = "PASSED" if result['success'] else "FAILED"
            duration = result['duration']
            print(f"{phase.upper().replace('_', ' '):<30} {status:<8} ({duration:.2f}s)")
        
        print(f"\n{'='*60}")
        print(f"OVERALL RESULTS: {passed_tests}/{total_tests} phases passed")
        print(f"SUCCESS RATE: {(passed_tests/total_tests)*100:.1f}%")
        print(f"{'='*60}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Student Promotion System is ready for production.")
            return True
        else:
            print(f"\n❌ {total_tests - passed_tests} test phase(s) failed. Please review and fix issues.")
            return False
    
    def run_all_tests(self):
        """Run all test phases."""
        self.start_time = time.time()
        
        print("Starting Comprehensive Student Promotion System Testing...")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test phases
        phases = [
            ("Database Migration", self.run_database_migration_test),
            ("Security Testing", self.run_security_tests),
            ("Functionality Testing", self.run_functionality_tests),
            ("Integration Testing", self.run_integration_tests),
            ("Performance Testing", self.run_performance_tests)
        ]
        
        for phase_name, phase_func in phases:
            try:
                phase_func()
            except Exception as e:
                print(f"ERROR in {phase_name}: {str(e)}")
                self.test_results[phase_name.lower().replace(' ', '_')] = {
                    'success': False,
                    'duration': 0,
                    'stdout': '',
                    'stderr': str(e),
                    'return_code': -1
                }
        
        self.end_time = time.time()
        
        # Generate final report
        success = self.generate_test_report()
        
        # Generate HTML report if requested
        if self.html_report:
            self.generate_html_report()
        
        return success
    
    def generate_html_report(self):
        """Generate HTML test report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Student Promotion System Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .phase {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .passed {{ background: #d4edda; border-color: #c3e6cb; }}
        .failed {{ background: #f8d7da; border-color: #f5c6cb; }}
        .summary {{ background: #e2e3e5; padding: 15px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Student Promotion System Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Duration: {(self.end_time - self.start_time):.2f} seconds</p>
    </div>
"""
        
        for phase, result in self.test_results.items():
            status_class = "passed" if result['success'] else "failed"
            status_text = "PASSED" if result['success'] else "FAILED"
            
            html_content += f"""
    <div class="phase {status_class}">
        <h3>{phase.replace('_', ' ').title()}</h3>
        <p><strong>Status:</strong> {status_text}</p>
        <p><strong>Duration:</strong> {result['duration']:.2f} seconds</p>
        <p><strong>Return Code:</strong> {result['return_code']}</p>
        {f'<pre>{result["stderr"]}</pre>' if result['stderr'] else ''}
    </div>
"""
        
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        total_tests = len(self.test_results)
        
        html_content += f"""
    <div class="summary">
        <h3>Summary</h3>
        <p><strong>Tests Passed:</strong> {passed_tests}/{total_tests}</p>
        <p><strong>Success Rate:</strong> {(passed_tests/total_tests)*100:.1f}%</p>
    </div>
</body>
</html>
"""
        
        with open('promotion_test_report.html', 'w') as f:
            f.write(html_content)
        
        print(f"\nHTML report generated: promotion_test_report.html")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Run comprehensive student promotion system tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', '-c', action='store_true', help='Generate coverage report')
    parser.add_argument('--html-report', '-r', action='store_true', help='Generate HTML report')
    
    args = parser.parse_args()
    
    runner = PromotionTestRunner(
        verbose=args.verbose,
        coverage=args.coverage,
        html_report=args.html_report
    )
    
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
