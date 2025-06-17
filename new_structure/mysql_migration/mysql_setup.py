#!/usr/bin/env python3
"""
MySQL Setup and Configuration Script for Hillview School Management System
This script sets up MySQL server, creates databases, and configures users for multi-tenant architecture.
"""

import mysql.connector
from mysql.connector import Error
import os
import sys
import json
from datetime import datetime

class MySQLSetup:
    def __init__(self, host='localhost', port=3306, admin_user='root', admin_password=None):
        """Initialize MySQL setup with admin credentials."""
        self.host = host
        self.port = port
        self.admin_user = admin_user
        self.admin_password = admin_password or self.get_admin_password()
        self.connection = None
        
    def get_admin_password(self):
        """Get MySQL admin password from user input."""
        import getpass
        return getpass.getpass("Enter MySQL root password: ")
    
    def connect_admin(self):
        """Connect to MySQL as admin user."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                autocommit=True
            )
            print(f"✅ Connected to MySQL server at {self.host}:{self.port}")
            return True
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            return False
    
    def create_master_database(self):
        """Create the master database for tenant management."""
        try:
            cursor = self.connection.cursor()
            
            # Create master database
            cursor.execute("CREATE DATABASE IF NOT EXISTS hillview_master CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Created master database: hillview_master")
            
            # Use master database
            cursor.execute("USE hillview_master")
            
            # Create tenants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tenant_code VARCHAR(50) UNIQUE NOT NULL,
                    school_name VARCHAR(200) NOT NULL,
                    database_name VARCHAR(100) UNIQUE NOT NULL,
                    admin_email VARCHAR(120) NOT NULL,
                    subscription_plan VARCHAR(50) DEFAULT 'basic',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_tenant_code (tenant_code),
                    INDEX idx_database_name (database_name)
                )
            """)
            print("✅ Created tenants table")
            
            # Create tenant_users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenant_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tenant_id INT NOT NULL,
                    username VARCHAR(100) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    privileges TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_tenant_user (tenant_id, username)
                )
            """)
            print("✅ Created tenant_users table")
            
            # Create tenant_settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenant_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tenant_id INT NOT NULL,
                    setting_key VARCHAR(100) NOT NULL,
                    setting_value TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_tenant_setting (tenant_id, setting_key)
                )
            """)
            print("✅ Created tenant_settings table")
            
            cursor.close()
            return True
            
        except Error as e:
            print(f"❌ Error creating master database: {e}")
            return False
    
    def create_tenant_database(self, tenant_code, school_name, admin_email):
        """Create a new tenant database for a school."""
        try:
            cursor = self.connection.cursor()
            
            # Generate database name
            db_name = f"hillview_{tenant_code.lower()}"
            
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Created tenant database: {db_name}")
            
            # Create database user
            user_name = f"hillview_{tenant_code.lower()}_user"
            user_password = self.generate_password()
            
            cursor.execute(f"CREATE USER IF NOT EXISTS '{user_name}'@'%' IDENTIFIED BY '{user_password}'")
            cursor.execute(f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{user_name}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
            print(f"✅ Created database user: {user_name}")
            
            # Register tenant in master database
            cursor.execute("USE hillview_master")
            cursor.execute("""
                INSERT INTO tenants (tenant_code, school_name, database_name, admin_email)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                school_name = VALUES(school_name),
                admin_email = VALUES(admin_email),
                updated_at = CURRENT_TIMESTAMP
            """, (tenant_code, school_name, db_name, admin_email))
            
            tenant_id = cursor.lastrowid or self.get_tenant_id(tenant_code)
            
            # Store database credentials
            cursor.execute("""
                INSERT INTO tenant_users (tenant_id, username, password_hash, privileges)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                password_hash = VALUES(password_hash),
                privileges = VALUES(privileges)
            """, (tenant_id, user_name, user_password, 'ALL'))
            
            print(f"✅ Registered tenant: {tenant_code}")
            
            cursor.close()
            
            return {
                'tenant_code': tenant_code,
                'database_name': db_name,
                'username': user_name,
                'password': user_password,
                'tenant_id': tenant_id
            }
            
        except Error as e:
            print(f"❌ Error creating tenant database: {e}")
            return None
    
    def generate_password(self, length=16):
        """Generate a secure random password."""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def get_tenant_id(self, tenant_code):
        """Get tenant ID by tenant code."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM tenants WHERE tenant_code = %s", (tenant_code,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        except Error:
            return None
    
    def setup_connection_pooling(self):
        """Configure MySQL for connection pooling."""
        try:
            cursor = self.connection.cursor()
            
            # Set MySQL variables for better performance
            mysql_config = [
                "SET GLOBAL max_connections = 500",
                "SET GLOBAL innodb_buffer_pool_size = 1073741824",  # 1GB
                "SET GLOBAL query_cache_size = 67108864",  # 64MB
                "SET GLOBAL query_cache_type = 1",
                "SET GLOBAL slow_query_log = 1",
                "SET GLOBAL long_query_time = 2"
            ]
            
            for config in mysql_config:
                try:
                    cursor.execute(config)
                    print(f"✅ Applied: {config}")
                except Error as e:
                    print(f"⚠️ Could not apply: {config} - {e}")
            
            cursor.close()
            return True
            
        except Error as e:
            print(f"❌ Error configuring MySQL: {e}")
            return False
    
    def create_sample_tenant(self):
        """Create a sample tenant for testing."""
        return self.create_tenant_database(
            tenant_code="DEMO001",
            school_name="Demo Primary School",
            admin_email="admin@demo.school"
        )
    
    def close_connection(self):
        """Close MySQL connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ MySQL connection closed")

def main():
    """Main setup function."""
    print("🚀 MySQL Setup for Hillview School Management System")
    print("=" * 60)
    
    # Get MySQL connection details
    host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    port = input("MySQL Port (default: 3306): ").strip() or "3306"
    
    try:
        port = int(port)
    except ValueError:
        print("❌ Invalid port number")
        return False
    
    # Initialize setup
    setup = MySQLSetup(host=host, port=port)
    
    # Connect to MySQL
    if not setup.connect_admin():
        return False
    
    # Create master database
    if not setup.create_master_database():
        return False
    
    # Configure MySQL for performance
    setup.setup_connection_pooling()
    
    # Create sample tenant
    print("\n📋 Creating sample tenant...")
    tenant_info = setup.create_sample_tenant()
    
    if tenant_info:
        print("\n🎉 MySQL setup completed successfully!")
        print("\n📋 Sample Tenant Created:")
        print(f"  Tenant Code: {tenant_info['tenant_code']}")
        print(f"  Database: {tenant_info['database_name']}")
        print(f"  Username: {tenant_info['username']}")
        print(f"  Password: {tenant_info['password']}")
        
        # Save credentials to file
        credentials_file = "mysql_credentials.json"
        with open(credentials_file, 'w') as f:
            json.dump(tenant_info, f, indent=2)
        print(f"\n💾 Credentials saved to: {credentials_file}")
        
    setup.close_connection()
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)

    print("\n🔄 Next Steps:")
    print("1. Run schema migration: python schema_migration.py")
    print("2. Run data migration: python data_migration.py")
    print("3. Update application config: python update_config.py")
    print("4. Test the application: python test_mysql_integration.py")
