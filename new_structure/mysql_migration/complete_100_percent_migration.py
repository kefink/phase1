#!/usr/bin/env python3
"""
100% Complete Migration Analysis and Execution
Ensures EVERY table and EVERY record is migrated from SQLite to MySQL.
"""

import sqlite3
import mysql.connector
import json
import os
from datetime import datetime

def get_complete_sqlite_analysis():
    """Get complete analysis of ALL SQLite tables and data."""
    print("🔍 COMPLETE SQLite Database Analysis")
    print("=" * 60)
    
    sqlite_db = "../kirima_primary.db"
    if not os.path.exists(sqlite_db):
        print(f"❌ SQLite database not found: {sqlite_db}")
        return None
    
    try:
        conn = sqlite3.connect(sqlite_db)
        cursor = conn.cursor()
        
        # Get ALL tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        complete_analysis = {}
        total_records = 0
        
        print(f"📋 Found {len(all_tables)} tables in SQLite")
        print("\nDETAILED TABLE ANALYSIS:")
        print("-" * 80)
        print(f"{'Table':<30} {'Records':<10} {'Columns':<10} {'Schema'}")
        print("-" * 80)
        
        for table in sorted(all_tables):
            try:
                # Get record count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                record_count = cursor.fetchone()[0]
                total_records += record_count
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table})")
                columns_info = cursor.fetchall()
                column_count = len(columns_info)
                
                # Get column details
                columns = []
                for col in columns_info:
                    columns.append({
                        'name': col[1],
                        'type': col[2],
                        'not_null': bool(col[3]),
                        'default': col[4],
                        'primary_key': bool(col[5])
                    })
                
                # Get sample data if exists
                sample_data = None
                if record_count > 0:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                    sample_data = cursor.fetchone()
                
                complete_analysis[table] = {
                    'record_count': record_count,
                    'columns': columns,
                    'sample_data': sample_data
                }
                
                # Display summary
                schema_summary = f"{column_count} cols"
                print(f"{table:<30} {record_count:<10} {column_count:<10} {schema_summary}")
                
                # Show important tables with data
                if record_count > 0:
                    print(f"  └─ Columns: {', '.join([col['name'] for col in columns[:5]])}{'...' if len(columns) > 5 else ''}")
                
            except Exception as e:
                print(f"{table:<30} ERROR: {e}")
                complete_analysis[table] = {'error': str(e)}
        
        print("-" * 80)
        print(f"TOTAL RECORDS IN SQLITE: {total_records}")
        print(f"TOTAL TABLES: {len(all_tables)}")
        
        conn.close()
        return complete_analysis
        
    except Exception as e:
        print(f"❌ Error analyzing SQLite: {e}")
        return None

def get_complete_mysql_analysis():
    """Get complete analysis of ALL MySQL tables and data."""
    print("\n🔍 COMPLETE MySQL Database Analysis")
    print("=" * 60)
    
    # Load MySQL credentials
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
    except FileNotFoundError:
        print("❌ MySQL credentials not found!")
        return None
    
    try:
        connection = mysql.connector.connect(
            host=creds['host'],
            database=creds['database_name'],
            user=creds['username'],
            password=creds['password'],
            port=creds['port']
        )
        
        cursor = connection.cursor()
        
        # Get ALL tables
        cursor.execute("SHOW TABLES")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        complete_analysis = {}
        total_records = 0
        
        print(f"📋 Found {len(all_tables)} tables in MySQL")
        print("\nDETAILED TABLE ANALYSIS:")
        print("-" * 80)
        print(f"{'Table':<30} {'Records':<10} {'Columns':<10} {'Schema'}")
        print("-" * 80)
        
        for table in sorted(all_tables):
            try:
                # Get record count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                record_count = cursor.fetchone()[0]
                total_records += record_count
                
                # Get table schema
                cursor.execute(f"DESCRIBE {table}")
                columns_info = cursor.fetchall()
                column_count = len(columns_info)
                
                # Get column details
                columns = []
                for col in columns_info:
                    columns.append({
                        'name': col[0],
                        'type': col[1],
                        'null': col[2] == 'YES',
                        'key': col[3],
                        'default': col[4],
                        'extra': col[5]
                    })
                
                complete_analysis[table] = {
                    'record_count': record_count,
                    'columns': columns
                }
                
                # Display summary
                schema_summary = f"{column_count} cols"
                print(f"{table:<30} {record_count:<10} {column_count:<10} {schema_summary}")
                
            except Exception as e:
                print(f"{table:<30} ERROR: {e}")
                complete_analysis[table] = {'error': str(e)}
        
        print("-" * 80)
        print(f"TOTAL RECORDS IN MYSQL: {total_records}")
        print(f"TOTAL TABLES: {len(all_tables)}")
        
        cursor.close()
        connection.close()
        return complete_analysis
        
    except Exception as e:
        print(f"❌ Error analyzing MySQL: {e}")
        return None

