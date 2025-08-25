#!/usr/bin/env python3
"""
Fix English Grammar subject configuration to work with class reports.

The issue is that English Grammar is marked as:
- education_level: 'primary' (should be 'junior_secondary' for Grade 9)
- is_component: True (should be False since it's used as standalone subject)

This script fixes these issues so the class report can find the marks.
"""

import sys
import os
sys.path.append('2ndrev')

from new_structure import create_app
from new_structure.models.academic import Subject
from new_structure.extensions import db

def fix_english_grammar_subject():
    """Fix the English Grammar subject configuration."""
    app = create_app()
    
    with app.app_context():
        # Find the English Grammar subject
        english_grammar = Subject.query.filter_by(name='English Grammar').first()
        
        if not english_grammar:
            print("❌ English Grammar subject not found")
            return False
        
        print(f"📋 Found English Grammar subject:")
        print(f"   ID: {english_grammar.id}")
        print(f"   Current education_level: {english_grammar.education_level}")
        print(f"   Current is_component: {getattr(english_grammar, 'is_component', 'Not set')}")
        
        # Update the subject
        print(f"\n🔧 Updating English Grammar subject...")
        english_grammar.education_level = 'junior_secondary'
        english_grammar.is_component = False
        
        try:
            db.session.commit()
            print(f"✅ Successfully updated English Grammar subject:")
            print(f"   New education_level: {english_grammar.education_level}")
            print(f"   New is_component: {english_grammar.is_component}")
            return True
        except Exception as e:
            print(f"❌ Error updating subject: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("🚀 Fixing English Grammar subject configuration...")
    success = fix_english_grammar_subject()
    
    if success:
        print("\n✅ Fix completed successfully!")
        print("📋 The class report should now show the English Grammar marks.")
    else:
        print("\n❌ Fix failed!")
