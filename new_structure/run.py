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
    print("🌐 Access URLs:")
    print("   Local:      http://localhost:5000")
    print("   Network:    http://192.168.1.124:5000")
    print("   Health:     http://localhost:5000/health")
    print("")
    print("🔧 Debug URLs:")
    print("   Blueprints:     http://localhost:5000/debug/blueprints")
    print("   Login Test:     http://localhost:5000/debug/login_test")
    print("   Form Test:      http://localhost:5000/debug/test_login")
    print("   Simple Login:   http://localhost:5000/debug/simple_login")
    print("   Admin Dashboard:http://localhost:5000/debug/test_admin_dashboard")
    print("   Init DB:        http://localhost:5000/debug/init_database")

    # Get the actual IP address
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print(f"🌐 Detected IP Address: {local_ip}")
    print(f"🌐 Network Access: http://{local_ip}:8080")

    app.run(debug=True, host='0.0.0.0', port=8080, threaded=True, use_reloader=False)

except Exception as e:
    print(f"❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