def identify_missing_data(sqlite_analysis, mysql_analysis):
    """Identify exactly what's missing in MySQL."""
    print("\n🚨 MISSING DATA ANALYSIS")
    print("=" * 60)
    
    if not sqlite_analysis or not mysql_analysis:
        print("❌ Cannot analyze - missing database data")
        return None
    
    missing_tables = []
    missing_data = []
    schema_mismatches = []
    
    print(f"{'Table':<30} {'SQLite':<10} {'MySQL':<10} {'Status':<20}")
    print("-" * 70)
    
    # Check every SQLite table
    for table, sqlite_info in sqlite_analysis.items():
        if 'error' in sqlite_info:
            continue
            
        sqlite_count = sqlite_info['record_count']
        
        if table not in mysql_analysis:
            missing_tables.append(table)
            print(f"{table:<30} {sqlite_count:<10} {'MISSING':<10} ❌ TABLE MISSING")
        else:
            mysql_count = mysql_analysis[table]['record_count']
            
            if sqlite_count != mysql_count:
                missing_data.append({
                    'table': table,
                    'sqlite_count': sqlite_count,
                    'mysql_count': mysql_count,
                    'missing': sqlite_count - mysql_count
                })
                status = f"❌ MISSING {sqlite_count - mysql_count}"
                print(f"{table:<30} {sqlite_count:<10} {mysql_count:<10} {status}")
            elif sqlite_count == 0:
                print(f"{table:<30} {sqlite_count:<10} {mysql_count:<10} ⚠️ EMPTY")
            else:
                print(f"{table:<30} {sqlite_count:<10} {mysql_count:<10} ✅ COMPLETE")
    
    # Summary
    print("\n📊 MISSING DATA SUMMARY:")
    print("-" * 40)
    print(f"❌ Missing Tables: {len(missing_tables)}")
    print(f"❌ Tables with Missing Data: {len(missing_data)}")
    
    if missing_tables:
        print(f"\n🚨 MISSING TABLES ({len(missing_tables)}):")
        for table in missing_tables:
            sqlite_count = sqlite_analysis[table]['record_count']
            print(f"   - {table}: {sqlite_count} records")
    
    if missing_data:
        print(f"\n🚨 MISSING DATA ({len(missing_data)} tables):")
        for item in missing_data:
            print(f"   - {item['table']}: Missing {item['missing']} records ({item['sqlite_count']} → {item['mysql_count']})")
    
    return {
        'missing_tables': missing_tables,
        'missing_data': missing_data,
        'sqlite_analysis': sqlite_analysis,
        'mysql_analysis': mysql_analysis
    }

