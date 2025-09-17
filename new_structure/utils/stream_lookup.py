"""Utilities for safe, disambiguated Stream lookups.

Historically code fetched streams with only the name (e.g. 'A'), which can
collide across grades. Centralize a helper that always scopes by grade when
available to eliminate accidental cross‑grade matches.
"""
from typing import Optional, Union

from ..extensions import db
from ..models import Grade, Stream


def get_stream_by_name_and_grade(stream_name: str, grade: Union[Grade, str, int, None]) -> Optional[Stream]:
    """Return the unique Stream for a given grade context.

    Accepts a Grade model instance, a grade primary key (int), or a grade name (str).
    Falls back to None if grade cannot be resolved or stream not found.
    """
    if not stream_name or grade is None:
        return None

    grade_obj: Optional[Grade] = None
    # Resolve grade reference
    if isinstance(grade, Grade):
        grade_obj = grade
    elif isinstance(grade, int):
        grade_obj = db.session.get(Grade, grade)
    elif isinstance(grade, str):
        grade_obj = Grade.query.filter_by(name=grade).first()

    if not grade_obj:
        return None

    return Stream.query.filter_by(name=stream_name, grade_id=grade_obj.id).first()
