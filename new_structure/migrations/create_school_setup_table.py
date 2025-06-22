#!/usr/bin/env python3
"""
Migration script to create the missing school_setup table in MySQL database.
This fixes the ProgrammingError when accessing school setup functionality.
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def create_school_setup_table():
    """Create the school_setup table with all required columns."""
    
    try:
        from new_structure import create_app
        from new_structure.extensions import db
        from new_structure.models.school_setup import SchoolSetup
        
        print("🔧 Creating school_setup table...")
        
        # Create Flask app context
        app = create_app('development')
        
        with app.app_context():
            # Check if table already exists
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'school_setup' in existing_tables:
                print("✅ school_setup table already exists!")
                return True
            
            # Create the table
            print("📋 Creating school_setup table with all columns...")
            
            # Use SQLAlchemy to create the table
            SchoolSetup.__table__.create(db.engine, checkfirst=True)
            
            print("✅ school_setup table created successfully!")
            
            # Verify table creation
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'school_setup' in tables:
                print("✅ Table 'school_setup' confirmed in database")
                
                # Show table structure
                columns = inspector.get_columns('school_setup')
                print("\n📋 Table structure:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
                
                # Create default school setup record
                print("\n🏫 Creating default school setup record...")
                
                default_setup = SchoolSetup(
                    school_name='Hillview School',
                    school_motto='Excellence in Education',
                    school_vision='To be a leading institution in providing quality education',
                    school_mission='To nurture and develop students to their full potential',
                    current_academic_year='2024',
                    current_term='Term 1',
                    total_terms_per_year=3,
                    education_system='CBC',
                    school_type='Private',
                    school_category='Primary',
                    uses_streams=True,
                    lowest_grade='PP1',
                    highest_grade='Grade 6',
                    grading_system='CBC',
                    max_raw_marks_default=100,
                    pass_mark_percentage=50.0,
                    show_position=True,
                    show_class_average=True,
                    show_subject_teacher=False,
                    report_footer='Powered by Hillview SMS',
                    timezone='Africa/Nairobi',
                    language='en',
                    currency='KES',
                    primary_color='#1f7d53',
                    secondary_color='#18230f',
                    accent_color='#4ade80',
                    setup_completed=False,
                    setup_step=1,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.session.add(default_setup)
                db.session.commit()
                
                print("✅ Default school setup record created!")
                print(f"   School Name: {default_setup.school_name}")
                print(f"   Academic Year: {default_setup.current_academic_year}")
                print(f"   Current Term: {default_setup.current_term}")
                print(f"   Education System: {default_setup.education_system}")
                
                return True
            else:
                print("❌ Table 'school_setup' not found after creation attempt")
                return False
                
    except Exception as e:
        print(f"❌ Error creating school_setup table: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_school_branding_table():
    """Create the school_branding table if it doesn't exist."""
    
    try:
        from new_structure import create_app
        from new_structure.extensions import db
        from new_structure.models.school_setup import SchoolBranding
        
        print("\n🎨 Creating school_branding table...")
        
        # Create Flask app context
        app = create_app('development')
        
        with app.app_context():
            # Check if table already exists
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'school_branding' in existing_tables:
                print("✅ school_branding table already exists!")
                return True
            
            # Create the table
            SchoolBranding.__table__.create(db.engine, checkfirst=True)
            
            print("✅ school_branding table created successfully!")
            
            # Create default branding record
            default_branding = SchoolBranding(
                primary_color='#1f7d53',
                secondary_color='#18230f',
                accent_color='#4ade80',
                text_color='#1e293b',
                background_color='#ffffff',
                primary_font='Arial, sans-serif',
                secondary_font='Georgia, serif',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(default_branding)
            db.session.commit()
            
            print("✅ Default school branding record created!")
            return True
            
    except Exception as e:
        print(f"❌ Error creating school_branding table: {str(e)}")
        return False

def create_school_customization_table():
    """Create the school_customization table if it doesn't exist."""
    
    try:
        from new_structure import create_app
        from new_structure.extensions import db
        from new_structure.models.school_setup import SchoolCustomization
        
        print("\n⚙️ Creating school_customization table...")
        
        # Create Flask app context
        app = create_app('development')
        
        with app.app_context():
            # Check if table already exists
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'school_customization' in existing_tables:
                print("✅ school_customization table already exists!")
                return True
            
            # Create the table
            SchoolCustomization.__table__.create(db.engine, checkfirst=True)
            
            print("✅ school_customization table created successfully!")
            
            # Create default customization record
            default_customization = SchoolCustomization(
                enable_analytics=True,
                enable_parent_portal=False,
                enable_sms_notifications=False,
                enable_email_notifications=True,
                enable_mobile_app=False,
                ministry_integration=False,
                auto_backup_enabled=True,
                backup_frequency='daily',
                data_retention_days=365,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(default_customization)
            db.session.commit()
            
            print("✅ Default school customization record created!")
            return True
            
    except Exception as e:
        print(f"❌ Error creating school_customization table: {str(e)}")
        return False

def main():
    """Main function to create all school setup related tables."""
    print("🚀 Starting School Setup Tables Migration")
    print("=" * 50)
    
    success_count = 0
    total_tables = 3
    
    # Create school_setup table
    if create_school_setup_table():
        success_count += 1
    
    # Create school_branding table
    if create_school_branding_table():
        success_count += 1
    
    # Create school_customization table
    if create_school_customization_table():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"🎊 Migration Complete: {success_count}/{total_tables} tables created successfully!")
    
    if success_count == total_tables:
        print("✅ All school setup tables are now ready!")
        print("🔗 You can now access: http://localhost:5000/school-setup/")
        return True
    else:
        print(f"⚠️ {total_tables - success_count} tables failed to create")
        return False

if __name__ == '__main__':
    main()
