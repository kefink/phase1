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
    # Define the port
    PORT = 8080

    print("🚀 Hillview School Management System")
    print(f"📍 Server running on: http://127.0.0.1:{PORT}")

    # Import create_app from the new_structure package
    from new_structure import create_app

    # Create the Flask application
    app = create_app('development')

    print("✅ Application initialized successfully")
    print("🌐 Ready to accept connections...")
    print("")

    app.run(debug=False, host='127.0.0.1', port=PORT, threaded=True, use_reloader=False)

except Exception as e:
    print(f"❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
