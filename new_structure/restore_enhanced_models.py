#!/usr/bin/env python3
"""
Script to restore the enhanced model definitions after migration.
This will uncomment the new fields in the Teacher and SchoolConfiguration models.
"""

import os
import re

def restore_teacher_model():
    """Restore the enhanced Teacher model."""
    
    model_file = 'models/user.py'
    
    if not os.path.exists(model_file):
        print(f"❌ Model file not found: {model_file}")
        return False
    
    try:
        # Read the current file
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the commented fields with active fields
        enhanced_teacher_fields = '''    # Enhanced teacher information
    full_name = db.Column(db.String(200), nullable=True)  # Full display name
    employee_id = db.Column(db.String(50), nullable=True, unique=True)  # Staff ID
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    qualification = db.Column(db.String(200), nullable=True)  # e.g., "B.Ed Mathematics"
    specialization = db.Column(db.String(200), nullable=True)  # e.g., "Primary Education"
    is_active = db.Column(db.Boolean, default=True)  # Whether teacher is currently active
    date_joined = db.Column(db.Date, nullable=True)'''
        
        # Find and replace the commented section
        pattern = r'    # Enhanced teacher information \(will be added after migration\).*?    # date_joined = db\.Column\(db\.Date, nullable=True\)'
        
        content = re.sub(pattern, enhanced_teacher_fields, content, flags=re.DOTALL)
        
        # Write the updated content
        with open(model_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Enhanced Teacher model restored in {model_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error restoring Teacher model: {e}")
        return False

def restore_school_config_model():
    """Restore the enhanced SchoolConfiguration model."""
    
    model_file = 'models/academic.py'
    
    if not os.path.exists(model_file):
        print(f"❌ Model file not found: {model_file}")
        return False
    
    try:
        # Read the current file
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the commented fields with active fields
        enhanced_config_fields = '''    # Dynamic Staff Assignment IDs (references to Teacher table)
    headteacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    deputy_headteacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    
    # Relationships for dynamic staff assignment
    headteacher = db.relationship('Teacher', foreign_keys=[headteacher_id], 
                                 backref='headteacher_schools')
    deputy_headteacher = db.relationship('Teacher', foreign_keys=[deputy_headteacher_id], 
                                        backref='deputy_headteacher_schools')'''
        
        # Find and replace the commented section
        pattern = r'    # Dynamic Staff Assignment IDs \(will be added after migration\).*?    # deputy_headteacher = db\.relationship.*?backref=\'deputy_headteacher_schools\'\)'
        
        content = re.sub(pattern, enhanced_config_fields, content, flags=re.DOTALL)
        
        # Write the updated content
        with open(model_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Enhanced SchoolConfiguration model restored in {model_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error restoring SchoolConfiguration model: {e}")
        return False

def main():
    print("🔄 Restoring Enhanced Models")
    print("=" * 50)
    print("This will restore the enhanced model definitions after migration.")
    print("=" * 50)
    
    success = True
    
    # Restore Teacher model
    print("🔧 Restoring Teacher model...")
    if not restore_teacher_model():
        success = False
    
    # Restore SchoolConfiguration model
    print("🔧 Restoring SchoolConfiguration model...")
    if not restore_school_config_model():
        success = False
    
    if success:
        print("\n🎉 Enhanced models restored successfully!")
        print("\n📋 What's been restored:")
        print("• Teacher model with all enhanced fields")
        print("• SchoolConfiguration model with dynamic staff assignments")
        print("• Relationships for headteacher and deputy headteacher")
        
        print("\n🚀 Next steps:")
        print("1. Restart your Flask application")
        print("2. Test the enhanced staff management features")
        print("3. Generate reports with dynamic staff information")
        
    else:
        print("\n❌ Some models could not be restored!")
        print("You may need to manually uncomment the enhanced fields.")

if __name__ == "__main__":
    main()
