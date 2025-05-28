#!/usr/bin/env python3
"""
Test script for the enhanced headteacher dashboard.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_structure import create_app
from new_structure.models import db, Teacher, Student, Grade, Stream, Subject, Term, AssessmentType, Mark
from new_structure.views.admin import generate_performance_assessment_data, get_upcoming_assessments, generate_system_alerts

def test_dashboard_functions():
    """Test the new dashboard functions."""
    app = create_app('development')
    
    with app.app_context():
        print("Testing headteacher dashboard enhancements...")
        
        # Test performance assessment data generation
        print("\n1. Testing performance assessment data generation...")
        try:
            performance_data = generate_performance_assessment_data()
            print(f"   ✓ Generated {len(performance_data)} performance records")
            if performance_data:
                sample = performance_data[0]
                print(f"   Sample record: Grade {sample['grade']}, Stream {sample['stream']}, Mean: {sample['mean_percentage']}%")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test upcoming assessments
        print("\n2. Testing upcoming assessments...")
        try:
            upcoming = get_upcoming_assessments()
            print(f"   ✓ Found {len(upcoming)} assessment types")
            for assessment in upcoming[:3]:  # Show first 3
                print(f"   - {assessment['name']} (Weight: {assessment['weight']}%)")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test system alerts
        print("\n3. Testing system alerts...")
        try:
            alerts = generate_system_alerts()
            print(f"   ✓ Generated {len(alerts)} system alerts")
            for alert in alerts[:3]:  # Show first 3
                print(f"   - {alert['type']}: {alert['title']}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test database queries
        print("\n4. Testing database connectivity...")
        try:
            student_count = Student.query.count()
            teacher_count = Teacher.query.count()
            grade_count = Grade.query.count()
            mark_count = Mark.query.count()
            
            print(f"   ✓ Students: {student_count}")
            print(f"   ✓ Teachers: {teacher_count}")
            print(f"   ✓ Grades: {grade_count}")
            print(f"   ✓ Marks: {mark_count}")
        except Exception as e:
            print(f"   ✗ Database error: {e}")
        
        print("\n✅ Dashboard enhancement tests completed!")

if __name__ == '__main__':
    test_dashboard_functions()
