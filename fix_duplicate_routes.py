#!/usr/bin/env python
"""
Script to check for and fix duplicate route functions in classteacher.py.
"""
import re

def fix_duplicate_routes():
    """Fix duplicate route functions in classteacher.py."""
    file_path = "new_structure/views/classteacher.py"
    
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Check for duplicate manage_students route
    manage_students_pattern = r"@classteacher_bp\.route\(\'/manage_students\'"
    matches = re.findall(manage_students_pattern, content)
    
    if len(matches) > 1:
        print(f"Found {len(matches)} instances of manage_students route. Fixing...")
        
        # Find the first occurrence
        first_match_pos = content.find("@classteacher_bp.route('/manage_students'")
        
        # Find the second occurrence
        second_match_pos = content.find("@classteacher_bp.route('/manage_students'", first_match_pos + 1)
        
        # Find the end of the second function
        function_pattern = r"@classteacher_bp\.route\('/manage_students'.*?def manage_students\(\).*?return render_template\(.*?\)"
        match = re.search(function_pattern, content[second_match_pos:], re.DOTALL)
        
        if match:
            # Remove the second function
            end_pos = second_match_pos + match.end()
            new_content = content[:second_match_pos] + content[end_pos:]
            
            # Write the updated content back to the file
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(new_content)
            
            print("Fixed duplicate manage_students route.")
        else:
            print("Could not find the end of the duplicate function.")
    else:
        print("No duplicate manage_students route found.")

if __name__ == "__main__":
    fix_duplicate_routes()