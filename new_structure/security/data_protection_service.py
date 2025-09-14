"""Data Protection Service: optional field-level encryption for sensitive PII.

If DATA_ENCRYPTION_KEY environment variable is provided (Fernet key), email & phone
fields on Teacher model are transparently encrypted at rest.

Design:
- Ciphertext stored as: enc:<base64>
- On load, values decrypted into transient attributes for application logic.
- If key absent, operates in passthrough mode.

This module is designed to be imported early (e.g., in app factory after models).
"""
from __future__ import annotations
import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import event
from sqlalchemy.orm.attributes import get_history
from ..models.user import Teacher

FERNET: Optional[Fernet] = None  # Dynamically (re)initialized via refresh_key()


def _build_fernet(key: str | None) -> Optional[Fernet]:
    if not key:
        return None
    try:
        return Fernet(key)
    except Exception:
        return None


def refresh_key() -> None:
    """(Re)load the DATA_ENCRYPTION_KEY from environment.

    This allows tests (or a secondary app factory invocation) to set the
    environment variable *after* the module was first imported. Event
    listeners consult the global FERNET variable at runtime, so updating it
    here immediately affects subsequent insert/update/load operations.
    """
    global FERNET
    key = os.environ.get('DATA_ENCRYPTION_KEY')
    FERNET = _build_fernet(key)


# Initialize once on import (will be a no-op if key absent). Tests that set the
# env var later should call refresh_key() via app factory hook.
refresh_key()

PREFIX = 'enc:'
SENSITIVE_FIELDS = ['email', 'phone']


def _encrypt(value: Optional[str]) -> Optional[str]:
    if not value or not FERNET:
        return value
    if value.startswith(PREFIX):
        return value  # already encrypted
    token = FERNET.encrypt(value.encode('utf-8'))
    return PREFIX + token.decode('utf-8')


def _decrypt(value: Optional[str]) -> Optional[str]:
    if not value or not FERNET:
        return value
    if not value.startswith(PREFIX):
        return value  # plaintext (legacy)
    data = value[len(PREFIX):]
    try:
        return FERNET.decrypt(data.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        return None  # Corrupted or wrong key


@event.listens_for(Teacher, 'load')
def receive_load(target: Teacher, context):  # noqa: D401
    if not FERNET:
        return
    for field in SENSITIVE_FIELDS:
        raw = getattr(target, field, None)
        decrypted = _decrypt(raw)
        setattr(target, field, decrypted)


@event.listens_for(Teacher, 'before_insert')
@event.listens_for(Teacher, 'before_update')
def receive_before_flush(mapper, connection, target: Teacher):  # noqa: D401
    if not FERNET:
        return
    for field in SENSITIVE_FIELDS:
        raw = getattr(target, field, None)
        # If already encrypted (starts with prefix), leave untouched
        if isinstance(raw, str) and raw.startswith(PREFIX):
            continue
        enc = _encrypt(raw)
        setattr(target, field, enc)


@event.listens_for(Teacher, 'refresh')
def receive_refresh(target: Teacher, context, attrs):  # noqa: D401
    if not FERNET:
        return
    for field in SENSITIVE_FIELDS:
        raw = getattr(target, field, None)
        dec = _decrypt(raw)
        setattr(target, field, dec)
