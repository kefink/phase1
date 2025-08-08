#!/usr/bin/env python3
"""
Database Identification Script
This script identifies the database being used in your system.
"""

import sys
import os

def identify_database():
    """Identify the database configuration and test connection."""
    
    print("🔍 DATABASE IDENTIFICATION")
    print("=" * 40)
    
    try:
        # Import config
        from config import Config
        
        # Get database URI
        db_uri = Config.SQLALCHEMY_DATABASE_URI
        print(f"📊 Database URI: {db_uri}")
        
        # Parse the URI to get details
        if db_uri.startswith('mysql'):
            print("🗄️  Database Type: MySQL")
            
            # Extract details from URI
            import re
            pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
            match = re.match(pattern, db_uri)
            
            if match:
                username, password, host, port, database = match.groups()
                print(f"🏠 Host: {host}")
                print(f"🔌 Port: {port}")
                print(f"👤 Username: {username}")
                print(f"🗄️  Database Name: {database}")
                
                # Test connection
                print(f"\n🔗 Testing database connection...")
                try:
                    import pymysql
                    connection = pymysql.connect(
                        host=host,
                        port=int(port),
                        user=username,
                        password=password.replace('%40', '@').replace('%2F', '/'),
                        database=database,
                        charset='utf8mb4'
                    )
                    
                    cursor = connection.cursor()
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()
                    print(f"✅ Connection successful!")
                    print(f"📊 MySQL Version: {version[0]}")
                    
                    # List tables
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    print(f"📋 Total tables: {len(tables)}")
                    
                    if tables:
                        print("🗂️  Sample tables:")
                        for i, table in enumerate(tables[:10]):  # Show first 10 tables
                            print(f"   - {table[0]}")
                            if i == 9 and len(tables) > 10:
                                print(f"   ... and {len(tables) - 10} more")
                    
                    cursor.close()
                    connection.close()
                    
                    return True
                    
                except Exception as e:
                    print(f"❌ Connection failed: {e}")
                    return False
            else:
                print("❌ Could not parse database URI")
                return False
                
        elif db_uri.startswith('sqlite'):
            print("🗄️  Database Type: SQLite")
            # Extract SQLite database path
            db_path = db_uri.replace('sqlite:///', '')
            print(f"📁 Database file: {db_path}")
            
            if os.path.exists(db_path):
                print("✅ Database file exists")
                
                try:
                    import sqlite3
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # List tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    print(f"📋 Total tables: {len(tables)}")
                    
                    if tables:
                        print("🗂️  Tables:")
                        for table in tables:
                            print(f"   - {table[0]}")
                    
                    conn.close()
                    return True
                    
                except Exception as e:
                    print(f"❌ SQLite connection failed: {e}")
                    return False
            else:
                print("❌ Database file not found")
                return False
        else:
            print(f"❓ Unknown database type: {db_uri}")
            return False
            
    except Exception as e:
        print(f"❌ Error identifying database: {e}")
        return False

if __name__ == '__main__':
    identify_database()
