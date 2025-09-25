#!/usr/bin/env python3
"""
Modified run script for HTTPS support.
Based on the working run.py but with HTTPS capability.
"""

import os
import sys

# Add the current directory to the Python path so we can import new_structure as a package
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Environment loader (same as original run.py)
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
                        if key and key not in os.environ:
                            os.environ[key] = val
                break
            except Exception:
                pass

_load_env_file()

try:
    # Check if HTTPS mode is requested
    USE_HTTPS = os.environ.get('USE_HTTPS', 'false').lower() in ('true', '1', 'yes')
    HTTPS_PORT = int(os.environ.get('HTTPS_PORT', '8443'))
    HTTP_PORT = int(os.environ.get('HTTP_PORT', '8080'))
    
    PORT = HTTPS_PORT if USE_HTTPS else HTTP_PORT
    
    # Only show startup messages if this is the main process (not reloader)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("🚀 Hillview School Management System")
        if USE_HTTPS:
            print(f"🔐 HTTPS Server: https://127.0.0.1:{PORT}")
            print("📝 Browser will show security warning - click 'Advanced' -> 'Proceed'")
        else:
            print(f"📍 HTTP Server: http://127.0.0.1:{PORT}")
        print("⏳ Starting application...")

    # Import create_app from the new_structure package (same as original)
    from new_structure import create_app

    # Default: disable Redis-backed rate limiting in dev unless explicitly forced
    if not os.environ.get('FORCE_REDIS') and not os.environ.get('REDIS_DISABLED'):
        os.environ['REDIS_DISABLED'] = '1'

    # Create the Flask application (same as original)
    app = create_app('development')

    # Only show success message for the main process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("✅ Application initialized successfully")
        if USE_HTTPS:
            print("🔐 HTTPS mode enabled")
            print("🛡️ Security features active")
        print("🌐 Ready to accept connections...")
        print("")

    # Allow overriding host with environment variable; default to bind to all interfaces
    HOST = os.environ.get('APP_HOST', '0.0.0.0')
    
    # Run with or without HTTPS
    if USE_HTTPS:
        # Run with HTTPS using adhoc SSL context
        app.run(
            debug=True, 
            host=HOST, 
            port=PORT, 
            threaded=True, 
            use_reloader=False,
            ssl_context='adhoc'
        )
    else:
        # Run regular HTTP (original behavior)
        app.run(debug=True, host=HOST, port=PORT, threaded=True, use_reloader=False)

except Exception as e:
    print(f"❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)