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

# List of all blueprints to register with the app
blueprints = [
    auth_bp, teacher_bp, classteacher_bp, admin_bp,
    bulk_assignments_bp, setup_bp, staff_bp,
    permission_bp, universal_bp, analytics_api_bp,
    school_setup_bp, subject_config_api
]