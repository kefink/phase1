#!/usr/bin/env python3
"""
Main startup script for the Hillview School Management System.
This script should be run from the root directory to properly load all modules.
"""

import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Main function to start the Hillview application."""
    try:
        print("🚀 Hillview School Management System")
        print("📍 Server: http://localhost:5000")
        print("📦 Loading application modules...")

        # Import the create_app function from new_structure
        from new_structure import create_app

        print("⚙️ Creating Flask application...")
        # Create the application with development config
        app = create_app('development')

        print("✅ Application created successfully!")
        print("🌐 Starting development server...")
        print("📱 Access your system at: http://localhost:5000")
        print("🔐 Available portals:")
        print("   • Login: http://localhost:5000/login")
        print("   • Headteacher: http://localhost:5000/headteacher")
        print("   • Class Teacher: http://localhost:5000/classteacher")
        print("   • Subject Teacher: http://localhost:5000/teacher")
        print("   • Student Promotion: http://localhost:5000/student-promotion")
        print("   • Analytics: http://localhost:5000/analytics")
        print("   • Parent Portal: http://localhost:5000/parent")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 60)

        # Run the application
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            use_reloader=False  # Disable reloader to prevent import issues
        )

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure you're running this script from the root directory")
        print("💡 Try: python start_hillview.py")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
