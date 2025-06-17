#!/usr/bin/env python3
"""
Fix subject_configuration table and complete 100% migration
"""

import sqlite3
import mysql.connector
import json
import os

def fix_subject_configuration_table():
    """Fix the subject_configuration table schema and migrate data."""
    print("🔧 Fixing subject_configuration table...")
    
    # Load MySQL credentials
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
    except FileNotFoundError:
        print("❌ MySQL credentials not found!")
        return False
    
    # First, let's check the exact SQLite schema
    sqlite_db = "../kirima_primary.db"
    if not os.path.exists(sqlite_db):
        print(f"❌ SQLite database not found: {sqlite_db}")
        return False
    
    try:
        # Connect to SQLite to get exact schema
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Get exact column structure
        sqlite_cursor.execute("PRAGMA table_info(subject_configuration)")
        columns_info = sqlite_cursor.fetchall()
        
        print("📋 SQLite subject_configuration schema:")
        for col in columns_info:
            print(f"   {col[1]:<25} {col[2]:<15} {'NOT NULL' if col[3] else 'NULL'}")
        
        # Get sample data to understand structure
        sqlite_cursor.execute("SELECT * FROM subject_configuration LIMIT 1")
        sample_row = sqlite_cursor.fetchone()
        
        if sample_row:
            print(f"\n📋 Sample data ({len(sample_row)} values):")
            for i, (col_info, value) in enumerate(zip(columns_info, sample_row)):
                print(f"   {col_info[1]:<25} = {value}")
        
        # Connect to MySQL
        mysql_conn = mysql.connector.connect(
            host=creds['host'],
            database=creds['database_name'],
            user=creds['username'],
            password=creds['password'],
            port=creds['port'],
            autocommit=True
        )
        
        mysql_cursor = mysql_conn.cursor()
        
        # Drop and recreate table with exact SQLite schema
        mysql_cursor.execute("DROP TABLE IF EXISTS subject_configuration")
        
        # Create table with exact column names from SQLite
        create_sql = """CREATE TABLE subject_configuration (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject_name TEXT NOT NULL,
            education_level TEXT NOT NULL,
            is_composite BOOLEAN DEFAULT FALSE,
            component_1_name TEXT,
            component_1_weight DECIMAL(5,2),
            component_2_name TEXT,
            component_2_weight DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"""
        
        mysql_cursor.execute(create_sql)
        print("✅ Recreated subject_configuration table with correct schema")
        
        # Now migrate the data
        sqlite_cursor.execute("SELECT * FROM subject_configuration")
        rows = sqlite_cursor.fetchall()
        
        if rows:
            # Get column names
            column_names = [description[0] for description in sqlite_cursor.description]
            
            # Prepare insert statement
            placeholders = ', '.join(['%s'] * len(column_names))
            column_list = ', '.join([f'`{col}`' for col in column_names])
            insert_sql = f"INSERT INTO subject_configuration ({column_list}) VALUES ({placeholders})"
            
            migrated_count = 0
            for row in rows:
                try:
                    mysql_cursor.execute(insert_sql, row)
                    migrated_count += 1
                except Exception as e:
                    print(f"⚠️ Error migrating row: {e}")
                    print(f"   Row data: {row}")
                    continue
            
            print(f"✅ Migrated {migrated_count}/{len(rows)} records to subject_configuration")
        
        sqlite_conn.close()
        mysql_conn.close()
        
        return migrated_count > 0
        
    except Exception as e:
        print(f"❌ Error fixing subject_configuration: {e}")
        return False

def final_100_percent_verification():
    """Final verification that we have 100% migration."""
    print("\n🔍 FINAL 100% MIGRATION VERIFICATION")
    print("=" * 60)
    
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
        sqlite_cursor = sqlite_conn.cursor()
        
        mysql_conn = mysql.connector.connect(
            host=creds['host'],
            database=creds['database_name'],
            user=creds['username'],
            password=creds['password'],
            port=creds['port']
        )
        mysql_cursor = mysql_conn.cursor()
        
        # Get all SQLite tables
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        sqlite_tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        # Get all MySQL tables
        mysql_cursor.execute("SHOW TABLES")
        mysql_tables = [row[0] for row in mysql_cursor.fetchall()]
        
        print(f"📊 SQLite Tables: {len(sqlite_tables)}")
        print(f"📊 MySQL Tables: {len(mysql_tables)}")
        
        # Check table counts
        print(f"\n{'Table':<30} {'SQLite':<10} {'MySQL':<10} {'Status'}")
        print("-" * 60)
        
        total_sqlite_records = 0
        total_mysql_records = 0
        perfect_matches = 0
        mismatches = []
        
        for table in sorted(sqlite_tables):
            try:
                # Get SQLite count
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                sqlite_count = sqlite_cursor.fetchone()[0]
                total_sqlite_records += sqlite_count
                
                # Get MySQL count
                if table in mysql_tables:
                    mysql_cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                    mysql_count = mysql_cursor.fetchone()[0]
                    total_mysql_records += mysql_count
                    
                    if sqlite_count == mysql_count:
                        status = "✅ PERFECT"
                        perfect_matches += 1
                    else:
                        status = f"❌ MISSING {sqlite_count - mysql_count}"
                        mismatches.append({
                            'table': table,
                            'sqlite': sqlite_count,
                            'mysql': mysql_count,
                            'missing': sqlite_count - mysql_count
                        })
                else:
                    mysql_count = 0
                    status = "❌ NO TABLE"
                    mismatches.append({
                        'table': table,
                        'sqlite': sqlite_count,
                        'mysql': 0,
                        'missing': sqlite_count
                    })
                
                print(f"{table:<30} {sqlite_count:<10} {mysql_count:<10} {status}")
                
            except Exception as e:
                print(f"{table:<30} ERROR: {e}")
        
        print("-" * 60)
        print(f"TOTALS{'':<24} {total_sqlite_records:<10} {total_mysql_records:<10}")
        
        # Final summary
        print(f"\n📊 MIGRATION SUMMARY:")
        print(f"✅ Perfect Matches: {perfect_matches}/{len(sqlite_tables)} tables")
        print(f"❌ Mismatches: {len(mismatches)} tables")
        print(f"📊 Total Records: {total_mysql_records}/{total_sqlite_records} ({(total_mysql_records/total_sqlite_records*100):.1f}%)")
        
        if not mismatches:
            print(f"\n🎉 100% MIGRATION ACHIEVED!")
            print(f"✅ ALL {len(sqlite_tables)} tables migrated")
            print(f"✅ ALL {total_sqlite_records} records migrated")
            print(f"✅ ZERO missing data")
            success = True
        else:
            print(f"\n⚠️ Still have {len(mismatches)} mismatches:")
            for mismatch in mismatches:
                print(f"   - {mismatch['table']}: Missing {mismatch['missing']} records")
            success = False
        
        sqlite_conn.close()
        mysql_conn.close()
        
        return success
        
    except Exception as e:
        print(f"❌ Error in verification: {e}")
        return False

def main():
    """Main function to complete 100% migration."""
    print("🎯 COMPLETING 100% MIGRATION")
    print("=" * 50)
    
    # Fix subject_configuration table
    if fix_subject_configuration_table():
        print("✅ subject_configuration fixed and migrated")
    else:
        print("❌ Failed to fix subject_configuration")
        return False
    
    # Final verification
    success = final_100_percent_verification()
    
    if success:
        print(f"\n🎉 MISSION ACCOMPLISHED!")
        print(f"🎯 100% COMPLETE MIGRATION ACHIEVED!")
    else:
        print(f"\n⚠️ Migration not yet 100% complete")
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
