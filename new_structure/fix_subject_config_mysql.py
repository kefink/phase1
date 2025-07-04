#!/usr/bin/env python3
"""
Fix subject configuration issues in MySQL database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pymysql
from config import config

def connect_to_mysql():
    """Connect directly to MySQL database."""
    conf = config['development']()
    
    try:
        connection = pymysql.connect(
            host=conf.MYSQL_HOST,
            user=conf.MYSQL_USER,
            password='@2494/lK',  # Direct password
            database=conf.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        print(f"✅ Connected to MySQL database: {conf.MYSQL_DATABASE}")
        return connection
    except Exception as e:
        print(f"❌ Failed to connect to MySQL: {e}")
        return None

def fix_subject_configuration():
    """Fix subject configuration table and data."""
    connection = connect_to_mysql()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'subject_configuration'")
        table_exists = cursor.fetchone() is not None
        print(f"📋 subject_configuration table exists: {table_exists}")
        
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
            cursor.execute(create_table_sql)
            print("✅ Table created successfully!")
        
        # Check existing records
        cursor.execute("SELECT COUNT(*) FROM subject_configuration")
        count = cursor.fetchone()[0]
        print(f"📊 Current records: {count}")
        
        # Clear and insert fresh data
        print("🔄 Clearing existing configurations...")
        cursor.execute("DELETE FROM subject_configuration")
        
        print("📝 Adding default configurations...")
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
            cursor.execute(insert_sql, config)
        
        connection.commit()
        print(f"✅ Added {len(configs)} configurations")
        
        # Verify the data
        cursor.execute("SELECT * FROM subject_configuration ORDER BY subject_name, education_level")
        records = cursor.fetchall()
        
        print("\n📋 Current configurations:")
        for record in records:
            print(f"  {record}")
        
        # Also update the Subject table to mark English and Kiswahili as composite
        print("\n🔄 Updating Subject table...")
        
        # Check if Subject table has is_composite column
        cursor.execute("SHOW COLUMNS FROM subject LIKE 'is_composite'")
        has_composite_column = cursor.fetchone() is not None
        
        if not has_composite_column:
            print("➕ Adding is_composite column to Subject table...")
            cursor.execute("ALTER TABLE subject ADD COLUMN is_composite BOOLEAN DEFAULT FALSE")
        
        # Update English and Kiswahili subjects to be composite
        cursor.execute("""
            UPDATE subject 
            SET is_composite = TRUE 
            WHERE LOWER(name) IN ('english', 'kiswahili')
        """)
        
        affected_rows = cursor.rowcount
        print(f"✅ Updated {affected_rows} subjects to composite")
        
        connection.commit()
        print("\n🎉 Subject configuration fix completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        connection.close()

if __name__ == '__main__':
    print("🚀 Starting MySQL subject configuration fix...")
    success = fix_subject_configuration()
    if success:
        print("\n✅ All fixes applied successfully!")
        print("🔄 Please restart your Flask application to see the changes.")
    else:
        print("\n❌ Fix failed. Please check the errors above.")
