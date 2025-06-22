"""
Fix Subject Component Table Schema
Add missing columns to subject_component table to match the model definition
"""

import pymysql
import sys

def fix_subject_component_table():
    """Fix the subject_component table by adding missing columns."""
    try:
        # Connect to MySQL
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='@2494/lK',
            database='hillview_demo001'
        )
        cursor = connection.cursor()
        
        print("🔧 FIXING SUBJECT COMPONENT TABLE SCHEMA")
        print("=" * 60)
        
        # Check if subject_component table exists
        cursor.execute("SHOW TABLES LIKE 'subject_component'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("📋 Creating subject_component table...")
            # Create the table if it doesn't exist
            create_table_sql = """
            CREATE TABLE subject_component (
                id INT AUTO_INCREMENT PRIMARY KEY,
                subject_id INT NOT NULL,
                name VARCHAR(100) NOT NULL,
                weight FLOAT DEFAULT 1.0,
                max_raw_mark INT DEFAULT 100,
                FOREIGN KEY (subject_id) REFERENCES subject(id)
            )
            """
            cursor.execute(create_table_sql)
            print("✅ Created subject_component table")
        else:
            print("📋 subject_component table exists, checking columns...")
            
            # Get current columns
            cursor.execute("DESCRIBE subject_component")
            columns = cursor.fetchall()
            existing_columns = [col[0] for col in columns]
            
            print("Current columns:", existing_columns)
            
            # Check and add missing columns
            required_columns = {
                'weight': 'FLOAT DEFAULT 1.0',
                'max_raw_mark': 'INT DEFAULT 100'
            }
            
            for column_name, column_def in required_columns.items():
                if column_name not in existing_columns:
                    print(f"➕ Adding missing column: {column_name}")
                    alter_sql = f"ALTER TABLE subject_component ADD COLUMN {column_name} {column_def}"
                    cursor.execute(alter_sql)
                    print(f"✅ Added column: {column_name}")
                else:
                    print(f"✅ Column {column_name} already exists")
        
        # Check if component_mark table exists
        cursor.execute("SHOW TABLES LIKE 'component_mark'")
        component_mark_exists = cursor.fetchone()
        
        if not component_mark_exists:
            print("📋 Creating component_mark table...")
            create_component_mark_sql = """
            CREATE TABLE component_mark (
                id INT AUTO_INCREMENT PRIMARY KEY,
                mark_id INT NOT NULL,
                component_id INT NOT NULL,
                raw_mark FLOAT NOT NULL,
                FOREIGN KEY (mark_id) REFERENCES mark(id),
                FOREIGN KEY (component_id) REFERENCES subject_component(id)
            )
            """
            cursor.execute(create_component_mark_sql)
            print("✅ Created component_mark table")
        else:
            print("✅ component_mark table already exists")
        
        # Commit changes
        connection.commit()
        
        # Verify the fix
        print("\n🔍 VERIFYING TABLE STRUCTURE")
        print("-" * 40)
        cursor.execute("DESCRIBE subject_component")
        columns = cursor.fetchall()
        print("subject_component columns:")
        for column in columns:
            print(f"  - {column[0]} ({column[1]})")
        
        # Add some sample data if table is empty
        cursor.execute("SELECT COUNT(*) FROM subject_component")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("\n📝 Adding sample subject components...")
            
            # Get English subjects
            cursor.execute("SELECT id, name FROM subject WHERE name LIKE '%English%'")
            english_subjects = cursor.fetchall()
            
            for subject_id, subject_name in english_subjects:
                # Add Grammar and Composition components for English
                components = [
                    (subject_id, 'Grammar', 0.5, 50),
                    (subject_id, 'Composition', 0.5, 50)
                ]
                
                for comp_subject_id, comp_name, comp_weight, comp_max_mark in components:
                    cursor.execute("""
                        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
                        VALUES (%s, %s, %s, %s)
                    """, (comp_subject_id, comp_name, comp_weight, comp_max_mark))
                
                print(f"✅ Added components for {subject_name}")
            
            # Get Kiswahili subjects
            cursor.execute("SELECT id, name FROM subject WHERE name LIKE '%Kiswahili%'")
            kiswahili_subjects = cursor.fetchall()
            
            for subject_id, subject_name in kiswahili_subjects:
                # Add Lugha and Insha components for Kiswahili
                components = [
                    (subject_id, 'Lugha', 0.5, 50),
                    (subject_id, 'Insha', 0.5, 50)
                ]
                
                for comp_subject_id, comp_name, comp_weight, comp_max_mark in components:
                    cursor.execute("""
                        INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
                        VALUES (%s, %s, %s, %s)
                    """, (comp_subject_id, comp_name, comp_weight, comp_max_mark))
                
                print(f"✅ Added components for {subject_name}")
            
            connection.commit()
        
        # Final verification
        cursor.execute("SELECT COUNT(*) FROM subject_component")
        final_count = cursor.fetchone()[0]
        print(f"\n📊 Total subject components: {final_count}")
        
        connection.close()
        
        print("\n🎉 SUCCESS: subject_component table fixed!")
        print("✅ All required columns added")
        print("✅ Sample data populated")
        print("✅ Ready for testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing subject_component table: {e}")
        return False

if __name__ == '__main__':
    success = fix_subject_component_table()
    if success:
        print("\n🚀 Database schema fixed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Failed to fix database schema!")
        sys.exit(1)
