#!/usr/bin/env python3
"""
Migration script to fix composite subject architecture.
Converts to clean component-as-independent-subject architecture.
"""

import sys
import os

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Now import from the project
from app import create_app
from extensions import db
from models.academic import Subject, SubjectComponent, Mark, ComponentMark
from services.enhanced_composite_service import EnhancedCompositeService
from sqlalchemy import text


def analyze_current_state():
    """Analyze the current state of composite subjects."""
    print("🔍 Analyzing current composite subject state...")
    
    # Get all subjects
    all_subjects = Subject.query.all()
    
    composite_subjects = [s for s in all_subjects if s.is_composite]
    component_subjects = [s for s in all_subjects if s.is_component]
    regular_subjects = [s for s in all_subjects if not s.is_composite and not s.is_component]
    
    print(f"📊 Current state:")
    print(f"   - Composite subjects: {len(composite_subjects)}")
    print(f"   - Component subjects: {len(component_subjects)}")
    print(f"   - Regular subjects: {len(regular_subjects)}")
    
    print(f"\n📚 Composite subjects found:")
    for subject in composite_subjects:
        print(f"   - {subject.name} ({subject.education_level})")
        
    print(f"\n🔧 Component subjects found:")
    for subject in component_subjects:
        print(f"   - {subject.name} ({subject.education_level}) -> parent: {subject.composite_parent}")
    
    # Check for marks
    composite_marks = 0
    component_marks = 0
    
    for subject in composite_subjects:
        marks_count = Mark.query.filter_by(subject_id=subject.id).count()
        composite_marks += marks_count
        if marks_count > 0:
            print(f"   ⚠️ {subject.name} has {marks_count} marks that need migration")
    
    for subject in component_subjects:
        marks_count = Mark.query.filter_by(subject_id=subject.id).count()
        component_marks += marks_count
    
    print(f"\n📈 Marks summary:")
    print(f"   - Marks on composite subjects: {composite_marks}")
    print(f"   - Marks on component subjects: {component_marks}")
    
    return {
        'composite_subjects': composite_subjects,
        'component_subjects': component_subjects,
        'regular_subjects': regular_subjects,
        'composite_marks': composite_marks,
        'component_marks': component_marks
    }


def migrate_composite_marks_to_components():
    """Migrate marks from composite subjects to component subjects."""
    print("\n🔄 Migrating composite subject marks to component subjects...")
    
    migrated_count = 0
    
    # Get all composite subjects that have marks
    composite_subjects = Subject.query.filter_by(is_composite=True).all()
    
    for composite_subject in composite_subjects:
        print(f"\n📚 Processing {composite_subject.name}...")
        
        # Get all marks for this composite subject
        composite_marks = Mark.query.filter_by(subject_id=composite_subject.id).all()
        
        if not composite_marks:
            print(f"   ✅ No marks to migrate for {composite_subject.name}")
            continue
        
        print(f"   📊 Found {len(composite_marks)} marks to migrate")
        
        # Get component marks for these composite marks
        for mark in composite_marks:
            component_marks = ComponentMark.query.filter_by(mark_id=mark.id).all()
            
            if not component_marks:
                print(f"   ⚠️ No component marks found for mark ID {mark.id}")
                continue
            
            # Migrate each component mark to a separate subject mark
            for comp_mark in component_marks:
                component = SubjectComponent.query.get(comp_mark.component_id)
                if not component:
                    continue
                
                # Find or create the component subject
                component_subject_name = f"{composite_subject.name} {component.name}"
                component_subject = Subject.query.filter_by(
                    name=component_subject_name,
                    education_level=composite_subject.education_level
                ).first()
                
                if not component_subject:
                    # Create component subject
                    component_subject = Subject(
                        name=component_subject_name,
                        education_level=composite_subject.education_level,
                        is_composite=False,
                        is_component=True,
                        composite_parent=composite_subject.name,
                        component_weight=component.weight
                    )
                    db.session.add(component_subject)
                    db.session.flush()  # Get the ID
                
                # Check if mark already exists for this component subject
                existing_mark = Mark.query.filter_by(
                    student_id=mark.student_id,
                    subject_id=component_subject.id,
                    term_id=mark.term_id,
                    assessment_type_id=mark.assessment_type_id
                ).first()
                
                if not existing_mark:
                    # Create new mark for component subject
                    new_mark = Mark(
                        student_id=mark.student_id,
                        subject_id=component_subject.id,
                        term_id=mark.term_id,
                        assessment_type_id=mark.assessment_type_id,
                        grade_id=mark.grade_id,
                        stream_id=mark.stream_id,
                        raw_mark=comp_mark.raw_mark,
                        raw_total_marks=comp_mark.max_raw_mark,
                        percentage=comp_mark.percentage,
                        is_uploaded=mark.is_uploaded,
                        uploaded_by_teacher_id=mark.uploaded_by_teacher_id,
                        upload_date=mark.upload_date,
                        created_at=mark.created_at
                    )
                    db.session.add(new_mark)
                    migrated_count += 1
                    
                    if migrated_count % 10 == 0:
                        print(f"   📈 Migrated {migrated_count} component marks...")
    
    print(f"\n✅ Migration completed. Total marks migrated: {migrated_count}")
    return migrated_count


