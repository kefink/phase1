#!/usr/bin/env python
"""
Script to add CSRF tokens to all forms in HTML templates
"""
import os
import re

def add_csrf_token_to_file(file_path):
    """Add CSRF token to all forms in a file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Pattern to match form tags that don't already have a CSRF token
    form_pattern = r'<form[^>]*method=["\']POST["\'][^>]*>'
    
    # Check if the file already has CSRF tokens
    csrf_pattern = r'<input[^>]*name=["\']csrf_token["\'][^>]*>'
    has_csrf = bool(re.search(csrf_pattern, content))
    
    if not has_csrf:
        # Add CSRF token after each form tag
        modified_content = re.sub(
            form_pattern,
            lambda match: match.group(0) + '\n          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>',
            content
        )
        
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(modified_content)
        
        return True
    
    return False

def process_directory(directory):
    """Process all HTML files in a directory"""
    modified_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                if add_csrf_token_to_file(file_path):
                    modified_files.append(file_path)
    
    return modified_files

if __name__ == "__main__":
    templates_dir = "templates"
    modified_files = process_directory(templates_dir)
    
    print(f"Added CSRF tokens to {len(modified_files)} files:")
    for file in modified_files:
        print(f"  - {file}")
