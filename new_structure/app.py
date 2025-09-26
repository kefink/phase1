#!/usr/bin/env python3
"""
WSGI entry point for Render deployment.
This file uses the original application factory from __init__.py
"""

import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Load environment variables (same as run.py)
def _load_env_file():
    """Load environment variables from .env file if it exists."""
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

# Global variable to store initialization error for fallback routes
initialization_error = None

try:
    # Import create_app from the original application factory
    from new_structure import create_app

    # Default: disable Redis-backed rate limiting in production unless explicitly enabled
    if not os.environ.get('FORCE_REDIS') and not os.environ.get('REDIS_DISABLED'):
        os.environ['REDIS_DISABLED'] = '1'
    
    # Allow in-memory rate limiting for free tier deployment
    if not os.environ.get('ALLOW_IN_MEMORY_LIMITS'):
        os.environ['ALLOW_IN_MEMORY_LIMITS'] = '1'

    # Create the Flask application using the original factory
    # Use production config for Render deployment
    config_name = os.environ.get('FLASK_ENV', 'production')
    app = create_app(config_name)

    print("✅ Hillview School Management System initialized successfully")
    print(f"🌐 Using configuration: {config_name}")

except Exception as e:
    initialization_error = str(e)
    print(f"❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a MINIMAL Flask app with ONLY health endpoint - NO SECURITY
    from flask import Flask
    app = Flask(__name__)
    
    print("⚠️ Using minimal health-only app due to initialization error")

# ALWAYS add a health endpoint that works - overrides any other /health routes
@app.route('/health', methods=['GET'])
def health_endpoint():
    """Health check for Render - always works regardless of app state."""
    return {"status": "healthy", "app": "hillview"}, 200

# Fallback routes for error cases (only if main app failed)
if 'initialization_error' in locals():
    @app.route('/')
    def error_page():
        return f"""
        <h1>❌ Application Error</h1>
        <p>The application failed to initialize.</p>
        <p>Error: {initialization_error}</p>
        <p><a href="/health">Health Check</a></p>
        """

# Create the application for Gunicorn
if __name__ == '__main__':
    # This won't be called in production, but useful for local testing
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)