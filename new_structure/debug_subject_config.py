#!/usr/bin/env python3
"""
Debug subject configuration issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_javascript_function():
    """Check if the JavaScript function exists in the template."""
    template_path = "templates/subject_configuration.html"
    
    print("🔍 Checking JavaScript function in template...")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for the function
        if 'function saveAllConfigurations()' in content:
            print("✅ saveAllConfigurations function found")
        else:
            print("❌ saveAllConfigurations function NOT found")
            
        # Check for the button onclick
        if 'onclick="saveAllConfigurations()"' in content:
            print("✅ Button onclick handler found")
        else:
            print("❌ Button onclick handler NOT found")
            
        # Check for fetch call
        if '/api/subject-config/save-all' in content:
            print("✅ API endpoint call found")
        else:
            print("❌ API endpoint call NOT found")
            
        # Check for showNotification function
        if 'function showNotification(' in content:
            print("✅ showNotification function found")
        else:
            print("❌ showNotification function NOT found")
            
    except Exception as e:
        print(f"❌ Error reading template: {e}")

def test_api_endpoint():
    """Test the API endpoint directly."""
    print("\n🧪 Testing API endpoint...")
    
    try:
        from flask import Flask
        from extensions import db
        from config import config
        from views.subject_config_api import subject_config_api
        
        app = Flask(__name__)
        app.config.from_object(config['development'])
        db.init_app(app)
        app.register_blueprint(subject_config_api)
        
        with app.app_context():
            with app.test_client() as client:
                # Test the endpoint
                response = client.post('/api/subject-config/save-all',
                                     headers={'Content-Type': 'application/json'})
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.get_data(as_text=True)}")
                
                if response.status_code == 200:
                    print("✅ API endpoint is working")
                else:
                    print("❌ API endpoint has issues")
                    
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        import traceback
        traceback.print_exc()

def check_route_registration():
    """Check if the route is properly registered."""
    print("\n📋 Checking route registration...")
    
    try:
        from flask import Flask
        from extensions import db
        from config import config
        from views import blueprints
        
        app = Flask(__name__)
        app.config.from_object(config['development'])
        db.init_app(app)
        
        # Register all blueprints
        for blueprint in blueprints:
            app.register_blueprint(blueprint)
            
        # Check if our route exists
        with app.app_context():
            rules = []
            for rule in app.url_map.iter_rules():
                if 'subject-config' in rule.rule:
                    rules.append(f"{rule.rule} -> {rule.endpoint}")
                    
            if rules:
                print("✅ Subject config routes found:")
                for rule in rules:
                    print(f"   {rule}")
            else:
                print("❌ No subject config routes found")
                
    except Exception as e:
        print(f"❌ Error checking routes: {e}")

if __name__ == '__main__':
    print("🚀 Starting Subject Configuration Debug...")
    
    check_javascript_function()
    test_api_endpoint()
    check_route_registration()
    
    print("\n🔧 Potential fixes:")
    print("1. Check browser console (F12) for JavaScript errors")
    print("2. Verify you're logged in as headteacher")
    print("3. Check if CSRF protection is blocking the request")
    print("4. Try refreshing the page and clicking again")
