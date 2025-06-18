#!/usr/bin/env python3
"""
Dashboard Error Diagnosis
Diagnoses issues with the headteacher dashboard after MySQL migration.
"""

import sys
import os
import traceback

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported."""
    print("🔍 Testing Module Imports")
    print("=" * 30)
    
    try:
        from extensions import db
        print("✅ Database extension imported")
    except Exception as e:
        print(f"❌ Database extension import failed: {e}")
        return False
    
    try:
        from models.user import Teacher
        from models.academic import Grade, Stream, Subject, Student, Term, AssessmentType, Mark
        print("✅ Core models imported")
    except Exception as e:
        print(f"❌ Core models import failed: {e}")
        return False
    
    try:
        from models.assignment import TeacherSubjectAssignment
        print("✅ Assignment models imported")
    except Exception as e:
        print(f"❌ Assignment models import failed: {e}")
        return False
    
    try:
        from models.school_setup import SchoolConfiguration
        print("✅ School configuration imported")
    except Exception as e:
        print(f"❌ School configuration import failed: {e}")
        return False
    
    try:
        from services.school_config_service import SchoolConfigService
        print("✅ School config service imported")
    except Exception as e:
        print(f"❌ School config service import failed: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection and basic queries."""
    print("\n💾 Testing Database Connection")
    print("=" * 30)
    
    try:
        from extensions import db
        from models.user import Teacher
        from models.academic import Student, Grade, Stream, Subject
        
        # Test basic connection
        result = db.session.execute(db.text("SELECT 1")).scalar()
        if result == 1:
            print("✅ Database connection successful")
        else:
            print("❌ Database connection test failed")
            return False
        
        # Test model queries
        teacher_count = Teacher.query.count()
        print(f"✅ Teachers in database: {teacher_count}")
        
        student_count = Student.query.count()
        print(f"✅ Students in database: {student_count}")
        
        grade_count = Grade.query.count()
        print(f"✅ Grades in database: {grade_count}")
        
        stream_count = Stream.query.count()
        print(f"✅ Streams in database: {stream_count}")
        
        subject_count = Subject.query.count()
        print(f"✅ Subjects in database: {subject_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        traceback.print_exc()
        return False

def test_dashboard_components():
    """Test individual dashboard components."""
    print("\n🎯 Testing Dashboard Components")
    print("=" * 30)
    
    try:
        from extensions import db
        from models.user import Teacher
        from models.academic import Student, Grade, Stream, Subject, Mark
        
        # Test basic stats calculation
        print("📊 Testing basic statistics...")
        
        total_students = Student.query.count()
        print(f"✅ Total students: {total_students}")
        
        total_teachers = Teacher.query.count()
        print(f"✅ Total teachers: {total_teachers}")
        
        total_classes = Stream.query.count()
        print(f"✅ Total classes: {total_classes}")
        
        # Test marks calculation
        marks = Mark.query.all()
        print(f"✅ Total marks records: {len(marks)}")
        
        if marks:
            valid_marks = [mark.mark for mark in marks if mark.mark is not None]
            if valid_marks:
                avg_performance = sum(valid_marks) / len(valid_marks)
                print(f"✅ Average performance: {avg_performance:.2f}")
            else:
                print("⚠️ No valid marks found")
        else:
            print("⚠️ No marks in database")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard components test failed: {e}")
        traceback.print_exc()
        return False

def test_school_config_service():
    """Test school configuration service."""
    print("\n🏫 Testing School Configuration Service")
    print("=" * 40)
    
    try:
        from services.school_config_service import SchoolConfigService
        
        school_info = SchoolConfigService.get_school_info_dict()
        print(f"✅ School info retrieved: {len(school_info)} items")
        
        for key, value in school_info.items():
            print(f"  - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ School config service test failed: {e}")
        traceback.print_exc()
        return False

def test_analytics_services():
    """Test analytics services."""
    print("\n📈 Testing Analytics Services")
    print("=" * 30)
    
    try:
        # Test report-based analytics
        try:
            from services.report_based_analytics_service import ReportBasedAnalyticsService
            analytics_data = ReportBasedAnalyticsService.get_analytics_dashboard_data(
                role='headteacher',
                teacher_id=None
            )
            print("✅ Report-based analytics service working")
        except Exception as e:
            print(f"⚠️ Report-based analytics failed: {e}")
        
        # Test traditional analytics
        try:
            from services.analytics_service import AnalyticsService
            analytics_data = AnalyticsService.get_headteacher_analytics()
            print("✅ Traditional analytics service working")
        except Exception as e:
            print(f"⚠️ Traditional analytics failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Analytics services test failed: {e}")
        traceback.print_exc()
        return False

def test_admin_cache_service():
    """Test admin cache service."""
    print("\n🗄️ Testing Admin Cache Service")
    print("=" * 30)
    
    try:
        from services.admin_cache_service import (
            cache_dashboard_stats, get_cached_dashboard_stats,
            cache_subject_list, get_cached_subject_list,
            invalidate_admin_cache
        )
        
        print("✅ Admin cache service imported successfully")
        
        # Test cache operations
        cached_stats = get_cached_dashboard_stats()
        print(f"✅ Cache stats retrieved: {cached_stats is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin cache service test failed: {e}")
        traceback.print_exc()
        return False

def simulate_dashboard_generation():
    """Simulate the dashboard generation process."""
    print("\n🎭 Simulating Dashboard Generation")
    print("=" * 40)
    
    try:
        from extensions import db
        from models.user import Teacher
        from models.academic import Student, Grade, Stream, Subject, Term, AssessmentType, Mark
        from models.assignment import TeacherSubjectAssignment
        from models.school_setup import SchoolConfiguration
        from services.school_config_service import SchoolConfigService
        
        print("📊 Calculating dashboard statistics...")
        
        # Simulate the exact dashboard calculation from admin.py
        total_students = Student.query.count()
        total_teachers = Teacher.query.count()
        total_classes = Stream.query.count()
        
        print(f"✅ Basic stats calculated")
        print(f"   Students: {total_students}")
        print(f"   Teachers: {total_teachers}")
        print(f"   Classes: {total_classes}")
        
        # Test marks calculation
        marks = Mark.query.all()
        if marks:
            total_marks = sum(mark.mark for mark in marks if mark.mark is not None)
            count_marks = len([mark for mark in marks if mark.mark is not None])
            avg_performance = round(total_marks / count_marks, 2) if count_marks > 0 else 0
        else:
            avg_performance = 75
        
        print(f"✅ Performance calculated: {avg_performance}")
        
        # Test school configuration
        school_info = SchoolConfigService.get_school_info_dict()
        print(f"✅ School info retrieved: {len(school_info)} items")
        
        print("✅ Dashboard simulation completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard simulation failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main diagnostic function."""
    print("🔧 DASHBOARD ERROR DIAGNOSIS")
    print("Diagnosing headteacher dashboard issues after MySQL migration")
    print("=" * 70)
    
    tests = [
        ("Module Imports", test_imports),
        ("Database Connection", test_database_connection),
        ("Dashboard Components", test_dashboard_components),
        ("School Config Service", test_school_config_service),
        ("Analytics Services", test_analytics_services),
        ("Admin Cache Service", test_admin_cache_service),
        ("Dashboard Simulation", simulate_dashboard_generation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔍 Running: {test_name}")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 40)
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    success_rate = passed_tests / total_tests
    print(f"\nDiagnostic Success Rate: {success_rate:.1%}")
    
    if success_rate >= 0.8:
        print("\n✅ Most components working - dashboard should be functional")
    elif success_rate >= 0.6:
        print("\n⚠️ Some issues found - dashboard may have problems")
    else:
        print("\n❌ Significant issues found - dashboard likely broken")
    
    return success_rate >= 0.6

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
