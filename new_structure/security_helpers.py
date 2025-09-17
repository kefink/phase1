"""Unified security helper utilities.

Provides:
- wants_json(request)
- audit_log(event, **fields)
- secure_endpoint decorator for consistent RBAC, rate limiting hook, validation, error envelope, and debug gating.

Assumptions:
- Session keys: 'teacher_id', 'role'
- error_response function available (imported from utils.error_responses)
- Optional global `limiter` (from extensions) may be used externally; we allow internal simple IP rate tracking fallback for endpoints specifying rate without external limiter binding.
"""
from __future__ import annotations
from functools import wraps
from typing import Callable, Iterable, Optional, Any, Type
import time
import uuid
from flask import request, session, current_app, make_response
from utils.error_responses import error_response

# Simple in-process fallback rate counter (per IP per key) for endpoints that specify a rate but no external limiter binding
_rate_counters: dict[str, list[float]] = {}

def wants_json(req) -> bool:
    """Determine if client expects JSON."""
    if req.args.get('format') == 'json':
        return True
    accept = (req.headers.get('Accept') or '').lower()
    if 'application/json' in accept and 'text/html' not in accept:
        return True
    if req.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True
    return False

def audit_log(event: str, **fields):
    """Emit a structured audit style log entry."""
    payload = {
        'event': event,
        'correlation_id': request.headers.get('X-Correlation-ID') or str(uuid.uuid4()),
        'ip': request.remote_addr,
        'method': request.method,
        'path': request.path,
        'role': session.get('role'),
        'teacher_id': session.get('teacher_id')
    }
    payload.update(fields)
    current_app.logger.info(payload)

class ValidationError(Exception):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.details = details or {}

def validate_uploaded_file(field_name: str,
                           allowed_exts: set,
                           max_bytes: int,
                           required: bool = True,
                           strict_mime: bool = True):
    """Generic file validation helper (Phase C) enforcing presence, extension & size.

    Returns dict with file metadata or None if optional & absent.
    Raises ValidationError on violation.
    """
    from flask import request
    import os
    if field_name not in request.files:
        if required:
            raise ValidationError('No file uploaded', {'field': field_name})
        return None
    file = request.files[field_name]
    if not file.filename:
        raise ValidationError('Filename missing', {'field': field_name})
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise ValidationError('Unsupported file extension', {'allowed': sorted(list(allowed_exts)), 'received': ext})
    # Determine size by seeking stream (safe for modest academic uploads)
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > max_bytes:
        raise ValidationError('File too large', {'max_bytes': max_bytes, 'received_bytes': size})
    if strict_mime and not (file.mimetype and '/' in file.mimetype):
        raise ValidationError('Unrecognized MIME type', {'mimetype': file.mimetype})
    return {'file': file, 'filename': file.filename, 'ext': ext, 'size': size}

Validator = Callable[[], Any]

# Rate tuple type: (max_requests, window_seconds)
RateTuple = tuple[int, int]

def _check_rate(rate: RateTuple, key: str) -> bool:
    max_req, window = rate
    now = time.time()
    entries = _rate_counters.get(key, [])
    # prune
    entries = [t for t in entries if now - t < window]
    if len(entries) >= max_req:
        _rate_counters[key] = entries
        return False
    entries.append(now)
    _rate_counters[key] = entries
    return True

