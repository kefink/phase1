"""Unified Authorization Layer

Bridges role hierarchy, resource/action policies, and fine-grained class/function permissions
into a single, auditable interface.

Contract:
    authorize(resource, action, *, grade=None, stream=None, subject=None,
              owner_id=None, require_roles=None, allow_head=True, audit=True,
              function=None)

Decorators:
    @require_roles(*roles)
    @require_permission(resource, action)
    @require_class_scope(grade_arg='grade', stream_arg='stream')
    @enforce(resource, action, class_scope=False, grade_arg='grade', stream_arg='stream', roles=None)

Return / Raise semantics:
    - Raises werkzeug HTTPException via abort(401/403) on failure
    - Returns True on success (decorators proceed to wrapped function)

NOTE: Phase 1 implements class scope via PermissionService only for classteacher role.
      Subject-level scoping and function permission integration are planned in Phase 2.
"""
from __future__ import annotations
import functools
import logging
from typing import Iterable, Optional, Callable, Any
from flask import request, session, abort
try:
    from ..utils.audit import audit_event
except Exception:  # pragma: no cover
    def audit_event(*a, **k):  # type: ignore
        logging.getLogger(__name__).debug('audit_event fallback', extra={'args': a, 'kwargs': k})

try:
    from .access_control import AccessControlProtection  # Enhanced existing module
except Exception:  # pragma: no cover
    from . import access_control as AccessControlProtection  # type: ignore

try:
    from ..services.permission_service import PermissionService
except Exception:  # pragma: no cover
    class PermissionService:  # Fallback stub
        @staticmethod
        def check_class_access(user_id, grade_id, stream_id=None):
            return True

try:
    from ..services.enhanced_permission_service import EnhancedPermissionService
except Exception:  # pragma: no cover
    class EnhancedPermissionService:  # type: ignore
        @staticmethod
        def check_function_permission(teacher_id, function_name, grade_id=None, stream_id=None):
            return True

try:
    from ..services.subject_permission_service import SubjectPermissionService
except Exception:  # pragma: no cover
    class SubjectPermissionService:  # type: ignore
        @staticmethod
        def check_subject_access(teacher_id, role, subject_value):
            return True

try:
    from ..services import get_role, is_authenticated
except Exception:  # pragma: no cover
    def get_role(sess):
        return sess.get('role')
    def is_authenticated(sess):
        return bool(sess.get('teacher_id'))

logger = logging.getLogger(__name__)

# Mapping resource/action to existing AccessControlProtection (ACP) resource keys
RESOURCE_ALIAS = {
    'class_report': 'reports',
    'individual_report': 'reports',
    'marksheet': 'marks',
    'marks': 'marks',
    'teacher_mgmt': 'teacher_management',
    'staff_mgmt': 'teacher_management',
    'permissions': 'teacher_management',  # permission delegation treated as management
    'system': 'system_config',
}


def _resolve_resource(resource: str) -> str:
    return RESOURCE_ALIAS.get(resource, resource)


