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
from .missing_routes import missing_routes_bp

# Import parent portal blueprints with error handling - TEMPORARILY DISABLED
# try:
#     from .parent_simple import parent_simple_bp
#     parent_bp_available = True
# except ImportError:
#     parent_simple_bp = None
#     parent_bp_available = False
parent_simple_bp = None
parent_bp_available = False

# Import parent management blueprint with error handling - TEMPORARILY DISABLED
# try:
#     from .parent_management import parent_management_bp
#     parent_mgmt_bp_available = True
# except ImportError:
#     parent_management_bp = None
#     parent_mgmt_bp_available = False
parent_management_bp = None
parent_mgmt_bp_available = False

# Import email configuration blueprint with error handling - TEMPORARILY DISABLED
# try:
#     from .email_config import email_config_bp
#     email_config_bp_available = True
# except ImportError:
email_config_bp = None
email_config_bp_available = False

# List of all blueprints to register with the app
blueprints = [
    auth_bp, teacher_bp, classteacher_bp, admin_bp,
    bulk_assignments_bp, setup_bp, staff_bp,
    permission_bp, universal_bp, analytics_api_bp,
    school_setup_bp, subject_config_api, missing_routes_bp
]

# Add parent blueprint if available
if parent_bp_available and parent_simple_bp:
    blueprints.append(parent_simple_bp)

# Add parent management blueprint if available
if parent_mgmt_bp_available and parent_management_bp:
    blueprints.append(parent_management_bp)

# Add email configuration blueprint if available
if email_config_bp_available and email_config_bp:
    blueprints.append(email_config_bp)