#!/usr/bin/env python3
"""
Add new columns to Subject table manually
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'new_structure'))

def add_columns():
    print("🔧 Starting column addition process...")

    try:
        print("📦 Importing modules...")
        from new_structure import create_app, db
        print("✅ Modules imported successfully")

        print("🚀 Creating app...")
        app = create_app('development')
        print("✅ App created successfully")

        print("🔧 Entering app context...")
        with app.app_context():
            print("✅ App context created successfully")
            
            # Add columns using raw SQL (SQLAlchemy 2.0 syntax)
            try:
                from sqlalchemy import text

                # Check if columns already exist
                with db.engine.connect() as conn:
                    result = conn.execute(text("DESCRIBE subject"))
                    existing_columns = [row[0] for row in result]
                    print(f"📊 Existing columns: {existing_columns}")

                    # Add is_component column if it doesn't exist
                    if 'is_component' not in existing_columns:
                        conn.execute(text("ALTER TABLE subject ADD COLUMN is_component BOOLEAN DEFAULT FALSE"))
                        conn.commit()
                        print("✅ Added is_component column")
                    else:
                        print("⚠️ is_component column already exists")

                    # Add composite_parent column if it doesn't exist
                    if 'composite_parent' not in existing_columns:
                        conn.execute(text("ALTER TABLE subject ADD COLUMN composite_parent VARCHAR(100)"))
                        conn.commit()
                        print("✅ Added composite_parent column")
                    else:
                        print("⚠️ composite_parent column already exists")

                    # Add component_weight column if it doesn't exist
                    if 'component_weight' not in existing_columns:
                        conn.execute(text("ALTER TABLE subject ADD COLUMN component_weight FLOAT DEFAULT 1.0"))
                        conn.commit()
                        print("✅ Added component_weight column")
                    else:
                        print("⚠️ component_weight column already exists")

                    print("🎉 Column addition completed successfully!")

                    # Verify the columns were added
                    result = conn.execute(text("DESCRIBE subject"))
                    new_columns = [row[0] for row in result]
                    print(f"📊 Updated columns: {new_columns}")
                
            except Exception as e:
                print(f"❌ Error adding columns: {e}")
                raise
            
    except Exception as e:
        print(f"❌ Column addition failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_columns()