def cleanup_old_architecture():
    """Clean up the old composite architecture."""
    print("\n🧹 Cleaning up old composite architecture...")
    
    # Delete component marks (they're now separate Mark records)
    component_marks_count = ComponentMark.query.count()
    if component_marks_count > 0:
        print(f"   🗑️ Deleting {component_marks_count} component marks...")
        ComponentMark.query.delete()
    
    # Delete subject components (components are now independent subjects)
    subject_components_count = SubjectComponent.query.count()
    if subject_components_count > 0:
        print(f"   🗑️ Deleting {subject_components_count} subject components...")
        SubjectComponent.query.delete()
    
    # Delete marks on composite subjects (they're now on component subjects)
    composite_subjects = Subject.query.filter_by(is_composite=True).all()
    deleted_marks = 0
    
    for composite_subject in composite_subjects:
        marks_count = Mark.query.filter_by(subject_id=composite_subject.id).count()
        if marks_count > 0:
            print(f"   🗑️ Deleting {marks_count} marks from {composite_subject.name}...")
            Mark.query.filter_by(subject_id=composite_subject.id).delete()
            deleted_marks += marks_count
    
    print(f"   ✅ Deleted {deleted_marks} composite subject marks")
    
    return {
        'component_marks_deleted': component_marks_count,
        'subject_components_deleted': subject_components_count,
        'composite_marks_deleted': deleted_marks
    }


def setup_enhanced_architecture():
    """Set up the enhanced component-as-independent-subject architecture."""
    print("\n🚀 Setting up enhanced composite architecture...")
    
    # Ensure all education levels have proper component subjects
    education_levels = ['lower_primary', 'upper_primary', 'junior_secondary']
    
    for education_level in education_levels:
        print(f"   📚 Setting up {education_level}...")
        EnhancedCompositeService.ensure_component_subjects_exist(education_level)
    
    print("   ✅ Enhanced architecture setup completed")


def main():
    """Main migration function."""
    print("🎯 Starting Composite Subject Architecture Fix")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Analyze current state
            current_state = analyze_current_state()
            
            # Step 2: Migrate composite marks to component subjects
            if current_state['composite_marks'] > 0:
                migrated_count = migrate_composite_marks_to_components()
                db.session.commit()
                print(f"✅ Committed {migrated_count} migrated marks")
            
            # Step 3: Clean up old architecture
            cleanup_stats = cleanup_old_architecture()
            db.session.commit()
            print("✅ Committed cleanup changes")
            
            # Step 4: Set up enhanced architecture
            setup_enhanced_architecture()
            db.session.commit()
            print("✅ Committed enhanced architecture setup")
            
            print("\n🎉 Migration completed successfully!")
            print("=" * 60)
            print("📋 Summary:")
            print(f"   - Marks migrated: {migrated_count if 'migrated_count' in locals() else 0}")
            print(f"   - Component marks deleted: {cleanup_stats['component_marks_deleted']}")
            print(f"   - Subject components deleted: {cleanup_stats['subject_components_deleted']}")
            print(f"   - Composite marks deleted: {cleanup_stats['composite_marks_deleted']}")
            print("\n✅ Your system now uses the enhanced component-as-independent-subject architecture!")
            print("📝 Teachers can now upload Grammar and Composition marks separately.")
            print("📊 Reports will show combined English and Kiswahili columns with component breakdowns.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