def authorize(resource: str, action: str, *, grade: Optional[Any] = None, stream: Optional[Any] = None,
              subject: Optional[str] = None, owner_id: Optional[Any] = None,
              require_roles: Optional[Iterable[str]] = None, allow_head: bool = True, audit: bool = True,
              function: Optional[str] = None) -> bool:
    """Perform composite authorization check.

    Steps:
        1. Session / authentication validation
        2. Explicit role allow-list (if provided)
        3. Resource/action policy check
        4. (Optional) Function-level permission check (Phase 2)
        5. Class scope enforcement (classteacher/teacher)
        6. Ownership / subject-level (future extension points)
    """
    if not is_authenticated(session):
        audit_event('auth_failure', actor=session.get('teacher_id'), target=resource, outcome='denied', category='auth', details={'reason': 'unauthenticated', 'action': action})
        abort(401, description="Authentication required")
    else:
        logger.debug('AUTHZ debug session keys=%s', list(session.keys()))

    user_id = session.get('teacher_id')
    role = get_role(session)

    # Role allow-list check
    if require_roles and role not in require_roles:
        audit_event('role_denied', actor=user_id, target=resource, outcome='denied', category='authorization', details={'required_roles': list(require_roles), 'role': role, 'action': action})
        abort(403, description="Insufficient role")

    acp_resource = _resolve_resource(resource)
    if not AccessControlProtection.check_resource_permission(role, acp_resource, action):
        AccessControlProtection.log_access_attempt(user_id, acp_resource, action, False)
        audit_event('permission_denied', actor=user_id, target=f"{acp_resource}:{action}", outcome='denied', category='authorization')
        abort(403, description=f"No permission for {action} on {resource}")

    # Function-level permission (only applies to non-head elevated roles)
    if function and role not in ('headteacher', 'admin', 'superadmin'):
        # Attempt to derive grade/stream ids if provided so scoped function permissions can apply
        grade_id = None
        stream_id = None
        if grade is not None:
            try:
                if isinstance(grade, int) or (isinstance(grade, str) and grade.isdigit()):
                    grade_id = int(grade)
            except Exception:  # pragma: no cover
                grade_id = None
        if stream is not None:
            try:
                if isinstance(stream, int) or (isinstance(stream, str) and str(stream).isdigit()):
                    stream_id = int(stream)
            except Exception:  # pragma: no cover
                stream_id = None
        if not EnhancedPermissionService.check_function_permission(user_id, function, grade_id, stream_id):
            AccessControlProtection.log_access_attempt(user_id, f"function:{function}", action, False)
            audit_event('function_permission_denied', actor=user_id, target=function, outcome='denied', category='authorization', details={'grade_id': grade_id, 'stream_id': stream_id})
            abort(403, description=f"No function permission for {function}")

    # Class scope (applies where grade provided and role is classteacher or teacher)
    if grade is not None and role in ('classteacher', 'teacher'):
        # Normalize identifiers (grade might be name or id; PermissionService expects names in some flows)
        # We attempt flexible matching: if numeric -> treat as id path else treat as name.
        try:
            from ..models import Grade, Stream  # lazy import
        except Exception:  # pragma: no cover
            Grade = Stream = None  # type: ignore

        grade_id = None
        stream_id = None

        if isinstance(grade, int) or (isinstance(grade, str) and grade.isdigit()):
            grade_id = int(grade)
        else:
            if 'Grade' in str(grade) or str(grade).startswith('PP'):
                if Grade:
                    g_obj = Grade.query.filter_by(name=str(grade)).first()
                    grade_id = g_obj.id if g_obj else None
            else:
                grade_id = None
        if stream is not None:
            if isinstance(stream, int) or (isinstance(stream, str) and str(stream).isdigit()):
                stream_id = int(stream)
            else:
                if Stream:
                    if grade_id and isinstance(stream, str):
                        s_obj = Stream.query.filter_by(name=stream, grade_id=grade_id).first()
                        stream_id = s_obj.id if s_obj else None
        # Fallback: if we couldn't resolve grade id, deny (classteacher must have resolvable scope)
        if grade_id is None:
            audit_event('class_scope_unresolved', actor=user_id, target=str(grade), outcome='denied', category='authorization', details={'grade_input': str(grade)})
            abort(403, description="Class scope unresolved")
        has_access = PermissionService.check_class_access(user_id, grade_id, stream_id)
        if not has_access:
            AccessControlProtection.log_access_attempt(user_id, f"class_{grade}_{stream}", action, False)
            audit_event('class_scope_denied', actor=user_id, target=f"grade:{grade} stream:{stream}", outcome='denied', category='authorization')
            abort(403, description="No class scope access")

    # Subject scope (Phase 2): ensure teacher assigned to subject when provided
    if subject is not None and role in ('classteacher', 'teacher'):
        if not SubjectPermissionService.check_subject_access(user_id, role, subject):
            AccessControlProtection.log_access_attempt(user_id, f"subject_{subject}", action, False)
            audit_event('subject_scope_denied', actor=user_id, target=subject, outcome='denied', category='authorization')
            abort(403, description="No subject access")

    # (Future) Ownership or subject-level checks can be inserted here

    if audit:
        AccessControlProtection.log_access_attempt(user_id, acp_resource, action, True)
        audit_event('authorize', actor=user_id, target=f"{acp_resource}:{action}", outcome='success', category='authorization')
    return True


