#!/usr/bin/env python3
"""
Minimal test to debug the Response object issue.
"""

import os
import sys

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Load .env file
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
os.environ['REDIS_DISABLED'] = '1'

try:
    print("🧪 Minimal app creation test...")
    
    # Try step by step
    print("📦 Step 1: Import Flask...")
    from flask import Flask
    
    print("📦 Step 2: Create basic Flask app...")
    app = Flask(__name__)
    print(f"✅ Basic app created: {type(app)}")
    
    print("📦 Step 3: Import create_app...")
    from new_structure import create_app
    
    print("📦 Step 4: Call create_app...")
    result = create_app('development')
    print(f"📋 create_app returned: {type(result)}")
    
    if hasattr(result, '__class__'):
        print(f"📋 Class: {result.__class__}")
        print(f"📋 Module: {result.__class__.__module__}")
    
    # Try to see if it has Flask app attributes
    if hasattr(result, 'config'):
        print("✅ Has config attribute")
    else:
        print("❌ No config attribute")
        
    if hasattr(result, 'run'):
        print("✅ Has run method")
    else:
        print("❌ No run method")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()