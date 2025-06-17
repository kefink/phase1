#!/usr/bin/env python3
"""
Simple Configuration Update for MySQL
Updates the existing Flask configuration to use MySQL.
"""

import json
import os
import shutil
from datetime import datetime

def load_mysql_credentials():
    """Load MySQL credentials."""
    try:
        with open('mysql_credentials.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ MySQL credentials not found!")
        return None

def update_config_py():
    """Update the main config.py file."""
    config_path = '../config.py'
    
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        return False
    
    # Load credentials
    creds = load_mysql_credentials()
    if not creds:
        return False
    
    try:
        # Backup original config
        backup_path = f"../config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        shutil.copy2(config_path, backup_path)
        print(f"✅ Backed up config to: {backup_path}")
        
        # Read current config
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Create new MySQL configuration
        mysql_config = f'''"""
Configuration settings for the Hillview School Management System.
Updated for MySQL database.
"""
import os

class Config:
    """Base configuration class with settings common to all environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here_change_in_production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MySQL Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or '{creds['username']}'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or '{creds['password']}'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or '{creds['database_name']}'
    
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
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True
    SERVER_NAME = 'localhost:5000'
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'http'


class TestingConfig(Config):
    """Configuration for testing environment."""
    TESTING = True


class ProductionConfig(Config):
    """Configuration for production environment."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


# Configuration dictionary
config = {{
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}}
'''
        
        # Write new config
        with open(config_path, 'w') as f:
            f.write(mysql_config)
        
        print("✅ Updated config.py for MySQL")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False

def create_env_file():
    """Create .env file with MySQL configuration."""
    creds = load_mysql_credentials()
    if not creds:
        return False
    
    try:
        env_content = f"""# MySQL Configuration for Hillview School Management System
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER={creds['username']}
MYSQL_PASSWORD={creds['password']}
MYSQL_DATABASE={creds['database_name']}

# Security
SECRET_KEY=your_secret_key_here_change_in_production

# Flask Environment
FLASK_ENV=development
FLASK_DEBUG=1
"""
        
        with open('../.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Created .env file")
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def update_requirements():
    """Update requirements.txt with MySQL dependencies."""
    try:
        requirements_path = '../requirements.txt'
        
        # MySQL dependencies
        mysql_deps = [
            "PyMySQL>=1.0.2",
            "mysql-connector-python>=8.0.33",
            "cryptography>=3.4.8"
        ]
        
        # Read existing requirements
        existing_reqs = []
        if os.path.exists(requirements_path):
            with open(requirements_path, 'r') as f:
                existing_reqs = [line.strip() for line in f.readlines() if line.strip()]
        
        # Add MySQL dependencies if not present
        updated_reqs = existing_reqs.copy()
        for dep in mysql_deps:
            package_name = dep.split('>=')[0].split('==')[0]
            if not any(package_name in req for req in existing_reqs):
                updated_reqs.append(dep)
        
        # Write updated requirements
        with open(requirements_path, 'w') as f:
            for req in sorted(updated_reqs):
                f.write(f"{req}\\n")
        
        print("✅ Updated requirements.txt")
        return True
        
    except Exception as e:
        print(f"❌ Error updating requirements: {e}")
        return False

def main():
    """Main configuration update function."""
    print("🔄 Simple MySQL Configuration Update")
    print("=" * 50)
    
    success = True
    success &= update_config_py()
    success &= create_env_file()
    success &= update_requirements()
    
    if success:
        print("\\n🎉 Configuration update completed!")
        print("\\n📋 Next Steps:")
        print("1. Test the application: python run.py")
        print("2. Verify MySQL connection works")
        print("3. Check all features are working")
        
        print("\\n🔗 MySQL Database Details:")
        creds = load_mysql_credentials()
        if creds:
            print(f"Database: {creds['database_name']}")
            print(f"Username: {creds['username']}")
            print(f"Host: {creds['host']}:{creds['port']}")
    else:
        print("\\n❌ Configuration update failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
