#!/usr/bin/env python3
"""
Complete Missing Data Migration
Migrates all the missing tables and data that weren't included in the initial migration.
"""

import sqlite3
import mysql.connector
import json
import os

def load_mysql_credentials():
    """Load MySQL credentials."""
    try:
        with open('mysql_credentials.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ MySQL credentials not found!")
        return None

def create_missing_mysql_tables(mysql_conn):
    """Create all missing MySQL tables."""
    print("🔄 Creating missing MySQL tables...")
    
    cursor = mysql_conn.cursor()
    
    # Missing table definitions
    missing_tables = [
        # Parent Portal Tables
        """CREATE TABLE IF NOT EXISTS parent (
            id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(120) UNIQUE,
            phone VARCHAR(20),
            password VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
        
        """CREATE TABLE IF NOT EXISTS parent_student (
            id INT AUTO_INCREMENT PRIMARY KEY,
            parent_id INT NOT NULL,
            student_id INT NOT NULL,
            relationship VARCHAR(50) DEFAULT 'Parent',
            is_primary_contact BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES parent(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
            UNIQUE KEY unique_parent_student (parent_id, student_id)
        ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
        
        """CREATE TABLE IF NOT EXISTS parent_email_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            parent_id INT NOT NULL,
            student_id INT NOT NULL,
            subject VARCHAR(255) NOT NULL,
            body TEXT,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'sent',
            FOREIGN KEY (parent_id) REFERENCES parent(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
        ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
        
        """CREATE TABLE IF NOT EXISTS email_template (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            subject VARCHAR(255) NOT NULL,
            body TEXT NOT NULL,
            template_type VARCHAR(50) DEFAULT 'general',
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by INT,
            placeholders TEXT,
            description TEXT
        ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
        
        # Subject Configuration Tables
        """CREATE TABLE IF NOT EXISTS subject_component (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject_id INT NOT NULL,
            component_name VARCHAR(100) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE
        ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
        
        """CREATE TABLE IF NOT EXISTS subject_configuration (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject_id INT NOT NULL,
            grade_id INT NOT NULL,
            is_composite BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE,
            FOREIGN KEY (grade_id) REFERENCES grade(id) ON DELETE CASCADE,
            UNIQUE KEY unique_subject_grade (subject_id, grade_id)
        ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
        
        # Teacher Assignment Table
        """CREATE TABLE IF NOT EXISTS teacher_subject_assignment (
            id INT AUTO_INCREMENT PRIMARY KEY,
            teacher_id INT NOT NULL,
            subject_id INT NOT NULL,
            grade_id INT,
            stream_id INT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES teacher(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE,
            FOREIGN KEY (grade_id) REFERENCES grade(id) ON DELETE SET NULL,
            FOREIGN KEY (stream_id) REFERENCES stream(id) ON DELETE SET NULL
        ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
        
        # Permission System Tables
        """CREATE TABLE IF NOT EXISTS class_teacher_permissions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            teacher_id INT NOT NULL,
            permission_type VARCHAR(100) NOT NULL,
            granted_by INT,
            granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (teacher_id) REFERENCES teacher(id) ON DELETE CASCADE,
            FOREIGN KEY (granted_by) REFERENCES teacher(id) ON DELETE SET NULL
        ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
        
        """CREATE TABLE IF NOT EXISTS function_permissions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            function_name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            requires_permission BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
        
        """CREATE TABLE IF NOT EXISTS permission_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            teacher_id INT NOT NULL,
            permission_type VARCHAR(100) NOT NULL,
            reason TEXT,
            status VARCHAR(50) DEFAULT 'pending',
            requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            reviewed_by INT,
            reviewed_at DATETIME,
            FOREIGN KEY (teacher_id) REFERENCES teacher(id) ON DELETE CASCADE,
            FOREIGN KEY (reviewed_by) REFERENCES teacher(id) ON DELETE SET NULL
        ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
        
        # School Configuration Table
        """CREATE TABLE IF NOT EXISTS school_configuration (
            id INT AUTO_INCREMENT PRIMARY KEY,
            config_key VARCHAR(100) NOT NULL UNIQUE,
            config_value TEXT,
            config_type VARCHAR(50) DEFAULT 'string',
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"""
    ]
    
    for i, table_sql in enumerate(missing_tables, 1):
        try:
            cursor.execute(table_sql)
            print(f"✅ Created missing table {i}/{len(missing_tables)}")
        except Exception as e:
            print(f"❌ Error creating table {i}: {e}")
    
    cursor.close()
    print("✅ Missing MySQL tables created!")

def migrate_missing_data(sqlite_conn, mysql_conn):
    """Migrate data from missing tables."""
    print("🔄 Migrating missing data...")
    
    # Tables with actual data to migrate
    tables_with_data = [
        'email_template',
        'subject_component', 
        'subject_configuration',
        'teacher_subject_assignment'
    ]
    
    migrated_count = 0
    
    for table in tables_with_data:
        try:
            sqlite_cursor = sqlite_conn.cursor()
            mysql_cursor = mysql_conn.cursor()
            
            # Get data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"⚠️ No data in {table}")
                continue
            
            # Get column names
            columns = [description[0] for description in sqlite_cursor.description]
            
            # Prepare INSERT statement
            placeholders = ', '.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Insert data
            table_migrated = 0
            for row in rows:
                try:
                    mysql_cursor.execute(insert_sql, row)
                    table_migrated += 1
                except Exception as e:
                    print(f"⚠️ Error migrating row in {table}: {e}")
                    continue
            
            mysql_conn.commit()
            migrated_count += table_migrated
            print(f"✅ Migrated {table_migrated} records from {table}")
            
            sqlite_cursor.close()
            mysql_cursor.close()
            
        except Exception as e:
            print(f"❌ Error migrating {table}: {e}")
            continue
    
    print(f"✅ Total missing records migrated: {migrated_count}")

def verify_complete_migration(mysql_conn):
    """Verify that all tables now exist in MySQL."""
    print("🔍 Verifying complete migration...")
    
    cursor = mysql_conn.cursor()
    
    # Expected tables after complete migration
    expected_tables = [
        'grade', 'stream', 'subject', 'term', 'assessment_type', 'teacher', 'student', 'mark',
        'teacher_subjects', 'parent', 'parent_student', 'parent_email_log', 'email_template',
        'subject_component', 'subject_configuration', 'teacher_subject_assignment',
        'class_teacher_permissions', 'function_permissions', 'permission_requests', 'school_configuration'
    ]
    
    # Get actual tables
    cursor.execute("SHOW TABLES")
    actual_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Expected tables: {len(expected_tables)}")
    print(f"Actual tables: {len(actual_tables)}")
    
    missing_tables = [t for t in expected_tables if t not in actual_tables]
    extra_tables = [t for t in actual_tables if t not in expected_tables]
    
    if missing_tables:
        print(f"❌ Still missing: {missing_tables}")
    else:
        print("✅ All expected tables present!")
    
    if extra_tables:
        print(f"ℹ️ Extra tables: {extra_tables}")
    
    # Count records in each table
    print("\nTable record counts:")
    print("-" * 40)
    total_records = 0
    for table in sorted(actual_tables):
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_records += count
            print(f"{table:<25} {count:>8} records")
        except Exception as e:
            print(f"{table:<25} ERROR: {e}")
    
    print("-" * 40)
    print(f"Total records: {total_records:>8}")
    
    cursor.close()

def main():
    """Main migration function."""
    print("🔄 Complete Missing Data Migration")
    print("=" * 50)
    
    # Load MySQL credentials
    creds = load_mysql_credentials()
    if not creds:
        return False
    
    # Connect to databases
    sqlite_db = "../kirima_primary.db"
    if not os.path.exists(sqlite_db):
        print(f"❌ SQLite database not found: {sqlite_db}")
        return False
    
    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(sqlite_db)
        print("✅ Connected to SQLite")
        
        # Connect to MySQL
        mysql_conn = mysql.connector.connect(
            host=creds['host'],
            database=creds['database_name'],
            user=creds['username'],
            password=creds['password'],
            port=creds['port'],
            autocommit=False
        )
        print("✅ Connected to MySQL")
        
        # Create missing tables
        create_missing_mysql_tables(mysql_conn)
        
        # Migrate missing data
        migrate_missing_data(sqlite_conn, mysql_conn)
        
        # Verify migration
        verify_complete_migration(mysql_conn)
        
        # Close connections
        sqlite_conn.close()
        mysql_conn.close()
        
        print("\n🎉 Complete migration finished!")
        print("\n📋 Next Steps:")
        print("1. Test the application with all features")
        print("2. Verify parent portal functionality")
        print("3. Check subject configurations")
        print("4. Test teacher permissions system")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
