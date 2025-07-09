#!/usr/bin/env python3
"""
Student Promotion System Migration
==================================

This migration adds the student promotion system to the Hillview School Management System.

Changes:
1. Add promotion-related fields to the Student table
2. Create StudentPromotionHistory table for tracking all promotion activities
3. Add indexes for performance optimization

Run this migration after implementing the student promotion service and views.
"""

import mysql.connector
from mysql.connector import Error
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import Config
    import urllib.parse
    # Decode the URL-encoded password
    password = urllib.parse.unquote_plus(Config.MYSQL_PASSWORD)
    DB_CONFIG = {
        'host': Config.MYSQL_HOST,
        'database': Config.MYSQL_DATABASE,
        'user': Config.MYSQL_USER,
        'password': password,
        'port': Config.MYSQL_PORT
    }
except ImportError:
    # Fallback configuration
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'hillview_demo001',
        'user': 'root',
        'password': '@2494/lK',
        'port': 3306
    }

def get_db_connection():
    """Get database connection."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def execute_sql(connection, sql, description):
    """Execute SQL statement with error handling."""
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()
        print(f"✓ {description}")
        return True
    except Error as e:
        print(f"✗ {description}: {e}")
        return False
    finally:
        if cursor:
            cursor.close()

def check_column_exists(connection, table_name, column_name):
    """Check if a column exists in a table."""
    try:
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '{DB_CONFIG['database']}' 
            AND TABLE_NAME = '{table_name}' 
            AND COLUMN_NAME = '{column_name}'
        """)
        result = cursor.fetchone()
        return result[0] > 0
    except Error as e:
        print(f"Error checking column {column_name} in {table_name}: {e}")
        return False
    finally:
        if cursor:
            cursor.close()

