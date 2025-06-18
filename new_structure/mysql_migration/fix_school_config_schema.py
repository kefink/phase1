#!/usr/bin/env python3
"""
Fix School Configuration Schema
Fixes the school configuration table schema mismatch.
"""

import mysql.connector
import json

def check_school_tables(cursor):
    """Check what school-related tables exist."""
    print("🔍 Checking school-related tables...")
    
    cursor.execute("SHOW TABLES LIKE '%school%'")
    school_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Found school tables: {', '.join(school_tables)}")
    
    for table in school_tables:
        print(f"\n📊 {table} structure:")
        cursor.execute(f"DESCRIBE {table}")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]:<25} {col[1]:<20}")
    
    return school_tables

def fix_school_configuration_table(cursor):
    """Fix the school_configuration table to match Flask model."""
    print("\n🔧 Fixing school_configuration table...")
    
    # Check if table exists
    cursor.execute("SHOW TABLES LIKE 'school_configuration'")
    if not cursor.fetchall():
        print("❌ school_configuration table doesn't exist")
        return False
    
    # Get current columns
    cursor.execute("DESCRIBE school_configuration")
    columns = [row[0] for row in cursor.fetchall()]
    print(f"Current columns: {', '.join(columns)}")
    
    # Expected columns based on Flask model usage
    expected_columns = {
        'school_name': 'VARCHAR(200)',
        'school_motto': 'VARCHAR(500)',
        'school_vision': 'TEXT',
        'school_mission': 'TEXT',
        'school_address': 'TEXT',
        'postal_address': 'VARCHAR(200)',
        'school_phone': 'VARCHAR(50)',
        'school_mobile': 'VARCHAR(50)',
        'school_email': 'VARCHAR(100)',
        'school_website': 'VARCHAR(100)',
        'registration_number': 'VARCHAR(100)',
        'ministry_code': 'VARCHAR(50)',
        'county': 'VARCHAR(100)',
        'sub_county': 'VARCHAR(100)',
        'ward': 'VARCHAR(100)',
        'constituency': 'VARCHAR(100)',
        'school_type': 'VARCHAR(50)',
        'school_category': 'VARCHAR(50)',
        'education_system': 'VARCHAR(50) DEFAULT "CBC"',
        'current_academic_year': 'VARCHAR(20)',
        'current_term': 'VARCHAR(50)',
        'total_terms_per_year': 'INTEGER DEFAULT 3',
        'uses_streams': 'BOOLEAN DEFAULT TRUE',
        'lowest_grade': 'VARCHAR(20) DEFAULT "PP1"',
        'highest_grade': 'VARCHAR(20) DEFAULT "Grade 6"',
        'logo_filename': 'VARCHAR(200)',
        'primary_color': 'VARCHAR(7) DEFAULT "#1f7d53"',
        'secondary_color': 'VARCHAR(7) DEFAULT "#18230f"',
        'accent_color': 'VARCHAR(7) DEFAULT "#4ade80"',
        'grading_system': 'VARCHAR(50) DEFAULT "CBC"',
        'max_raw_marks_default': 'INTEGER DEFAULT 100',
        'pass_mark_percentage': 'DECIMAL(5,2) DEFAULT 50.0',
        'show_position': 'BOOLEAN DEFAULT TRUE',
        'show_class_average': 'BOOLEAN DEFAULT TRUE',
        'show_subject_teacher': 'BOOLEAN DEFAULT FALSE',
        'report_footer': 'TEXT DEFAULT "Powered by CbcTeachkit"',
        'timezone': 'VARCHAR(50) DEFAULT "Africa/Nairobi"',
        'language': 'VARCHAR(10) DEFAULT "en"',
        'currency': 'VARCHAR(10) DEFAULT "KES"',
        'setup_completed': 'BOOLEAN DEFAULT FALSE',
        'setup_step': 'INTEGER DEFAULT 1',
        'setup_completed_at': 'DATETIME',
        'setup_completed_by': 'INTEGER',
        'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
    }
    
    # Add missing columns
    missing_columns = []
    for col_name, col_def in expected_columns.items():
        if col_name not in columns:
            missing_columns.append((col_name, col_def))
    
    if missing_columns:
        print(f"Adding {len(missing_columns)} missing columns...")
        for col_name, col_def in missing_columns:
            try:
                cursor.execute(f"ALTER TABLE school_configuration ADD COLUMN {col_name} {col_def}")
                print(f"✅ Added: {col_name}")
            except Exception as e:
                print(f"⚠️ Error adding {col_name}: {e}")
    else:
        print("✅ All expected columns already exist")
    
    # Insert default data if table is empty
    cursor.execute("SELECT COUNT(*) FROM school_configuration")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("📝 Inserting default school configuration...")
        default_config = {
            'school_name': 'Your School Name',
            'school_motto': 'Excellence in Education',
            'current_academic_year': '2024',
            'current_term': 'Term 1',
            'education_system': 'CBC',
            'grading_system': 'CBC',
            'setup_completed': False,
            'setup_step': 1
        }
        
        columns_str = ', '.join(default_config.keys())
        values_str = ', '.join(['%s'] * len(default_config))
        
        cursor.execute(
            f"INSERT INTO school_configuration ({columns_str}) VALUES ({values_str})",
            list(default_config.values())
        )
        print("✅ Default configuration inserted")
    
    return True

