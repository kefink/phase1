#!/usr/bin/env python3
"""
Script to clear analytics cache after fixing the total marks calculation issue.
This ensures users see the corrected total marks immediately.
"""

import os
import sys
import shutil

def clear_analytics_cache():
    """Clear all analytics cache files and directories."""
    try:
        # Define cache directories
        cache_dirs = [
            'cache/analytics',
            'cache/reports', 
            'cache/marksheets',
            'cache/admin'
        ]
        
        cleared_count = 0
        
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                print(f"🧹 Clearing cache directory: {cache_dir}")
                
                # Remove all files in the directory
                for filename in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            cleared_count += 1
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            cleared_count += 1
                    except Exception as e:
                        print(f"⚠️  Warning: Could not remove {file_path}: {e}")
                
                print(f"✅ Cleared {cache_dir}")
            else:
                print(f"ℹ️  Cache directory {cache_dir} does not exist")
        
        print(f"\n🎉 Successfully cleared {cleared_count} cache files/directories")
        print("📊 Analytics cache has been cleared - users will now see corrected total marks")
        
        return True
        
    except Exception as e:
        print(f"❌ Error clearing analytics cache: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Clearing Analytics Cache - Total Marks Fix")
    print("=" * 50)
    
    # Change to the new_structure directory if we're not already there
    if os.path.exists('new_structure'):
        os.chdir('new_structure')
        print("📁 Changed to new_structure directory")
    
    success = clear_analytics_cache()
    
    if success:
        print("\n✅ Cache clearing completed successfully!")
        print("🚀 The School Top Performers will now show correct total marks")
        print("   that match the generated stream reports.")
    else:
        print("\n❌ Cache clearing failed!")
        sys.exit(1)
