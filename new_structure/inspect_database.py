#!/usr/bin/env python3
"""
Database inspection script to check current MySQL schema.
"""

import pymysql
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

def inspect_database():
    """Inspect the current database schema."""
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
            
            # Check parent_student table
            print("\n🔍 Checking parent_student table...")
            cursor.execute("SHOW TABLES LIKE 'parent_student'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                cursor.execute("DESCRIBE parent_student")
                columns = cursor.fetchall()
                print("📋 Current parent_student table columns:")
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f"DEFAULT {col[4]}" if col[4] else ""
                    print(f"  - {col[0]}: {col[1]} {nullable} {default}")
            else:
                print("❌ parent_student table does not exist")
            
            # Check parent table
            print("\n🔍 Checking parent table...")
            cursor.execute("SHOW TABLES LIKE 'parent'")
            parent_table_exists = cursor.fetchone()
            
            if parent_table_exists:
                cursor.execute("DESCRIBE parent")
                columns = cursor.fetchall()
                print("📋 Current parent table columns:")
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f"DEFAULT {col[4]}" if col[4] else ""
                    print(f"  - {col[0]}: {col[1]} {nullable} {default}")
            else:
                print("❌ parent table does not exist")
            
            # Check student table
            print("\n🔍 Checking student table...")
            cursor.execute("SHOW TABLES LIKE 'student'")
            student_table_exists = cursor.fetchone()
            
            if student_table_exists:
                cursor.execute("DESCRIBE student")
                columns = cursor.fetchall()
                print("📋 Current student table columns:")
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f"DEFAULT {col[4]}" if col[4] else ""
                    print(f"  - {col[0]}: {col[1]} {nullable} {default}")
            else:
                print("❌ student table does not exist")
            
            # List all tables
            print("\n🔍 All tables in database:")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            for table in tables:
                print(f"  - {table[0]}")
                
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    inspect_database()
