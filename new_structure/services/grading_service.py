"""
GradingService: fetch and convert grading configuration for use by calculators and reports.
Non-invasive: uses existing GradingSystem model; provides safe defaults when none exist.
"""
from __future__ import annotations
from typing import List, Dict, Optional

from ..models.grading_system import GradingSystem
from .mark_calculator import GradeBand


class GradingService:
    """Service to resolve grading schemes and bands for the current school."""

    @staticmethod
    def get_active_system() -> Optional[GradingSystem]:
        # For now, use default system. Later, resolve per-school or from SchoolConfiguration.
        try:
            sys = GradingSystem.get_default_system()
            if sys:
                return sys
            # Fallback: any active
            actives = GradingSystem.get_active_systems()
            return actives[0] if actives else None
        except Exception:
            return None

    @staticmethod
    def convert_bands_to_calculator(bands_json: List[Dict]) -> List[GradeBand]:
        """Pure converter: JSON bands -> MarkCalculator GradeBand list."""
        out: List[GradeBand] = []
        for b in bands_json:
            try:
                out.append(
                    GradeBand(
                        min_inclusive=float(b.get('min_percentage', 0)),
                        max_inclusive=float(b.get('max_percentage', 100)),
                        grade=str(b.get('grade', '')),
                        points=float(b.get('points', 0)),
                        remark=b.get('name'),
                    )
                )
            except Exception:
                # Skip malformed band
                continue
        # Ensure sorted ascending by min_inclusive
        out.sort(key=lambda x: x.min_inclusive)
        return out

    @staticmethod
    def get_calculator_grade_bands() -> List[GradeBand]:
        """Resolve bands from the active grading system; fallback to a simple default set."""
        sys = GradingService.get_active_system()
        if sys:
            try:
                bands_json = sys.get_grade_bands()
                bands = GradingService.convert_bands_to_calculator(bands_json)
                if bands:
                    return bands
            except Exception:
                pass
        # Fallback simple bands
        return [
            GradeBand(0.0, 39.9, 'E', 1),
            GradeBand(40.0, 49.9, 'D', 2),
            GradeBand(50.0, 59.9, 'C', 3),
            GradeBand(60.0, 69.9, 'B', 4),
            GradeBand(70.0, 100.0, 'A', 5),
        ]

    @staticmethod
    def get_rounding_mode() -> str:
        """Return rounding mode. Default to ROUND_HALF_UP until configurable.
        Later, pull from SchoolConfiguration or GradingSystem metadata.
        """
        return 'ROUND_HALF_UP'

    @staticmethod
    def get_legend_grade_bands() -> List[Dict]:
        bands = GradingService.get_calculator_grade_bands()
        return [
            {
                'min': b.min_inclusive,
                'max': b.max_inclusive,
                'grade': b.grade,
                'points': b.points,
                'remark': b.remark,
            }
            for b in bands
        ]
