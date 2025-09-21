"""
Performance calculation utilities for the Hillview School Management System.

Feature-flagged enhancement:
- When `Config.REPORTS_USE_MARK_CALCULATOR` is enabled, `get_grade_and_points`
    will use database-configured grading bands via `GradingService`.
- Default behavior remains unchanged.
"""

from __future__ import annotations

from typing import Optional, Tuple

try:
        # Optional imports to avoid hard dependency when used outside app context
        from ..services.grading_service import GradingService  # type: ignore
        from ..config import get_config  # type: ignore
except Exception:  # pragma: no cover - fallback when imports not available
        GradingService = None  # type: ignore
        get_config = None  # type: ignore

def get_performance_category(percentage):
    """
    Convert a percentage to a performance category using detailed CBC grading.

    Args:
        percentage: The percentage score (0-100)

    Returns:
        String representing the performance category (EE1, EE2, ME1, ME2, AE1, AE2, BE1, BE2)
    """
    if percentage >= 90:
        return "EE1"  # Exceeding Expectation 1
    elif percentage >= 75:
        return "EE2"  # Exceeding Expectation 2
    elif percentage >= 58:
        return "ME1"  # Meeting Expectation 1
    elif percentage >= 41:
        return "ME2"  # Meeting Expectation 2
    elif percentage >= 31:
        return "AE1"  # Approaching Expectation 1
    elif percentage >= 21:
        return "AE2"  # Approaching Expectation 2
    elif percentage >= 11:
        return "BE1"  # Below Expectation 1
    else:
        return "BE2"  # Below Expectation 2

def _map_with_configured_bands(average: float) -> Optional[Tuple[str, float]]:
    """Attempt to map using DB-configured bands via GradingService.

    Returns (grade, points) or None if unavailable.
    """
    # Guard if optional imports not available
    if not (GradingService and get_config):
        return None
    try:
        # Respect feature flag; default off
        cfg = get_config()
        use_calc = getattr(cfg, 'REPORTS_USE_MARK_CALCULATOR', False)
        if not use_calc:
            return None
        # Fetch calculator bands and map
        bands = GradingService.get_calculator_grade_bands()
        for b in bands:
            if b.min_inclusive <= average <= b.max_inclusive:
                # Prefer remark if present and resembles a grade code; else use grade field
                grade = getattr(b, 'grade', None) or getattr(b, 'remark', None) or 'GRADE'
                points = getattr(b, 'points', None)
                if grade is not None and points is not None:
                    return str(grade), float(points)
        return None
    except Exception:
        # On any failure, silently fall back to legacy mapping
        return None


def get_grade_and_points(average: float):
    """
    Convert an average score to a performance level and points.

    Args:
        average: The average score (0-100)

    Returns:
        Tuple of (performance_level, points)
    """
    mapped = _map_with_configured_bands(average)
    if mapped is not None:
        return mapped
    # Legacy CBC thresholds (default path)
    if average >= 90:
        return "EE1", 4.0
    elif average >= 75:
        return "EE2", 3.5
    elif average >= 58:
        return "ME1", 3.0
    elif average >= 41:
        return "ME2", 2.5
    elif average >= 31:
        return "AE1", 2.0
    elif average >= 21:
        return "AE2", 1.5
    elif average >= 11:
        return "BE1", 1.0
    else:
        return "BE2", 0.5

def get_performance_remarks(mark, total_marks=100):
    """
    Generate CBC-compliant performance remarks based on a mark.

    Args:
        mark: The mark achieved
        total_marks: The total possible marks (default: 100)

    Returns:
        String with detailed CBC grading level (EE1, EE2, ME1, ME2, AE1, AE2, BE1, BE2)
    """
    if total_marks > 0:
        percentage = (mark / total_marks) * 100
    else:
        percentage = 0

    # Detailed CBC Grading System
    if percentage >= 90:
        return "EE1"  # Exceeding Expectation 1
    elif percentage >= 75:
        return "EE2"  # Exceeding Expectation 2
    elif percentage >= 58:
        return "ME1"  # Meeting Expectation 1
    elif percentage >= 41:
        return "ME2"  # Meeting Expectation 2
    elif percentage >= 31:
        return "AE1"  # Approaching Expectation 1
    elif percentage >= 21:
        return "AE2"  # Approaching Expectation 2
    elif percentage >= 11:
        return "BE1"  # Below Expectation 1
    else:
        return "BE2"  # Below Expectation 2

def get_performance_summary(marks_data):
    """
    Generate a summary of performance categories from marks data.

    Args:
        marks_data: List of student mark data

    Returns:
        Dictionary with counts of each performance category
    """
    from collections import defaultdict
    summary = defaultdict(int)
    for student in marks_data:
        summary[student[3]] += 1
    return dict(summary)