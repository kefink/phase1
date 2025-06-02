"""
Database migration script to create the function_permissions table
for the enhanced permission system.
"""
import sqlite3
import os
from datetime import datetime

def create_function_permissions_table(db_path):
    """Create the function_permissions table in the database."""
    
    # SQL to create the function_permissions table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS function_permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        function_name VARCHAR(100) NOT NULL,
        function_category VARCHAR(50) NOT NULL,
        scope_type VARCHAR(20) DEFAULT 'global',
        grade_id INTEGER,
        stream_id INTEGER,
        granted_by INTEGER NOT NULL,
        granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME,
        revoked_at DATETIME,
        is_active BOOLEAN DEFAULT 1,
        notes TEXT,
        auto_granted BOOLEAN DEFAULT 0,
        FOREIGN KEY (teacher_id) REFERENCES teacher (id),
        FOREIGN KEY (grade_id) REFERENCES grade (id),
        FOREIGN KEY (stream_id) REFERENCES stream (id),
        FOREIGN KEY (granted_by) REFERENCES teacher (id)
    );
    """
    
    # SQL to create indexes for better performance
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_function_permissions_teacher_id ON function_permissions(teacher_id);",
        "CREATE INDEX IF NOT EXISTS idx_function_permissions_function_name ON function_permissions(function_name);",
        "CREATE INDEX IF NOT EXISTS idx_function_permissions_is_active ON function_permissions(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_function_permissions_scope ON function_permissions(scope_type, grade_id, stream_id);",
        "CREATE INDEX IF NOT EXISTS idx_function_permissions_granted_by ON function_permissions(granted_by);"
    ]
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Creating function_permissions table in {db_path}...")
        
        # Create the table
        cursor.execute(create_table_sql)
        print("✅ function_permissions table created successfully")
        
        # Create indexes
        for index_sql in create_indexes_sql:
            cursor.execute(index_sql)
        print("✅ Indexes created successfully")
        
        # Commit the changes
        conn.commit()
        print("✅ Database migration completed successfully")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error creating function_permissions table: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def verify_table_creation(db_path):
    """Verify that the function_permissions table was created correctly."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='function_permissions';
        """)
        
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Get table schema
            cursor.execute("PRAGMA table_info(function_permissions);")
            columns = cursor.fetchall()
            
            print("✅ function_permissions table verified")
            print("📋 Table schema:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
            
            return True
        else:
            print("❌ function_permissions table not found")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Error verifying table: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def run_migration():
    """Run the migration for both possible database locations."""
    
    # Possible database paths
    db_paths = [
        "kirima_primary.db",
        "new_structure/kirima_primary.db",
        "../kirima_primary.db"
    ]
    
    migration_success = False
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\n🔍 Found database at: {db_path}")
            
            # Create the table
            if create_function_permissions_table(db_path):
                # Verify the creation
                if verify_table_creation(db_path):
                    migration_success = True
                    print(f"✅ Migration completed successfully for {db_path}")
                else:
                    print(f"❌ Migration verification failed for {db_path}")
            else:
                print(f"❌ Migration failed for {db_path}")
        else:
            print(f"⚠️  Database not found at: {db_path}")
    
    if migration_success:
        print("\n🎉 Function permissions table migration completed!")
        print("You can now use the enhanced permission system.")
    else:
        print("\n❌ Migration failed. Please check the database path and try again.")
    
    return migration_success

if __name__ == "__main__":
    print("🚀 Starting function_permissions table migration...")
    run_migration()
