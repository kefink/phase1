#!/usr/bin/env python3
"""
Run script for the Hillview School Management System.
This script creates and runs the Flask application.
"""

import os
import sys

# Add the parent directory to the Python path so we can import new_structure as a package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    print("🔄 Starting Hillview School Management System...")
    print("📍 Current directory:", os.getcwd())

    print("🔍 Attempting to import create_app...")
    # Import create_app from the new_structure package
    from new_structure import create_app
    print("✅ Successfully imported create_app")

    print("🔍 Attempting to create Flask app...")
    # Create the Flask application
    app = create_app('development')
    print("✅ Successfully created Flask app")

    print("🚀 Starting server on http://localhost:5000")
    print("📋 Parent Management: http://localhost:5000/headteacher/parent_management")
    print("🔐 Parent Portal: http://localhost:5000/parent/login")

    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)

except Exception as e:
    print(f"❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
