"""
Script to copy the Kirima Primary School logo to the static/images directory.
"""
import os
import shutil
import sys
from pathlib import Path

def copy_logo():
    """Copy the logo image to the static/images directory."""
    # Get the current directory
    current_dir = Path.cwd()
    
    # Source file (the logo image provided by the user)
    source_file = current_dir / "kirima_logo.png"
    
    # Destination directory and file
    dest_dir = current_dir / "new_structure" / "static" / "images"
    dest_file = dest_dir / "kirima_logo.png"
    
    # Create the destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    
    # Check if the source file exists
    if not source_file.exists():
        print(f"Error: Source file '{source_file}' not found.")
        print("Please make sure the logo image is named 'kirima_logo.png' and is in the current directory.")
        return False
    
    try:
        # Copy the file
        shutil.copy2(source_file, dest_file)
        print(f"Successfully copied logo to {dest_file}")
        return True
    except Exception as e:
        print(f"Error copying file: {e}")
        return False

if __name__ == "__main__":
    success = copy_logo()
    sys.exit(0 if success else 1)
