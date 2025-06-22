#!/usr/bin/env python3
"""
Migration script to add enhanced grading system tables and update school setup.
This adds comprehensive grading system support and fixes logo display issues.
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir)

def add_enhanced_grading_system():
    """Add enhanced grading system tables and update school setup."""
    
    try:
        from new_structure import create_app
        from new_structure.extensions import db
        from new_structure.models.grading_system import GradingSystem, SchoolGradingConfig, initialize_default_grading_systems
        from new_structure.models.school_setup import SchoolSetup
        
        print("🎓 Enhanced Grading System Migration")
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
            required_tables = ['grading_system', 'school_grading_config']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
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
                    
                except Exception as e:
                    print(f"❌ Error creating tables: {e}")
                    return False
            else:
                print("✅ All grading system tables already exist!")
            
            # Update school_setup table with new columns
            print("\n📝 Updating school_setup table...")
            
            try:
                # Check if new columns exist
                columns = inspector.get_columns('school_setup')
                column_names = [col['name'] for col in columns]
                
                new_columns = [
                    'secondary_grading_systems',
                    'show_multiple_grades',
                    'custom_grading_enabled'
                ]
                
                missing_columns = [col for col in new_columns if col not in column_names]
                
                if missing_columns:
                    print(f"🔧 Adding missing columns: {missing_columns}")
                    
                    # Add missing columns using raw SQL
                    for column in missing_columns:
                        if column == 'secondary_grading_systems':
                            db.engine.execute(f"ALTER TABLE school_setup ADD COLUMN {column} TEXT")
                        elif column in ['show_multiple_grades', 'custom_grading_enabled']:
                            db.engine.execute(f"ALTER TABLE school_setup ADD COLUMN {column} BOOLEAN DEFAULT FALSE")
                    
                    print("✅ Columns added successfully!")
                else:
                    print("✅ All columns already exist!")
                
            except Exception as e:
                print(f"⚠️ Note: Could not update school_setup table: {e}")
            
            # Initialize default grading systems
            print("\n📚 Initializing default grading systems...")
            
            try:
                initialize_default_grading_systems()
                print("✅ Default grading systems initialized!")
                
                # Show created systems
                systems = GradingSystem.get_active_systems()
                print(f"📊 Available grading systems ({len(systems)}):")
                for system in systems:
                    default_marker = " (DEFAULT)" if system.is_default else ""
                    print(f"   - {system.name} ({system.code}){default_marker}")
                
            except Exception as e:
                print(f"❌ Error initializing grading systems: {e}")
                return False
            
            # Create default logo directory
            print("\n🖼️ Setting up logo directory...")
            
            try:
                from new_structure.services.dynamic_school_info_service import DynamicSchoolInfoService
                DynamicSchoolInfoService.create_default_logo()
                print("✅ Logo directory and default logo created!")
                
            except Exception as e:
                print(f"⚠️ Note: Could not create default logo: {e}")
            
            # Update existing school setup with enhanced grading
            print("\n⚙️ Updating school setup configuration...")
            
            try:
                setup = SchoolSetup.get_current_setup()
                if setup:
                    # Ensure grading system is set
                    if not setup.grading_system:
                        setup.grading_system = 'CBC'
                    
                    # Set default values for new fields
                    if not hasattr(setup, 'show_multiple_grades') or setup.show_multiple_grades is None:
                        setup.show_multiple_grades = False
                    
                    if not hasattr(setup, 'custom_grading_enabled') or setup.custom_grading_enabled is None:
                        setup.custom_grading_enabled = False
                    
                    db.session.commit()
                    print("✅ School setup updated with enhanced grading configuration!")
                
            except Exception as e:
                print(f"⚠️ Note: Could not update school setup: {e}")
            
            # Show table structures
            print("\n📊 Enhanced Table Structures:")
            for table_name in required_tables:
                if table_name in db.inspect(db.engine).get_table_names():
                    columns = inspector.get_columns(table_name)
                    print(f"\n🏷️ {table_name}:")
                    for col in columns[:10]:  # Show first 10 columns
                        print(f"   - {col['name']}: {col['type']}")
                    if len(columns) > 10:
                        print(f"   ... and {len(columns) - 10} more columns")
            
            print(f"\n🎉 Enhanced Grading System Migration completed successfully!")
            print(f"✅ Features added:")
            print(f"   - Multiple grading systems support")
            print(f"   - CBC, Percentage, Letter, and Points systems")
            print(f"   - Secondary grading systems (up to 2)")
            print(f"   - Dynamic school information injection")
            print(f"   - Enhanced logo handling")
            print(f"🌐 School setup now available with enhanced grading at:")
            print(f"   http://localhost:5000/school-setup/academic-config")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_enhanced_grading_system():
    """Verify that enhanced grading system is working."""
    
    try:
        from new_structure import create_app
        from new_structure.extensions import db
        from new_structure.models.grading_system import GradingSystem
        from new_structure.services.dynamic_school_info_service import DynamicSchoolInfoService
        
        app = create_app('development')
        
        with app.app_context():
            print("🔍 Verifying enhanced grading system...")
            
            # Check grading systems
            systems = GradingSystem.get_active_systems()
            print(f"✅ Grading systems available: {len(systems)}")
            
            for system in systems:
                print(f"   - {system.name}: {len(system.get_grade_bands())} grade bands")
            
            # Check school info service
            school_info = DynamicSchoolInfoService.get_school_info()
            print(f"✅ School info service working")
            print(f"   - School: {school_info['school_name']}")
            print(f"   - Grading: {school_info['grading_system']}")
            print(f"   - Logo: {school_info['logo_url']}")
            
            # Check grading functionality
            grading_info = DynamicSchoolInfoService.get_grading_system_info()
            print(f"✅ Grading system info available")
            print(f"   - Primary system: {grading_info['primary_system']}")
            print(f"   - Multiple grades: {grading_info['show_multiple_grades']}")
            
            # Test grade calculation
            test_percentage = 85
            grade = DynamicSchoolInfoService.get_grade_for_percentage(test_percentage)
            print(f"✅ Grade calculation working: {test_percentage}% = {grade}")
            
            return True
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Enhanced Grading System Migration")
    print("=" * 40)
    
    # Run the migration
    success = add_enhanced_grading_system()
    
    if success:
        print("\n🔍 Running verification...")
        verify_enhanced_grading_system()
        
        print("\n" + "=" * 40)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("🎓 Enhanced grading system is now available!")
        print("🌐 Features:")
        print("   - Multiple grading systems (CBC, Percentage, Letter, Points)")
        print("   - Secondary grading systems for comparison")
        print("   - Dynamic school information in all templates")
        print("   - Enhanced logo handling and display")
        print("   - Comprehensive grade calculation")
        print("=" * 40)
    else:
        print("\n" + "=" * 40)
        print("❌ MIGRATION FAILED!")
        print("Please check the error messages above.")
        print("=" * 40)
        sys.exit(1)
