
from flask import request, redirect, url_for

@app.before_request
def force_https():
    """Force HTTPS in production."""
    if not request.is_secure and app.config.get('FORCE_HTTPS', False):
        return redirect(request.url.replace('http://', 'https://'))
