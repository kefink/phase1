#!/usr/bin/env python3
"""
Run script for the Hillview School Management System.
This script creates and runs the Flask application.
"""

import os
import sys

# Add the current directory to the Python path so we can import new_structure as a package
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Lightweight .env loader (no external dependency). This ensures MySQL creds are
# available before the app reads configuration. We intentionally do NOT fallback
# to SQLite – the app remains MySQL-first. Supported files (first found wins):
#   .env, .env.development, .env.local
def _load_env_file():
    candidates = [
        os.path.join(current_dir, '.env'),
        os.path.join(current_dir, '.env.development'),
        os.path.join(current_dir, '.env.local'),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for raw in f:
                        line = raw.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' not in line:
                            continue
                        key, val = line.split('=', 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        # Don't override if already set in the environment
                        if key and key not in os.environ:
                            os.environ[key] = val
                # Only load the first existing env file
                break
            except Exception:
                # Non-fatal: proceed without .env if parsing fails
                pass

_load_env_file()

try:
    # Define the port
    PORT = 8080

    # Only show startup messages if this is the main process (not reloader)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("🚀 Hillview School Management System")
        print(f"📍 Server running on: http://127.0.0.1:{PORT}")
        print("⏳ Starting application...")

    # Import create_app from the new_structure package
    from new_structure import create_app

    # Default: disable Redis-backed rate limiting in dev unless explicitly forced
    if not os.environ.get('FORCE_REDIS') and not os.environ.get('REDIS_DISABLED'):
        os.environ['REDIS_DISABLED'] = '1'

    # Create the Flask application
    app = create_app('development')

    # Only show success message for the main process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("✅ Application initialized successfully")
        print("🌐 Ready to accept connections...")
        print("")

    # Disable the auto-reloader to avoid detaching from terminal on Windows bash
    # Allow overriding host with environment variable; default to bind to all interfaces
    HOST = os.environ.get('APP_HOST', '0.0.0.0')
    app.run(debug=True, host=HOST, port=PORT, threaded=True, use_reloader=False)

except Exception as e:
    print(f"❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
