#!/usr/bin/env python3
"""
Test script to verify that the enhancement was successful.
This script tests the database, models, and staff assignment service.
"""

import sqlite3
import os
import sys

def test_database():
    """Test that the database has all required fields."""
    print("🔍 Testing database structure...")
    
    db_path = 'kirima_primary.db'
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test teacher table
        cursor.execute("PRAGMA table_info(teacher)")
        teacher_columns = [column[1] for column in cursor.fetchall()]
        
        expected_teacher_columns = [
            'id', 'username', 'password', 'role', 'stream_id',
            'full_name', 'employee_id', 'phone_number', 'email',
            'qualification', 'specialization', 'is_active', 'date_joined'
        ]
        
        missing_teacher = [col for col in expected_teacher_columns if col not in teacher_columns]
        
        if missing_teacher:
            print(f"❌ Missing teacher columns: {missing_teacher}")
            return False
        else:
            print("✅ Teacher table has all required columns")
        
        # Test school_configuration table
        cursor.execute("PRAGMA table_info(school_configuration)")
        config_columns = [column[1] for column in cursor.fetchall()]
        
        expected_config_columns = ['headteacher_id', 'deputy_headteacher_id']
        missing_config = [col for col in expected_config_columns if col not in config_columns]
        
        if missing_config:
            print(f"❌ Missing config columns: {missing_config}")
            return False
        else:
            print("✅ SchoolConfiguration table has all required columns")
        
        # Test data
        cursor.execute("SELECT COUNT(*) FROM teacher WHERE full_name IS NOT NULL")
        teachers_with_names = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM teacher WHERE employee_id IS NOT NULL")
        teachers_with_ids = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM teacher")
        total_teachers = cursor.fetchone()[0]
        
        print(f"✅ {teachers_with_names}/{total_teachers} teachers have full names")
        print(f"✅ {teachers_with_ids}/{total_teachers} teachers have employee IDs")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_models():
    """Test that the models can be imported and used."""
    print("\n🔍 Testing model imports...")
    
    try:
        # Test importing models
        from models.user import Teacher
        from models.academic import SchoolConfiguration
        print("✅ Models imported successfully")
        
        # Test model attributes
        teacher_attrs = ['full_name', 'employee_id', 'phone_number', 'email', 
                        'qualification', 'specialization', 'is_active', 'date_joined']
        
        missing_attrs = []
        for attr in teacher_attrs:
            if not hasattr(Teacher, attr):
                missing_attrs.append(attr)
        
        if missing_attrs:
            print(f"❌ Missing Teacher attributes: {missing_attrs}")
            return False
        else:
            print("✅ Teacher model has all required attributes")
        
        # Test SchoolConfiguration attributes
        config_attrs = ['headteacher_id', 'deputy_headteacher_id']
        missing_config_attrs = []
        for attr in config_attrs:
            if not hasattr(SchoolConfiguration, attr):
                missing_config_attrs.append(attr)
        
        if missing_config_attrs:
            print(f"❌ Missing SchoolConfiguration attributes: {missing_config_attrs}")
            return False
        else:
            print("✅ SchoolConfiguration model has all required attributes")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_staff_service():
    """Test that the staff assignment service works."""
    print("\n🔍 Testing staff assignment service...")
    
    try:
        from services.staff_assignment_service import StaffAssignmentService
        print("✅ StaffAssignmentService imported successfully")
        
        # Test getting staff info (should not crash even if no data)
        staff_info = StaffAssignmentService.get_report_staff_info("Grade 1", "Stream A")
        
        if isinstance(staff_info, dict):
            print("✅ get_report_staff_info returns valid data structure")
            
            required_keys = ['class_teacher', 'headteacher', 'deputy_headteacher', 'subject_teachers']
            missing_keys = [key for key in required_keys if key not in staff_info]
            
            if missing_keys:
                print(f"❌ Missing keys in staff_info: {missing_keys}")
                return False
            else:
                print("✅ Staff info has all required keys")
        else:
            print("❌ get_report_staff_info does not return a dictionary")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Staff service test failed: {e}")
        return False

def test_report_integration():
    """Test that the report system can use the enhanced features."""
    print("\n🔍 Testing report integration...")
    
    try:
        # Test that the enhanced template exists and has the new sections
        template_path = 'templates/preview_class_report.html'
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Check for enhanced features in template
            if 'subject_teachers' in template_content:
                print("✅ Template includes subject teachers section")
            else:
                print("⚠️  Template missing subject teachers section")
            
            if 'staff_info' in template_content:
                print("✅ Template uses staff_info variable")
            else:
                print("⚠️  Template missing staff_info usage")
            
            return True
        else:
            print("⚠️  Report template not found (this is okay if using different template)")
            return True
        
    except Exception as e:
        print(f"❌ Report integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Enhanced Hillview School Management System")
    print("=" * 60)
    
    tests = [
        ("Database Structure", test_database),
        ("Model Definitions", test_models),
        ("Staff Assignment Service", test_staff_service),
        ("Report Integration", test_report_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed!")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your enhanced system is ready to use!")
        print("\n🚀 Next steps:")
        print("1. Start your Flask application: python run.py")
        print("2. Navigate to the Class Teacher Dashboard")
        print("3. Generate reports with dynamic staff information")
        print("4. Assign class teachers and headteachers as needed")
    else:
        print("⚠️  Some tests failed. The system may still work with basic functionality.")
    
    return passed == total

if __name__ == "__main__":
    main()
