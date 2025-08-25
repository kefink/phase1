#!/usr/bin/env python3
"""
Fix parent subjects for component subjects
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'new_structure'))

def fix_parent_subjects():
    print("🔧 Fixing parent subjects for components...")
    
    try:
        from new_structure import create_app, db
        from new_structure.models.academic import Subject
        
        app = create_app('development')
        
        with app.app_context():
            print("✅ App context created")
            
            # Create proper parent subjects if they don't exist
            parent_subjects_needed = [
                {'name': 'English', 'education_level': 'primary', 'is_composite': True},
                {'name': 'English', 'education_level': 'junior secondary', 'is_composite': True},
                {'name': 'Kiswahili', 'education_level': 'primary', 'is_composite': True},
                {'name': 'Kiswahili', 'education_level': 'junior secondary', 'is_composite': True}
            ]
            
            created_count = 0
            
            for parent_data in parent_subjects_needed:
                existing = Subject.query.filter_by(
                    name=parent_data['name'],
                    education_level=parent_data['education_level'],
                    is_composite=True
                ).first()
                
                if not existing:
                    new_parent = Subject(
                        name=parent_data['name'],
                        education_level=parent_data['education_level'],
                        is_composite=parent_data['is_composite'],
                        is_component=False
                    )
                    
                    db.session.add(new_parent)
                    created_count += 1
                    print(f"✅ Created parent: {parent_data['name']} ({parent_data['education_level']})")
                else:
                    print(f"⚠️ Parent already exists: {parent_data['name']} ({parent_data['education_level']})")
            
            if created_count > 0:
                db.session.commit()
                print(f"✅ Created {created_count} parent subjects")
            
            # Verify all components now have valid parents
            print("\n🔍 Verifying component-parent relationships...")
            component_subjects = Subject.query.filter_by(is_component=True).all()
            
            valid_count = 0
            invalid_count = 0
            
            for component in component_subjects:
                parent = Subject.query.filter_by(
                    name=component.composite_parent,
                    education_level=component.education_level,
                    is_composite=True
                ).first()
                
                if parent:
                    valid_count += 1
                    print(f"✅ {component.name} -> {component.composite_parent} (Valid)")
                else:
                    invalid_count += 1
                    print(f"❌ {component.name} -> {component.composite_parent} (Invalid)")
            
            print(f"\n📊 Results:")
            print(f"✅ Valid relationships: {valid_count}")
            print(f"❌ Invalid relationships: {invalid_count}")
            
            if invalid_count == 0:
                print("🎉 All component subjects have valid parents!")
            
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_parent_subjects()
