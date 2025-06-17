#!/usr/bin/env python3
"""
Quick MySQL Migration Script
Uses existing working configuration to perform migration without interactive input.
"""

import mysql.connector
from mysql.connector import Error
import json
import os
import sys
import sqlite3
from datetime import datetime

def load_mysql_config():
    """Load existing MySQL configuration."""
    config_files = ['mysql_working_config.json', 'mysql_manual_config.json']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
    
    print("❌ No MySQL configuration found!")
    return None

def create_tenant_database(config):
    """Create tenant database and user."""
    print("🔄 Setting up MySQL tenant database...")
    
    try:
        # Connect to MySQL
        connection = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            port=config.get('port', 3306),
            autocommit=True
        )
        
        cursor = connection.cursor()
        
        # Create database
        db_name = "hillview_demo001"
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ Created database: {db_name}")
        
        # Create user
        user_name = "hillview_demo001_user"
        user_password = "hillview_demo_pass_2024"
        
        cursor.execute(f"CREATE USER IF NOT EXISTS '{user_name}'@'%' IDENTIFIED BY '{user_password}'")
        cursor.execute(f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{user_name}'@'%'")
        cursor.execute("FLUSH PRIVILEGES")
        print(f"✅ Created user: {user_name}")
        
        # Save tenant credentials
        tenant_config = {
            'tenant_code': 'DEMO001',
            'database_name': db_name,
            'username': user_name,
            'password': user_password,
            'host': config['host'],
            'port': config.get('port', 3306)
        }
        
        with open('mysql_credentials.json', 'w') as f:
            json.dump(tenant_config, f, indent=2)
        
        print("💾 Tenant credentials saved!")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_mysql_schema(tenant_config):
    """Create MySQL schema."""
    print("🔄 Creating MySQL schema...")
    
    try:
        connection = mysql.connector.connect(
            host=tenant_config['host'],
            database=tenant_config['database_name'],
            user=tenant_config['username'],
            password=tenant_config['password'],
            port=tenant_config['port'],
            autocommit=True
        )
        
        cursor = connection.cursor()
        
        # Create tables (simplified version)
        tables = [
            """CREATE TABLE IF NOT EXISTS grade (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                education_level VARCHAR(50) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
            
            """CREATE TABLE IF NOT EXISTS stream (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                grade_id INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (grade_id) REFERENCES grade(id) ON DELETE CASCADE
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
            
            """CREATE TABLE IF NOT EXISTS subject (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                education_level VARCHAR(50) NOT NULL,
                is_composite BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
            
            """CREATE TABLE IF NOT EXISTS term (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                academic_year VARCHAR(20) NOT NULL,
                start_date DATE,
                end_date DATE,
                is_current BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
            
            """CREATE TABLE IF NOT EXISTS assessment_type (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                weight DECIMAL(5,2) DEFAULT 100.00,
                group_name VARCHAR(100),
                show_on_reports BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
            
            """CREATE TABLE IF NOT EXISTS teacher (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'teacher',
                stream_id INT,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                email VARCHAR(120),
                phone VARCHAR(20),
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stream_id) REFERENCES stream(id) ON DELETE SET NULL
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
            
            """CREATE TABLE IF NOT EXISTS student (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                admission_number VARCHAR(50) UNIQUE,
                stream_id INT,
                grade_id INT,
                gender VARCHAR(20) DEFAULT 'Unknown',
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stream_id) REFERENCES stream(id) ON DELETE SET NULL,
                FOREIGN KEY (grade_id) REFERENCES grade(id) ON DELETE SET NULL
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
            
            """CREATE TABLE IF NOT EXISTS mark (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                subject_id INT NOT NULL,
                term_id INT NOT NULL,
                assessment_type_id INT NOT NULL,
                grade_id INT NOT NULL,
                stream_id INT,
                marks DECIMAL(6,2),
                total_marks DECIMAL(6,2),
                percentage DECIMAL(5,2),
                is_uploaded BOOLEAN DEFAULT FALSE,
                uploaded_by_teacher_id INT,
                upload_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE,
                FOREIGN KEY (term_id) REFERENCES term(id) ON DELETE CASCADE,
                FOREIGN KEY (assessment_type_id) REFERENCES assessment_type(id) ON DELETE CASCADE,
                FOREIGN KEY (grade_id) REFERENCES grade(id) ON DELETE CASCADE,
                FOREIGN KEY (stream_id) REFERENCES stream(id) ON DELETE CASCADE,
                FOREIGN KEY (uploaded_by_teacher_id) REFERENCES teacher(id) ON DELETE SET NULL
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
            
            """CREATE TABLE IF NOT EXISTS teacher_subjects (
                teacher_id INT NOT NULL,
                subject_id INT NOT NULL,
                PRIMARY KEY (teacher_id, subject_id),
                FOREIGN KEY (teacher_id) REFERENCES teacher(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"""
        ]
        
        for i, table_sql in enumerate(tables, 1):
            cursor.execute(table_sql)
            print(f"✅ Created table {i}/{len(tables)}")
        
        cursor.close()
        connection.close()
        print("✅ MySQL schema created successfully!")
        return True
        
    except Error as e:
        print(f"❌ Schema creation failed: {e}")
        return False

def migrate_data(tenant_config):
    """Migrate data from SQLite to MySQL."""
    print("🔄 Migrating data from SQLite to MySQL...")
    
    sqlite_db = "../kirima_primary.db"
    if not os.path.exists(sqlite_db):
        print(f"❌ SQLite database not found: {sqlite_db}")
        return False
    
    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_conn.row_factory = sqlite3.Row
        
        # Connect to MySQL
        mysql_conn = mysql.connector.connect(
            host=tenant_config['host'],
            database=tenant_config['database_name'],
            user=tenant_config['username'],
            password=tenant_config['password'],
            port=tenant_config['port'],
            autocommit=False
        )
        
        # Migrate tables in order
        tables_to_migrate = ['grade', 'stream', 'subject', 'term', 'assessment_type', 'teacher', 'student', 'teacher_subjects', 'mark']
        
        for table in tables_to_migrate:
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
                migrated_count = 0
                for row in rows:
                    try:
                        values = [dict(row)[col] for col in columns]
                        mysql_cursor.execute(insert_sql, values)
                        migrated_count += 1
                    except Error as e:
                        print(f"⚠️ Error migrating row in {table}: {e}")
                        continue
                
                mysql_conn.commit()
                print(f"✅ Migrated {migrated_count} records from {table}")
                
                sqlite_cursor.close()
                mysql_cursor.close()
                
            except Exception as e:
                print(f"⚠️ Error migrating {table}: {e}")
                continue
        
        sqlite_conn.close()
        mysql_conn.close()
        print("✅ Data migration completed!")
        return True
        
    except Exception as e:
        print(f"❌ Data migration failed: {e}")
        return False

def main():
    """Main migration function."""
    print("🚀 Quick MySQL Migration for Hillview School Management System")
    print("=" * 70)
    
    # Load MySQL configuration
    config = load_mysql_config()
    if not config:
        return False
    
    print(f"✅ Using MySQL configuration: {config['host']}:{config.get('port', 3306)}")
    
    # Step 1: Create tenant database
    if not create_tenant_database(config):
        return False
    
    # Load tenant configuration
    with open('mysql_credentials.json', 'r') as f:
        tenant_config = json.load(f)
    
    # Step 2: Create schema
    if not create_mysql_schema(tenant_config):
        return False
    
    # Step 3: Migrate data
    if not migrate_data(tenant_config):
        return False
    
    print("\n🎉 MySQL Migration Completed Successfully!")
    print("\n📋 Next Steps:")
    print("1. Update application configuration")
    print("2. Test the application with MySQL")
    print("3. Verify all data migrated correctly")
    
    print(f"\n🔗 MySQL Database Details:")
    print(f"Database: {tenant_config['database_name']}")
    print(f"Username: {tenant_config['username']}")
    print(f"Host: {tenant_config['host']}:{tenant_config['port']}")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
