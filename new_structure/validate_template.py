#!/usr/bin/env python3
"""
Template Validation Script
Checks for proper nesting of Jinja2 control structures
"""
import re
import sys

def validate_jinja_template(file_path):
    """Validate Jinja2 template for proper nesting"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    stack = []
    errors = []
    
    # Pattern to match Jinja2 control structures
    pattern = r'{%\s*(if|for|elif|else|endif|endfor|set)\s*.*?%}'
    
    for line_num, line in enumerate(lines, 1):
        matches = re.findall(pattern, line)
        
        for match in matches:
            tag = match.strip()
            
            if tag in ['if', 'for']:
                # Opening tags
                stack.append((tag, line_num, line.strip()))
            elif tag == 'set':
                # Set tags don't need closing
                continue
            elif tag in ['elif', 'else']:
                # Middle tags - should have matching if
                if not stack or stack[-1][0] != 'if':
                    errors.append(f"Line {line_num}: '{tag}' without matching 'if' - {line.strip()}")
            elif tag in ['endif', 'endfor']:
                # Closing tags
                expected = 'if' if tag == 'endif' else 'for'
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

def main():
    template_file = r'C:\Users\MKT\desktop\phase1\2ndrev\new_structure\templates\classteacher.html'
    
    print("Validating Jinja2 template structure...")
    print(f"File: {template_file}")
    print("-" * 50)
    
    errors = validate_jinja_template(template_file)
    
    if errors:
        print("❌ ERRORS FOUND:")
        for error in errors:
            print(f"  {error}")
        print(f"\nTotal errors: {len(errors)}")
        return 1
    else:
        print("✅ Template structure is valid!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
