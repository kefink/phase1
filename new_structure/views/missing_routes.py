"""
Missing Routes Handler
Provides simple routes for features that were missing 404 errors.
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from .admin import admin_required

# Create blueprint for missing routes
missing_routes_bp = Blueprint('missing_routes', __name__)

@missing_routes_bp.route('/subject_config')
@admin_required
def subject_config():
    """Subject configuration page."""
    return redirect(url_for('subject_config_api.subject_configuration_page'))

# TEMPORARILY DISABLED - Parent portal under development
# @missing_routes_bp.route('/parent_management')
# @admin_required
# def parent_management():
#     """Parent management page."""
#     return redirect(url_for('parent_management.dashboard'))

@missing_routes_bp.route('/parent_management')
@admin_required
def parent_management():
    """Parent management page - temporarily disabled."""
    flash('Parent management is temporarily disabled while under development.', 'info')
    return redirect(url_for('admin.dashboard'))

@missing_routes_bp.route('/permission')
@admin_required
def permission_management():
    """Permission management page."""
    return redirect(url_for('permission.manage'))

@missing_routes_bp.route('/headteacher/universal_access')
@admin_required
def universal_access():
    """Universal access page - redirect to correct route."""
    return redirect(url_for('universal.dashboard'))
