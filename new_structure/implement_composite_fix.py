#!/usr/bin/env python3
"""
Direct implementation of composite subject fix.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def implement_composite_fix():
    """Implement the composite subject fix directly."""
    print("🎯 Implementing Composite Subject Architecture Fix")
    print("=" * 60)
    
    try:
        # Import Flask app and database
        from app import create_app
        from extensions import db
        from models.academic import Subject, SubjectComponent, Mark, ComponentMark
        
        app = create_app()
        
        with app.app_context():
            print("📊 Analyzing current composite subject state...")
            
            # Get all subjects
            all_subjects = Subject.query.all()
            
            composite_subjects = [s for s in all_subjects if s.is_composite]
            component_subjects = [s for s in all_subjects if s.is_component]
            regular_subjects = [s for s in all_subjects if not s.is_composite and not s.is_component]
            
            print(f"   - Composite subjects: {len(composite_subjects)}")
            print(f"   - Component subjects: {len(component_subjects)}")
            print(f"   - Regular subjects: {len(regular_subjects)}")
            
            # Define the composite mappings we want
            composite_mappings = {
                'English': {
                    'components': ['English Grammar', 'English Composition'],
                    'weights': [0.6, 0.4]
                },
                'Kiswahili': {
                    'components': ['Kiswahili Lugha', 'Kiswahili Insha'],
                    'weights': [0.6, 0.4]
                }
            }
            
            print("\n🔧 Setting up enhanced composite architecture...")
            
            # Process each education level
            education_levels = ['lower_primary', 'upper_primary', 'junior_secondary']
            
            for education_level in education_levels:
                print(f"\n📚 Processing {education_level}...")
                
                for composite_name, config in composite_mappings.items():
                    # Ensure composite parent exists
                    composite_subject = Subject.query.filter_by(
                        name=composite_name,
                        education_level=education_level
                    ).first()
                    
                    if not composite_subject:
                        print(f"   ➕ Creating composite subject: {composite_name}")
                        composite_subject = Subject(
                            name=composite_name,
                            education_level=education_level,
                            is_composite=True,
                            is_component=False
                        )
                        db.session.add(composite_subject)
                    else:
                        print(f"   ✅ Updating composite subject: {composite_name}")
                        composite_subject.is_composite = True
                        composite_subject.is_component = False
                    
                    # Create/update component subjects
                    for i, component_name in enumerate(config['components']):
                        component_subject = Subject.query.filter_by(
                            name=component_name,
                            education_level=education_level
                        ).first()
                        
                        if not component_subject:
                            print(f"   ➕ Creating component subject: {component_name}")
                            component_subject = Subject(
                                name=component_name,
                                education_level=education_level,
                                is_composite=False,
                                is_component=True,
                                composite_parent=composite_name,
                                component_weight=config['weights'][i]
                            )
                            db.session.add(component_subject)
                        else:
                            print(f"   ✅ Updating component subject: {component_name}")
                            component_subject.is_component = True
                            component_subject.is_composite = False
                            component_subject.composite_parent = composite_name
                            component_subject.component_weight = config['weights'][i]
            
            # Commit the changes
            db.session.commit()
            print("\n✅ Database changes committed successfully!")
            
            # Verify the setup
            print("\n🔍 Verifying the setup...")
            
            for education_level in education_levels:
                print(f"\n📚 {education_level}:")
                
                for composite_name in composite_mappings.keys():
                    composite_subject = Subject.query.filter_by(
                        name=composite_name,
                        education_level=education_level,
                        is_composite=True
                    ).first()
                    
                    if composite_subject:
                        print(f"   ✅ {composite_name} (composite)")
                        
                        # Check components
                        components = Subject.query.filter_by(
                            composite_parent=composite_name,
                            education_level=education_level,
                            is_component=True
                        ).all()
                        
                        for component in components:
                            print(f"      └─ {component.name} (weight: {component.component_weight})")
                    else:
                        print(f"   ❌ {composite_name} not found")
            
            print("\n🎉 Implementation completed successfully!")
            print("=" * 60)
            print("📋 What was implemented:")
            print("✅ English Grammar and English Composition are now separate uploadable subjects")
            print("✅ Kiswahili Lugha and Kiswahili Insha are now separate uploadable subjects")
            print("✅ All subjects properly configured with composite relationships")
            print("✅ Component weights set (Grammar/Lugha: 60%, Composition/Insha: 40%)")
            
            print("\n📝 Next steps:")
            print("1. Test uploading marks for English Grammar separately")
            print("2. Test uploading marks for English Composition separately")
            print("3. Generate a class report to see the new structure")
            print("4. Verify that marks combine properly in reports")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error during implementation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    success = implement_composite_fix()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
