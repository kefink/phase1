#!/usr/bin/env python3
"""
Comprehensive Template Validation Script
Checks all HTML templates in the project for Jinja2 syntax errors
"""
import os
import re
import sys
from pathlib import Path

def validate_jinja_template(file_path):
    """Validate Jinja2 template for proper nesting"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [f"Error reading file: {e}"]
    
    lines = content.split('\n')
    stack = []
    errors = []
    
    # Pattern to match Jinja2 control structures
    pattern = r'{%\s*(if|for|elif|else|endif|endfor|set|with|endwith|block|endblock|macro|endmacro)\s*.*?%}'
    
    for line_num, line in enumerate(lines, 1):
        matches = re.findall(pattern, line)
        
        for match in matches:
            tag = match.strip()
            
            if tag in ['if', 'for', 'with', 'block', 'macro']:
                # Opening tags
                stack.append((tag, line_num, line.strip()))
            elif tag == 'set':
                # Set tags don't need closing
                continue
            elif tag in ['elif', 'else']:
                # Middle tags - should have matching if/for
                if not stack or stack[-1][0] not in ['if', 'for']:
                    errors.append(f"Line {line_num}: '{tag}' without matching 'if' - {line.strip()}")
            elif tag in ['endif', 'endfor', 'endwith', 'endblock', 'endmacro']:
                # Closing tags
                expected_map = {
                    'endif': 'if',
                    'endfor': 'for', 
                    'endwith': 'with',
                    'endblock': 'block',
                    'endmacro': 'macro'
                }
                expected = expected_map[tag]
                
                if not stack:
                    errors.append(f"Line {line_num}: '{tag}' without matching '{expected}' - {line.strip()}")
                elif stack[-1][0] != expected:
                    last_tag, last_line, last_content = stack[-1]
                    errors.append(f"Line {line_num}: '{tag}' doesn't match '{last_tag}' from line {last_line}")
                    errors.append(f"  Opening: {last_content}")
                    errors.append(f"  Closing: {line.strip()}")
                else:
                    stack.pop()
    
    # Check for unclosed tags
    for tag, line_num, line_content in stack:
        errors.append(f"Line {line_num}: Unclosed '{tag}' tag - {line_content}")
    
    return errors

def find_template_files(root_dir):
    """Find all HTML template files"""
    template_files = []
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.html'):
                template_files.append(os.path.join(root, file))
    
    return template_files

def main():
    project_root = r'C:\Users\MKT\desktop\phase1\2ndrev\new_structure'
    
    print("🔍 Comprehensive Template Validation")
    print("=" * 50)
    
    # Find all template files
    template_files = find_template_files(project_root)
    
    if not template_files:
        print("❌ No template files found!")
        return 1
    
    print(f"Found {len(template_files)} template file(s):")
    for file in template_files:
        relative_path = os.path.relpath(file, project_root)
        print(f"  📄 {relative_path}")
    
    print("\n" + "=" * 50)
    
    total_errors = 0
    
    for template_file in template_files:
        relative_path = os.path.relpath(template_file, project_root)
        print(f"\n🔍 Validating: {relative_path}")
        print("-" * 40)
        
        errors = validate_jinja_template(template_file)
        
        if errors:
            print("❌ ERRORS FOUND:")
            for error in errors:
                print(f"  {error}")
            print(f"  → {len(errors)} error(s) in this file")
            total_errors += len(errors)
        else:
            print("✅ Template structure is valid!")
    
    print("\n" + "=" * 50)
    
    if total_errors > 0:
        print(f"❌ VALIDATION FAILED: {total_errors} total error(s) found across all templates")
        return 1
    else:
        print("🎉 ALL TEMPLATES VALIDATED SUCCESSFULLY!")
        print("✅ No Jinja2 syntax errors found in any template file")
        return 0

if __name__ == "__main__":
    sys.exit(main())
