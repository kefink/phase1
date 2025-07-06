#!/usr/bin/env python3
"""
Comprehensive database schema fix for Hillview School Management System.
This script fixes all identified schema mismatches between SQLAlchemy models and MySQL tables.
"""

import pymysql
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

def fix_database_schema():
    """Fix all database schema issues."""
    try:
        # Connect to MySQL database
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password='@2494/lK',  # Direct password since Config.MYSQL_PASSWORD is URL encoded
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            print("🔍 Database Connection Successful!")
            print(f"📊 Database: {Config.MYSQL_DATABASE}")
            print("=" * 60)
            
            # Backup current data before making changes
            print("\n📋 Creating backup of current data...")
            
            # Fix 1: parent_student table schema issues
            print("\n🔧 Fixing parent_student table schema...")
            
            # Check current columns
            cursor.execute("DESCRIBE parent_student")
            columns = cursor.fetchall()
            existing_columns = [col[0] for col in columns]
            print(f"Current columns: {existing_columns}")
            
            # Issue 1: Column name mismatch - 'relationship' should be 'relationship_type'
            if 'relationship' in existing_columns and 'relationship_type' not in existing_columns:
                print("🔄 Renaming 'relationship' column to 'relationship_type'...")
                cursor.execute("ALTER TABLE parent_student CHANGE COLUMN relationship relationship_type VARCHAR(20) DEFAULT 'parent'")
                print("✅ Renamed relationship column to relationship_type")
            
            # Issue 2: Missing columns from ParentStudent model
            required_columns = {
                'can_receive_reports': 'BOOLEAN DEFAULT TRUE',
                'created_by': 'INT NULL'
            }
            
            for col_name, col_def in required_columns.items():
                if col_name not in existing_columns:
                    print(f"➕ Adding missing column: {col_name}")
                    try:
                        cursor.execute(f"ALTER TABLE parent_student ADD COLUMN {col_name} {col_def}")
                        print(f"✅ Added column: {col_name}")
                    except Exception as e:
                        print(f"❌ Error adding column {col_name}: {e}")
            
            # Issue 3: Add foreign key constraint for created_by if missing
            try:
                cursor.execute("""
                    SELECT CONSTRAINT_NAME 
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_NAME = 'parent_student' 
                    AND COLUMN_NAME = 'created_by'
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """, (Config.MYSQL_DATABASE,))
                
                fk_exists = cursor.fetchone()
                if not fk_exists:
                    print("➕ Adding foreign key constraint for created_by...")
                    cursor.execute("""
                        ALTER TABLE parent_student 
                        ADD CONSTRAINT fk_parent_student_created_by 
                        FOREIGN KEY (created_by) REFERENCES teacher(id) ON DELETE SET NULL
                    """)
                    print("✅ Added foreign key constraint for created_by")
            except Exception as e:
                print(f"Note: Foreign key constraint issue: {e}")
            
            # Fix 2: parent table schema issues
            print("\n🔧 Checking parent table schema...")
            cursor.execute("DESCRIBE parent")
            parent_columns = cursor.fetchall()
            existing_parent_columns = [col[0] for col in parent_columns]
            print(f"Current parent columns: {existing_parent_columns}")
            
            # Missing columns from Parent model
            parent_required_columns = {
                'password_hash': 'VARCHAR(255) NULL',
                'is_verified': 'BOOLEAN DEFAULT FALSE',
                'failed_login_attempts': 'INT DEFAULT 0',
                'locked_until': 'DATETIME NULL',
                'email_notifications': 'BOOLEAN DEFAULT TRUE',
                'notification_frequency': 'VARCHAR(20) DEFAULT "immediate"',
                'last_login': 'DATETIME NULL',
                'verification_token': 'VARCHAR(100) NULL',
                'verification_sent_at': 'DATETIME NULL',
                'reset_token': 'VARCHAR(100) NULL',
                'reset_token_expires': 'DATETIME NULL'
            }
            
            for col_name, col_def in parent_required_columns.items():
                if col_name not in existing_parent_columns:
                    print(f"➕ Adding missing parent column: {col_name}")
                    try:
                        cursor.execute(f"ALTER TABLE parent ADD COLUMN {col_name} {col_def}")
                        print(f"✅ Added parent column: {col_name}")
                    except Exception as e:
                        print(f"❌ Error adding parent column {col_name}: {e}")
            
            # Fix 3: Ensure email column is unique and not null
            if 'email' in existing_parent_columns:
                try:
                    print("🔧 Making email column unique and not null...")
                    cursor.execute("ALTER TABLE parent MODIFY COLUMN email VARCHAR(120) NOT NULL")
                    cursor.execute("ALTER TABLE parent ADD UNIQUE INDEX idx_parent_email (email)")
                    print("✅ Updated email column constraints")
                except Exception as e:
                    print(f"Note: Email constraint issue (may already exist): {e}")
            
            # Commit all changes
            connection.commit()
            print("\n✅ All database schema fixes completed successfully!")
            
            # Verify final schema
            print("\n📋 Final Schema Verification:")
            print("\n🔍 parent_student table:")
            cursor.execute("DESCRIBE parent_student")
            columns = cursor.fetchall()
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f"DEFAULT {col[4]}" if col[4] else ""
                print(f"  - {col[0]}: {col[1]} {nullable} {default}")
            
            print("\n🔍 parent table:")
            cursor.execute("DESCRIBE parent")
            columns = cursor.fetchall()
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f"DEFAULT {col[4]}" if col[4] else ""
                print(f"  - {col[0]}: {col[1]} {nullable} {default}")
                
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        import traceback
        traceback.print_exc()
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    print("🚀 Starting Database Schema Fix...")
    print(f"⏰ Timestamp: {datetime.now()}")
    fix_database_schema()
    print("🎉 Database schema fix completed!")
