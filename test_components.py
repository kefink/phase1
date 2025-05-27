"""
Test script to check if components are being retrieved correctly.
"""
import sqlite3
import sys
import os
from new_structure.models.academic import Subject, SubjectComponent
from new_structure.extensions import db
from new_structure import create_app

def test_components():
    """Test if components are being retrieved correctly."""
    app = create_app()
    with app.app_context():
        # Get all subjects
        subjects = Subject.query.all()
        
        print("\n=== ALL SUBJECTS ===")
        for subject in subjects:
            print(f"Subject: {subject.name}, ID: {subject.id}, Is Composite: {subject.is_composite}")
            
            # Get components
            components = subject.get_components()
            if components:
                print(f"  Components: {[comp.name for comp in components]}")
            else:
                print("  No components")
        
        # Test specific subjects
        english = Subject.query.get(2)
        kiswahili = Subject.query.get(7)
        
        print("\n=== ENGLISH (ID 2) ===")
        print(f"Subject: {english.name}, ID: {english.id}, Is Composite: {english.is_composite}")
        components = english.get_components()
        if components:
            print(f"  Components: {[comp.name for comp in components]}")
        else:
            print("  No components")
        
        print("\n=== KISWAHILI (ID 7) ===")
        print(f"Subject: {kiswahili.name}, ID: {kiswahili.id}, Is Composite: {kiswahili.is_composite}")
        components = kiswahili.get_components()
        if components:
            print(f"  Components: {[comp.name for comp in components]}")
        else:
            print("  No components")
        
        # Check if components exist in the database
        print("\n=== COMPONENTS IN DATABASE ===")
        components = SubjectComponent.query.all()
        for component in components:
            print(f"Component: {component.name}, ID: {component.id}, Subject ID: {component.subject_id}")

if __name__ == "__main__":
    test_components()
