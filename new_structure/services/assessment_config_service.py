"""
Service to resolve assessment weights and missing policies from the database
and convert them to MarkCalculator types with safe fallbacks.
"""
from __future__ import annotations

from typing import Dict, Optional, List

from flask import current_app

from new_structure.extensions import db
from new_structure.models.assessment_config import AssessmentWeightsConfig, MissingPolicyConfig
from new_structure.services.mark_calculator import Weight, MissingPolicy
from new_structure.services import mark_calculator_adapter as adapter

# Simple in-process caches; can be replaced with Redis-backed cache_manager later
_weights_cache: Dict[str, List[Weight]] = {}
_policies_cache: Dict[str, Dict[str, MissingPolicy]] = {}


def _load_active_weights(education_level: Optional[str] = None) -> Optional[AssessmentWeightsConfig]:
    q = AssessmentWeightsConfig.query.filter_by(is_active=True)
    if education_level:
        q = q.filter_by(education_level=education_level)
    return q.order_by(AssessmentWeightsConfig.id.desc()).first()


def _load_active_policies(education_level: Optional[str] = None) -> Optional[MissingPolicyConfig]:
    q = MissingPolicyConfig.query.filter_by(is_active=True)
    if education_level:
        q = q.filter_by(education_level=education_level)
    return q.order_by(MissingPolicyConfig.id.desc()).first()


def get_effective_weights(education_level: Optional[str] = None) -> List[Weight]:
    """
    Resolve effective assessment weights. If DB config exists, use it;
    otherwise fall back to adapter defaults.
    """
    cache_key = education_level or '__all__'
    if cache_key in _weights_cache:
        return _weights_cache[cache_key]
    rec = _load_active_weights(education_level)
    if not rec:
        return adapter.get_default_weights()
    try:
        import json
        data = json.loads(rec.weights_json or '{}')
        result: List[Weight] = []
        for key, val in data.items():
            try:
                result.append(Weight(key, float(val)))
            except Exception:
                continue
        # If nothing parsed, fallback
        out = result or adapter.get_default_weights()
        _weights_cache[cache_key] = out
        return out
    except Exception:
        current_app.logger.exception("Failed parsing AssessmentWeightsConfig; using defaults")
        out = adapter.get_default_weights()
        _weights_cache[cache_key] = out
        return out


def get_effective_missing_policies(education_level: Optional[str] = None) -> Dict[str, MissingPolicy]:
    cache_key = education_level or '__all__'
    if cache_key in _policies_cache:
        return _policies_cache[cache_key]
    rec = _load_active_policies(education_level)
    if not rec:
        out = adapter.get_default_missing_policies()
        _policies_cache[cache_key] = out
        return out
    try:
        import json
        data = json.loads(rec.policies_json or '{}')
        result: Dict[str, MissingPolicy] = {}
        for key, mode in data.items():
            # Accept supported treatments; silently skip unknowns
            if mode not in {"exclude", "zero", "proxy"}:
                continue
            # MissingPolicy(status_code: MissingStatus, treatment: Treatment, requires_comment: bool=False)
            result[key] = MissingPolicy(status_code=key, treatment=mode)
        out = result or adapter.get_default_missing_policies()
        _policies_cache[cache_key] = out
        return out
    except Exception:
        current_app.logger.exception("Failed parsing MissingPolicyConfig; using defaults")
        out = adapter.get_default_missing_policies()
        _policies_cache[cache_key] = out
        return out


def invalidate_caches(education_level: Optional[str] = None) -> None:
    """Invalidate cached effective weights/policies for a scope or all."""
    if education_level is None:
        _weights_cache.clear()
        _policies_cache.clear()
    else:
        _weights_cache.pop(education_level, None)
        _policies_cache.pop(education_level, None)
