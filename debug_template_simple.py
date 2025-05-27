"""
Script to debug the template rendering.
"""
from new_structure import create_app
from new_structure.models.academic import Subject, SubjectComponent
from new_structure.extensions import db

def debug_template_simple():
    """Debug the template rendering."""
    app = create_app()
    with app.app_context():
        print("Debugging template rendering...")
        
        # Get English and Kiswahili subjects
        english = Subject.query.filter_by(id=2).first()
        kiswahili = Subject.query.filter_by(id=7).first()
        
        if not (english and kiswahili):
            print("Could not find English or Kiswahili subjects.")
            return
        
        print(f"English: {english.name}, ID: {english.id}, Is Composite: {english.is_composite}")
        print(f"Kiswahili: {kiswahili.name}, ID: {kiswahili.id}, Is Composite: {kiswahili.is_composite}")
        
        # Get components
        english_components = english.get_components()
        kiswahili_components = kiswahili.get_components()
        
        print(f"English Components: {[comp.name for comp in english_components]}")
        print(f"Kiswahili Components: {[comp.name for comp in kiswahili_components]}")
        
        # Test the if condition
        print(f"english.is_composite == True: {english.is_composite == True}")
        print(f"kiswahili.is_composite == True: {kiswahili.is_composite == True}")
        print(f"english.is_composite is True: {english.is_composite is True}")
        print(f"kiswahili.is_composite is True: {kiswahili.is_composite is True}")
        
        # Test the type of is_composite
        print(f"Type of english.is_composite: {type(english.is_composite)}")
        print(f"Type of kiswahili.is_composite: {type(kiswahili.is_composite)}")
        
        print("\nDebug completed.")

if __name__ == "__main__":
    debug_template_simple()
