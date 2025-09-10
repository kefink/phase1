"""Shared view decorators (environment & permission helpers)."""
import os
from functools import wraps
from flask import current_app, abort


def dev_only(f):
    """Block route in non-development environments.

    Returns 404 instead of 403 to avoid leaking route existence.
    Enabled when FLASK_ENV/APP_ENV indicates production or TESTING True.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        env = (current_app.config.get('ENV') or '').lower()
        app_env = (current_app.config.get('APP_ENV') or os.getenv('APP_ENV','')).lower()
        if current_app.config.get('TESTING') or env == 'production' or app_env in {'prod','production'}:
            abort(404)
        return f(*args, **kwargs)
    return wrapper
