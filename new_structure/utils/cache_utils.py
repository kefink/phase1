"""Backward-compatible cache utility shim.

Older code imports `utils.cache_utils.invalidate_cache`.
The new cache system centralizes logic in `cache_manager.py`.
This file provides the expected function so legacy imports keep working.
"""
from __future__ import annotations
from typing import Optional

try:
    from .cache_manager import cache  # existing cache instance
except Exception:  # pragma: no cover - extremely unlikely
    cache = None  # type: ignore


def invalidate_cache(grade: str, stream: str, term: str, assessment_type: str, *, scope: Optional[str] = None) -> None:
    """Invalidate cached items related to a class report.

    Parameters
    ----------
    grade : str
        Grade name (e.g. "Grade 9"). Used to build pattern.
    stream : str
        Stream identifier (may include prefix "Stream ").
    term : str
        Academic term name.
    assessment_type : str
        Assessment type name.
    scope : Optional[str]
        Future extension; currently unused. Allows targeted invalidation.
    """
    if not cache:
        return  # No cache available; silently succeed

    # Normalize stream key portion
    stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream

    # Build broad patterns matching potential keys (defensive)
    patterns = [
        f"hillview:analytics_class:*{grade}*{stream_letter}*",
        f"hillview:students_class:*{grade}*{stream_letter}*",
        f"hillview:analytics_class:*{stream_letter}*",
    ]
    for p in patterns:
        try:
            cache.clear_pattern(p)  # type: ignore[attr-defined]
        except Exception:
            pass

__all__ = ["invalidate_cache"]
