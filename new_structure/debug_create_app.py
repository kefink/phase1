#!/usr/bin/env python3
"""
Debug script to test create_app function
"""

import os
import sys

# Add the paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Set environment variables to avoid issues
os.environ['REDIS_DISABLED'] = '1'

try:
    print("🔍 Testing create_app function...")
    
    # Import create_app
    from new_structure import create_app
    
    print("✅ Successfully imported create_app")
    
    # Create app
    print("⏳ Creating app...")
    app = create_app('development')
    
    print(f"📊 App type: {type(app)}")
    print(f"📊 App value: {repr(app)}")
    
    if hasattr(app, 'run'):
        print("✅ App has run method - it's a Flask app!")
    else:
        print("❌ App doesn't have run method - something's wrong")
        print(f"📋 App attributes: {dir(app)}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()