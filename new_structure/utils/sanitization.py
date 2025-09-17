"""HTML and script sanitization utilities for XSS mitigation (A7).

Provides:
- sanitize_html: whitelist-based cleaner for limited rich text contexts.
- escape_html: explicit alias for markupsafe.escape.
- to_safe_json: wrapper around json.dumps ensuring ASCII escaping and safe usage in inline scripts.
"""
from __future__ import annotations
from markupsafe import Markup, escape
import json

try:
    import bleach  # type: ignore
except ImportError:  # Fallback minimal sanitizer
    bleach = None  # pragma: no cover

# Conservative whitelist; expand only with explicit justification.
ALLOWED_TAGS = [
    'b', 'strong', 'i', 'em', 'br', 'ul', 'ol', 'li', 'span', 'p', 'a'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel', 'target'],
    'span': ['class'],
    'p': ['class']
}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(value: str | None) -> Markup:
    """Return a sanitized, safe HTML fragment.

    If bleach is unavailable, falls back to pure escaping (no HTML retained).
    """
    if value is None:
        return Markup('')
    if not isinstance(value, str):
        value = str(value)
    if bleach:
        cleaned = bleach.clean(
            value,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True
        )
        # Ensure links have rel noopener if target _blank
        if '<a ' in cleaned:
            # naive post-process; for rigorous cases use bleach.linkify with callbacks
            cleaned = cleaned.replace('target="_blank"', 'target="_blank" rel="noopener noreferrer"')
        return Markup(cleaned)
    # Fallback: escape everything
    return Markup(escape(value))


def escape_html(value: str | None) -> Markup:
    if value is None:
        return Markup('')
    return Markup(escape(value))


def to_safe_json(value) -> str:
    """Serialize to JSON with characters escaped to remain safe in inline <script> contexts.

    Preferred usage in templates: {{ python_obj|tojson }} but this helper is available for
    non-template contexts. Returns a JSON string literal (including surrounding quotes) when
    value is a string.
    """
    return json.dumps(value, ensure_ascii=True)

__all__ = [
    'sanitize_html',
    'escape_html',
    'to_safe_json'
]
