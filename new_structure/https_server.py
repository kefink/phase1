#!/usr/bin/env python3
"""
Clean HTTPS Server for Hillview School Management System
Minimal setup to get HTTPS working
"""

import os
import sys

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Environment setup for HTTPS testing
os.environ['REDIS_DISABLED'] = '1'
os.environ['FORCE_HTTPS'] = 'false'

def main():
    try:
        print("🚀 Hillview School - HTTPS Server")
        print("🔧 Setting up secure environment...")
        
        # Use the original working run.py approach
        PORT = 8080
        HTTPS_PORT = 8443
        HOST = '127.0.0.1'
        
        print("⏳ Importing application...")
        from new_structure import create_app
        
        print("✅ Creating Flask app...")
        
        # Try a safer approach - create with minimal config
        original_debug = os.environ.get('FLASK_DEBUG', '')
        os.environ['FLASK_DEBUG'] = 'false'  # Disable debug to avoid debug routes
        
        try:
            app = create_app('development')
            if isinstance(app, str) or hasattr(app, 'status_code'):
                raise Exception("create_app returned error instead of Flask app")
                
        except Exception as create_error:
            print(f"❌ Error with development config: {create_error}")
            print("🔧 Trying production config...")
            
            # Try production config which might have fewer debug routes
            os.environ['SECRET_KEY'] = 'temporary_key_for_https_testing_only'
            os.environ['WTF_CSRF_SECRET_KEY'] = 'temporary_csrf_key_for_https_testing_only'
            os.environ['MYSQL_PASSWORD'] = ''  # Use empty password for local testing
            
            app = create_app('production')
            if isinstance(app, str) or hasattr(app, 'status_code'):
                raise Exception("create_app returned error instead of Flask app")
        
        print(f"✅ Flask app created successfully: {type(app)}")
        print(f"🔐 Starting HTTPS server on: https://{HOST}:{HTTPS_PORT}")
        print("📝 Browser will show security warning - click 'Advanced' -> 'Proceed'")
        print("")
        
        # Run with HTTPS
        app.run(
            host=HOST,
            port=HTTPS_PORT,
            debug=False,  # Disable debug to avoid issues
            ssl_context='adhoc',
            threaded=True,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ Error starting HTTPS server: {e}")
        print(f"📋 Error type: {type(e)}")
        
        # Fallback: try regular HTTP with SSL context
        try:
            print("🔧 Attempting fallback HTTPS setup...")
            
            import ssl
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_default_certs()
            
            # This might work if adhoc doesn't
            app.run(
                host=HOST,
                port=HTTPS_PORT,
                debug=False,
                ssl_context=context,
                threaded=True,
                use_reloader=False
            )
            
        except Exception as fallback_error:
            print(f"❌ Fallback also failed: {fallback_error}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()