def require_roles(*roles: str):
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            authorize(resource='system', action='read', require_roles=roles)  # minimal auth + role gate
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(resource: str, action: str):
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            authorize(resource=resource, action=action)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_class_scope(grade_arg: str = 'grade', stream_arg: str = 'stream', resource: str = 'marks', action: str = 'read'):
    """Decorator adding class scope enforcement for classteachers.

    Extracts grade/stream from kwargs or request args/form.
    """
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            grade_val = kwargs.get(grade_arg) or request.view_args and request.view_args.get(grade_arg) or request.args.get(grade_arg) or request.form.get(grade_arg)
            stream_val = kwargs.get(stream_arg) or request.view_args and request.view_args.get(stream_arg) or request.args.get(stream_arg) or request.form.get(stream_arg)
            authorize(resource=resource, action=action, grade=grade_val, stream=stream_val)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def enforce(resource: str, action: str, *, class_scope: bool = False, grade_arg: str = 'grade', stream_arg: str = 'stream', roles: Optional[Iterable[str]] = None, function: Optional[str] = None):
    """Composite convenience decorator.

    Example:
        @enforce('marks', 'write', class_scope=True, grade_arg='grade', stream_arg='stream')
    """
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # DEBUG: inspect session content (temporary)
            try:
                print('ENFORCE DEBUG SESSION=', dict(session))
            except Exception:
                pass
            # Short-circuit authentication check to ensure 401 (tests rely on precise code) before deeper logic
            # Treat absence of teacher_id OR role as unauthenticated for stricter semantics
            if not (session.get('teacher_id') and session.get('role')):
                audit_event('auth_failure', actor=session.get('teacher_id'), target=resource, outcome='denied', category='auth', details={'reason': 'unauthenticated_precheck', 'action': action, 'role_present': bool(session.get('role'))})
                abort(401, description="Authentication required")
            grade_val = None
            stream_val = None
            if class_scope:
                grade_val = kwargs.get(grade_arg) or request.view_args and request.view_args.get(grade_arg) or request.args.get(grade_arg) or request.form.get(grade_arg)
                stream_val = kwargs.get(stream_arg) or request.view_args and request.view_args.get(stream_arg) or request.args.get(stream_arg) or request.form.get(stream_arg)
            authorize(resource=resource, action=action, grade=grade_val, stream=stream_val, require_roles=roles, function=function)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def enforce_subject(resource: str, action: str, subject_arg: str = 'subject', roles: Optional[Iterable[str]] = None, function: Optional[str] = None):
    """Decorator enforcing base resource/action plus subject-level scope.

    Extracts subject name/id from kwargs or request args and passes to authorize.
    Example:
        @enforce_subject('marks', 'read', subject_arg='subject_name')
        def view_subject(subject_name): ...
    """
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            subj_val = kwargs.get(subject_arg) or request.view_args and request.view_args.get(subject_arg) or request.args.get(subject_arg) or request.form.get(subject_arg)
            authorize(resource=resource, action=action, subject=subj_val, require_roles=roles, function=function)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def enforce_ownership(owner_arg: str = 'teacher_id', resource: str = 'reports', action: str = 'read', allow_roles: Optional[Iterable[str]] = None):
    """Decorator to enforce that the current user matches an owner identifier OR has elevated role.

    Parameters:
        owner_arg: Name of kwarg / request arg containing owner id.
        resource/action: For logging + policy alignment.
        allow_roles: Roles that can bypass ownership (defaults to head roles).
    """
    allowed_elevated = set(allow_roles or {'headteacher', 'admin', 'superadmin'})
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            owner_val = kwargs.get(owner_arg) or request.view_args and request.view_args.get(owner_arg) or request.args.get(owner_arg) or request.form.get(owner_arg)
            if not is_authenticated(session):
                abort(401, description="Authentication required")
            user_id = session.get('teacher_id')
            role = get_role(session)
            if owner_val is None:
                # Fallback to normal policy (must possess resource permission)
                authorize(resource, action)
                return fn(*args, **kwargs)
            if str(owner_val) != str(user_id) and role not in allowed_elevated:
                abort(403, description="Ownership required")
            authorize(resource, action)  # still enforce base permission for logging
            return fn(*args, **kwargs)
        return wrapper
    return decorator

__all__ = [
    'authorize', 'require_roles', 'require_permission', 'require_class_scope', 'enforce', 'enforce_subject', 'enforce_ownership'
]
