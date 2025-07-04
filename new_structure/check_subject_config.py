#!/usr/bin/env python3
"""
Check subject configuration table and fix issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from sqlalchemy import text
from config import config

def create_app():
    """Create Flask app for database operations."""
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    return app

def check_and_fix_subject_config():
    """Check and fix subject configuration issues."""
    print("🚀 Starting subject configuration check...")
    app = create_app()
    print(f"📊 Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    with app.app_context():
        try:
            print("🔍 Checking subject_configuration table...")
            
            # Check if table exists
            with db.engine.connect() as conn:
                # For MySQL
                if 'mysql' in str(db.engine.url):
                    result = conn.execute(text('SHOW TABLES LIKE "subject_configuration"'))
                    table_exists = result.fetchone() is not None
                else:
                    # For SQLite
                    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='subject_configuration'"))
                    table_exists = result.fetchone() is not None
                
                print(f"📋 Table exists: {table_exists}")
                
                if not table_exists:
                    print("🔧 Creating subject_configuration table...")
                    create_table_sql = """
                    CREATE TABLE subject_configuration (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        subject_name VARCHAR(100) NOT NULL,
                        education_level VARCHAR(50) NOT NULL,
                        is_composite BOOLEAN DEFAULT FALSE,
                        component_1_name VARCHAR(100),
                        component_1_weight DECIMAL(5,2) DEFAULT 50.00,
                        component_2_name VARCHAR(100),
                        component_2_weight DECIMAL(5,2) DEFAULT 50.00,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        UNIQUE KEY unique_subject_level (subject_name, education_level)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """

                    conn.execute(text(create_table_sql))
                    conn.commit()
                    print("✅ Table created successfully!")
                
                # Check records
                result = conn.execute(text('SELECT COUNT(*) FROM subject_configuration'))
                count = result.fetchone()[0]
                print(f"📊 Records in table: {count}")
                
                if count == 0:
                    print("📝 Adding default configurations...")
                    
                    # Default configurations for English and Kiswahili
                    configs = [
                        ('english', 'lower_primary', True, 'Grammar', 60.0, 'Composition', 40.0),
                        ('english', 'upper_primary', True, 'Grammar', 60.0, 'Composition', 40.0),
                        ('english', 'junior_secondary', True, 'Grammar', 60.0, 'Composition', 40.0),
                        ('kiswahili', 'lower_primary', True, 'Lugha', 50.0, 'Insha', 50.0),
                        ('kiswahili', 'upper_primary', True, 'Lugha', 50.0, 'Insha', 50.0),
                        ('kiswahili', 'junior_secondary', True, 'Lugha', 50.0, 'Insha', 50.0)
                    ]
                    
                    insert_sql = """
                    INSERT INTO subject_configuration
                    (subject_name, education_level, is_composite, component_1_name, component_1_weight, component_2_name, component_2_weight)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """

                    for config in configs:
                        conn.execute(text(insert_sql), config)
                    
                    conn.commit()
                    print(f"✅ Added {len(configs)} default configurations")
                
                # Show current configurations
                result = conn.execute(text('SELECT * FROM subject_configuration ORDER BY subject_name, education_level'))
                records = result.fetchall()
                
                print("\n📋 Current configurations:")
                for record in records:
                    print(f"  {record}")
                
                print("\n✅ Subject configuration check completed!")
                return True
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    check_and_fix_subject_config()