def secure_endpoint(
    *,
    roles: Optional[Iterable[str]] = None,
    rate: Optional[RateTuple] = None,
    validator: Optional[Validator] = None,
    audit_event: Optional[str] = None,
    json_errors: bool = True,
    debug_only: bool = False,
    forbid_if: Optional[Callable[[], bool]] = None,
    extra_check: Optional[Callable[[], Optional[tuple[bool, str]]]] = None,
):
    """Comprehensive endpoint guard.

    Parameters:
      roles: iterable of allowed roles (case-insensitive); if None -> any authenticated user.
      rate: (max_requests, window_seconds) simple in-memory throttle (test/dev friendly).
      validator: callable performing input validation; may raise ValidationError.
      audit_event: base string used for success/failure log events.
      json_errors: if True, uses unified error_response else raises default abort style exceptions.
      debug_only: restrict endpoint to DEBUG or TEST config.
      forbid_if: callable returning True if endpoint should return 403.
      extra_check: callable returning (ok, message) or None; if not ok -> 403.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            cid = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
            base_event = audit_event or fn.__name__
            # Debug gating
            if debug_only and not (current_app.debug or current_app.config.get('TESTING')):
                if json_errors:
                    audit_log(base_event+':denied_debug_only', correlation_id=cid)
                    return error_response('FORBIDDEN', 'Endpoint disabled in this environment', 403)
                from flask import abort
                abort(403)
            # Auth check
            teacher_id = session.get('teacher_id')
            if not teacher_id:
                if json_errors and wants_json(request):
                    audit_log(base_event+':unauthenticated', correlation_id=cid)
                    return error_response('UNAUTHENTICATED', 'Login required', 401)
                from flask import abort
                abort(401)
            role = (session.get('role') or '').lower()
            if roles is not None:
                allowed = [r.lower() for r in roles]
                if role not in allowed:
                    if json_errors and wants_json(request):
                        audit_log(base_event+':forbidden_role', correlation_id=cid, role=role)
                        return error_response('FORBIDDEN', 'Access denied', 403)
                    from flask import abort
                    abort(403)
            if forbid_if and forbid_if():
                if json_errors and wants_json(request):
                    audit_log(base_event+':forbidden_condition', correlation_id=cid)
                    return error_response('FORBIDDEN', 'Not permitted', 403)
                from flask import abort
                abort(403)
            if extra_check:
                res = extra_check()
                if res is not None:
                    ok, msg = res
                    if not ok:
                        if json_errors and wants_json(request):
                            audit_log(base_event+':forbidden_extra', correlation_id=cid, reason=msg)
                            return error_response('FORBIDDEN', msg or 'Access denied', 403)
                        from flask import abort
                        abort(403)
            # Rate limiting
            if rate:
                key = f"{request.remote_addr}:{fn.__name__}:{rate[0]}:{rate[1]}"
                if not _check_rate(rate, key):
                    if json_errors and wants_json(request):
                        audit_log(base_event+':rate_limited', correlation_id=cid)
                        return error_response('RATE_LIMITED', 'Too many requests', 429)
                    from flask import abort
                    abort(429)
            # Validation
            if validator:
                try:
                    validated = validator()
                except ValidationError as ve:
                    if json_errors and wants_json(request):
                        audit_log(base_event+':invalid', correlation_id=cid, details=ve.details)
                        return error_response('INVALID_REQUEST', str(ve), 422, ve.details)
                    from flask import abort
                    abort(400, str(ve))
                # Attach to request context via kwargs if not present
                if isinstance(validated, dict):
                    kwargs.setdefault('_validated', validated)
            try:
                resp = fn(*args, **kwargs)
                # Ensure response is a Flask response object so we can set header
                try:
                    flask_resp = current_app.make_response(resp)
                except Exception:
                    flask_resp = resp
                # Echo correlation id header for client traceability
                try:
                    if hasattr(flask_resp, 'headers') and 'X-Correlation-ID' not in flask_resp.headers:
                        flask_resp.headers['X-Correlation-ID'] = cid
                except Exception:  # pragma: no cover
                    pass
                # Only mark success if status code is <400 (avoid false positives for handled redirects/errors)
                try:
                    status_code = getattr(flask_resp, 'status_code', 200)
                    if status_code < 400:
                        audit_log(base_event+':success', correlation_id=cid, status=status_code)
                    else:
                        audit_log(base_event+':completed', correlation_id=cid, status=status_code)
                except Exception:  # pragma: no cover
                    audit_log(base_event+':success', correlation_id=cid)
                return flask_resp
            except Exception as e:  # noqa
                current_app.logger.exception('Unhandled error in secure endpoint')
                if json_errors and wants_json(request):
                    audit_log(base_event+':error', correlation_id=cid, error=str(e))
                    return error_response('SERVER_ERROR', 'Unexpected error', 500)
                raise
        return wrapper
    return decorator

__all__ = ['wants_json', 'audit_log', 'secure_endpoint', 'ValidationError', 'validate_uploaded_file']
