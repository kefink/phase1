"""
New authentication views for testing.
"""
from flask import Blueprint

# Create a blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/test')
def test():
    return "New auth blueprint test route"
