#!/usr/bin/env python
"""
Script to update URL endpoints in templates to use blueprint prefixes.
This version directly edits specific files and patterns.
"""
import os
import re

def fix_login_html():
    """Fix URL endpoints in login.html."""
    file_path = "new_structure/templates/login.html"
    
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Fix specific patterns
    content = content.replace("url_for('admin_login')", "url_for('auth.admin_login')")
    content = content.replace("url_for(\"admin_login\")", "url_for(\"auth.admin_login\")")
    content = content.replace("url_for('teacher_login')", "url_for('auth.teacher_login')")
    content = content.replace("url_for(\"teacher_login\")", "url_for(\"auth.teacher_login\")")
    content = content.replace("url_for('classteacher_login')", "url_for('auth.classteacher_login')")
    content = content.replace("url_for(\"classteacher_login\")", "url_for(\"auth.classteacher_login\")")
    
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    
    print(f"Fixed URL endpoints in {file_path}")

def fix_all_templates():
    """Fix URL endpoints in all template files."""
    templates_dir = "new_structure/templates"
    
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
    
    modified_files = []
    
    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                original_content = content
                
                # Update all url_for calls with different quote styles
                for old_endpoint, new_endpoint in endpoint_mappings.items():
                    # Handle single quotes
                    content = content.replace(f"url_for('{old_endpoint}')", f"url_for('{new_endpoint}')")
                    # Handle double quotes
                    content = content.replace(f"url_for(\"{old_endpoint}\")", f"url_for(\"{new_endpoint}\")")
                
                if content != original_content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    modified_files.append(file_path)
    
    print(f"Updated {len(modified_files)} template files:")
    for file in modified_files:
        print(f"  - {file}")

if __name__ == "__main__":
    # Fix login.html specifically
    fix_login_html()
    
    # Fix all templates
    fix_all_templates()