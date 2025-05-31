#!/usr/bin/env python3
"""
Clear all caches and test the Flask application.
"""

import os
import sys
import glob
import shutil

def clear_all_caches():
    """Clear all Python and SQLAlchemy caches."""
    print("🧹 Clearing all caches...")

    try:
        # Remove .pyc files
        pyc_files = glob.glob("**/*.pyc", recursive=True)
        for pyc_file in pyc_files:
            try:
                os.remove(pyc_file)
                print(f"Removed: {pyc_file}")
            except:
                pass

        # Remove __pycache__ directories
        pycache_dirs = glob.glob("**/__pycache__", recursive=True)
        for pycache_dir in pycache_dirs:
            try:
                shutil.rmtree(pycache_dir)
                print(f"Removed: {pycache_dir}")
            except:
                pass

        print("✅ Python cache cleared")

        # Clear any SQLite temporary files
        temp_files = glob.glob("*.db-*")
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
                print(f"Removed temp file: {temp_file}")
            except:
                pass

        return True

    except Exception as e:
        print(f"⚠️  Cache clearing failed: {e}")
        return False

def test_database_direct():
    """Test database directly with sqlite3."""
    print("🔍 Testing database directly...")

    try:
        import sqlite3
        conn = sqlite3.connect('kirima_primary.db')
        cursor = conn.cursor()

        # Test teacher table
        cursor.execute("SELECT id, username, full_name, employee_id FROM teacher LIMIT 3")
        teachers = cursor.fetchall()
        print(f"✅ Direct database test - found {len(teachers)} teachers:")
        for teacher in teachers:
            print(f"  - ID: {teacher[0]}, Username: {teacher[1]}, Full Name: {teacher[2]}, Employee ID: {teacher[3]}")

        # Test columns
        cursor.execute("PRAGMA table_info(teacher)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"✅ Teacher table columns: {columns}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Direct database test failed: {e}")
        return False

def test_flask_models():
    """Test Flask models with fresh import."""
    print("🔧 Testing Flask models...")

    try:
        # Ensure we're in the right directory
        if not os.path.exists('run.py'):
            print("❌ run.py not found. Make sure you're in the correct directory.")
            return False

        # Clear sys.modules of our app modules
        modules_to_clear = [key for key in sys.modules.keys() if key.startswith('new_structure')]
        for module in modules_to_clear:
            del sys.modules[module]

        print("✅ Cleared module cache")

        # Add parent directory to path
        parent_dir = os.path.dirname(os.getcwd())
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # Fresh import
        from new_structure import create_app
        from new_structure.extensions import db

        app = create_app('development')

        with app.app_context():
            # Force SQLAlchemy to reconnect
            db.engine.dispose()

            # Import models
            from new_structure.models.user import Teacher
            from new_structure.models.academic import SchoolConfiguration

            print("✅ Models imported successfully")

            # Test basic query
            try:
                teacher_count = Teacher.query.count()
                print(f"✅ Teacher.query.count() = {teacher_count}")

                if teacher_count > 0:
                    # Test getting first teacher
                    first_teacher = Teacher.query.first()
                    print(f"✅ First teacher: {first_teacher.username}")

                    # Test enhanced fields
                    print(f"✅ Full name: {first_teacher.full_name}")
                    print(f"✅ Employee ID: {first_teacher.employee_id}")
                    print(f"✅ Is active: {first_teacher.is_active}")

                # Test school configuration
                config = SchoolConfiguration.query.first()
                if config:
                    print(f"✅ School config: {config.school_name}")

                print("✅ Flask models test successful!")
                return True

            except Exception as e:
                print(f"❌ Model query failed: {e}")
                import traceback
                traceback.print_exc()
                return False

    except Exception as e:
        print(f"❌ Flask models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Cache Clear and Database Test")
    print("=" * 50)

    # Step 1: Clear caches
    clear_all_caches()

    # Step 2: Test database directly
    if not test_database_direct():
        print("❌ Direct database test failed")
        return False

    # Step 3: Test Flask models
    if not test_flask_models():
        print("❌ Flask models test failed")
        return False

    print("\n" + "=" * 50)
    print("🎉 All tests passed!")
    print("\n🚀 Your Flask application should now work.")
    print("Try starting it with: python run.py")

    return True

if __name__ == "__main__":
    main()
