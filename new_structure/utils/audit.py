"""Central audit logging helper.
Provides a single function `audit_event` to emit normalized audit trail entries.
"""
from __future__ import annotations
import logging
from datetime import datetime
from flask import g, has_request_context, request

SENSITIVE_KEYS = {'password', 'passwd', 'secret', 'token', 'auth', 'authorization', 'api_key'}

_audit_logger = logging.getLogger('audit')


def _scrub(value):
    if value is None:
        return None
    if isinstance(value, dict):
        redacted = {}
        for k, v in value.items():
            if k.lower() in SENSITIVE_KEYS:
                redacted[k] = '[REDACTED]'
            else:
                redacted[k] = _scrub(v)
        return redacted
    if isinstance(value, (list, tuple)):
        return [_scrub(v) for v in value]
    text = str(value)
    if len(text) > 500:
        return text[:500] + '…'
    return text


def audit_event(action: str, *, actor: str | None = None, target: str | None = None,
                outcome: str = 'success', category: str = 'general', details: dict | None = None,
                severity: str = 'info'):
    """Emit a normalized audit event.

    Fields:
      timestamp, request_id, actor, action, target, outcome, category, ip, user_agent, details, severity
    """
    if details is None:
        details = {}
    rid = None
    ip = None
    ua = None
    if has_request_context():
        rid = getattr(g, 'request_id', None)
        ip = request.remote_addr
        ua = request.headers.get('User-Agent')
    record = {
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': rid,
        'actor': actor,
        'action': action,
        'target': target,
        'outcome': outcome,
        'category': category,
        'ip': ip,
        'user_agent': ua,
        'severity': severity,
        'details': _scrub(details)
    }
    # Log as a single line key=value for easier grepping; structured processors can be layered later
    msg = 'AUDIT ' + ' '.join(f"{k}={repr(v)}" for k, v in record.items())
    level = {'info': logging.INFO, 'warning': logging.WARNING, 'error': logging.ERROR}.get(severity, logging.INFO)
    _audit_logger.log(level, msg)
    return record

__all__ = ['audit_event']