def create_missing_tables_with_exact_schemas(missing_analysis):
    """Create missing tables with exact SQLite schemas."""
    print("\n🔧 CREATING MISSING TABLES WITH EXACT SCHEMAS")
    print("=" * 60)
    
    missing_tables = missing_analysis['missing_tables']
    sqlite_analysis = missing_analysis['sqlite_analysis']
    
    if not missing_tables:
        print("✅ No missing tables to create")
        return True
    
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
        
        for table in missing_tables:
            try:
                sqlite_info = sqlite_analysis[table]
                columns = sqlite_info['columns']
                
                # Build CREATE TABLE statement
                column_definitions = []
                primary_keys = []
                
                for col in columns:
                    # Map SQLite types to MySQL types
                    mysql_type = map_sqlite_to_mysql_type(col['type'])
                    
                    col_def = f"`{col['name']}` {mysql_type}"
                    
                    if col['not_null']:
                        col_def += " NOT NULL"
                    
                    if col['default'] is not None:
                        if col['default'].upper() in ['CURRENT_TIMESTAMP', 'NOW()']:
                            col_def += " DEFAULT CURRENT_TIMESTAMP"
                        else:
                            col_def += f" DEFAULT '{col['default']}'"
                    
                    if col['primary_key']:
                        if mysql_type.startswith('INT'):
                            col_def += " AUTO_INCREMENT"
                        primary_keys.append(col['name'])
                    
                    column_definitions.append(col_def)
                
                # Add primary key constraint
                if primary_keys:
                    column_definitions.append(f"PRIMARY KEY (`{'`, `'.join(primary_keys)}`)")
                
                column_defs_str = ',\n    '.join(column_definitions)
                create_sql = f"""CREATE TABLE `{table}` (
    {column_defs_str}
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"""
                
                cursor.execute(create_sql)
                print(f"✅ Created table: {table}")
                
            except Exception as e:
                print(f"❌ Error creating {table}: {e}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return False

def map_sqlite_to_mysql_type(sqlite_type):
    """Map SQLite data types to MySQL data types."""
    sqlite_type = sqlite_type.upper()
    
    type_mapping = {
        'INTEGER': 'INT',
        'TEXT': 'TEXT',
        'REAL': 'DECIMAL(10,2)',
        'BLOB': 'BLOB',
        'BOOLEAN': 'BOOLEAN',
        'DATETIME': 'DATETIME',
        'TIMESTAMP': 'TIMESTAMP',
        'VARCHAR(100)': 'VARCHAR(100)',
        'VARCHAR(50)': 'VARCHAR(50)',
        'VARCHAR(200)': 'VARCHAR(200)',
        'VARCHAR(255)': 'VARCHAR(255)',
        'VARCHAR(120)': 'VARCHAR(120)',
        'VARCHAR(20)': 'VARCHAR(20)'
    }
    
    # Check for exact matches first
    if sqlite_type in type_mapping:
        return type_mapping[sqlite_type]
    
    # Check for VARCHAR patterns
    if sqlite_type.startswith('VARCHAR'):
        return sqlite_type
    
    # Default mappings
    if 'INT' in sqlite_type:
        return 'INT'
    elif 'TEXT' in sqlite_type:
        return 'TEXT'
    elif 'REAL' in sqlite_type or 'FLOAT' in sqlite_type:
        return 'DECIMAL(10,2)'
    elif 'BLOB' in sqlite_type:
        return 'BLOB'
    else:
        return 'TEXT'  # Default fallback

def migrate_all_missing_data(missing_analysis):
    """Migrate ALL missing data from SQLite to MySQL."""
    print("\n🔄 MIGRATING ALL MISSING DATA")
    print("=" * 60)
    
    missing_tables = missing_analysis['missing_tables']
    missing_data = missing_analysis['missing_data']
    sqlite_analysis = missing_analysis['sqlite_analysis']
    
    # Tables that need data migration
    tables_to_migrate = []
    
    # Add tables that are completely missing
    for table in missing_tables:
        if sqlite_analysis[table]['record_count'] > 0:
            tables_to_migrate.append(table)
    
    # Add tables with missing data
    for item in missing_data:
        if item['missing'] > 0:
            tables_to_migrate.append(item['table'])
    
    if not tables_to_migrate:
        print("✅ No data to migrate")
        return True
    
    print(f"📋 Migrating data for {len(tables_to_migrate)} tables...")
    
    # Connect to databases
    sqlite_db = "../kirima_primary.db"
    
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
    except FileNotFoundError:
        print("❌ MySQL credentials not found!")
        return False
    
    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_conn.row_factory = sqlite3.Row
        
        # Connect to MySQL
        mysql_conn = mysql.connector.connect(
            host=creds['host'],
            database=creds['database_name'],
            user=creds['username'],
            password=creds['password'],
            port=creds['port'],
            autocommit=False
        )
        
        total_migrated = 0
        
        for table in tables_to_migrate:
            try:
                print(f"\n🔄 Migrating {table}...")
                
                sqlite_cursor = sqlite_conn.cursor()
                mysql_cursor = mysql_conn.cursor()
                
                # Clear existing data in MySQL for this table
                mysql_cursor.execute(f"DELETE FROM `{table}`")
                
                # Get all data from SQLite
                sqlite_cursor.execute(f"SELECT * FROM `{table}`")
                rows = sqlite_cursor.fetchall()
                
                if not rows:
                    print(f"   ⚠️ No data in {table}")
                    continue
                
                # Get column names
                columns = [description[0] for description in sqlite_cursor.description]
                
                # Prepare INSERT statement
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join([f'`{col}`' for col in columns])
                insert_sql = f"INSERT INTO `{table}` ({column_names}) VALUES ({placeholders})"
                
                # Insert all data
                migrated_count = 0
                for row in rows:
                    try:
                        values = [dict(row)[col] for col in columns]
                        mysql_cursor.execute(insert_sql, values)
                        migrated_count += 1
                    except Exception as e:
                        print(f"   ⚠️ Error migrating row: {e}")
                        continue
                
                mysql_conn.commit()
                total_migrated += migrated_count
                print(f"   ✅ Migrated {migrated_count}/{len(rows)} records")
                
                sqlite_cursor.close()
                mysql_cursor.close()
                
            except Exception as e:
                print(f"   ❌ Error migrating {table}: {e}")
                continue
        
        sqlite_conn.close()
        mysql_conn.close()
        
        print(f"\n✅ TOTAL RECORDS MIGRATED: {total_migrated}")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main 100% migration function."""
    print("🎯 100% COMPLETE MIGRATION ANALYSIS AND EXECUTION")
    print("=" * 70)
    print("Ensuring EVERY table and EVERY record is migrated!")
    
    # Step 1: Complete SQLite analysis
    sqlite_analysis = get_complete_sqlite_analysis()
    if not sqlite_analysis:
        return False
    
    # Step 2: Complete MySQL analysis
    mysql_analysis = get_complete_mysql_analysis()
    if not mysql_analysis:
        return False
    
    # Step 3: Identify missing data
    missing_analysis = identify_missing_data(sqlite_analysis, mysql_analysis)
    if not missing_analysis:
        return False
    
    # Step 4: Create missing tables
    if not create_missing_tables_with_exact_schemas(missing_analysis):
        return False
    
    # Step 5: Migrate all missing data
    if not migrate_all_missing_data(missing_analysis):
        return False
    
    # Step 6: Final verification
    print("\n🔍 FINAL VERIFICATION")
    print("=" * 40)
    final_mysql_analysis = get_complete_mysql_analysis()
    
    if final_mysql_analysis:
        final_missing = identify_missing_data(sqlite_analysis, final_mysql_analysis)
        
        missing_tables = final_missing['missing_tables']
        missing_data = final_missing['missing_data']
        
        if not missing_tables and not missing_data:
            print("\n🎉 100% MIGRATION SUCCESSFUL!")
            print("✅ ALL tables migrated")
            print("✅ ALL data migrated")
            print("✅ ZERO missing records")
        else:
            print(f"\n⚠️ Still missing: {len(missing_tables)} tables, {len(missing_data)} data mismatches")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
