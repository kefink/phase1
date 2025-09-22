"""
GradingService: fetch and convert grading configuration for use by calculators and reports.
Non-invasive: uses existing GradingSystem model; provides safe defaults when none exist.
"""
from __future__ import annotations
from typing import List, Dict, Optional

from ..models.grading_system import GradingSystem
from ..models.rounding_config import RoundingModeConfig
from .mark_calculator import GradeBand


class GradingService:
    """Service to resolve grading schemes and bands for the current school."""

    @staticmethod
    def get_active_system() -> Optional[GradingSystem]:
        """Resolve the active grading system, preferring School Setup selection.

        Order of precedence:
        1) SchoolSetup.grading_system (by code), case-insensitive
        2) Default GradingSystem (is_default=True)
        3) First active GradingSystem
        """
        try:
            # Attempt to read current School Setup preference without hard-dependency at import time
            try:
                from ..models.school_setup import SchoolSetup  # type: ignore
                setup = SchoolSetup.get_current_setup()
                code_raw = getattr(setup, 'grading_system', None)
            except Exception:
                code_raw = None

            # Normalize possible values from setup UI (e.g., 'CBC', 'Percentage', 'Letter') to codes
            code = None
            if code_raw:
                mapping = {
                    'cbc': 'CBC',
                    'percentage': 'PERCENTAGE',
                    'letter': 'LETTER',
                    # Accept direct codes as well
                    'cbc (competency based curriculum)': 'CBC',
                }
                code = mapping.get(str(code_raw).strip().lower(), str(code_raw).strip().upper())

            if code:
                sys = GradingSystem.query.filter_by(code=code, is_active=True).first()
                if sys:
                    return sys

            # Fallback: default, then any active
            sys = GradingSystem.get_default_system()
            if sys:
                return sys
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
        """Resolve bands from the active grading system; fallback to a simple default set.
        Cached in-process for the lifetime of the process.
        """
        if hasattr(GradingService, '_bands_cache') and getattr(GradingService, '_bands_cache'):
            return getattr(GradingService, '_bands_cache')
        sys = GradingService.get_active_system()
        if sys:
            try:
                bands_json = sys.get_grade_bands()
                bands = GradingService.convert_bands_to_calculator(bands_json)
                if bands:
                    setattr(GradingService, '_bands_cache', bands)
                    return bands
            except Exception:
                pass
        # Fallback simple bands
        fallback = [
            GradeBand(0.0, 39.9, 'E', 1),
            GradeBand(40.0, 49.9, 'D', 2),
            GradeBand(50.0, 59.9, 'C', 3),
            GradeBand(60.0, 69.9, 'B', 4),
            GradeBand(70.0, 100.0, 'A', 5),
        ]
        setattr(GradingService, '_bands_cache', fallback)
        return fallback

    @staticmethod
    def get_rounding_mode() -> str:
        """Return default rounding mode when no context provided."""
        return GradingService.get_rounding_mode_for_level(None)

    # Simple in-process cache for rounding mode lookups
    _rounding_cache: dict = {}

    @staticmethod
    def get_rounding_mode_for_level(education_level: Optional[str]) -> str:
        """Resolve rounding mode for a specific education level with fallback and caching.
        Supported modes: ROUND_HALF_UP, FLOOR, CEIL, TRUNC
        """
        cache_key = education_level or '__all__'
        if cache_key in GradingService._rounding_cache:
            return GradingService._rounding_cache[cache_key]
        try:
            q = RoundingModeConfig.query.filter_by(is_active=True)
            if education_level:
                q = q.filter_by(education_level=education_level)
            rec = q.order_by(RoundingModeConfig.id.desc()).first()
            if rec and rec.rounding_mode in {'ROUND_HALF_UP', 'FLOOR', 'CEIL', 'TRUNC'}:
                mode = rec.rounding_mode
            else:
                mode = 'ROUND_HALF_UP'
        except Exception:
            mode = 'ROUND_HALF_UP'
        GradingService._rounding_cache[cache_key] = mode
        return mode

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
