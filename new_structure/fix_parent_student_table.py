#!/usr/bin/env python3
"""
Fix parent_student table structure to match the ParentStudent model.
This script ensures the table has all required columns.
"""

import pymysql
from config import Config

def fix_parent_student_table():
    """Fix the parent_student table structure."""
    try:
        # Connect to MySQL database
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            print("🔍 Checking parent_student table...")
            
            # Check if table exists
            cursor.execute("SHOW TABLES LIKE 'parent_student'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("📋 Creating parent_student table...")
                create_table_sql = """
                CREATE TABLE parent_student (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    parent_id INT NOT NULL,
                    student_id INT NOT NULL,
                    relationship_type VARCHAR(20) DEFAULT 'parent',
                    is_primary_contact BOOLEAN DEFAULT FALSE,
                    can_receive_reports BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by INT,
                    FOREIGN KEY (parent_id) REFERENCES parent(id) ON DELETE CASCADE,
                    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES teacher(id) ON DELETE SET NULL,
                    UNIQUE KEY unique_parent_student (parent_id, student_id)
                )
                """
                cursor.execute(create_table_sql)
                print("✅ Created parent_student table with all required columns")
                
            else:
                print("✅ parent_student table exists")
                
                # Check current columns
                cursor.execute("DESCRIBE parent_student")
                columns = cursor.fetchall()
                existing_columns = [col[0] for col in columns]
                
                print(f"Current columns: {existing_columns}")
                
                # Check for missing columns
                required_columns = {
                    'relationship_type': 'VARCHAR(20) DEFAULT "parent"',
                    'is_primary_contact': 'BOOLEAN DEFAULT FALSE',
                    'can_receive_reports': 'BOOLEAN DEFAULT TRUE',
                    'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                    'created_by': 'INT'
                }
                
                missing_columns = []
                for col_name, col_def in required_columns.items():
                    if col_name not in existing_columns:
                        missing_columns.append((col_name, col_def))
                
                if missing_columns:
                    print(f"Missing columns: {[col[0] for col in missing_columns]}")
                    
                    for col_name, col_def in missing_columns:
                        print(f"Adding column: {col_name}")
                        try:
                            cursor.execute(f"ALTER TABLE parent_student ADD COLUMN {col_name} {col_def}")
                            print(f"✅ Added column: {col_name}")
                        except Exception as e:
                            print(f"❌ Error adding column {col_name}: {e}")
                    
                    # Add foreign key constraints if missing
                    try:
                        cursor.execute("""
                            ALTER TABLE parent_student 
                            ADD CONSTRAINT fk_parent_student_created_by 
                            FOREIGN KEY (created_by) REFERENCES teacher(id) ON DELETE SET NULL
                        """)
                        print("✅ Added foreign key constraint for created_by")
                    except Exception as e:
                        print(f"Note: Foreign key constraint: {e}")
                    
                    connection.commit()
                    print("✅ Schema update completed")
                    
                else:
                    print("✅ All required columns are present")
            
            # Verify final schema
            print("\n📋 Final Schema Verification:")
            cursor.execute("DESCRIBE parent_student")
            columns = cursor.fetchall()
            
            for col in columns:
                print(f"  - {col[0]}: {col[1]} {col[2] if col[2] == 'NO' else ''} {col[4] if col[4] else ''}")
            
            connection.commit()
            print("\n✅ parent_student table is now properly configured!")
            
    except Exception as e:
        print(f"❌ Error fixing parent_student table: {e}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    fix_parent_student_table()
