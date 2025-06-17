#!/usr/bin/env python3
"""
Complete MySQL Migration Runner
This script orchestrates the entire migration process from SQLite to MySQL.
"""

import os
import sys
import subprocess
import time
from datetime import datetime

class MigrationRunner:
    def __init__(self):
        """Initialize migration runner."""
        self.start_time = datetime.now()
        self.steps_completed = 0
        self.total_steps = 6
        
    def print_header(self, title):
        """Print formatted header."""
        print("\n" + "=" * 70)
        print(f"🔄 {title}")
        print("=" * 70)
    
    def print_step(self, step_num, title):
        """Print step information."""
        print(f"\n📋 Step {step_num}/{self.total_steps}: {title}")
        print("-" * 50)
    
    def run_script(self, script_name, description):
        """Run a Python script and handle errors."""
        try:
            print(f"🚀 Running {script_name}...")
            result = subprocess.run([sys.executable, script_name], 
                                  capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                print(f"✅ {description} completed successfully!")
                if result.stdout:
                    print("Output:", result.stdout[-500:])  # Show last 500 chars
                return True
            else:
                print(f"❌ {description} failed!")
                print("Error:", result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error running {script_name}: {e}")
            return False
    
    def check_prerequisites(self):
        """Check if all prerequisites are met."""
        self.print_step(1, "Checking Prerequisites")

        # Check if SQLite database exists (in parent directory)
        sqlite_db_path = '../kirima_primary.db'
        if not os.path.exists(sqlite_db_path):
            print("❌ SQLite database 'kirima_primary.db' not found!")
            print("Please ensure the database exists in the parent directory.")
            return False

        print("✅ SQLite database found")
        
        # Check if MySQL is accessible
        try:
            import mysql.connector
            print("✅ MySQL connector available")
        except ImportError:
            print("❌ MySQL connector not installed!")
            print("Please install: pip install mysql-connector-python")
            return False
        
        # Check if required scripts exist
        required_scripts = [
            'mysql_setup.py',
            'schema_migration.py', 
            'data_migration.py',
            'update_config.py',
            'test_mysql_integration.py'
        ]
        
        for script in required_scripts:
            if not os.path.exists(script):
                print(f"❌ Required script missing: {script}")
                return False
        
        print("✅ All required scripts found")
        
        self.steps_completed += 1
        return True
    
    def setup_mysql(self):
        """Set up MySQL server and create tenant database."""
        self.print_step(2, "MySQL Setup and Configuration")
        
        if self.run_script('mysql_setup.py', 'MySQL setup'):
            self.steps_completed += 1
            return True
        return False
    
    def migrate_schema(self):
        """Migrate database schema from SQLite to MySQL."""
        self.print_step(3, "Schema Migration")
        
        if self.run_script('schema_migration.py', 'Schema migration'):
            self.steps_completed += 1
            return True
        return False
    
    def migrate_data(self):
        """Migrate data from SQLite to MySQL."""
        self.print_step(4, "Data Migration")
        
        if self.run_script('data_migration.py', 'Data migration'):
            self.steps_completed += 1
            return True
        return False
    
    def update_configuration(self):
        """Update application configuration for MySQL."""
        self.print_step(5, "Configuration Update")
        
        if self.run_script('update_config.py', 'Configuration update'):
            self.steps_completed += 1
            return True
        return False
    
    def test_integration(self):
        """Test MySQL integration."""
        self.print_step(6, "Integration Testing")
        
        if self.run_script('test_mysql_integration.py', 'Integration testing'):
            self.steps_completed += 1
            return True
        return False
    
    def install_dependencies(self):
        """Install required MySQL dependencies."""
        print("📦 Installing MySQL dependencies...")
        
        try:
            # Install MySQL dependencies
            subprocess.run([sys.executable, '-m', 'pip', 'install', 
                          'PyMySQL>=1.0.2', 
                          'mysql-connector-python>=8.0.33',
                          'cryptography>=3.4.8'], 
                         check=True)
            print("✅ MySQL dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def create_backup(self):
        """Create backup of current SQLite database."""
        print("💾 Creating backup of SQLite database...")

        try:
            sqlite_db_path = '../kirima_primary.db'
            backup_name = f"../kirima_primary_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            import shutil
            shutil.copy2(sqlite_db_path, backup_name)
            print(f"✅ Backup created: {backup_name}")
            return True
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def print_summary(self, success):
        """Print migration summary."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 70)
        print("📊 MIGRATION SUMMARY")
        print("=" * 70)
        
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration}")
        print(f"Steps Completed: {self.steps_completed}/{self.total_steps}")
        
        if success:
            print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("\n📋 What's Next:")
            print("1. Review the configuration files created")
            print("2. Test the application thoroughly")
            print("3. Update any custom configurations as needed")
            print("4. Deploy to production when ready")
            
            print("\n🔗 Important Files Created:")
            print("- mysql_credentials.json (Database credentials)")
            print("- .env (Environment configuration)")
            print("- requirements.txt (Updated dependencies)")
            print("- database_utils.py (Multi-tenant utilities)")
            
            print("\n⚠️ Security Notes:")
            print("- Change default passwords in production")
            print("- Review and secure database credentials")
            print("- Enable SSL/TLS for production databases")
            print("- Set up regular backups")
            
        else:
            print(f"\n❌ MIGRATION FAILED at step {self.steps_completed + 1}")
            print("\n🔧 Troubleshooting:")
            print("1. Check error messages above")
            print("2. Ensure MySQL server is running")
            print("3. Verify database credentials")
            print("4. Check network connectivity")
            print("5. Review log files for detailed errors")
    
    def run_complete_migration(self):
        """Run the complete migration process."""
        self.print_header("Hillview School Management System - MySQL Migration")
        
        print("🚀 Starting complete migration from SQLite to MySQL...")
        print(f"📅 Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Create backup first
        if not self.create_backup():
            print("❌ Failed to create backup. Aborting migration.")
            return False
        
        # Install dependencies
        if not self.install_dependencies():
            print("❌ Failed to install dependencies. Aborting migration.")
            return False
        
        # Run migration steps
        steps = [
            self.check_prerequisites,
            self.setup_mysql,
            self.migrate_schema,
            self.migrate_data,
            self.update_configuration,
            self.test_integration
        ]
        
        for step in steps:
            if not step():
                self.print_summary(False)
                return False
            time.sleep(1)  # Brief pause between steps
        
        self.print_summary(True)
        return True

def main():
    """Main migration function."""
    print("🔄 Hillview School Management System")
    print("📊 Complete MySQL Migration Tool")
    print("=" * 50)
    
    # Confirm migration
    response = input("\n⚠️ This will migrate your system from SQLite to MySQL. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return False
    
    # Run migration
    runner = MigrationRunner()
    success = runner.run_complete_migration()
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    
    print("\n🎯 Migration completed! Your system is now running on MySQL.")
    print("🚀 Start your application with: python run.py")
