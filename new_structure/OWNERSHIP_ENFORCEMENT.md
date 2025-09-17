# Ownership Enforcement (Phase 2)

## Overview

Ownership enforcement ensures that user-specific resources (e.g., profiles, personal dashboards, drafts) are accessible only by their owner unless an elevated role overrides the restriction.

## Decorator Added

`enforce_ownership(owner_arg='teacher_id', resource='reports', action='read', allow_roles=None)`

## Behavior

1. Requires authentication.
2. Extracts `owner_arg` from kwargs / view args / query / form.
3. If owner value is absent, falls back to standard `authorize(resource, action)` to preserve logging and policy enforcement.
4. If owner does not match current session `teacher_id` and role not in elevated allow-list → 403.
5. Always invokes `authorize(resource, action)` for consistent resource/action logging.

## Elevated Roles

Default elevated bypass set: `{'headteacher', 'admin', 'superadmin'}`.
Customizable via `allow_roles` parameter.

## Test Coverage

Added ephemeral route: `/profile/<int:teacher_id>/summary` protected with:

```python
@enforce_ownership(owner_arg='teacher_id', resource='marks', action='read')
```

Why resource = `marks`? The base resource/action must be one the owning role possesses (`teacher` lacks `system_config.read`).

Scenarios:

- Owner (teacher) accessing own profile → 200
- Different teacher accessing another teacher's profile → 403
- Headteacher accessing any teacher's profile → 200

## Security Principles

- Explicit owner match prevents horizontal privilege escalation.
- Resource/action check still enforced → layered defense.
- Secure default: missing owner id triggers normal authorization (never silent allow).

## Integration Guidance

Use for any route whose semantics are user-specific:

```python
@enforce_ownership(owner_arg='teacher_id', resource='marks', action='read')
def view_personal_marks(teacher_id): ...
```

If route already requires class or subject scope, call both explicitly or layer decorators (`enforce_ownership` then subject/class logic via `authorize`).

## Future Enhancements

- Ownership metadata embedding into audit log model (planned next task).
- Ownership for student/parent resources (extend decorator with model lookup).
- Soft-deletion / tombstone checks prior to ownership validation.

## Status

Ownership enforcement is implemented, tested, and ready for extension into audit logging.
