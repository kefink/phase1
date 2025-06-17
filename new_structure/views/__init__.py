"""
Views package for the Hillview School Management System.
This file imports and exposes view blueprints for registration with the Flask app.
"""
from .auth import auth_bp
from .teacher import teacher_bp
from .classteacher import classteacher_bp
from .admin import admin_bp
from .bulk_assignments import bulk_assignments_bp
from .setup import setup_bp
from .staff_management import staff_bp
from .permission_management import permission_bp
from .headteacher_universal import universal_bp
from .analytics_api import analytics_api_bp
from .school_setup import school_setup_bp
from .subject_config_api import subject_config_api

# Import parent portal blueprints with error handling
try:
    from .parent_simple import parent_simple_bp
    parent_bp_available = True
    print("✅ Parent portal blueprint imported successfully")
except ImportError as e:
    parent_simple_bp = None
    parent_bp_available = False
    print(f"❌ Warning: Could not import parent portal blueprint: {e}")

# Import parent management blueprint with error handling
try:
    from .parent_management import parent_management_bp
    parent_mgmt_bp_available = True
    print("✅ Parent management blueprint imported successfully")
except ImportError as e:
    parent_management_bp = None
    parent_mgmt_bp_available = False
    print(f"❌ Warning: Could not import parent management blueprint: {e}")

# List of all blueprints to register with the app
blueprints = [
    auth_bp, teacher_bp, classteacher_bp, admin_bp,
    bulk_assignments_bp, setup_bp, staff_bp,
    permission_bp, universal_bp, analytics_api_bp,
    school_setup_bp, subject_config_api
]

# Add parent blueprint if available
if parent_bp_available and parent_simple_bp:
    blueprints.append(parent_simple_bp)
    print("✅ Parent portal blueprint added to registration list")

# Add parent management blueprint if available
if parent_mgmt_bp_available and parent_management_bp:
    blueprints.append(parent_management_bp)
    print("✅ Parent management blueprint added to registration list")

print(f"📋 Total blueprints to register: {len(blueprints)}")