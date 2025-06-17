#!/usr/bin/env python3
"""
Configuration Update Script - Update Flask app to use MySQL
This script updates the application configuration to use MySQL instead of SQLite.
"""

import json
import os
import sys
import shutil
from datetime import datetime

class ConfigUpdater:
    def __init__(self, credentials_file="mysql_credentials.json"):
        """Initialize with MySQL credentials."""
        self.credentials = self.load_credentials(credentials_file)
        self.backup_dir = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def load_credentials(self, credentials_file):
        """Load MySQL credentials from file."""
        try:
            with open(credentials_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Credentials file not found: {credentials_file}")
            print("Please run mysql_setup.py first")
            sys.exit(1)
    
    def backup_config_files(self):
        """Create backup of existing configuration files."""
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Files to backup
            config_files = [
                'config.py',
                'extensions.py',
                '__init__.py'
            ]
            
            for file in config_files:
                if os.path.exists(file):
                    shutil.copy2(file, os.path.join(self.backup_dir, file))
                    print(f"✅ Backed up {file}")
            
            print(f"📁 Configuration backup created in: {self.backup_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False
    
    def update_config_py(self):
        """Update config.py to use MySQL."""
        try:
            # Read current config
            with open('config.py', 'r') as f:
                content = f.read()
            
            # Create MySQL configuration
            mysql_config = f"""\"\"\"
Configuration settings for the Hillview School Management System.
Updated for MySQL multi-tenant architecture.
\"\"\"
import os

class Config:
    \"\"\"Base configuration class with settings common to all environments.\"\"\"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here_change_in_production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MySQL Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or '{self.credentials['username']}'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or '{self.credentials['password']}'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or '{self.credentials['database_name']}'
    
    # SQLAlchemy MySQL URI
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{{MYSQL_USER}}:{{MYSQL_PASSWORD}}@{{MYSQL_HOST}}:{{MYSQL_PORT}}/{{MYSQL_DATABASE}}"
        "?charset=utf8mb4"
    )
    
    # Connection Pool Settings
    SQLALCHEMY_ENGINE_OPTIONS = {{
        'pool_size': 10,
        'pool_timeout': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }}
    
    # Session configuration for better persistence
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Multi-tenant configuration
    TENANT_CODE = os.environ.get('TENANT_CODE') or '{self.credentials['tenant_code']}'
    MASTER_DATABASE_URI = os.environ.get('MASTER_DATABASE_URI') or 'mysql+pymysql://root:password@localhost:3306/hillview_master'


class DevelopmentConfig(Config):
    \"\"\"Configuration for development environment.\"\"\"
    DEBUG = True
    SERVER_NAME = 'localhost:5000'
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'http'
    
    # Development-specific MySQL settings
    SQLALCHEMY_ECHO = False  # Set to True for SQL query logging


class TestingConfig(Config):
    \"\"\"Configuration for testing environment.\"\"\"
    TESTING = True
    # Use separate test database
    MYSQL_DATABASE = '{self.credentials['database_name']}_test'
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{{Config.MYSQL_USER}}:{{Config.MYSQL_PASSWORD}}@{{Config.MYSQL_HOST}}:{{Config.MYSQL_PORT}}/{{MYSQL_DATABASE}}"
        "?charset=utf8mb4"
    )


class ProductionConfig(Config):
    \"\"\"Configuration for production environment.\"\"\"
    DEBUG = False
    
    # Production-specific settings
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_ENGINE_OPTIONS = {{
        'pool_size': 20,
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 40
    }}
    
    # SSL Configuration for production
    MYSQL_SSL_DISABLED = False
    MYSQL_SSL_CA = os.environ.get('MYSQL_SSL_CA')
    MYSQL_SSL_CERT = os.environ.get('MYSQL_SSL_CERT')
    MYSQL_SSL_KEY = os.environ.get('MYSQL_SSL_KEY')


# Configuration dictionary to easily select environment
config = {{
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}}

# Multi-tenant database routing
class TenantConfig:
    \"\"\"Tenant-specific configuration management.\"\"\"
    
    @staticmethod
    def get_tenant_database_uri(tenant_code):
        \"\"\"Get database URI for a specific tenant.\"\"\"
        base_config = config['default']()
        tenant_db = f"hillview_{{tenant_code.lower()}}"
        
        return (
            f"mysql+pymysql://{{base_config.MYSQL_USER}}:{{base_config.MYSQL_PASSWORD}}"
            f"@{{base_config.MYSQL_HOST}}:{{base_config.MYSQL_PORT}}/{{tenant_db}}"
            "?charset=utf8mb4"
        )
    
    @staticmethod
    def get_master_database_uri():
        \"\"\"Get master database URI for tenant management.\"\"\"
        base_config = config['default']()
        return base_config.MASTER_DATABASE_URI
"""
            
            # Write updated config
            with open('config.py', 'w') as f:
                f.write(mysql_config)
            
            print("✅ Updated config.py for MySQL")
            return True
            
        except Exception as e:
            print(f"❌ Error updating config.py: {e}")
            return False
    
    def create_requirements_txt(self):
        """Create/update requirements.txt with MySQL dependencies."""
        try:
            mysql_requirements = [
                "PyMySQL>=1.0.2",
                "cryptography>=3.4.8",  # Required for PyMySQL
                "mysql-connector-python>=8.0.33",
                "SQLAlchemy>=1.4.0",
                "Flask-SQLAlchemy>=2.5.1"
            ]
            
            # Read existing requirements if they exist
            existing_requirements = []
            if os.path.exists('requirements.txt'):
                with open('requirements.txt', 'r') as f:
                    existing_requirements = [line.strip() for line in f.readlines() if line.strip()]
            
            # Add MySQL requirements if not already present
            updated_requirements = existing_requirements.copy()
            for req in mysql_requirements:
                package_name = req.split('>=')[0].split('==')[0]
                if not any(package_name in existing_req for existing_req in existing_requirements):
                    updated_requirements.append(req)
            
            # Write updated requirements
            with open('requirements.txt', 'w') as f:
                for req in sorted(updated_requirements):
                    f.write(f"{req}\\n")
            
            print("✅ Updated requirements.txt with MySQL dependencies")
            return True
            
        except Exception as e:
            print(f"❌ Error updating requirements.txt: {e}")
            return False
    
    def create_environment_file(self):
        """Create .env file with MySQL configuration."""
        try:
            env_content = f"""# MySQL Configuration for Hillview School Management System
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER={self.credentials['username']}
MYSQL_PASSWORD={self.credentials['password']}
MYSQL_DATABASE={self.credentials['database_name']}

# Tenant Configuration
TENANT_CODE={self.credentials['tenant_code']}

# Security
SECRET_KEY=your_secret_key_here_change_in_production

# Master Database (for multi-tenant management)
MASTER_DATABASE_URI=mysql+pymysql://root:password@localhost:3306/hillview_master

# Flask Environment
FLASK_ENV=development
FLASK_DEBUG=1
"""
            
            with open('.env', 'w') as f:
                f.write(env_content)
            
            print("✅ Created .env file with MySQL configuration")
            return True
            
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    
    def create_database_utils(self):
        """Create database utility functions for multi-tenant support."""
        try:
            utils_content = '''"""
Database utilities for multi-tenant MySQL support.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import TenantConfig

class DatabaseManager:
    """Manage database connections for multi-tenant architecture."""
    
    def __init__(self):
        self.engines = {}
        self.sessions = {}
    
    def get_tenant_engine(self, tenant_code):
        """Get or create database engine for a tenant."""
        if tenant_code not in self.engines:
            database_uri = TenantConfig.get_tenant_database_uri(tenant_code)
            self.engines[tenant_code] = create_engine(
                database_uri,
                pool_size=10,
                pool_timeout=20,
                pool_recycle=3600,
                pool_pre_ping=True
            )
        return self.engines[tenant_code]
    
    def get_master_engine(self):
        """Get master database engine."""
        if 'master' not in self.engines:
            database_uri = TenantConfig.get_master_database_uri()
            self.engines['master'] = create_engine(database_uri)
        return self.engines['master']
    
    def get_tenant_session(self, tenant_code):
        """Get database session for a tenant."""
        if tenant_code not in self.sessions:
            engine = self.get_tenant_engine(tenant_code)
            Session = sessionmaker(bind=engine)
            self.sessions[tenant_code] = Session()
        return self.sessions[tenant_code]
    
    def close_all_sessions(self):
        """Close all database sessions."""
        for session in self.sessions.values():
            session.close()
        self.sessions.clear()

# Global database manager instance
db_manager = DatabaseManager()

def get_current_tenant():
    """Get current tenant code from environment or request context."""
    return os.environ.get('TENANT_CODE', 'DEMO001')

def with_tenant_db(tenant_code=None):
    """Decorator to execute function with tenant database context."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            tenant = tenant_code or get_current_tenant()
            # Set up tenant database context
            return func(*args, **kwargs)
        return wrapper
    return decorator
'''
            
            with open('database_utils.py', 'w') as f:
                f.write(utils_content)
            
            print("✅ Created database_utils.py for multi-tenant support")
            return True
            
        except Exception as e:
            print(f"❌ Error creating database utilities: {e}")
            return False
    
    def update_application(self):
        """Update the main application configuration."""
        print("🔄 Updating application configuration...")
        
        success = True
        success &= self.backup_config_files()
        success &= self.update_config_py()
        success &= self.create_requirements_txt()
        success &= self.create_environment_file()
        success &= self.create_database_utils()
        
        return success

def main():
    """Main configuration update function."""
    print("⚙️ Updating Application Configuration for MySQL")
    print("=" * 55)
    
    updater = ConfigUpdater()
    success = updater.update_application()
    
    if success:
        print("\\n🎉 Configuration update completed successfully!")
        print("\\n📋 Next Steps:")
        print("1. Install MySQL dependencies: pip install -r requirements.txt")
        print("2. Test the application: python test_mysql_integration.py")
        print("3. Start the application: python run.py")
        print("\\n⚠️ Important Notes:")
        print("- Configuration backup created in:", updater.backup_dir)
        print("- Review .env file and update passwords as needed")
        print("- Test thoroughly before deploying to production")
    else:
        print("\\n❌ Configuration update failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
