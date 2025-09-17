# Subject-Level Scope Enforcement (Phase 2)

## Overview

Phase 2 enhances the unified authorization layer by adding _subject-level_ access control. This builds on Phase 1's role + resource/action + class scope model to ensure teachers may only access subject-specific operations for the subjects they are assigned to teach.

## Key Goals

1. Prevent horizontal access to subjects a teacher is not assigned.
2. Support composite subjects (a composite parent is accessible if the teacher teaches at least one of its component subjects).
3. Maintain secure defaults: unknown/unresolvable subject => deny.
4. Preserve elevated role bypass (headteacher/admin/superadmin) for operational continuity.

## Implementation Components

1. Service: `services/subject_permission_service.py`

   - Resolves subject by ID or case-insensitive name.
   - Checks direct teacher → subject association via the `teacher_subjects` many-to-many table.
   - Supports composite subjects by allowing access when teacher is assigned to any component.
   - Defensive: returns False on resolution failure or missing teacher.

2. Authorization Integration: `security/authorization.py`

   - Added import & fallback stub for `SubjectPermissionService`.
   - New subject enforcement block executes after class scope logic:
     ```python
     if subject is not None and role in ("classteacher", "teacher"):
         if not SubjectPermissionService.check_subject_access(user_id, role, subject):
             abort(403, description="No subject access")
     ```

3. New Convenience Decorator: `enforce_subject`

   - Simplifies attaching subject validation to routes.
   - Pattern mirrors `enforce` and `require_class_scope` semantics.
   - Example:
     ```python
     @enforce_subject('marks', 'read', subject_arg='subject_name')
     def subject_marks(subject_name): ...
     ```

4. Tests: Extended `tests/test_access_control.py`
   - Added ephemeral route: `/subject/<subject_name>/view`.
   - Cases:
     - Denied for unassigned teacher.
     - Bypass success for headteacher.
     - Success after associating teacher with subject.
   - Regression tests confirm function-level permission logic unaffected.

## Security Considerations

- Secure Defaults: Unknown subject => 403.
- Least Privilege: Teachers gain only the subjects explicitly assigned.
- Composite Handling: Prevents artificial privilege escalation—still requires legitimate component assignment.
- Defense in Depth: Subject check occurs only after successful resource/action and (if present) class scope validation.

## Edge Cases Covered

1. Numeric vs string subject identifiers.
2. Composite subject access via component link.
3. Missing teacher or deleted subject -> deny.
4. Elevated roles short-circuit (authorization caller still logs access).

## Future Enhancements (Deferred)

- Subject-scoped function permissions (combine function + subject context).
- Caching layer for subject membership lookups.
- Audit log enrichment with `subject_id` or `subject_name` metadata row.
- Delegated temporary subject assignments (expiry-based) separate from core teacher mapping.

## How To Use

1. For existing routes already using `enforce`, add a direct call:
   ```python
   authorize('marks', 'read', subject=subject_name)
   ```
2. For new routes, prefer the decorator:
   ```python
   @enforce_subject('marks', 'read', subject_arg='subject_name')
   def view_subject(subject_name): ...
   ```

## Validation Status

All new tests pass alongside existing access control suite.

## Related Files

- `services/subject_permission_service.py`
- `security/authorization.py`
- `tests/test_access_control.py`

## Completion

Subject-level scope enforcement is now integrated and tested, enabling subsequent Phase 2 tasks (ownership enforcement & audit persistence) to include subject metadata.
