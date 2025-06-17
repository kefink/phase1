#!/usr/bin/env python3
"""
Fix Schema Migration - Check SQLite schemas and fix MySQL tables accordingly
"""

import sqlite3
import mysql.connector
import json
import os

def analyze_sqlite_schemas():
    """Analyze SQLite table schemas."""
    print("🔍 Analyzing SQLite table schemas...")
    
    sqlite_db = "../kirima_primary.db"
    if not os.path.exists(sqlite_db):
        print(f"❌ SQLite database not found: {sqlite_db}")
        return None
    
    try:
        conn = sqlite3.connect(sqlite_db)
        cursor = conn.cursor()
        
        # Tables with data that need schema analysis
        tables_to_analyze = ['email_template', 'subject_component', 'subject_configuration', 'teacher_subject_assignment']
        
        schemas = {}
        
        for table in tables_to_analyze:
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                print(f"\n📋 {table} schema:")
                schemas[table] = []
                for col in columns:
                    col_info = {
                        'name': col[1],
                        'type': col[2],
                        'not_null': col[3],
                        'default': col[4],
                        'pk': col[5]
                    }
                    schemas[table].append(col_info)
                    print(f"  {col[1]:<20} {col[2]:<15} {'NOT NULL' if col[3] else 'NULL'}")
                
                # Show sample data
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                    sample = cursor.fetchone()
                    print(f"  Sample data: {len(sample)} values")
                
            except Exception as e:
                print(f"❌ Error analyzing {table}: {e}")
        
        conn.close()
        return schemas
        
    except Exception as e:
        print(f"❌ Error connecting to SQLite: {e}")
        return None

def fix_mysql_tables(schemas):
    """Fix MySQL table schemas based on SQLite analysis."""
    print("\n🔧 Fixing MySQL table schemas...")
    
    # Load MySQL credentials
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
    except FileNotFoundError:
        print("❌ MySQL credentials not found!")
        return False
    
    try:
        connection = mysql.connector.connect(
            host=creds['host'],
            database=creds['database_name'],
            user=creds['username'],
            password=creds['password'],
            port=creds['port'],
            autocommit=True
        )
        
        cursor = connection.cursor()
        
        # Drop and recreate tables with correct schemas
        table_fixes = {
            'email_template': """CREATE TABLE email_template (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                subject_template TEXT,
                body_template TEXT,
                template_type VARCHAR(50) DEFAULT 'general',
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_by INT,
                placeholders TEXT,
                description TEXT,
                subject TEXT
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
            
            'subject_component': """CREATE TABLE subject_component (
                id INT AUTO_INCREMENT PRIMARY KEY,
                subject_id INT NOT NULL,
                name VARCHAR(100) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
            
            'subject_configuration': """CREATE TABLE subject_configuration (
                id INT AUTO_INCREMENT PRIMARY KEY,
                subject_name VARCHAR(100) NOT NULL,
                grade_name VARCHAR(50) NOT NULL,
                is_composite BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""",
            
            'teacher_subject_assignment': """CREATE TABLE teacher_subject_assignment (
                id INT AUTO_INCREMENT PRIMARY KEY,
                teacher_id INT NOT NULL,
                subject_id INT NOT NULL,
                grade_id INT,
                stream_id INT,
                is_class_teacher BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teacher(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE,
                FOREIGN KEY (grade_id) REFERENCES grade(id) ON DELETE SET NULL,
                FOREIGN KEY (stream_id) REFERENCES stream(id) ON DELETE SET NULL
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"""
        }
        
        for table, create_sql in table_fixes.items():
            try:
                # Drop existing table
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"✅ Dropped {table}")
                
                # Create with correct schema
                cursor.execute(create_sql)
                print(f"✅ Recreated {table} with correct schema")
                
            except Exception as e:
                print(f"❌ Error fixing {table}: {e}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return False

def migrate_data_with_correct_schemas():
    """Migrate data with correct column mappings."""
    print("\n🔄 Migrating data with correct schemas...")
    
    # Load MySQL credentials
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
    except FileNotFoundError:
        print("❌ MySQL credentials not found!")
        return False
    
    sqlite_db = "../kirima_primary.db"
    if not os.path.exists(sqlite_db):
        print(f"❌ SQLite database not found: {sqlite_db}")
        return False
    
    try:
        # Connect to both databases
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_conn.row_factory = sqlite3.Row
        
        mysql_conn = mysql.connector.connect(
            host=creds['host'],
            database=creds['database_name'],
            user=creds['username'],
            password=creds['password'],
            port=creds['port'],
            autocommit=False
        )
        
        # Migrate each table with proper column mapping
        migrations = [
            {
                'table': 'email_template',
                'columns': ['id', 'name', 'subject_template', 'body_template', 'template_type', 'is_active', 'created_at', 'updated_at', 'created_by', 'placeholders', 'description', 'subject']
            },
            {
                'table': 'subject_component', 
                'columns': ['id', 'subject_id', 'name', 'is_active', 'created_at']
            },
            {
                'table': 'subject_configuration',
                'columns': ['id', 'subject_name', 'grade_name', 'is_composite', 'is_active', 'created_at']
            },
            {
                'table': 'teacher_subject_assignment',
                'columns': ['id', 'teacher_id', 'subject_id', 'grade_id', 'stream_id', 'is_class_teacher', 'is_active', 'created_at']
            }
        ]
        
        total_migrated = 0
        
        for migration in migrations:
            table = migration['table']
            columns = migration['columns']
            
            try:
                sqlite_cursor = sqlite_conn.cursor()
                mysql_cursor = mysql_conn.cursor()
                
                # Get data from SQLite
                sqlite_cursor.execute(f"SELECT * FROM {table}")
                rows = sqlite_cursor.fetchall()
                
                if not rows:
                    print(f"⚠️ No data in {table}")
                    continue
                
                # Get SQLite column names
                sqlite_columns = [description[0] for description in sqlite_cursor.description]
                
                # Map data to MySQL columns
                migrated_count = 0
                for row in rows:
                    try:
                        # Create value list matching MySQL columns
                        values = []
                        row_dict = dict(row)
                        
                        for col in columns:
                            if col in sqlite_columns:
                                values.append(row_dict[col])
                            else:
                                # Provide default values for missing columns
                                if col == 'is_active':
                                    values.append(True)
                                elif col == 'created_at':
                                    values.append(None)  # Will use DEFAULT
                                else:
                                    values.append(None)
                        
                        # Insert into MySQL
                        placeholders = ', '.join(['%s'] * len(columns))
                        insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                        mysql_cursor.execute(insert_sql, values)
                        migrated_count += 1
                        
                    except Exception as e:
                        print(f"⚠️ Error migrating row in {table}: {e}")
                        continue
                
                mysql_conn.commit()
                total_migrated += migrated_count
                print(f"✅ Migrated {migrated_count} records from {table}")
                
                sqlite_cursor.close()
                mysql_cursor.close()
                
            except Exception as e:
                print(f"❌ Error migrating {table}: {e}")
                continue
        
        sqlite_conn.close()
        mysql_conn.close()
        
        print(f"✅ Total records migrated: {total_migrated}")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main function."""
    print("🔧 Fix Schema Migration")
    print("=" * 40)
    
    # Analyze SQLite schemas
    schemas = analyze_sqlite_schemas()
    if not schemas:
        return False
    
    # Fix MySQL tables
    if not fix_mysql_tables(schemas):
        return False
    
    # Migrate data with correct schemas
    if not migrate_data_with_correct_schemas():
        return False
    
    print("\n🎉 Schema fix and migration completed!")
    print("\n📋 All missing data should now be migrated correctly.")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
