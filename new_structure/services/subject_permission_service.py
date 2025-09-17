"""Subject Permission Service

Provides helper for subject-level scope enforcement leveraging the existing
many-to-many association table `teacher_subjects` between `Teacher` and `Subject`.

Phase 2 Enhancement:
    This lightweight service is consumed by the unified authorization layer
    when a route supplies a `subject` parameter (either id or name). It mirrors
    the philosophy of `PermissionService.check_class_access` for clarity and
    future extensibility (e.g., caching, temporal validity, delegated subject
    permissions separate from core teacher assignments).
"""
from __future__ import annotations
from typing import Optional, Union

from ..extensions import db  # noqa: F401 (reserved for potential future optimizations)

try:  # Local imports isolated for testability
    from ..models.academic import Subject
    from ..models.user import Teacher
except Exception:  # pragma: no cover
    Subject = Teacher = None  # type: ignore


class SubjectPermissionService:
    """Encapsulates subject-level access checks.

    Current rule set (Phase 2 initial):
        * Headteacher / admin / superadmin bypass handled in caller (authorization layer)
        * If teacher role is 'classteacher' or 'teacher', they must be explicitly
          associated to the subject through `teacher_subjects` unless the subject
          is composite and they are linked to at least one of its component subjects.
        * Unknown or unresolvable subject -> deny (secure default).
    """

    ELEVATED_ROLES = {"headteacher", "admin", "superadmin"}

    @staticmethod
    def resolve_subject(subject: Union[int, str]):  # -> Optional[Subject]: (omitted to avoid forward ref issues)
        """Resolve subject by id (int-like) or by case-insensitive name.

        Returns None if not found.
        """
        if Subject is None:  # pragma: no cover
            return None
        if subject is None:
            return None
        # ID path
        if isinstance(subject, int) or (isinstance(subject, str) and subject.isdigit()):
            try:
                sid = int(subject)  # noqa: F841
                return Subject.query.get(int(subject))
            except Exception:  # pragma: no cover
                return None
        # Name path (case-insensitive match)
        return Subject.query.filter(db.func.lower(Subject.name) == str(subject).lower()).first()

    @classmethod
    def check_subject_access(cls, teacher_id: int, role: str, subject_value: Union[int, str]) -> bool:
        """Return True if the teacher with role may access the subject.

        Elevated roles bypass (enforced upstream - kept defensive here).
        """
        if not teacher_id or not role:
            return False
        if role in cls.ELEVATED_ROLES:
            return True
        subject_obj = cls.resolve_subject(subject_value)
        if not subject_obj:
            return False
        if Teacher is None:  # pragma: no cover
            return False
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            return False
        # Direct association
        if subject_obj in teacher.subjects:
            return True
        # If composite subject requested, allow if teacher has at least one component
        if subject_obj.is_composite:
            components = subject_obj.get_component_subjects()
            teacher_subject_ids = {s.id for s in teacher.subjects}
            if any(c.id in teacher_subject_ids for c in components):
                return True
        return False

__all__ = ["SubjectPermissionService"]
