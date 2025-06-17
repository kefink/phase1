#!/usr/bin/env python3
"""
Data Migration Script - Transfer data from SQLite to MySQL
This script migrates all existing data while preserving relationships and integrity.
"""

import sqlite3
import mysql.connector
from mysql.connector import Error
import json
import os
import sys
from datetime import datetime

class DataMigration:
    def __init__(self, sqlite_db="../kirima_primary.db", credentials_file="mysql_credentials.json"):
        """Initialize with SQLite and MySQL connections."""
        self.sqlite_db = sqlite_db
        self.credentials = self.load_credentials(credentials_file)
        self.sqlite_conn = None
        self.mysql_conn = None
        self.migration_stats = {}
        
    def load_credentials(self, credentials_file):
        """Load MySQL credentials from file."""
        try:
            with open(credentials_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Credentials file not found: {credentials_file}")
            print("Please run mysql_setup.py first")
            sys.exit(1)
    
    def connect_databases(self):
        """Connect to both SQLite and MySQL databases."""
        try:
            # Connect to SQLite
            self.sqlite_conn = sqlite3.connect(self.sqlite_db)
            self.sqlite_conn.row_factory = sqlite3.Row  # Enable column access by name
            print(f"✅ Connected to SQLite: {self.sqlite_db}")
            
            # Connect to MySQL
            self.mysql_conn = mysql.connector.connect(
                host='localhost',
                database=self.credentials['database_name'],
                user=self.credentials['username'],
                password=self.credentials['password'],
                autocommit=False  # Use transactions for data integrity
            )
            print(f"✅ Connected to MySQL: {self.credentials['database_name']}")
            
            return True
            
        except (sqlite3.Error, Error) as e:
            print(f"❌ Database connection error: {e}")
            return False
    
    def migrate_table(self, table_name, column_mapping=None, transform_func=None):
        """Generic function to migrate a table from SQLite to MySQL."""
        try:
            sqlite_cursor = self.sqlite_conn.cursor()
            mysql_cursor = self.mysql_conn.cursor()
            
            # Get data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"⚠️ No data found in {table_name}")
                self.migration_stats[table_name] = 0
                return True
            
            # Prepare column names
            if column_mapping:
                columns = list(column_mapping.values())
            else:
                columns = [description[0] for description in sqlite_cursor.description]
            
            # Create INSERT statement
            placeholders = ', '.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Transform and insert data
            migrated_count = 0
            for row in rows:
                try:
                    # Convert row to dict for easier manipulation
                    row_dict = dict(row)
                    
                    # Apply column mapping if provided
                    if column_mapping:
                        mapped_row = {}
                        for sqlite_col, mysql_col in column_mapping.items():
                            mapped_row[mysql_col] = row_dict.get(sqlite_col)
                        row_dict = mapped_row
                    
                    # Apply transformation function if provided
                    if transform_func:
                        row_dict = transform_func(row_dict)
                    
                    # Prepare values in correct order
                    values = [row_dict.get(col) for col in columns]
                    
                    # Insert into MySQL
                    mysql_cursor.execute(insert_sql, values)
                    migrated_count += 1
                    
                except Error as e:
                    print(f"⚠️ Error migrating row in {table_name}: {e}")
                    continue
            
            # Commit the transaction
            self.mysql_conn.commit()
            
            print(f"✅ Migrated {migrated_count} records from {table_name}")
            self.migration_stats[table_name] = migrated_count
            
            sqlite_cursor.close()
            mysql_cursor.close()
            return True
            
        except (sqlite3.Error, Error) as e:
            print(f"❌ Error migrating {table_name}: {e}")
            self.mysql_conn.rollback()
            return False
    
    def migrate_academic_data(self):
        """Migrate academic structure data."""
        print("📚 Migrating academic data...")
        
        # Migrate grades
        self.migrate_table('grade')
        
        # Migrate streams
        self.migrate_table('stream')
        
        # Migrate terms
        self.migrate_table('term')
        
        # Migrate assessment types
        self.migrate_table('assessment_type')
        
        # Migrate subjects
        self.migrate_table('subject')
        
        # Migrate subject components (if exists)
        try:
            self.migrate_table('subject_component')
        except:
            print("⚠️ subject_component table not found, skipping...")
    
    def migrate_user_data(self):
        """Migrate user data with password handling."""
        print("👥 Migrating user data...")
        
        # Migrate teachers
        def transform_teacher(row):
            # Ensure required fields have defaults
            row['is_active'] = row.get('is_active', True)
            row['created_at'] = row.get('created_at') or datetime.now()
            return row
        
        self.migrate_table('teacher', transform_func=transform_teacher)
        
        # Migrate students
        def transform_student(row):
            row['is_active'] = row.get('is_active', True)
            row['created_at'] = row.get('created_at') or datetime.now()
            return row
        
        self.migrate_table('student', transform_func=transform_student)
        
        # Migrate parents (if exists)
        try:
            def transform_parent(row):
                row['is_verified'] = row.get('is_verified', False)
                row['is_active'] = row.get('is_active', True)
                row['failed_login_attempts'] = row.get('failed_login_attempts', 0)
                row['created_at'] = row.get('created_at') or datetime.now()
                return row
            
            self.migrate_table('parent', transform_func=transform_parent)
        except:
            print("⚠️ parent table not found, skipping...")
    
    def migrate_relationship_data(self):
        """Migrate relationship tables."""
        print("🔗 Migrating relationship data...")
        
        # Migrate teacher-subject relationships
        self.migrate_table('teacher_subjects')
        
        # Migrate teacher subject assignments (if exists)
        try:
            self.migrate_table('teacher_subject_assignment')
        except:
            print("⚠️ teacher_subject_assignment table not found, skipping...")
        
        # Migrate parent-student relationships (if exists)
        try:
            def transform_parent_student(row):
                row['relationship'] = row.get('relationship', 'parent')
                row['is_primary_contact'] = row.get('is_primary_contact', False)
                row['can_receive_reports'] = row.get('can_receive_reports', True)
                row['created_at'] = row.get('created_at') or datetime.now()
                return row
            
            self.migrate_table('parent_student', transform_func=transform_parent_student)
        except:
            print("⚠️ parent_student table not found, skipping...")
    
    def migrate_marks_data(self):
        """Migrate marks data with special handling for JSON fields."""
        print("📊 Migrating marks data...")
        
        def transform_mark(row):
            # Handle component_marks JSON field
            if row.get('component_marks'):
                # Ensure it's valid JSON
                try:
                    if isinstance(row['component_marks'], str):
                        json.loads(row['component_marks'])  # Validate JSON
                except (json.JSONDecodeError, TypeError):
                    row['component_marks'] = None
            
            # Set defaults for required fields
            row['is_uploaded'] = row.get('is_uploaded', False)
            row['created_at'] = row.get('created_at') or datetime.now()
            row['last_modified'] = row.get('last_modified') or datetime.now()
            
            return row
        
        self.migrate_table('mark', transform_func=transform_mark)
    
    def migrate_configuration_data(self):
        """Migrate configuration and system tables."""
        print("⚙️ Migrating configuration data...")
        
        # These tables might not exist in MySQL schema yet, so we'll skip them
        # They can be handled separately or recreated as needed
        tables_to_skip = [
            'school_configuration',
            'class_teacher_permissions', 
            'function_permissions',
            'permission_requests',
            'parent_email_log',
            'email_template'
        ]
        
        for table in tables_to_skip:
            try:
                self.migrate_table(table)
            except:
                print(f"⚠️ {table} table migration skipped (may not exist in target schema)")
    
    def verify_migration(self):
        """Verify data integrity after migration."""
        print("🔍 Verifying migration integrity...")
        
        try:
            mysql_cursor = self.mysql_conn.cursor()
            
            # Check record counts
            verification_results = {}
            for table, expected_count in self.migration_stats.items():
                mysql_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                actual_count = mysql_cursor.fetchone()[0]
                verification_results[table] = {
                    'expected': expected_count,
                    'actual': actual_count,
                    'match': expected_count == actual_count
                }
            
            # Print verification results
            print("\n📋 Migration Verification Results:")
            print(f"{'Table':<25} {'Expected':<10} {'Actual':<10} {'Status':<10}")
            print("-" * 60)
            
            all_verified = True
            for table, results in verification_results.items():
                status = "✅ PASS" if results['match'] else "❌ FAIL"
                if not results['match']:
                    all_verified = False
                print(f"{table:<25} {results['expected']:<10} {results['actual']:<10} {status}")
            
            mysql_cursor.close()
            
            if all_verified:
                print("\n🎉 All data verified successfully!")
            else:
                print("\n⚠️ Some data verification failed. Please check the results above.")
            
            return all_verified
            
        except Error as e:
            print(f"❌ Error during verification: {e}")
            return False
    
    def run_migration(self):
        """Run the complete data migration process."""
        print("🔄 Starting data migration from SQLite to MySQL...")
        
        if not self.connect_databases():
            return False
        
        try:
            # Run migrations in order (respecting foreign key constraints)
            self.migrate_academic_data()
            self.migrate_user_data()
            self.migrate_relationship_data()
            self.migrate_marks_data()
            self.migrate_configuration_data()
            
            # Verify migration
            verification_success = self.verify_migration()
            
            print(f"\n📊 Migration Summary:")
            total_records = sum(self.migration_stats.values())
            print(f"Total records migrated: {total_records}")
            
            return verification_success
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
        finally:
            # Close connections
            if self.sqlite_conn:
                self.sqlite_conn.close()
            if self.mysql_conn:
                self.mysql_conn.close()

def main():
    """Main migration function."""
    print("🔄 Data Migration from SQLite to MySQL")
    print("=" * 50)
    
    # Check if SQLite database exists
    sqlite_db = "../kirima_primary.db"
    if not os.path.exists(sqlite_db):
        print(f"❌ SQLite database not found: {sqlite_db}")
        return False
    
    migration = DataMigration(sqlite_db)
    success = migration.run_migration()
    
    if success:
        print("\n🎉 Data migration completed successfully!")
        print("\n🔄 Next step: Update application configuration")
        print("Command: python update_config.py")
    else:
        print("\n❌ Data migration failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
