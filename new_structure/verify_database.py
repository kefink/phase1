#!/usr/bin/env python3
"""
Verify that the database is complete and working.
"""

import sqlite3
import os
import sys

# Add parent directory to path
parent_dir = os.path.dirname(os.getcwd())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def verify_database_direct():
    """Verify database using direct SQLite connection."""
    print("🔍 Verifying database with direct connection...")
    
    try:
        conn = sqlite3.connect('../kirima_primary.db')
        cursor = conn.cursor()
        
        # Check all tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        required_tables = [
            'teacher', 'school_configuration', 'subject', 'grade', 'stream',
            'student', 'term', 'assessment_type', 'marks', 'teacher_subjects',
            'teacher_subject_assignment'
        ]
        
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        print(f"✅ All required tables present: {len(tables)} total")
        
        # Check data counts
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} records")
        
        # Test specific queries that were failing
        print("\n🔍 Testing specific queries...")
        
        # Test subject query
        cursor.execute("SELECT id, name, education_level FROM subject LIMIT 5")
        subjects = cursor.fetchall()
        print(f"✅ Subject query successful - sample: {subjects[:2]}")
        
        # Test teacher query with enhanced fields
        cursor.execute("SELECT id, username, full_name, employee_id FROM teacher LIMIT 3")
        teachers = cursor.fetchall()
        print(f"✅ Teacher query successful - sample: {teachers}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Direct database verification failed: {e}")
        return False

def verify_flask_models():
    """Verify Flask models work with the database."""
    print("\n🔧 Verifying Flask models...")
    
    try:
        from new_structure import create_app
        from new_structure.extensions import db
        from new_structure.models.user import Teacher
        from new_structure.models.academic import Subject, Grade, Stream, Term, AssessmentType
        
        app = create_app('development')
        
        with app.app_context():
            # Force SQLAlchemy to reconnect
            db.engine.dispose()
            
            # Test queries
            teacher_count = Teacher.query.count()
            subject_count = Subject.query.count()
            grade_count = Grade.query.count()
            stream_count = Stream.query.count()
            term_count = Term.query.count()
            
            print(f"✅ Teachers: {teacher_count}")
            print(f"✅ Subjects: {subject_count}")
            print(f"✅ Grades: {grade_count}")
            print(f"✅ Streams: {stream_count}")
            print(f"✅ Terms: {term_count}")
            
            # Test specific subject query that was failing
            subjects = Subject.query.order_by(Subject.education_level, Subject.name).limit(5).all()
            print(f"✅ Subject model query successful - found {len(subjects)} subjects")
            
            if subjects:
                for subject in subjects[:3]:
                    print(f"  - {subject.name} ({subject.education_level})")
            
            return True
        
    except Exception as e:
        print(f"❌ Flask models verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verifications."""
    print("🚀 Database Verification")
    print("=" * 50)
    
    # Step 1: Direct database verification
    if not verify_database_direct():
        print("❌ Direct database verification failed")
        return False
    
    # Step 2: Flask models verification
    if not verify_flask_models():
        print("❌ Flask models verification failed")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All verifications passed!")
    print("\n🚀 Your Flask application should now work perfectly.")
    print("✅ Manage Subjects should work")
    print("✅ All enhanced features should be functional")
    print("✅ Database is complete and ready")
    
    return True

if __name__ == "__main__":
    main()
