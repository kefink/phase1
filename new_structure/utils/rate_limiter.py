"""
Simple Rate Limiting for Hillview School Management System
Basic rate limiting implementation to prevent abuse.
"""

import time
import logging
from functools import wraps
from flask import request, abort, session
from collections import defaultdict

logger = logging.getLogger(__name__)
try:
    from .audit import audit_event
except Exception:  # pragma: no cover
    def audit_event(*a, **k):  # type: ignore
        logging.getLogger(__name__).debug('audit_event fallback', extra={'args': a, 'kwargs': k})

# Simple in-memory rate limiting storage
_rate_limit_storage = defaultdict(list)

def _get_client_id():
    """Get client identifier for rate limiting."""
    return request.remote_addr or 'unknown'

def _is_rate_limited(client_id, limit=5, window=60):
    """Check if client is rate limited."""
    now = time.time()
    
    # Clean old entries
    _rate_limit_storage[client_id] = [
        timestamp for timestamp in _rate_limit_storage[client_id]
        if now - timestamp < window
    ]
    
    # Check if limit exceeded
    if len(_rate_limit_storage[client_id]) >= limit:
        return True
    
    # Add current request
    _rate_limit_storage[client_id].append(now)
    return False

def auth_rate_limit(f):
    """Rate limit decorator for authentication routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_id = _get_client_id()
        
        # Check rate limit (5 requests per minute for auth)
        if _is_rate_limited(client_id, limit=5, window=60):
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            audit_event('rate_limit_exceeded', actor=session.get('teacher_id'), target='auth', outcome='denied', category='rate_limit', details={'client_id': client_id, 'limit': 5, 'window': 60})
            abort(429, "Too many requests. Please try again later.")
        
        return f(*args, **kwargs)
    return decorated_function

def api_rate_limit(f):
    """Rate limit decorator for API routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_id = _get_client_id()
        
        # Check rate limit (30 requests per minute for API)
        if _is_rate_limited(client_id, limit=30, window=60):
            logger.warning(f"API rate limit exceeded for client: {client_id}")
            audit_event('rate_limit_exceeded', actor=session.get('teacher_id'), target='api', outcome='denied', category='rate_limit', details={'client_id': client_id, 'limit': 30, 'window': 60})
            abort(429, "Too many requests. Please try again later.")
        
        return f(*args, **kwargs)
    return decorated_function
