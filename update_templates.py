#!/usr/bin/env python
"""
Script to update URL endpoints in templates to use blueprint prefixes.
"""
import os
import re

def update_template(file_path):
    """Update URL endpoints in a template file."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Define the endpoint mappings (old_endpoint -> new_endpoint)
    endpoint_mappings = {
        "admin_login": "auth.admin_login",
        "teacher_login": "auth.teacher_login",
        "classteacher_login": "auth.classteacher_login",
        "index": "auth.index",
        "logout": "auth.logout_route",
        "teacher": "teacher.dashboard",
        "classteacher": "classteacher.dashboard",
        "headteacher": "admin.dashboard",
        "manage_teachers": "admin.manage_teachers",
        "manage_subjects": "admin.manage_subjects",
        "manage_grades_streams": "admin.manage_grades_streams",
        "manage_terms_assessments": "admin.manage_terms_assessments",
        "manage_students": "classteacher.manage_students",
        "preview_class_report": "classteacher.preview_class_report",
        "preview_individual_report": "classteacher.preview_individual_report",
        "generate_class_pdf": "classteacher.generate_class_pdf",
        "generate_individual_report": "classteacher.generate_individual_report",
    }
    
    # Update all url_for calls
    for old_endpoint, new_endpoint in endpoint_mappings.items():
        pattern = r"url_for\([\"]" + old_endpoint + r"[\"]"
        replacement = r"url_for(\"" + new_endpoint + r"\""
        content = re.sub(pattern, replacement, content)
    
    # Write the updated content back to the file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    
    return True

def process_directory(directory):
    """Process all HTML files in a directory."""
    modified_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                if update_template(file_path):
                    modified_files.append(file_path)
    
    return modified_files

if __name__ == "__main__":
    templates_dir = "new_structure/templates"
    modified_files = process_directory(templates_dir)
    
    print(f"Updated {len(modified_files)} template files:")
    for file in modified_files:
        print(f"  - {file}")
