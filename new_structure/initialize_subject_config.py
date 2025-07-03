#!/usr/bin/env python3
"""
Initialize Subject Configuration Table
Creates the subject_configuration table and populates it with default configurations
"""

import sys
import os

# Add the new_structure directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from extensions import db
from . import create_app

def create_subject_configuration_table():
    """Create the subject_configuration table if it doesn't exist."""
    try:
        # Create table SQL
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS subject_configuration (
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        db.engine.execute(create_table_sql)
        print("✅ Subject configuration table created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

def populate_default_configurations():
    """Populate the table with default configurations for English and Kiswahili."""
    try:
        # Default configurations
        default_configs = [
            # English configurations
            {
                'subject_name': 'english',
                'education_level': 'lower_primary',
                'is_composite': True,
                'component_1_name': 'Grammar',
                'component_1_weight': 60.0,
                'component_2_name': 'Composition',
                'component_2_weight': 40.0
            },
            {
                'subject_name': 'english',
                'education_level': 'upper_primary',
                'is_composite': True,
                'component_1_name': 'Grammar',
                'component_1_weight': 60.0,
                'component_2_name': 'Composition',
                'component_2_weight': 40.0
            },
            {
                'subject_name': 'english',
                'education_level': 'junior_secondary',
                'is_composite': True,
                'component_1_name': 'Grammar',
                'component_1_weight': 60.0,
                'component_2_name': 'Composition',
                'component_2_weight': 40.0
            },
            # Kiswahili configurations
            {
                'subject_name': 'kiswahili',
                'education_level': 'lower_primary',
                'is_composite': True,
                'component_1_name': 'Lugha',
                'component_1_weight': 50.0,
                'component_2_name': 'Insha',
                'component_2_weight': 50.0
            },
            {
                'subject_name': 'kiswahili',
                'education_level': 'upper_primary',
                'is_composite': True,
                'component_1_name': 'Lugha',
                'component_1_weight': 50.0,
                'component_2_name': 'Insha',
                'component_2_weight': 50.0
            },
            {
                'subject_name': 'kiswahili',
                'education_level': 'junior_secondary',
                'is_composite': True,
                'component_1_name': 'Lugha',
                'component_1_weight': 50.0,
                'component_2_name': 'Insha',
                'component_2_weight': 50.0
            }
        ]
        
        # Insert configurations
        insert_sql = """
        INSERT IGNORE INTO subject_configuration 
        (subject_name, education_level, is_composite, component_1_name, component_1_weight, component_2_name, component_2_weight)
        VALUES (%(subject_name)s, %(education_level)s, %(is_composite)s, %(component_1_name)s, %(component_1_weight)s, %(component_2_name)s, %(component_2_weight)s)
        """
        
        for config in default_configs:
            db.engine.execute(insert_sql, config)
        
        print(f"✅ Inserted {len(default_configs)} default configurations")
        return True
        
    except Exception as e:
        print(f"❌ Error populating configurations: {e}")
        return False

def main():
    """Main function to initialize subject configuration."""
    print("🚀 Initializing Subject Configuration...")
    
    app = create_app()
    with app.app_context():
        # Step 1: Create table
        if not create_subject_configuration_table():
            print("❌ Failed to create table")
            return False
        
        # Step 2: Populate with defaults
        if not populate_default_configurations():
            print("❌ Failed to populate configurations")
            return False
        
        # Step 3: Verify
        try:
            result = db.engine.execute("SELECT COUNT(*) FROM subject_configuration")
            count = result.fetchone()[0]
            print(f"✅ Subject configuration initialized successfully with {count} configurations")
            
            # Show configurations
            result = db.engine.execute("""
                SELECT subject_name, education_level, is_composite, component_1_name, component_2_name 
                FROM subject_configuration 
                ORDER BY subject_name, education_level
            """)
            
            print("\n📋 Current Configurations:")
            for row in result.fetchall():
                status = "Composite" if row[2] else "Simple"
                components = f" ({row[3]} + {row[4]})" if row[2] else ""
                print(f"   - {row[0].title()} ({row[1].replace('_', ' ').title()}): {status}{components}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error verifying configurations: {e}")
            return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Subject configuration initialization completed successfully!")
        print("You can now access the Subject Configuration page from the headteacher dashboard.")
    else:
        print("\n💥 Subject configuration initialization failed!")
        sys.exit(1)
