#!/usr/bin/env python3
"""
Simple HTTPS Server for Hillview School Management System
"""

import os
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set environment for development with HTTPS testing
os.environ['REDIS_DISABLED'] = '1'
os.environ['FORCE_HTTPS'] = 'false'  # Don't force HTTPS redirect in testing

def main():
    try:
        print("🚀 Starting Hillview School Management System with HTTPS")
        print("🔐 Generating SSL certificate...")
        
        # Import Flask and the app
        from new_structure import create_app
        
        # Create app in development mode
        app = create_app('development')
        
        # Configure for HTTPS
        PORT = 8443
        HOST = '127.0.0.1'
        
        print(f"✅ Application ready")
        print(f"🌐 HTTPS Server: https://{HOST}:{PORT}")
        print("📝 Browser will show security warning - click 'Advanced' -> 'Proceed'")
        print("⚡ Starting server...")
        
        # Run with adhoc SSL (Flask will generate certificate)
        app.run(
            host=HOST, 
            port=PORT, 
            debug=True, 
            ssl_context='adhoc',
            threaded=True,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()