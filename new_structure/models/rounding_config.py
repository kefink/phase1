"""
Rounding mode configuration model.
Allows configuring rounding mode per education level or (future) per grade.
"""
from datetime import datetime
from new_structure.extensions import db


class RoundingModeConfig(db.Model):
    __tablename__ = 'rounding_mode_config'

    id = db.Column(db.Integer, primary_key=True)
    # Scope: align with assessment config scope for now
    education_level = db.Column(db.String(50), nullable=True)  # lower_primary, upper_primary, junior_secondary
    # Optional future scope: grade_id (kept nullable/not used yet)
    grade_id = db.Column(db.Integer, nullable=True)
    rounding_mode = db.Column(db.String(32), nullable=False, default='ROUND_HALF_UP')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        scope = self.education_level or 'all'
        return f"<RoundingModeConfig {scope}:{self.rounding_mode} active={self.is_active}>"
