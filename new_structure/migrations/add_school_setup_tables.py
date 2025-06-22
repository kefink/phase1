#!/usr/bin/env python3
"""
Migration script to add missing school_setup related tables to MySQL database.
This fixes the "Table 'hillview_demo001.school_setup' doesn't exist" error.
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir)

def create_school_setup_tables():
    """Create all school setup related tables in MySQL database."""
    
    try:
        from new_structure import create_app
        from new_structure.extensions import db
        from new_structure.models.school_setup import SchoolSetup, SchoolBranding, SchoolCustomization
        
        print("🔧 Creating School Setup Tables Migration")
        print("=" * 50)
        
        # Create Flask app context
        app = create_app('development')
        
        with app.app_context():
            # Check current database connection
            print(f"📍 Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Check if tables already exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"📋 Current tables in database: {len(existing_tables)}")
            
            # Tables we need to create
            required_tables = ['school_setup', 'school_branding', 'school_customization']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if not missing_tables:
                print("✅ All school setup tables already exist!")
                return True
            
            print(f"🔍 Missing tables: {missing_tables}")
            
            # Create the missing tables
            print("\n🚀 Creating missing tables...")
            
            try:
                # Create all tables defined in the models
                db.create_all()
                print("✅ Tables created successfully!")
                
                # Verify tables were created
                new_tables = db.inspect(db.engine).get_table_names()
                created_tables = [table for table in required_tables if table in new_tables and table not in existing_tables]
                
                if created_tables:
                    print(f"✅ Successfully created tables: {created_tables}")
                
                # Create default school setup record
                print("\n📝 Creating default school setup record...")
                
                existing_setup = SchoolSetup.query.first()
                if not existing_setup:
                    default_setup = SchoolSetup(
                        school_name='Hillview School',
                        school_motto='Excellence in Education',
                        school_vision='To be a leading institution in providing quality education',
                        school_mission='To nurture and develop students to their full potential',
                        current_academic_year='2024',
                        current_term='Term 1',
                        education_system='CBC',
                        school_type='Private',
                        school_category='Primary',
                        county='Nairobi',
                        grading_system='CBC',
                        setup_completed=False,
                        setup_step=1
                    )
                    
                    db.session.add(default_setup)
                    db.session.commit()
                    print("✅ Default school setup record created!")
                else:
                    print("ℹ️ School setup record already exists")
                
                # Show table structures
                print("\n📊 Table Structures:")
                for table_name in required_tables:
                    if table_name in new_tables:
                        columns = inspector.get_columns(table_name)
                        print(f"\n🏷️ {table_name}:")
                        for col in columns[:10]:  # Show first 10 columns
                            print(f"   - {col['name']}: {col['type']}")
                        if len(columns) > 10:
                            print(f"   ... and {len(columns) - 10} more columns")
                
                print(f"\n🎉 Migration completed successfully!")
                print(f"✅ School setup tables are now available")
                print(f"🌐 You can now access: http://localhost:5000/school-setup/")
                
                return True
                
            except Exception as e:
                print(f"❌ Error creating tables: {e}")
                db.session.rollback()
                return False
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_school_setup_tables():
    """Verify that school setup tables exist and are accessible."""
    
    try:
        from new_structure import create_app
        from new_structure.extensions import db
        from new_structure.models.school_setup import SchoolSetup
        
        app = create_app('development')
        
        with app.app_context():
            # Test database connection
            print("🔍 Verifying school setup tables...")
            
            # Check if we can query the SchoolSetup table
            setup_count = SchoolSetup.query.count()
            print(f"✅ SchoolSetup table accessible - {setup_count} records found")
            
            # Try to get current setup
            current_setup = SchoolSetup.get_current_setup()
            if current_setup:
                print(f"✅ Current school setup: {current_setup.school_name}")
                print(f"   - Academic Year: {current_setup.current_academic_year}")
                print(f"   - Current Term: {current_setup.current_term}")
                print(f"   - Setup Completed: {current_setup.setup_completed}")
            
            return True
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 School Setup Tables Migration")
    print("=" * 40)
    
    # Run the migration
    success = create_school_setup_tables()
    
    if success:
        print("\n🔍 Running verification...")
        verify_school_setup_tables()
        
        print("\n" + "=" * 40)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("🌐 School Setup is now available at:")
        print("   http://localhost:5000/school-setup/")
        print("=" * 40)
    else:
        print("\n" + "=" * 40)
        print("❌ MIGRATION FAILED!")
        print("Please check the error messages above.")
        print("=" * 40)
        sys.exit(1)
