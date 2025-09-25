"""
Database initialization script for production deployment.
Run this after deploying to initialize the database with default data.
"""

import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def init_production_database():
    """Initialize database for production deployment."""
    from app import application
    from new_structure.utils.database_init import initialize_database_completely, check_database_integrity
    
    with application.app_context():
        print("🔍 Checking database status...")
        status = check_database_integrity()
        print(f"Database status: {status['status']}")
        
        if status['status'] != 'healthy':
            print("🚀 Initializing database...")
            result = initialize_database_completely()
            
            if result['success']:
                print("✅ Database initialized successfully!")
                print(f"📊 Teachers: {result['status']['teacher_count']}")
                print(f"📚 Subjects: {result['status']['subject_count']}")
                print(f"🎓 Grades: {result['status']['grade_count']}")
                print(f"🏫 Streams: {result['status']['stream_count']}")
                
                print("\n🔐 Default Login Credentials:")
                print("👨‍💼 Headteacher: headteacher / admin123")
                print("👩‍🏫 Class Teacher: kevin / kev123")
                print("👨‍🎓 Subject Teacher: telvo / telvo123")
                
                return True
            else:
                print(f"❌ Database initialization failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print("✅ Database is already healthy!")
            return True

if __name__ == '__main__':
    try:
        success = init_production_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)