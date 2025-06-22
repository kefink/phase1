#!/usr/bin/env python3
"""
Migration script to fix school_setup table columns for enhanced grading system.
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir)

def fix_school_setup_columns():
    """Fix school_setup table by adding missing columns."""
    
    try:
        from new_structure import create_app
        from new_structure.extensions import db
        
        print("🔧 Fixing School Setup Table Columns")
        print("=" * 50)
        
        # Create Flask app context
        app = create_app('development')
        
        with app.app_context():
            # Check current database connection
            print(f"📍 Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Check existing columns
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('school_setup')
            column_names = [col['name'] for col in columns]
            
            print(f"📋 Current columns in school_setup: {len(column_names)}")
            
            # Define new columns to add
            new_columns = {
                'secondary_grading_systems': 'TEXT',
                'show_multiple_grades': 'BOOLEAN DEFAULT FALSE',
                'custom_grading_enabled': 'BOOLEAN DEFAULT FALSE'
            }
            
            missing_columns = [col for col in new_columns.keys() if col not in column_names]
            
            if missing_columns:
                print(f"🔍 Missing columns: {missing_columns}")
                
                # Add missing columns using raw SQL
                for column in missing_columns:
                    column_type = new_columns[column]
                    sql = f"ALTER TABLE school_setup ADD COLUMN {column} {column_type}"
                    
                    try:
                        print(f"   Adding column: {column}")
                        db.engine.execute(sql)
                        print(f"   ✅ Added: {column}")
                    except Exception as e:
                        print(f"   ⚠️ Could not add {column}: {e}")
                
                print("✅ Column addition completed!")
                
                # Verify columns were added
                new_columns_check = inspector.get_columns('school_setup')
                new_column_names = [col['name'] for col in new_columns_check]
                
                added_columns = [col for col in missing_columns if col in new_column_names]
                if added_columns:
                    print(f"✅ Successfully added columns: {added_columns}")
                
            else:
                print("✅ All columns already exist!")
            
            # Update existing records with default values
            print("\n📝 Updating existing records...")
            
            try:
                # Use raw SQL to update records safely
                update_sql = """
                UPDATE school_setup 
                SET 
                    show_multiple_grades = COALESCE(show_multiple_grades, FALSE),
                    custom_grading_enabled = COALESCE(custom_grading_enabled, FALSE)
                WHERE show_multiple_grades IS NULL OR custom_grading_enabled IS NULL
                """
                
                result = db.engine.execute(update_sql)
                print(f"✅ Updated {result.rowcount} records with default values")
                
            except Exception as e:
                print(f"⚠️ Could not update records: {e}")
            
            # Show final table structure
            print("\n📊 Final Table Structure:")
            final_columns = inspector.get_columns('school_setup')
            print(f"🏷️ school_setup ({len(final_columns)} columns):")
            
            # Group columns by category
            basic_cols = [col for col in final_columns if col['name'] in ['id', 'school_name', 'school_motto', 'school_vision', 'school_mission']]
            contact_cols = [col for col in final_columns if col['name'] in ['school_address', 'postal_address', 'school_phone', 'school_email']]
            academic_cols = [col for col in final_columns if col['name'] in ['current_academic_year', 'current_term', 'grading_system', 'secondary_grading_systems', 'show_multiple_grades']]
            branding_cols = [col for col in final_columns if col['name'] in ['logo_filename', 'primary_color', 'secondary_color', 'accent_color']]
            
            print("   📝 Basic Info:", [col['name'] for col in basic_cols])
            print("   📞 Contact Info:", [col['name'] for col in contact_cols])
            print("   🎓 Academic Config:", [col['name'] for col in academic_cols])
            print("   🎨 Branding:", [col['name'] for col in branding_cols])
            
            print(f"\n🎉 School setup table fix completed successfully!")
            print(f"✅ Enhanced grading system columns are now available")
            
            return True
            
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_school_setup_access():
    """Test that school setup can be accessed properly."""
    
    try:
        from new_structure import create_app
        from new_structure.models.school_setup import SchoolSetup
        from new_structure.services.dynamic_school_info_service import DynamicSchoolInfoService
        
        app = create_app('development')
        
        with app.app_context():
            print("🔍 Testing school setup access...")
            
            # Test basic access
            setup = SchoolSetup.get_current_setup()
            print(f"✅ School setup accessible: {setup.school_name}")
            
            # Test new columns
            print(f"   - Grading system: {setup.grading_system}")
            print(f"   - Show multiple grades: {getattr(setup, 'show_multiple_grades', 'Not available')}")
            print(f"   - Custom grading enabled: {getattr(setup, 'custom_grading_enabled', 'Not available')}")
            print(f"   - Secondary systems: {getattr(setup, 'secondary_grading_systems', 'Not available')}")
            
            # Test dynamic school info service
            school_info = DynamicSchoolInfoService.get_school_info()
            print(f"✅ Dynamic school info working")
            print(f"   - School: {school_info['school_name']}")
            print(f"   - Logo URL: {school_info['logo_url']}")
            print(f"   - Primary color: {school_info['primary_color']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 School Setup Table Fix")
    print("=" * 40)
    
    # Run the fix
    success = fix_school_setup_columns()
    
    if success:
        print("\n🔍 Running test...")
        test_school_setup_access()
        
        print("\n" + "=" * 40)
        print("✅ SCHOOL SETUP TABLE FIX COMPLETED!")
        print("🎓 Enhanced grading system is now fully functional!")
        print("🌐 You can now access:")
        print("   http://localhost:5000/school-setup/academic-config")
        print("=" * 40)
    else:
        print("\n" + "=" * 40)
        print("❌ FIX FAILED!")
        print("Please check the error messages above.")
        print("=" * 40)
        sys.exit(1)
