#!/usr/bin/env python3
"""
Debug startup script to identify the hanging issue.
"""

import os
import sys

# Add the parent directory to the Python path so we can import new_structure as a package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

print("🔍 Debug: Starting import test...")

try:
    print("Step 1: Importing Flask...")
    from flask import Flask
    print("✅ Flask imported successfully")
    
    print("Step 2: Importing new_structure.extensions...")
    from new_structure.extensions import db, csrf
    print("✅ Extensions imported successfully")
    
    print("Step 3: Importing new_structure.config...")
    from new_structure.config import config
    print("✅ Config imported successfully")
    
    print("Step 4: Importing new_structure.logging_config...")
    from new_structure.logging_config import setup_logging
    print("✅ Logging config imported successfully")
    
    print("Step 5: Creating Flask app...")
    app = Flask(__name__)
    print("✅ Flask app created successfully")
    
    print("Step 6: Loading configuration...")
    app.config.from_object(config['development'])
    print("✅ Configuration loaded successfully")
    
    print("Step 7: Setting up logging...")
    setup_logging(app)
    print("✅ Logging setup successfully")
    
    print("Step 8: Initializing extensions...")
    db.init_app(app)
    csrf.init_app(app)
    print("✅ Extensions initialized successfully")
    
    print("Step 9: Importing views...")
    from new_structure.views import blueprints
    print(f"✅ Views imported successfully - {len(blueprints)} blueprints found")
    
    print("Step 10: Registering blueprints...")
    for i, blueprint in enumerate(blueprints):
        print(f"  Registering blueprint {i+1}/{len(blueprints)}: {blueprint.name}")
        app.register_blueprint(blueprint)
    print("✅ All blueprints registered successfully")
    
    print("Step 11: Testing basic route...")
    @app.route('/debug')
    def debug_route():
        return "Debug route working!"
    print("✅ Debug route added successfully")
    
    print("🎉 All steps completed successfully!")
    print("🚀 Starting server on port 5001...")
    
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)
    
except Exception as e:
    print(f"❌ Error at step: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
