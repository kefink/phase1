#!/usr/bin/env python3
"""
MySQL Connection Test Script
This script tests MySQL connectivity before running the migration.
"""

import mysql.connector
from mysql.connector import Error
import sys

def test_mysql_connection():
    """Test MySQL connection with user input."""
    print("🔍 MySQL Connection Test")
    print("=" * 30)
    
    # Get connection details
    host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    port = input("MySQL Port (default: 3306): ").strip() or "3306"
    username = input("MySQL Username (default: root): ").strip() or "root"
    
    # Get password securely
    import getpass
    password = getpass.getpass("MySQL Password: ")
    
    try:
        port = int(port)
    except ValueError:
        print("❌ Invalid port number")
        return False
    
    try:
        print(f"\n🔄 Connecting to MySQL at {host}:{port}...")
        
        # Test connection
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            autocommit=True
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Get MySQL version
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            print(f"✅ MySQL Server connected successfully!")
            print(f"✅ MySQL Version: {version}")
            
            # Test database creation permissions
            try:
                cursor.execute("CREATE DATABASE IF NOT EXISTS test_hillview_connection")
                cursor.execute("DROP DATABASE test_hillview_connection")
                print("✅ Database creation permissions: OK")
            except Error as e:
                print(f"⚠️ Database creation test failed: {e}")
                print("You may need GRANT privileges for database creation")
            
            # Show existing databases
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            print(f"✅ Existing databases: {', '.join(databases)}")
            
            cursor.close()
            connection.close()
            
            print("\n🎉 MySQL connection test successful!")
            print("✅ Ready to proceed with migration!")
            
            # Save connection details for migration
            connection_info = {
                'host': host,
                'port': port,
                'username': username,
                'password': password
            }
            
            import json
            with open('mysql_connection.json', 'w') as f:
                json.dump(connection_info, f, indent=2)
            print("💾 Connection details saved to mysql_connection.json")
            
            return True
        else:
            print("❌ Failed to connect to MySQL")
            return False
            
    except Error as e:
        print(f"❌ MySQL connection error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure MySQL server is running")
        print("2. Check username and password")
        print("3. Verify host and port")
        print("4. Check firewall settings")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_mysql_service():
    """Check if MySQL service is running."""
    print("\n🔍 Checking MySQL Service Status...")
    
    import subprocess
    import platform
    
    try:
        if platform.system() == "Windows":
            # Check Windows service
            result = subprocess.run(['sc', 'query', 'MySQL80'], 
                                  capture_output=True, text=True)
            if 'RUNNING' in result.stdout:
                print("✅ MySQL80 service is running")
                return True
            else:
                print("⚠️ MySQL80 service is not running")
                print("Please start MySQL service:")
                print("1. Open Services (services.msc)")
                print("2. Find 'MySQL80' service")
                print("3. Right-click and select 'Start'")
                print("Or run as administrator: net start MySQL80")
                return False
        else:
            # Check Linux/Mac service
            result = subprocess.run(['systemctl', 'is-active', 'mysql'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ MySQL service is running")
                return True
            else:
                print("⚠️ MySQL service is not running")
                print("Please start MySQL service: sudo systemctl start mysql")
                return False
                
    except Exception as e:
        print(f"⚠️ Could not check service status: {e}")
        print("Please manually verify MySQL service is running")
        return None

def main():
    """Main function."""
    print("🚀 Hillview MySQL Migration - Connection Test")
    print("=" * 50)
    
    # Check service status first
    service_status = check_mysql_service()
    
    if service_status is False:
        print("\n❌ MySQL service is not running. Please start it first.")
        return False
    
    # Test connection
    connection_success = test_mysql_connection()
    
    if connection_success:
        print("\n🎯 Next Steps:")
        print("1. Run the migration: python run_migration.py")
        print("2. Or run individual steps:")
        print("   - python mysql_setup.py")
        print("   - python schema_migration.py")
        print("   - python data_migration.py")
        return True
    else:
        print("\n❌ Connection test failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
