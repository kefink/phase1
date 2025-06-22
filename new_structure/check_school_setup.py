#!/usr/bin/env python3
"""
Check current school setup status.
"""

import sys
import os

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def check_school_setup():
    """Check current school setup."""
    
    try:
        from new_structure import create_app
        from new_structure.models.school_setup import SchoolSetup
        from new_structure.services.dynamic_school_info_service import DynamicSchoolInfoService
        
        print("🏫 School Setup Status Check")
        print("=" * 30)
        
        app = create_app('development')
        
        with app.app_context():
            # Check school setup
            setup = SchoolSetup.query.first()
            
            if setup:
                print(f"✅ School Setup Found:")
                print(f"   - School Name: {setup.school_name}")
                print(f"   - School Motto: {setup.school_motto}")
                print(f"   - Logo Filename: {setup.logo_filename}")
                print(f"   - Setup Completed: {setup.setup_completed}")
                print(f"   - Primary Color: {setup.primary_color}")
                print(f"   - Secondary Color: {setup.secondary_color}")
                print(f"   - Accent Color: {setup.accent_color}")
                
                # Test dynamic school info service
                print(f"\n🔄 Dynamic School Info Service:")
                try:
                    school_info = DynamicSchoolInfoService.get_school_info()
                    print(f"   - Service School Name: {school_info.get('school_name')}")
                    print(f"   - Service Logo URL: {school_info.get('logo_url')}")
                    print(f"   - Service Logo Path: {school_info.get('logo_path')}")

                    # Test context processor
                    print(f"\n🔄 Context Processor Test:")
                    context = DynamicSchoolInfoService.inject_school_info()
                    print(f"   - Context School Name: {context['school_info']['school_name']}")
                    print(f"   - Context Logo URL: {context['school_info']['logo_url']}")

                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                
            else:
                print("❌ No school setup found")
                print("   Creating default setup...")
                
                # Create default setup
                default_setup = SchoolSetup(
                    school_name='Hillview School',
                    school_motto='Excellence in Education',
                    current_academic_year='2025/2026',
                    current_term='Term 2',
                    primary_color='#1f7d53',
                    secondary_color='#18230f',
                    accent_color='#4ade80',
                    setup_completed=True
                )
                
                from new_structure.extensions import db
                db.session.add(default_setup)
                db.session.commit()
                
                print("✅ Default setup created!")
                print(f"   - School Name: {default_setup.school_name}")
                print(f"   - School Motto: {default_setup.school_motto}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    check_school_setup()
