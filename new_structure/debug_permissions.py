#!/usr/bin/env python3
"""Debug script to test the permission system."""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from extensions import db
from models.function_permission import DefaultFunctionPermissions
from services.enhanced_permission_service import EnhancedPermissionService

def test_permissions():
    """Test the permission checking logic."""
    function_name = 'class_marks_status'
    teacher_id = 4  # Kevin's teacher ID
    
    print(f"=== PERMISSION DEBUG TEST ===")
    print(f"Function: {function_name}")
    print(f"Teacher ID: {teacher_id}")
    
    # Test 1: Check if function is in default allowed list
    is_default = DefaultFunctionPermissions.is_default_allowed(function_name)
    print(f"Is default allowed: {is_default}")
    
    # Test 2: Check if function is restricted
    is_restricted = DefaultFunctionPermissions.is_restricted(function_name)
    print(f"Is restricted: {is_restricted}")
    
    # Test 3: Get function category
    category = DefaultFunctionPermissions.get_function_category(function_name)
    print(f"Function category: {category}")
    
    # Test 4: Test enhanced permission service
    try:
        has_permission = EnhancedPermissionService.check_function_permission(
            teacher_id, function_name
        )
        print(f"Enhanced service result: {has_permission}")
    except Exception as e:
        print(f"Enhanced service error: {e}")
    
    # Test 5: Show default allowed functions for marks_management
    print(f"\nDefault allowed functions in marks_management:")
    for func in DefaultFunctionPermissions.DEFAULT_ALLOWED_FUNCTIONS.get('marks_management', []):
        print(f"  - {func}")
    
    print(f"\n=== END DEBUG TEST ===")

if __name__ == '__main__':
    # Create a minimal Flask app for testing
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        test_permissions()
