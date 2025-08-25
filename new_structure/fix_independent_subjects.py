#!/usr/bin/env python3
"""
Fix Independent Subjects Script
===============================

This script fixes the issue where English Grammar and English Composition
are not showing individual student marks in class reports because they're
still configured as composite/component subjects.

The script will:
1. Convert English Grammar and English Composition to independent subjects
2. Remove composite/component relationships
3. Ensure they appear in class reports as separate columns
"""

import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from __init__ import create_app
from models import Subject, Mark
from extensions import db


def fix_independent_subjects():
    """Fix English Grammar and English Composition to be independent subjects"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Converting to Independent Subject Upload")
        print("=" * 60)

        # Education levels to process
        education_levels = ['lower_primary', 'upper_primary', 'junior_secondary']
        
        subjects_to_convert = [
            'English Grammar', 
            'English Composition',
            'Kiswahili Lugha',
            'Kiswahili Insha'
        ]

        for education_level in education_levels:
            print(f"\n📚 Processing {education_level}...")
            
            for subject_name in subjects_to_convert:
                subject = Subject.query.filter_by(
                    name=subject_name,
                    education_level=education_level
                ).first()
                
                if subject:
                    # Convert to independent subject
                    old_composite = subject.is_composite
                    old_component = getattr(subject, 'is_component', False)
                    
                    subject.is_composite = False
                    if hasattr(subject, 'is_component'):
                        subject.is_component = False
                    
                    # Clear composite relationships
                    if hasattr(subject, 'composite_parent'):
                        subject.composite_parent = None
                    if hasattr(subject, 'component_weight'):
                        subject.component_weight = None
                    
                    print(f"   ✅ {subject_name}: composite={old_composite}→False, component={old_component}→False")
                else:
                    print(f"   ❌ {subject_name}: Not found")

        # Commit changes
        try:
            db.session.commit()
            print("\n✅ Database changes committed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error committing changes: {e}")
            return False
        
        # Check current marks for these subjects
        print(f"\n📊 Current marks status:")
        for subject_name in subjects_to_convert:
            subject = Subject.query.filter_by(name=subject_name).first()
            if subject:
                mark_count = Mark.query.filter_by(subject_id=subject.id).count()
                print(f"   - {subject_name}: {mark_count} marks in database")

        print(f"\n🎉 Conversion completed successfully!")
        print("✅ English Grammar and English Composition are now independent subjects")
        print("✅ Kiswahili Lugha and Kiswahili Insha are now independent subjects")
        print("✅ All subjects can be uploaded and displayed independently")
        
        print(f"\n📝 Next steps:")
        print("1. Visit any class report to see individual subject columns")
        print("2. Upload marks for each subject independently")
        print("3. Refresh any cached reports to see the changes")
        
        return True


def check_subject_configuration():
    """Check the current subject configuration"""
    app = create_app()
    
    with app.app_context():
        print("🔍 Current Subject Configuration")
        print("=" * 50)
        
        english_subjects = Subject.query.filter(Subject.name.like('%English%')).all()
        
        for subject in english_subjects:
            print(f"\nSubject: {subject.name}")
            print(f"  Education Level: {subject.education_level}")
            print(f"  Is Composite: {subject.is_composite}")
            print(f"  Is Component: {getattr(subject, 'is_component', 'N/A')}")
            print(f"  Composite Parent: {getattr(subject, 'composite_parent', 'N/A')}")
            print(f"  Component Weight: {getattr(subject, 'component_weight', 'N/A')}")
            
            # Check marks count
            mark_count = Mark.query.filter_by(subject_id=subject.id).count()
            print(f"  Marks in Database: {mark_count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix independent subjects configuration')
    parser.add_argument('--check', action='store_true', help='Check current configuration')
    parser.add_argument('--fix', action='store_true', help='Apply the fix')
    
    args = parser.parse_args()
    
    if args.check:
        check_subject_configuration()
    elif args.fix:
        if fix_independent_subjects():
            print("\n✅ Fix applied successfully!")
        else:
            print("\n❌ Fix failed!")
    else:
        print("Usage: python fix_independent_subjects.py --check | --fix")
        print("  --check  Check current subject configuration")
        print("  --fix    Apply the fix to convert subjects to independent")
