#!/usr/bin/env python3
"""
Fix the component_mark table schema to include missing columns.
"""

import sys
import os

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def fix_component_mark_schema():
    """Fix the component_mark table schema."""
    
    try:
        from new_structure import create_app
        from new_structure.extensions import db
        
        print("🔧 Fixing Component Mark Table Schema")
        print("=" * 40)
        
        app = create_app('development')
        
        with app.app_context():
            # Get database connection
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            # Check if component_mark table exists
            cursor.execute("SHOW TABLES LIKE 'component_mark'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("❌ component_mark table does not exist!")
                print("Creating component_mark table...")
                
                create_table_sql = """
                CREATE TABLE component_mark (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    mark_id INT NOT NULL,
                    component_id INT NOT NULL,
                    raw_mark FLOAT NOT NULL,
                    max_raw_mark INT DEFAULT 100,
                    percentage FLOAT NOT NULL,
                    FOREIGN KEY (mark_id) REFERENCES mark(id) ON DELETE CASCADE,
                    FOREIGN KEY (component_id) REFERENCES subject_component(id) ON DELETE CASCADE
                )
                """
                cursor.execute(create_table_sql)
                connection.commit()
                print("✅ Created component_mark table with all required columns")
                
            else:
                print("✅ component_mark table exists")
                
                # Check current columns
                cursor.execute("DESCRIBE component_mark")
                columns = cursor.fetchall()
                existing_columns = [col[0] for col in columns]
                
                print(f"Current columns: {existing_columns}")
                
                # Check for missing columns
                required_columns = {
                    'max_raw_mark': 'INT DEFAULT 100',
                    'percentage': 'FLOAT NOT NULL DEFAULT 0'
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
                            cursor.execute(f"ALTER TABLE component_mark ADD COLUMN {col_name} {col_def}")
                            print(f"✅ Added column: {col_name}")
                        except Exception as e:
                            print(f"❌ Error adding column {col_name}: {e}")
                    
                    connection.commit()
                    print("✅ Schema update completed")
                    
                else:
                    print("✅ All required columns are present")
            
            # Verify final schema
            print("\n📋 Final Schema Verification:")
            cursor.execute("DESCRIBE component_mark")
            columns = cursor.fetchall()
            
            for col in columns:
                print(f"  - {col[0]}: {col[1]} {col[2] if col[2] == 'NO' else ''} {col[4] if col[4] else ''}")
            
            # Check for any existing data
            cursor.execute("SELECT COUNT(*) FROM component_mark")
            count = cursor.fetchone()[0]
            print(f"\n📊 Current records in component_mark: {count}")
            
            # If there are records with NULL max_raw_mark, update them
            if count > 0:
                cursor.execute("SELECT COUNT(*) FROM component_mark WHERE max_raw_mark IS NULL")
                null_count = cursor.fetchone()[0]
                
                if null_count > 0:
                    print(f"🔧 Updating {null_count} records with NULL max_raw_mark...")
                    cursor.execute("UPDATE component_mark SET max_raw_mark = 100 WHERE max_raw_mark IS NULL")
                    connection.commit()
                    print("✅ Updated NULL max_raw_mark values to 100")
                
                # Update NULL percentage values
                cursor.execute("SELECT COUNT(*) FROM component_mark WHERE percentage IS NULL")
                null_percentage_count = cursor.fetchone()[0]
                
                if null_percentage_count > 0:
                    print(f"🔧 Updating {null_percentage_count} records with NULL percentage...")
                    cursor.execute("""
                        UPDATE component_mark 
                        SET percentage = (raw_mark / max_raw_mark) * 100 
                        WHERE percentage IS NULL AND max_raw_mark > 0
                    """)
                    connection.commit()
                    print("✅ Updated NULL percentage values")
            
            cursor.close()
            connection.close()
            
            print("\n🎉 Component Mark Schema Fix Completed!")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    fix_component_mark_schema()