def create_school_setup_table_if_needed(cursor):
    """Create school_setup table if the model expects it."""
    print("\n🔧 Checking if school_setup table is needed...")
    
    # Check if school_setup table exists
    cursor.execute("SHOW TABLES LIKE 'school_setup'")
    if cursor.fetchall():
        print("✅ school_setup table already exists")
        return True
    
    print("📝 Creating school_setup table...")
    
    create_table_sql = """
    CREATE TABLE school_setup (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        school_name VARCHAR(200) NOT NULL,
        school_motto VARCHAR(500),
        school_vision TEXT,
        school_mission TEXT,
        school_address TEXT,
        postal_address VARCHAR(200),
        school_phone VARCHAR(50),
        school_mobile VARCHAR(50),
        school_email VARCHAR(100),
        school_website VARCHAR(100),
        registration_number VARCHAR(100),
        ministry_code VARCHAR(50),
        county VARCHAR(100),
        sub_county VARCHAR(100),
        ward VARCHAR(100),
        constituency VARCHAR(100),
        school_type VARCHAR(50),
        school_category VARCHAR(50),
        education_system VARCHAR(50) DEFAULT 'CBC',
        current_academic_year VARCHAR(20) NOT NULL,
        current_term VARCHAR(50) NOT NULL,
        total_terms_per_year INTEGER DEFAULT 3,
        uses_streams BOOLEAN DEFAULT TRUE,
        lowest_grade VARCHAR(20) DEFAULT 'PP1',
        highest_grade VARCHAR(20) DEFAULT 'Grade 6',
        logo_filename VARCHAR(200),
        primary_color VARCHAR(7) DEFAULT '#1f7d53',
        secondary_color VARCHAR(7) DEFAULT '#18230f',
        accent_color VARCHAR(7) DEFAULT '#4ade80',
        grading_system VARCHAR(50) DEFAULT 'CBC',
        max_raw_marks_default INTEGER DEFAULT 100,
        pass_mark_percentage DECIMAL(5,2) DEFAULT 50.0,
        show_position BOOLEAN DEFAULT TRUE,
        show_class_average BOOLEAN DEFAULT TRUE,
        show_subject_teacher BOOLEAN DEFAULT FALSE,
        report_footer TEXT DEFAULT 'Powered by CbcTeachkit',
        timezone VARCHAR(50) DEFAULT 'Africa/Nairobi',
        language VARCHAR(10) DEFAULT 'en',
        currency VARCHAR(10) DEFAULT 'KES',
        setup_completed BOOLEAN DEFAULT FALSE,
        setup_step INTEGER DEFAULT 1,
        setup_completed_at DATETIME,
        setup_completed_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    
    try:
        cursor.execute(create_table_sql)
        print("✅ school_setup table created")
        
        # Insert default data
        cursor.execute("""
            INSERT INTO school_setup (school_name, school_motto, current_academic_year, current_term)
            VALUES ('Your School Name', 'Excellence in Education', '2024', 'Term 1')
        """)
        print("✅ Default data inserted")
        
        return True
    except Exception as e:
        print(f"❌ Error creating school_setup table: {e}")
        return False

def test_school_config_queries(cursor):
    """Test school configuration queries."""
    print("\n🧪 Testing school configuration queries...")
    
    test_queries = [
        "SELECT COUNT(*) FROM school_configuration",
        "SELECT school_name FROM school_configuration LIMIT 1",
        "SELECT school_motto FROM school_configuration LIMIT 1"
    ]
    
    for query in test_queries:
        try:
            cursor.execute(query)
            result = cursor.fetchone()
            print(f"✅ Query OK: {query} -> {result}")
        except Exception as e:
            print(f"❌ Query FAILED: {query} -> {e}")
            return False
    
    return True

def main():
    """Main function to fix school configuration schema."""
    print("🔧 SCHOOL CONFIGURATION SCHEMA FIX")
    print("=" * 50)
    
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
        
        # Check existing tables
        school_tables = check_school_tables(cursor)
        
        # Fix school_configuration table
        success1 = fix_school_configuration_table(cursor)
        
        # Create school_setup table if needed
        success2 = create_school_setup_table_if_needed(cursor)
        
        # Test queries
        success3 = test_school_config_queries(cursor)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        if success1 and success2 and success3:
            print("\n🎉 SCHOOL CONFIGURATION SCHEMA FIX COMPLETED!")
            print("✅ All school configuration tables are now properly set up")
            print("✅ Dashboard should now work without school_configuration errors")
            return True
        else:
            print("\n⚠️ PARTIAL SUCCESS - Some issues may remain")
            return False
        
    except Exception as e:
        print(f"❌ Schema fix failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
