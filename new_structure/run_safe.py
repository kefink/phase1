#!/usr/bin/env python3
"""
Safe run script for the Hillview School Management System.
This script creates and runs the Flask application with MSYS2 workarounds.
"""

import os
import sys

# MSYS2 Workarounds
if os.name == 'nt':  # Windows
    # Set environment variables to work around MSYS2 issues
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONHASHSEED'] = '0'
    
    # Disable threading in certain problematic modules
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['NUMEXPR_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'

# Add the parent directory to the Python path so we can import new_structure as a package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    # Define the port
    PORT = 8080

    # Only show startup messages if this is the main process (not reloader)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("🚀 Hillview School Management System (Safe Mode)")
        print(f"📍 Server running on: http://127.0.0.1:{PORT}")
        print("⏳ Starting application...")

    # Import create_app from the new_structure package
    from new_structure import create_app

    # Create the Flask application
    app = create_app('development')

    # Only show success message for the main process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("✅ Application initialized successfully")
        print("🌐 Ready to accept connections...")
        print("")

    # Run with reduced threading to avoid MSYS2 issues
    app.run(debug=True, host='127.0.0.1', port=PORT, threaded=False, use_reloader=True)

except Exception as e:
    print(f"❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
