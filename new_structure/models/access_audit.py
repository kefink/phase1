"""Access Audit Model

Stores authorization / access control decisions for security monitoring and forensics.

Design Goals:
    * Lightweight write: minimal indices (user_id, success)
    * Capture contextual metadata (grade_id, stream_id, subject, function, owner_id)
    * Avoid raising exceptions that could block request flow.
"""
from __future__ import annotations
from new_structure.extensions import db

class AccessAudit(db.Model):
    __tablename__ = 'access_audit'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    role = db.Column(db.String(50), nullable=True)
    resource = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    success = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    # Contextual metadata
    function = db.Column(db.String(100), nullable=True)
    grade_id = db.Column(db.Integer, nullable=True)
    stream_id = db.Column(db.Integer, nullable=True)
    subject = db.Column(db.String(100), nullable=True)
    owner_id = db.Column(db.Integer, nullable=True)
    message = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    @classmethod
    def record(cls, **kwargs):  # pragma: no cover (thin wrapper)
        obj = cls(**kwargs)
        db.session.add(obj)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return obj

__all__ = ["AccessAudit"]
