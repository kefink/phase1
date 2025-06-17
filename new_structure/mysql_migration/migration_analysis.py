#!/usr/bin/env python3
"""
Comprehensive Migration Analysis
Analyzes what was migrated and what might be missing.
"""

import sqlite3
import mysql.connector
import json
import os

def analyze_sqlite_database():
    """Analyze the original SQLite database."""
    print("📊 SQLite Database Analysis")
    print("=" * 50)
    
    sqlite_db = "../kirima_primary.db"
    if not os.path.exists(sqlite_db):
        print(f"❌ SQLite database not found: {sqlite_db}")
        return None
    
    try:
        conn = sqlite3.connect(sqlite_db)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Total Tables Found: {len(tables)}")
        print("\nTables and Record Counts:")
        print("-" * 50)
        
        sqlite_data = {}
        total_records = 0
        
        for table in sorted(tables):
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_records += count
                sqlite_data[table] = count
                print(f"{table:<25} {count:>8} records")
                
                # Show structure for important tables
                if count > 0 and table in ['parent', 'parent_student', 'student', 'teacher', 'mark']:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    print(f"  └─ Columns: {', '.join([col[1] for col in columns[:5]])}{'...' if len(columns) > 5 else ''}")
                    
            except Exception as e:
                print(f"{table:<25} ERROR: {e}")
                sqlite_data[table] = 0
        
        print("-" * 50)
        print(f"Total Records: {total_records:>8}")
        
        # Check for parent portal tables specifically
        print("\n🔍 Parent Portal Tables Analysis:")
        print("-" * 40)
        parent_tables = ['parent', 'parent_student', 'parent_email_log', 'email_template']
        for table in parent_tables:
            if table in tables:
                count = sqlite_data.get(table, 0)
                status = "✅" if count > 0 else "⚠️"
                print(f"{status} {table:<20} {count:>5} records")
            else:
                print(f"❌ {table:<20} NOT FOUND")
        
        # Check for other important tables
        print("\n🔍 Core System Tables Analysis:")
        print("-" * 40)
        core_tables = ['student', 'teacher', 'grade', 'stream', 'subject', 'mark', 'term', 'assessment_type']
        for table in core_tables:
            if table in tables:
                count = sqlite_data.get(table, 0)
                status = "✅" if count > 0 else "⚠️"
                print(f"{status} {table:<20} {count:>5} records")
            else:
                print(f"❌ {table:<20} NOT FOUND")
        
        conn.close()
        return sqlite_data
        
    except Exception as e:
        print(f"❌ Error analyzing SQLite database: {e}")
        return None

def analyze_mysql_database():
    """Analyze the migrated MySQL database."""
    print("\n📊 MySQL Database Analysis")
    print("=" * 50)
    
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
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Total Tables Found: {len(tables)}")
        print("\nTables and Record Counts:")
        print("-" * 50)
        
        mysql_data = {}
        total_records = 0
        
        for table in sorted(tables):
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_records += count
                mysql_data[table] = count
                print(f"{table:<25} {count:>8} records")
                
            except Exception as e:
                print(f"{table:<25} ERROR: {e}")
                mysql_data[table] = 0
        
        print("-" * 50)
        print(f"Total Records: {total_records:>8}")
        
        cursor.close()
        connection.close()
        return mysql_data
        
    except Exception as e:
        print(f"❌ Error analyzing MySQL database: {e}")
        return None

