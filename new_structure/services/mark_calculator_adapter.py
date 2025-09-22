"""
Adapter utilities for MarkCalculator.
Provides defaults and legends without altering existing report calculations.
Safe to import anywhere; does not access Flask app context.
"""
from __future__ import annotations
from typing import List, Dict, Tuple

from .mark_calculator import Weight, GradeBand, MissingPolicy
from .grading_service import GradingService
from . import assessment_config_service as acs


def get_default_weights() -> List[Weight]:
    """Default assessment weights (percentages) for OPENER/MIDTERM/ENDTERM."""
    return [
        Weight('OPENER', 10.0),
        Weight('MIDTERM', 30.0),
        Weight('ENDTERM', 60.0),
    ]


def get_effective_weights(education_level: str | None = None) -> List[Weight]:
    """Resolve DB-configured weights if present, otherwise defaults."""
    try:
        return acs.get_effective_weights(education_level)
    except Exception:
        return get_default_weights()


def get_default_grade_bands() -> List[GradeBand]:
    """Default grade bands (example bands)."""
    return [
        GradeBand(0.0, 39.9, 'E', 1),
        GradeBand(40.0, 49.9, 'D', 2),
        GradeBand(50.0, 59.9, 'C', 3),
        GradeBand(60.0, 69.9, 'B', 4),
        GradeBand(70.0, 100.0, 'A', 5),
    ]


def get_default_missing_policies() -> Dict[str, MissingPolicy]:
    """Default missing-mark policies: EXC/MED/NA excluded, INC counts as zero, ABS excluded by default."""
    return {
        'ABS': MissingPolicy('ABS', 'exclude'),
        'EXC': MissingPolicy('EXC', 'exclude'),
        'MED': MissingPolicy('MED', 'exclude'),
        'NA': MissingPolicy('NA', 'exclude'),
        'INC': MissingPolicy('INC', 'zero'),
    }


def get_effective_missing_policies(education_level: str | None = None) -> Dict[str, MissingPolicy]:
    try:
        return acs.get_effective_missing_policies(education_level)
    except Exception:
        return get_default_missing_policies()


def build_legends() -> Dict[str, object]:
    """Return dicts suitable for template legends (weights, grade bands, status legend)."""
    # Show effective (possibly DB-configured) weights in legends
    try:
        weights_list = get_effective_weights()
    except Exception:
        weights_list = get_default_weights()
    weights = [{'assessment': w.assessment_code, 'weight': w.weight} for w in weights_list]
    # Prefer DB-configured bands if available
    try:
        bands = GradingService.get_legend_grade_bands()
    except Exception:
        bands = [{'min': b.min_inclusive, 'max': b.max_inclusive, 'grade': b.grade, 'points': b.points} for b in get_default_grade_bands()]
    status_legend = [
        {'code': 'ABS', 'meaning': 'Absent (excluded by default)'},
        {'code': 'EXC', 'meaning': 'Exempted (excluded)'},
        {'code': 'MED', 'meaning': 'Medical (excluded)'},
        {'code': 'NA',  'meaning': 'Not Assessed (excluded)'},
        {'code': 'INC', 'meaning': 'Incomplete (counts as zero)'},
    ]
    return {
        'weights': weights,
        'grade_bands': bands,
        'status_legend': status_legend,
    }
