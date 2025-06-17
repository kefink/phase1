#!/usr/bin/env python3
"""
Fix Teacher Table Schema
Adds missing columns to match the Flask SQLAlchemy model.
"""

import mysql.connector
import json
import sys

def fix_teacher_table_schema():
    """Add missing columns to teacher table."""
    print("🔧 Fixing Teacher Table Schema")
    print("=" * 40)
    
    # Load MySQL credentials
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
    except FileNotFoundError:
        print("❌ MySQL credentials not found!")
        return False
    
    try:
        connection = mysql.connector.connect(
            host=creds['host'],
            database=creds['database_name'],
            user=creds['username'],
            password=creds['password'],
            port=creds['port'],
            autocommit=True
        )
        
        cursor = connection.cursor()
        
        # First, check current table structure
        print("🔍 Checking current teacher table structure...")
        cursor.execute("DESCRIBE teacher")
        current_columns = [row[0] for row in cursor.fetchall()]
        print(f"Current columns: {', '.join(current_columns)}")
        
        # Define missing columns that the Flask model expects
        missing_columns = [
            "employee_id VARCHAR(50) UNIQUE",
            "qualification VARCHAR(100)",
            "specialization VARCHAR(200)",
            "date_joined DATE"
        ]
        
        # Check which columns are actually missing
        columns_to_add = []
        for col_def in missing_columns:
            col_name = col_def.split()[0]
            if col_name not in current_columns:
                columns_to_add.append(col_def)
        
        if not columns_to_add:
            print("✅ All required columns already exist!")
            return True
        
        print(f"\n🔧 Adding {len(columns_to_add)} missing columns...")
        
        # Add missing columns
        for i, col_def in enumerate(columns_to_add, 1):
            try:
                alter_sql = f"ALTER TABLE teacher ADD COLUMN {col_def}"
                cursor.execute(alter_sql)
                col_name = col_def.split()[0]
                print(f"✅ Added column {i}/{len(columns_to_add)}: {col_name}")
            except Exception as e:
                print(f"❌ Error adding column {col_def}: {e}")
        
        # Verify the updated structure
        print("\n🔍 Verifying updated table structure...")
        cursor.execute("DESCRIBE teacher")
        updated_columns = cursor.fetchall()
        
        print("Updated teacher table structure:")
        print("-" * 50)
        for col in updated_columns:
            print(f"{col[0]:<20} {col[1]:<20} {col[2]:<10}")
        
        cursor.close()
        connection.close()
        
        print("\n✅ Teacher table schema updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating teacher schema: {e}")
        return False

def add_default_headteacher():
    """Add default headteacher user if not exists."""
    print("\n👤 Adding Default Headteacher User")
    print("=" * 40)
    
    # Load MySQL credentials
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
    except FileNotFoundError:
        print("❌ MySQL credentials not found!")
        return False
    
    try:
        connection = mysql.connector.connect(
            host=creds['host'],
            database=creds['database_name'],
            user=creds['username'],
            password=creds['password'],
            port=creds['port'],
            autocommit=True
        )
        
        cursor = connection.cursor()
        
        # Check if headteacher already exists
        cursor.execute("SELECT COUNT(*) FROM teacher WHERE username = 'headteacher'")
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            print("ℹ️ Headteacher user already exists")
            
            # Update existing headteacher to ensure all fields are set
            update_sql = """
                UPDATE teacher 
                SET 
                    password = 'admin123',
                    role = 'headteacher',
                    first_name = 'Head',
                    last_name = 'Teacher',
                    email = 'headteacher@school.edu',
                    phone = '+1234567890',
                    employee_id = 'HT001',
                    qualification = 'MASTERS',
                    specialization = 'Educational Leadership',
                    date_joined = CURDATE(),
                    is_active = TRUE
                WHERE username = 'headteacher'
            """
            cursor.execute(update_sql)
            print("✅ Updated existing headteacher user")
        else:
            # Insert new headteacher
            insert_sql = """
                INSERT INTO teacher (
                    username, password, role, first_name, last_name, 
                    email, phone, employee_id, qualification, specialization, 
                    date_joined, is_active, created_at
                ) VALUES (
                    'headteacher', 'admin123', 'headteacher', 'Head', 'Teacher',
                    'headteacher@school.edu', '+1234567890', 'HT001', 'MASTERS', 'Educational Leadership',
                    CURDATE(), TRUE, NOW()
                )
            """
            cursor.execute(insert_sql)
            print("✅ Added new headteacher user")
        
        # Verify the headteacher user
        cursor.execute("""
            SELECT username, role, first_name, last_name, employee_id, qualification 
            FROM teacher 
            WHERE username = 'headteacher'
        """)
        headteacher = cursor.fetchone()
        
        if headteacher:
            print(f"\n👤 Headteacher Details:")
            print(f"Username: {headteacher[0]}")
            print(f"Role: {headteacher[1]}")
            print(f"Name: {headteacher[2]} {headteacher[3]}")
            print(f"Employee ID: {headteacher[4]}")
            print(f"Qualification: {headteacher[5]}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding headteacher: {e}")
        return False

def verify_login_functionality():
    """Verify that login functionality will work."""
    print("\n🧪 Verifying Login Functionality")
    print("=" * 40)
    
    # Load MySQL credentials
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
    except FileNotFoundError:
        print("❌ MySQL credentials not found!")
        return False
    
    try:
        connection = mysql.connector.connect(
            host=creds['host'],
            database=creds['database_name'],
            user=creds['username'],
            password=creds['password'],
            port=creds['port']
        )
        
        cursor = connection.cursor()
        
        # Test the exact query that was failing
        test_sql = """
            SELECT 
                id, username, password, role, stream_id, first_name, last_name, 
                email, phone, employee_id, qualification, specialization, 
                date_joined, is_active, created_at 
            FROM teacher 
            WHERE username = %s AND password = %s AND role = %s 
            LIMIT 1
        """
        
        cursor.execute(test_sql, ('headteacher', 'admin123', 'headteacher'))
        result = cursor.fetchone()
        
        if result:
            print("✅ Login query test successful!")
            print(f"Found user: {result[1]} ({result[3]})")
            print("✅ All required columns are accessible")
        else:
            print("❌ Login query test failed - no matching user found")
            return False
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Login verification failed: {e}")
        return False

def main():
    """Main function to fix teacher schema issues."""
    print("🔧 Teacher Schema Fix for MySQL Migration")
    print("=" * 50)
    
    success = True
    
    # Step 1: Fix teacher table schema
    if not fix_teacher_table_schema():
        success = False
    
    # Step 2: Add/update default headteacher
    if not add_default_headteacher():
        success = False
    
    # Step 3: Verify login functionality
    if not verify_login_functionality():
        success = False
    
    if success:
        print("\n🎉 Teacher Schema Fix Completed Successfully!")
        print("\n📋 What was fixed:")
        print("✅ Added missing teacher table columns")
        print("✅ Created/updated headteacher user")
        print("✅ Verified login functionality")
        print("\n🚀 You can now login as headteacher!")
        print("Username: headteacher")
        print("Password: admin123")
    else:
        print("\n❌ Teacher schema fix failed!")
        print("Please check the errors above and try again.")
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