def compare_databases(sqlite_data, mysql_data):
    """Compare SQLite and MySQL databases."""
    print("\n🔍 Migration Comparison Analysis")
    print("=" * 60)
    
    if not sqlite_data or not mysql_data:
        print("❌ Cannot compare - missing database data")
        return
    
    # Get all unique tables
    all_tables = set(sqlite_data.keys()) | set(mysql_data.keys())
    
    print(f"{'Table':<25} {'SQLite':<10} {'MySQL':<10} {'Status':<15}")
    print("-" * 60)
    
    missing_tables = []
    data_mismatches = []
    successful_migrations = []
    
    for table in sorted(all_tables):
        sqlite_count = sqlite_data.get(table, 0)
        mysql_count = mysql_data.get(table, 0)
        
        if table not in mysql_data:
            status = "❌ NOT MIGRATED"
            missing_tables.append(table)
        elif sqlite_count == 0 and mysql_count == 0:
            status = "⚠️ EMPTY"
        elif sqlite_count == mysql_count:
            status = "✅ MATCH"
            successful_migrations.append(table)
        else:
            status = "⚠️ MISMATCH"
            data_mismatches.append((table, sqlite_count, mysql_count))
        
        print(f"{table:<25} {sqlite_count:<10} {mysql_count:<10} {status}")
    
    # Summary
    print("\n📊 Migration Summary:")
    print("-" * 30)
    print(f"✅ Successfully migrated: {len(successful_migrations)} tables")
    print(f"⚠️ Data mismatches: {len(data_mismatches)} tables")
    print(f"❌ Missing tables: {len(missing_tables)} tables")
    
    if missing_tables:
        print(f"\n❌ Tables NOT migrated:")
        for table in missing_tables:
            print(f"   - {table} ({sqlite_data.get(table, 0)} records)")
    
    if data_mismatches:
        print(f"\n⚠️ Data mismatches:")
        for table, sqlite_count, mysql_count in data_mismatches:
            print(f"   - {table}: SQLite={sqlite_count}, MySQL={mysql_count}")
    
    # Check critical missing data
    critical_tables = ['parent', 'parent_student', 'student', 'mark']
    missing_critical = [t for t in critical_tables if t in missing_tables or (sqlite_data.get(t, 0) > 0 and mysql_data.get(t, 0) == 0)]
    
    if missing_critical:
        print(f"\n🚨 CRITICAL: Missing important data!")
        print("The following tables contain important data that wasn't migrated:")
        for table in missing_critical:
            print(f"   - {table}: {sqlite_data.get(table, 0)} records in SQLite")

def check_parent_portal_migration():
    """Specifically check parent portal migration."""
    print("\n👨‍👩‍👧‍👦 Parent Portal Migration Analysis")
    print("=" * 50)
    
    # Check SQLite for parent portal data
    sqlite_db = "../kirima_primary.db"
    if not os.path.exists(sqlite_db):
        print("❌ SQLite database not found")
        return
    
    try:
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Check parent portal tables in SQLite
        parent_portal_tables = ['parent', 'parent_student', 'parent_email_log', 'email_template']
        sqlite_parent_data = {}
        
        print("SQLite Parent Portal Data:")
        for table in parent_portal_tables:
            try:
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = sqlite_cursor.fetchone()[0]
                sqlite_parent_data[table] = count
                print(f"  {table}: {count} records")
                
                if count > 0:
                    # Show sample data
                    sqlite_cursor.execute(f"SELECT * FROM {table} LIMIT 2")
                    rows = sqlite_cursor.fetchall()
                    if rows:
                        print(f"    Sample: {len(rows[0])} columns")
                        
            except Exception as e:
                print(f"  {table}: ERROR - {e}")
                sqlite_parent_data[table] = 0
        
        sqlite_conn.close()
        
        # Check if parent portal data exists but wasn't migrated
        total_parent_records = sum(sqlite_parent_data.values())
        if total_parent_records > 0:
            print(f"\n🚨 FOUND {total_parent_records} parent portal records in SQLite!")
            print("These need to be migrated to MySQL.")
            return True
        else:
            print("\n✅ No parent portal data found in SQLite")
            return False
            
    except Exception as e:
        print(f"❌ Error checking parent portal data: {e}")
        return False

def main():
    """Main analysis function."""
    print("🔍 Comprehensive Migration Analysis")
    print("=" * 70)
    print("Analyzing what was migrated and what might be missing...")
    
    # Analyze both databases
    sqlite_data = analyze_sqlite_database()
    mysql_data = analyze_mysql_database()
    
    # Compare the databases
    if sqlite_data and mysql_data:
        compare_databases(sqlite_data, mysql_data)
    
    # Check parent portal specifically
    parent_portal_missing = check_parent_portal_migration()
    
    # Final recommendations
    print("\n🎯 Recommendations:")
    print("-" * 30)
    
    if parent_portal_missing:
        print("1. ❗ URGENT: Migrate parent portal data")
        print("   - Run additional migration for parent tables")
        print("   - Update MySQL schema if needed")
    
    print("2. ✅ Test the application with MySQL")
    print("3. ✅ Verify all features work correctly")
    print("4. ✅ Check data integrity in critical tables")
    
    return True

if __name__ == "__main__":
    main()
