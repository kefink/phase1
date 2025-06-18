#!/usr/bin/env python3
"""
Fix Subject Configuration for MySQL
Updates subject configuration to work with MySQL instead of SQLite.
"""

import mysql.connector
import json

def create_subject_configuration_table():
    """Create subject_configuration table in MySQL if it doesn't exist."""
    print("🔧 Creating Subject Configuration Table")
    print("=" * 40)
    
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
        
        connection_params = {
            'host': creds['host'],
            'database': creds['database_name'],
            'user': creds['username'],
            'password': creds['password'],
            'port': creds['port']
        }
        
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'subject_configuration'")
        if cursor.fetchall():
            print("✅ subject_configuration table already exists")
        else:
            print("📝 Creating subject_configuration table...")
            
            create_table_sql = """
            CREATE TABLE subject_configuration (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                subject_name VARCHAR(100) NOT NULL,
                education_level VARCHAR(50) NOT NULL,
                is_composite BOOLEAN DEFAULT FALSE,
                component_1_name VARCHAR(100),
                component_1_weight DECIMAL(5,2) DEFAULT 50.0,
                component_2_name VARCHAR(100),
                component_2_weight DECIMAL(5,2) DEFAULT 50.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_subject_level (subject_name, education_level)
            )
            """
            
            cursor.execute(create_table_sql)
            print("✅ subject_configuration table created")
        
        # Check if subject_component table exists
        cursor.execute("SHOW TABLES LIKE 'subject_component'")
        if cursor.fetchall():
            print("✅ subject_component table already exists")
        else:
            print("📝 Creating subject_component table...")
            
            create_component_table_sql = """
            CREATE TABLE subject_component (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                subject_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                weight DECIMAL(5,2) DEFAULT 50.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE
            )
            """
            
            cursor.execute(create_component_table_sql)
            print("✅ subject_component table created")
        
        # Insert default configurations
        print("📝 Inserting default subject configurations...")
        
        default_configs = [
            ('english', 'Primary', True, 'Grammar', 60.0, 'Composition', 40.0),
            ('english', 'Pre-Primary', True, 'Grammar', 60.0, 'Composition', 40.0),
            ('kiswahili', 'Primary', True, 'Lugha', 50.0, 'Insha', 50.0),
            ('kiswahili', 'Pre-Primary', True, 'Lugha', 50.0, 'Insha', 50.0),
            ('mathematics', 'Primary', False, None, 100.0, None, 0.0),
            ('mathematics', 'Pre-Primary', False, None, 100.0, None, 0.0),
            ('science', 'Primary', False, None, 100.0, None, 0.0),
            ('social studies', 'Primary', False, None, 100.0, None, 0.0),
            ('creative arts', 'Primary', False, None, 100.0, None, 0.0)
        ]
        
        for config in default_configs:
            try:
                cursor.execute("""
                    INSERT IGNORE INTO subject_configuration 
                    (subject_name, education_level, is_composite, component_1_name, 
                     component_1_weight, component_2_name, component_2_weight)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, config)
                print(f"✅ Added config for {config[0]} ({config[1]})")
            except Exception as e:
                print(f"⚠️ Error adding config for {config[0]}: {e}")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n🎉 Subject configuration tables set up successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up subject configuration: {e}")
        return False

def create_missing_routes():
    """Create a simple route file for missing routes."""
    print("\n🔧 Creating Missing Routes")
    print("=" * 30)
    
    # Create a simple routes file for the missing endpoints
    missing_routes_content = '''"""
Missing Routes Handler
Provides simple routes for features that were missing 404 errors.
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from .admin import admin_required

# Create blueprint for missing routes
missing_routes_bp = Blueprint('missing_routes', __name__)

@missing_routes_bp.route('/subject_config')
@admin_required
def subject_config():
    """Subject configuration page."""
    return redirect(url_for('subject_config_api.subject_configuration_page'))

@missing_routes_bp.route('/parent_management')
@admin_required
def parent_management():
    """Parent management page."""
    return redirect(url_for('parent_management.dashboard'))

@missing_routes_bp.route('/permission')
@admin_required
def permission_management():
    """Permission management page."""
    return redirect(url_for('permission_management.dashboard'))

@missing_routes_bp.route('/headteacher/universal_access')
@admin_required
def universal_access():
    """Universal access page - redirect to correct route."""
    return redirect(url_for('universal.dashboard'))
'''
    
    try:
        with open('views/missing_routes.py', 'w') as f:
            f.write(missing_routes_content)
        print("✅ Created missing_routes.py")
        
        # Update views/__init__.py to include the new blueprint
        with open('views/__init__.py', 'r') as f:
            init_content = f.read()
        
        if 'missing_routes_bp' not in init_content:
            # Add import
            import_line = "from .missing_routes import missing_routes_bp\n"
            
            # Find the imports section and add our import
            lines = init_content.split('\n')
            import_index = -1
            for i, line in enumerate(lines):
                if line.startswith('from .'):
                    import_index = i
            
            if import_index >= 0:
                lines.insert(import_index + 1, import_line.strip())
            
            # Add to blueprints list
            for i, line in enumerate(lines):
                if 'blueprints = [' in line:
                    # Find the closing bracket
                    for j in range(i + 1, len(lines)):
                        if ']' in lines[j]:
                            lines.insert(j, '    missing_routes_bp,')
                            break
                    break
            
            # Write back
            with open('views/__init__.py', 'w') as f:
                f.write('\n'.join(lines))
            
            print("✅ Updated views/__init__.py")
        else:
            print("✅ missing_routes_bp already in __init__.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating missing routes: {e}")
        return False

def main():
    """Main function to fix subject configuration and missing routes."""
    print("🔧 FIXING SUBJECT CONFIGURATION AND MISSING ROUTES")
    print("=" * 60)
    
    success1 = create_subject_configuration_table()
    success2 = create_missing_routes()
    
    if success1 and success2:
        print("\n🎉 ALL FIXES COMPLETED!")
        print("✅ Subject configuration tables created")
        print("✅ Missing routes added")
        print("✅ System should now have fewer 404 errors")
        return True
    else:
        print("\n❌ SOME FIXES FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