def check_table_exists(connection, table_name):
    """Check if a table exists."""
    try:
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = '{DB_CONFIG['database']}' 
            AND TABLE_NAME = '{table_name}'
        """)
        result = cursor.fetchone()
        return result[0] > 0
    except Error as e:
        print(f"Error checking table {table_name}: {e}")
        return False
    finally:
        if cursor:
            cursor.close()

def add_student_promotion_fields(connection):
    """Add promotion-related fields to the Student table."""
    print("\n=== Adding Student Promotion Fields ===")
    
    # List of fields to add
    fields_to_add = [
        {
            'name': 'promotion_status',
            'sql': "ALTER TABLE Student ADD COLUMN promotion_status ENUM('active', 'promoted', 'repeated', 'transferred', 'graduated') DEFAULT 'active'",
            'description': 'Add promotion_status field'
        },
        {
            'name': 'academic_year',
            'sql': "ALTER TABLE Student ADD COLUMN academic_year VARCHAR(10) DEFAULT '2024'",
            'description': 'Add academic_year field'
        },
        {
            'name': 'date_last_promoted',
            'sql': "ALTER TABLE Student ADD COLUMN date_last_promoted DATETIME NULL",
            'description': 'Add date_last_promoted field'
        },
        {
            'name': 'is_eligible_for_promotion',
            'sql': "ALTER TABLE Student ADD COLUMN is_eligible_for_promotion BOOLEAN DEFAULT TRUE",
            'description': 'Add is_eligible_for_promotion field'
        },
        {
            'name': 'promotion_notes',
            'sql': "ALTER TABLE Student ADD COLUMN promotion_notes TEXT NULL",
            'description': 'Add promotion_notes field'
        }
    ]
    
    success_count = 0
    for field in fields_to_add:
        if not check_column_exists(connection, 'Student', field['name']):
            if execute_sql(connection, field['sql'], field['description']):
                success_count += 1
        else:
            print(f"✓ {field['description']} (already exists)")
            success_count += 1
    
    return success_count == len(fields_to_add)

def create_student_promotion_history_table(connection):
    """Create the StudentPromotionHistory table."""
    print("\n=== Creating StudentPromotionHistory Table ===")
    
    if check_table_exists(connection, 'StudentPromotionHistory'):
        print("✓ StudentPromotionHistory table already exists")
        return True
    
    create_table_sql = """
    CREATE TABLE StudentPromotionHistory (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL,
        promotion_type ENUM('promote', 'repeat', 'transfer', 'graduate') NOT NULL,
        academic_year_from VARCHAR(10) NOT NULL,
        academic_year_to VARCHAR(10) NULL,
        from_grade_id INT NULL,
        to_grade_id INT NULL,
        from_stream_id INT NULL,
        to_stream_id INT NULL,
        promotion_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        promoted_by_teacher_id INT NULL,
        batch_id VARCHAR(36) NULL,
        promotion_summary TEXT NULL,
        promotion_notes TEXT NULL,
        previous_performance_data JSON NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        -- Foreign key constraints
        FOREIGN KEY (student_id) REFERENCES Student(id) ON DELETE CASCADE,
        FOREIGN KEY (from_grade_id) REFERENCES Grade(id) ON DELETE SET NULL,
        FOREIGN KEY (to_grade_id) REFERENCES Grade(id) ON DELETE SET NULL,
        FOREIGN KEY (from_stream_id) REFERENCES Stream(id) ON DELETE SET NULL,
        FOREIGN KEY (to_stream_id) REFERENCES Stream(id) ON DELETE SET NULL,
        FOREIGN KEY (promoted_by_teacher_id) REFERENCES Teacher(id) ON DELETE SET NULL,
        
        -- Indexes for performance
        INDEX idx_student_promotion (student_id, promotion_date),
        INDEX idx_academic_year (academic_year_from, academic_year_to),
        INDEX idx_promotion_type (promotion_type),
        INDEX idx_batch_id (batch_id),
        INDEX idx_promotion_date (promotion_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    return execute_sql(connection, create_table_sql, "Create StudentPromotionHistory table")

def add_performance_indexes(connection):
    """Add performance indexes for the promotion system."""
    print("\n=== Adding Performance Indexes ===")
    
    indexes = [
        {
            'sql': "CREATE INDEX idx_student_promotion_status ON Student(promotion_status, academic_year)",
            'description': 'Add index on Student promotion_status and academic_year'
        },
        {
            'sql': "CREATE INDEX idx_student_grade_stream ON Student(grade_id, stream_id)",
            'description': 'Add index on Student grade_id and stream_id'
        },
        {
            'sql': "CREATE INDEX idx_student_eligibility ON Student(is_eligible_for_promotion, promotion_status)",
            'description': 'Add index on Student eligibility fields'
        }
    ]
    
    success_count = 0
    for index in indexes:
        if execute_sql(connection, index['sql'], index['description']):
            success_count += 1
        # Note: Index creation might fail if index already exists, which is okay
    
    return True  # Always return True as index failures are not critical

def run_migration():
    """Run the complete student promotion system migration."""
    print("=" * 60)
    print("STUDENT PROMOTION SYSTEM MIGRATION")
    print("=" * 60)
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"Migration started at: {datetime.now()}")
    
    # Get database connection
    connection = get_db_connection()
    if not connection:
        print("✗ Failed to connect to database")
        return False
    
    try:
        # Run migration steps
        steps = [
            ("Add Student Promotion Fields", add_student_promotion_fields),
            ("Create StudentPromotionHistory Table", create_student_promotion_history_table),
            ("Add Performance Indexes", add_performance_indexes)
        ]
        
        all_success = True
        for step_name, step_function in steps:
            print(f"\n--- {step_name} ---")
            if not step_function(connection):
                print(f"✗ {step_name} failed")
                all_success = False
            else:
                print(f"✓ {step_name} completed successfully")
        
        if all_success:
            print("\n" + "=" * 60)
            print("✓ MIGRATION COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Restart your application")
            print("2. Test the student promotion functionality")
            print("3. Verify the promotion history tracking")
            return True
        else:
            print("\n" + "=" * 60)
            print("✗ MIGRATION COMPLETED WITH ERRORS")
            print("=" * 60)
            print("Please review the errors above and fix them manually.")
            return False
            
    except Exception as e:
        print(f"\n✗ Migration failed with exception: {e}")
        return False
    finally:
        connection.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
