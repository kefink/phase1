#!/usr/bin/env python3
"""
HTTPS Server for Hillview School Management System
This runs the application with SSL/HTTPS support
"""

import os
import sys

# Add the paths like the original run.py does
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Load environment variables
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
    # HTTPS Configuration
    HTTPS_PORT = 8443
    HOST = '127.0.0.1'
    
    print("🚀 Hillview School Management System - HTTPS Mode")
    print(f"🔐 HTTPS Server: https://{HOST}:{HTTPS_PORT}")
    print("⏳ Starting application...")
    
    # Set up environment for HTTPS testing
    if not os.environ.get('FORCE_REDIS') and not os.environ.get('REDIS_DISABLED'):
        os.environ['REDIS_DISABLED'] = '1'
    
    # Import create_app using the same pattern as run.py
    from new_structure import create_app
    
    # Create the Flask application
    app = create_app('development')
    
    print("✅ Application initialized successfully")
    print("🛡️ HTTPS features:")
    print("  • SSL/TLS encryption")
    print("  • Security headers")  
    print("  • CSRF protection")
    print("🌐 Ready for HTTPS connections...")
    print("")
    print("📝 Note: Browser will show security warning for self-signed certificate")
    print("   Click 'Advanced' → 'Proceed to localhost (unsafe)' to continue")
    print("")
    
    # Run with HTTPS using Flask's adhoc SSL context
    app.run(
        debug=True, 
        host=HOST, 
        port=HTTPS_PORT, 
        threaded=True, 
        use_reloader=False,
        ssl_context='adhoc'  # Flask generates self-signed certificate
    )

except Exception as e:
    print(f"❌ Error starting HTTPS server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)