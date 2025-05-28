"""
Views package for the Hillview School Management System.
This file imports and exposes view blueprints for registration with the Flask app.
"""
from .auth import auth_bp
from .teacher import teacher_bp
from .classteacher import classteacher_bp
from .admin import admin_bp
from .structured_assignments import structured_assignments_bp
from .bulk_assignments import bulk_assignments_bp
from .setup import setup_bp

# List of all blueprints to register with the app
blueprints = [auth_bp, teacher_bp, classteacher_bp, admin_bp, structured_assignments_bp, bulk_assignments_bp, setup_bp]