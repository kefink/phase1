#!/usr/bin/env python3
"""
Simple script to run the composite subject architecture fix.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run the composite architecture fix."""
    print("🎯 Running Composite Subject Architecture Fix")
    print("=" * 50)
    
    try:
        # Change to the migrations directory and run the script directly
        migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')
        migration_script = os.path.join(migrations_dir, 'fix_composite_architecture.py')

        # Run the migration script
        import subprocess
        result = subprocess.run([sys.executable, migration_script],
                              capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        result = result.returncode
        
        if result == 0:
            print("\n🎉 SUCCESS! Composite subject architecture has been fixed.")
            print("\n📋 What changed:")
            print("✅ English Grammar and English Composition are now separate uploadable subjects")
            print("✅ Kiswahili Lugha and Kiswahili Insha are now separate uploadable subjects")
            print("✅ Reports will show combined English and Kiswahili columns with component breakdowns")
            print("✅ Teachers can upload marks for Grammar and Composition separately")
            print("✅ Better user experience - no need to upload both components simultaneously")
            
            print("\n📝 Next steps:")
            print("1. Test uploading marks for English Grammar separately")
            print("2. Test uploading marks for English Composition separately")
            print("3. Generate a class report to see the new column structure")
            print("4. Verify that marks appear in the correct composite columns")
            
        else:
            print("\n❌ Migration failed. Please check the error messages above.")
            
    except Exception as e:
        print(f"\n❌ Error running migration: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return result

if __name__ == "__main__":
    sys.exit(main())
