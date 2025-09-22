"""
Assessment configuration models: weights per assessment and missing-mark policies.
These enable DB-backed configurability for the MarkCalculator pipeline.
"""
from datetime import datetime
from new_structure.extensions import db


class AssessmentWeightsConfig(db.Model):
    __tablename__ = 'assessment_weights_config'

    id = db.Column(db.Integer, primary_key=True)
    # Scope: can be refined later (grade/stream/term); start with education level
    education_level = db.Column(db.String(50), nullable=True)  # lower_primary, upper_primary, junior_secondary
    # JSON: {"OPENER": 10.0, "MIDTERM": 30.0, "ENDTERM": 60.0}
    weights_json = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MissingPolicyConfig(db.Model):
    __tablename__ = 'missing_policy_config'

    id = db.Column(db.Integer, primary_key=True)
    education_level = db.Column(db.String(50), nullable=True)
    # JSON: {"ABS": "exclude", "EXC": "exclude", "MED": "exclude", "NA": "exclude", "INC": "zero"}
    policies_json = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
