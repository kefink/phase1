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
    print("🚀 Hillview School Management System")
    print("📍 Server: http://localhost:5000")

    # Import create_app from the new_structure package
    from new_structure import create_app

    # Create the Flask application
    app = create_app('development')

    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)

except Exception as e:
    print(f"❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
