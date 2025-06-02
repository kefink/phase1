"""
Setup script for the enhanced permission system.
This script initializes the permission system and grants default permissions.
"""
import sys
import os

# Add the parent directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Now import from the new_structure package
from new_structure.extensions import db
from new_structure.models.function_permission import FunctionPermission, DefaultFunctionPermissions
from new_structure.models.user import Teacher
from new_structure.models.academic import Grade, Stream
from flask import Flask

def create_app():
    """Create a minimal Flask app for database operations."""
    app = Flask(__name__)
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../kirima_primary.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    return app

def setup_permission_system():
    """Initialize the permission system with default settings."""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 Setting up enhanced permission system...")
            
            # Test database connection
            print("📊 Testing database connection...")
            teachers = Teacher.query.all()
            print(f"✅ Found {len(teachers)} teachers in database")
            
            # Check if function_permissions table exists and is accessible
            print("🔍 Checking function_permissions table...")
            try:
                existing_permissions = FunctionPermission.query.count()
                print(f"✅ function_permissions table accessible, found {existing_permissions} existing permissions")
            except Exception as e:
                print(f"❌ Error accessing function_permissions table: {e}")
                return False
            
            # Get headteacher for granting permissions
            headteacher = Teacher.query.filter_by(role='headteacher').first()
            if not headteacher:
                print("❌ No headteacher found in database. Please create a headteacher account first.")
                return False
            
            print(f"👨‍💼 Found headteacher: {headteacher.username}")
            
            # Get all classteachers
            classteachers = Teacher.query.filter_by(role='classteacher').all()
            print(f"👩‍🏫 Found {len(classteachers)} classteachers")
            
            if not classteachers:
                print("⚠️  No classteachers found. The permission system is ready but no teachers to configure.")
                return True
            
            # Display current permission status
            print("\n📋 Current Permission Status:")
            print("=" * 50)
            
            for teacher in classteachers:
                permissions = FunctionPermission.get_teacher_function_permissions(teacher.id)
                print(f"👤 {teacher.username}: {len(permissions)} explicit permissions")
            
            # Ask if user wants to grant sample permissions
            print("\n🎯 Permission System Setup Options:")
            print("1. Leave as default (only marks upload and report generation)")
            print("2. Grant sample permissions to demonstrate the system")
            print("3. Grant full permissions to all classteachers (for testing)")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "2":
                setup_sample_permissions(headteacher.id, classteachers)
            elif choice == "3":
                setup_full_permissions(headteacher.id, classteachers)
            else:
                print("✅ Keeping default permissions (marks upload and report generation only)")
            
            print("\n🎉 Permission system setup completed!")
            print("\n📖 Usage Instructions:")
            print("- Classteachers can upload marks and generate reports by default")
            print("- All other functions require explicit permission from headteacher")
            print("- Headteacher can manage permissions via: Dashboard → Permissions → Manage Functions")
            print("- Classteachers can request permissions when they try to access restricted functions")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up permission system: {e}")
            import traceback
            traceback.print_exc()
            return False

def setup_sample_permissions(headteacher_id, classteachers):
    """Grant sample permissions to demonstrate the system."""
    print("\n🔧 Setting up sample permissions...")
    
    # Sample permissions to grant
    sample_permissions = [
        ('manage_students', 'student_management'),
        ('download_student_template', 'student_management'),
    ]
    
    granted_count = 0
    
    for teacher in classteachers[:2]:  # Grant to first 2 teachers only
        for function_name, function_category in sample_permissions:
            permission = FunctionPermission.grant_function_permission(
                teacher_id=teacher.id,
                function_name=function_name,
                function_category=function_category,
                granted_by_id=headteacher_id,
                notes="Sample permission for demonstration"
            )
            
            if permission:
                granted_count += 1
                print(f"✅ Granted '{function_name}' to {teacher.username}")
    
    print(f"🎯 Granted {granted_count} sample permissions")

def setup_full_permissions(headteacher_id, classteachers):
    """Grant all restricted permissions to all classteachers (for testing)."""
    print("\n🔧 Setting up full permissions for testing...")
    
    granted_count = 0
    
    for teacher in classteachers:
        for category, functions in DefaultFunctionPermissions.RESTRICTED_FUNCTIONS.items():
            for function_name in functions:
                permission = FunctionPermission.grant_function_permission(
                    teacher_id=teacher.id,
                    function_name=function_name,
                    function_category=category,
                    granted_by_id=headteacher_id,
                    notes="Full permissions for testing"
                )
                
                if permission:
                    granted_count += 1
    
    print(f"🎯 Granted {granted_count} permissions for testing")

def check_system_status():
    """Check the current status of the permission system."""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Checking permission system status...")
            
            # Check database tables
            teachers = Teacher.query.count()
            permissions = FunctionPermission.query.count()
            
            print(f"👥 Teachers: {teachers}")
            print(f"🔐 Function Permissions: {permissions}")
            
            # Check default functions
            default_functions = len([f for funcs in DefaultFunctionPermissions.DEFAULT_ALLOWED_FUNCTIONS.values() for f in funcs])
            restricted_functions = len([f for funcs in DefaultFunctionPermissions.RESTRICTED_FUNCTIONS.values() for f in funcs])
            
            print(f"✅ Default Allowed Functions: {default_functions}")
            print(f"🔒 Restricted Functions: {restricted_functions}")
            
            # Check classteacher permissions
            classteachers = Teacher.query.filter_by(role='classteacher').all()
            
            if classteachers:
                print("\n👩‍🏫 Classteacher Permission Summary:")
                for teacher in classteachers:
                    teacher_permissions = FunctionPermission.get_teacher_function_permissions(teacher.id)
                    print(f"   {teacher.username}: {len(teacher_permissions)} explicit permissions")
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking system status: {e}")
            return False

if __name__ == "__main__":
    print("🎯 Enhanced Permission System Setup")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        check_system_status()
    else:
        setup_permission_system()
