#!/usr/bin/env python3
"""
Migration script to convert composite subjects to independent component subjects.
This implements Option 1: Component-as-Independent-Subject architecture.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from __init__ import create_app, db
from models.academic import Subject, SubjectComponent, Mark, ComponentMark
from sqlalchemy import text

def add_new_columns():
    """Add new columns to Subject table for component support."""
    print("🔧 Adding new columns to Subject table...")
    
    try:
        # Add new columns if they don't exist
        db.engine.execute(text("""
            ALTER TABLE subject 
            ADD COLUMN IF NOT EXISTS is_component BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS composite_parent VARCHAR(100),
            ADD COLUMN IF NOT EXISTS component_weight FLOAT DEFAULT 1.0
        """))
        
        db.session.commit()
        print("✅ Successfully added new columns to Subject table")
        
    except Exception as e:
        print(f"❌ Error adding columns: {e}")
        db.session.rollback()
        raise

def create_component_subjects():
    """Create individual component subjects from existing composite subjects."""
    print("🏗️ Creating component subjects...")
    
    # Define component subjects to create
    component_subjects = [
        # English components
        {
            'name': 'English Grammar',
            'education_level': 'primary',
            'is_component': True,
            'composite_parent': 'English',
            'component_weight': 0.6,  # 60% weight
            'is_composite': False
        },
        {
            'name': 'English Composition', 
            'education_level': 'primary',
            'is_component': True,
            'composite_parent': 'English',
            'component_weight': 0.4,  # 40% weight
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
            'component_weight': 0.5,  # 50% weight
            'is_composite': False
        },
        {
            'name': 'Kiswahili Insha',
            'education_level': 'primary',
            'is_component': True,
            'composite_parent': 'Kiswahili', 
            'component_weight': 0.5,  # 50% weight
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
            print(f"🔄 Updated: {subject_data['name']} ({subject_data['education_level']})")
    
    try:
        db.session.commit()
        print(f"✅ Successfully created/updated {created_count} component subjects")
    except Exception as e:
        print(f"❌ Error creating component subjects: {e}")
        db.session.rollback()
        raise

def migrate_existing_composite_marks():
    """Migrate existing composite marks to component marks."""
    print("🔄 Migrating existing composite marks to component marks...")
    
    # Find all existing composite subjects
    composite_subjects = Subject.query.filter_by(is_composite=True).all()
    
    migrated_count = 0
    
    for composite_subject in composite_subjects:
        print(f"📊 Processing composite subject: {composite_subject.name}")
        
        # Get all marks for this composite subject
        composite_marks = Mark.query.filter_by(subject_id=composite_subject.id).all()
        
        for mark in composite_marks:
            # Get component marks for this mark
            component_marks = ComponentMark.query.filter_by(mark_id=mark.id).all()
            
            for comp_mark in component_marks:
                # Get the component definition
                component = SubjectComponent.query.get(comp_mark.component_id)
                if not component:
                    continue
                
                # Find the corresponding component subject
                component_subject_name = f"{composite_subject.name} {component.name}"
                component_subject = Subject.query.filter_by(
                    name=component_subject_name,
                    education_level=composite_subject.education_level
                ).first()
                
                if component_subject:
                    # Check if mark already exists for this component subject
                    existing_component_mark = Mark.query.filter_by(
                        student_id=mark.student_id,
                        subject_id=component_subject.id,
                        term_id=mark.term_id,
                        assessment_type_id=mark.assessment_type_id
                    ).first()
                    
                    if not existing_component_mark:
                        # Create new mark for component subject
                        new_mark = Mark(
                            student_id=mark.student_id,
                            subject_id=component_subject.id,
                            term_id=mark.term_id,
                            assessment_type_id=mark.assessment_type_id,
                            raw_mark=comp_mark.raw_mark,
                            max_raw_mark=comp_mark.max_raw_mark,
                            percentage=comp_mark.percentage,
                            created_at=mark.created_at
                        )
                        
                        db.session.add(new_mark)
                        migrated_count += 1
                        
                        if migrated_count % 50 == 0:
                            print(f"📈 Migrated {migrated_count} component marks...")
    
    try:
        db.session.commit()
        print(f"✅ Successfully migrated {migrated_count} component marks")
    except Exception as e:
        print(f"❌ Error migrating marks: {e}")
        db.session.rollback()
        raise

def run_migration():
    """Run the complete migration process."""
    print("🚀 Starting composite to component migration...")
    print("=" * 60)
    
    try:
        # Step 1: Add new columns
        add_new_columns()
        
        # Step 2: Create component subjects
        create_component_subjects()
        
        # Step 3: Migrate existing marks
        migrate_existing_composite_marks()
        
        print("=" * 60)
        print("🎉 Migration completed successfully!")
        print("\n📋 Summary:")
        print("✅ Added new columns to Subject table")
        print("✅ Created component subjects (Grammar, Composition, Lugha, Insha)")
        print("✅ Migrated existing composite marks to component marks")
        print("\n🎯 Next Steps:")
        print("1. Update upload interface to show component subjects")
        print("2. Update report generation to combine component marks")
        print("3. Test the new system thoroughly")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("🔄 Rolling back changes...")
        db.session.rollback()
        raise

if __name__ == "__main__":
    app = create_app('development')
    
    with app.app_context():
        run_migration()
