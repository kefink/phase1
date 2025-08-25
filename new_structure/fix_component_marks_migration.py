#!/usr/bin/env python3
"""
Migration script to fix component marks issue.
This script converts standalone component subjects (like "Kiswahili Insha", "Kiswahili Lugha") 
into proper component marks for composite subjects.
"""

import sys
import os

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from new_structure import create_app
from new_structure.models.academic import *
from new_structure.extensions import db

def fix_component_marks():
    """Convert standalone component subject marks to proper component marks."""
    
    app = create_app()
    with app.app_context():
        print("🔧 Starting component marks migration...")
        
        # Step 1: Find all composite subjects and their components
        composite_subjects = Subject.query.filter_by(is_composite=True).all()
        print(f"Found {len(composite_subjects)} composite subjects")
        
        conversions_made = 0
        
        for composite_subject in composite_subjects:
            print(f"\n📚 Processing composite subject: {composite_subject.name}")
            components = composite_subject.get_components()
            
            for component in components:
                print(f"  🔍 Looking for standalone subject: {composite_subject.name} {component.name}")
                
                # Look for standalone subjects that match this component
                standalone_subject_patterns = [
                    f"{composite_subject.name} {component.name}",
                    f"{composite_subject.name.title()} {component.name}",
                    f"{composite_subject.name.upper()} {component.name.upper()}",
                    f"{composite_subject.name.lower()} {component.name.lower()}"
                ]
                
                for pattern in standalone_subject_patterns:
                    standalone_subject = Subject.query.filter_by(name=pattern).first()
                    
                    if standalone_subject:
                        print(f"    ✅ Found standalone subject: {standalone_subject.name} (ID: {standalone_subject.id})")
                        
                        # Get all marks for this standalone subject
                        marks = Mark.query.filter_by(subject_id=standalone_subject.id).all()
                        print(f"    📊 Found {len(marks)} marks to convert")
                        
                        for mark in marks:
                            # Check if component mark already exists
                            existing_component_mark = ComponentMark.query.filter_by(
                                component_id=component.id,
                                mark_id=mark.id
                            ).first()
                            
                            if not existing_component_mark:
                                # Create new component mark
                                component_mark = ComponentMark(
                                    component_id=component.id,
                                    mark_id=mark.id,
                                    raw_mark=mark.raw_mark,
                                    total_marks=mark.total_marks,
                                    percentage=mark.percentage
                                )
                                
                                db.session.add(component_mark)
                                conversions_made += 1
                                
                                print(f"      ➕ Created component mark: Student {mark.student_id}, {component.name}: {mark.raw_mark}")
                            else:
                                print(f"      ⚠️ Component mark already exists for Student {mark.student_id}")
        
        # Commit all changes
        if conversions_made > 0:
            try:
                db.session.commit()
                print(f"\n✅ Successfully converted {conversions_made} marks to component marks!")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error committing changes: {e}")
                return False
        else:
            print("\n📝 No conversions needed - all component marks already exist")
        
        # Step 2: Verify the conversion
        print("\n🔍 Verifying conversion...")
        component_marks = ComponentMark.query.all()
        print(f"Total component marks in database: {len(component_marks)}")
        
        # Check Kiswahili Insha specifically
        kiswahili = Subject.query.filter_by(name='KISWAHILI', is_composite=True).first()
        if not kiswahili:
            # Try other variations
            kiswahili = Subject.query.filter(
                Subject.name.ilike('%kiswahili%'),
                Subject.is_composite == True
            ).first()
        
        if kiswahili:
            components = kiswahili.get_components()
            insha_component = None
            for comp in components:
                if 'insha' in comp.name.lower():
                    insha_component = comp
                    break
            
            if insha_component:
                insha_marks = ComponentMark.query.filter_by(component_id=insha_component.id).all()
                print(f"✅ Kiswahili Insha component marks: {len(insha_marks)}")
                
                if len(insha_marks) > 0:
                    print("Sample marks:")
                    for mark in insha_marks[:3]:
                        student_id = mark.mark.student_id if mark.mark else 'N/A'
                        print(f"  - Student {student_id}: {mark.raw_mark}/{mark.total_marks}")
        
        return True

if __name__ == "__main__":
    success = fix_component_marks()
    if success:
        print("\n🎉 Component marks migration completed successfully!")
    else:
        print("\n💥 Component marks migration failed!")
        sys.exit(1)
