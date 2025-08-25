#!/usr/bin/env python3
"""
Simple migration to add component subjects
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'new_structure'))

def run_simple_migration():
    try:
        print("🚀 Starting simple migration...")
        
        from new_structure import create_app, db
        from new_structure.models.academic import Subject
        
        app = create_app('development')
        
        with app.app_context():
            print("✅ App context created")
            
            # First, let's create the database tables with new columns
            print("🔧 Creating/updating database tables...")
            db.create_all()
            print("✅ Database tables updated")
            
            # Create component subjects
            component_subjects = [
                # English components
                {
                    'name': 'English Grammar',
                    'education_level': 'primary',
                    'is_component': True,
                    'composite_parent': 'English',
                    'component_weight': 0.6,
                    'is_composite': False
                },
                {
                    'name': 'English Composition', 
                    'education_level': 'primary',
                    'is_component': True,
                    'composite_parent': 'English',
                    'component_weight': 0.4,
                    'is_composite': False
                },
                {
                    'name': 'English Grammar',
                    'education_level': 'junior secondary',
                    'is_component': True,
                    'composite_parent': 'English',
                    'component_weight': 0.6,
                    'is_composite': False
                },
                {
                    'name': 'English Composition',
                    'education_level': 'junior secondary', 
                    'is_component': True,
                    'composite_parent': 'English',
                    'component_weight': 0.4,
                    'is_composite': False
                },
                
                # Kiswahili components
                {
                    'name': 'Kiswahili Lugha',
                    'education_level': 'primary',
                    'is_component': True,
                    'composite_parent': 'Kiswahili',
                    'component_weight': 0.5,
                    'is_composite': False
                },
                {
                    'name': 'Kiswahili Insha',
                    'education_level': 'primary',
                    'is_component': True,
                    'composite_parent': 'Kiswahili', 
                    'component_weight': 0.5,
                    'is_composite': False
                },
                {
                    'name': 'Kiswahili Lugha',
                    'education_level': 'junior secondary',
                    'is_component': True,
                    'composite_parent': 'Kiswahili',
                    'component_weight': 0.5,
                    'is_composite': False
                },
                {
                    'name': 'Kiswahili Insha',
                    'education_level': 'junior secondary',
                    'is_component': True,
                    'composite_parent': 'Kiswahili',
                    'component_weight': 0.5,
                    'is_composite': False
                }
            ]
            
            created_count = 0
            updated_count = 0
            
            for subject_data in component_subjects:
                # Check if subject already exists
                existing = Subject.query.filter_by(
                    name=subject_data['name'],
                    education_level=subject_data['education_level']
                ).first()
                
                if not existing:
                    # Create new component subject
                    new_subject = Subject(
                        name=subject_data['name'],
                        education_level=subject_data['education_level'],
                        is_composite=subject_data['is_composite'],
                        is_component=subject_data['is_component'],
                        composite_parent=subject_data['composite_parent'],
                        component_weight=subject_data['component_weight']
                    )
                    
                    db.session.add(new_subject)
                    created_count += 1
                    print(f"✅ Created: {subject_data['name']} ({subject_data['education_level']})")
                else:
                    # Update existing subject to be a component
                    existing.is_component = subject_data['is_component']
                    existing.composite_parent = subject_data['composite_parent']
                    existing.component_weight = subject_data['component_weight']
                    updated_count += 1
                    print(f"🔄 Updated: {subject_data['name']} ({subject_data['education_level']})")
            
            # Commit changes
            db.session.commit()
            
            print(f"\n🎉 Migration completed successfully!")
            print(f"✅ Created {created_count} new component subjects")
            print(f"🔄 Updated {updated_count} existing subjects")
            
            # Verify the results
            print("\n📊 Verification:")
            component_subjects_count = Subject.query.filter_by(is_component=True).count()
            print(f"Total component subjects in database: {component_subjects_count}")
            
            # List all component subjects
            components = Subject.query.filter_by(is_component=True).all()
            for comp in components:
                print(f"  - {comp.name} ({comp.education_level}) -> {comp.composite_parent}")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_simple_migration()
