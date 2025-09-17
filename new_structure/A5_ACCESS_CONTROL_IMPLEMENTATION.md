# A5 Broken Access Control – Implementation Summary

This document complements `A5_ACCESS_CONTROL_ASSESSMENT.md` and records the concrete changes, rationale, and verification outcomes for the unified authorization rollout.

## 1. Objectives

- Consolidate fragmented access logic (legacy decorators, ad‑hoc role checks) into a single auditable layer.
- Enforce consistent responses (401 unauthenticated / 403 unauthorized).
- Introduce class-scope (grade/stream) enforcement for class/marks/report operations.
- Preserve backward compatibility while incrementally migrating high‑risk routes.

## 2. Key Artifacts

| Component                          | File                                  | Purpose                                                                                      |
| ---------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------- |
| Unified Authorization Layer        | `security/authorization.py`           | Central orchestration: role allow-list, resource/action policy, class scope, ownership hook. |
| Legacy Access Control (deprecated) | `security/access_control.py`          | Retained for untouched routes; resource permission mapping still leveraged as policy source. |
| Permission Service Extension       | `services/permission_service.py`      | Added `check_class_access(user_id, grade_id, stream_id)` for id-based scope checks.          |
| Test Coverage                      | `tests/test_access_control.py`        | Validates authentication, role gating, resource permissions, class scope enforcement.        |
| Assessment Doc                     | `A5_ACCESS_CONTROL_ASSESSMENT.md`     | Original threat model & phased plan.                                                         |
| Implementation Doc (this)          | `A5_ACCESS_CONTROL_IMPLEMENTATION.md` | Final implementation details & verification status.                                          |

## 3. Authorization Flow (Phase 1)

1. Validate session → abort 401 if unauthenticated.
2. Optional explicit role allow-list (e.g. headteacher-only) via `@require_roles` or `@enforce(..., roles=[...])`.
3. Resource/action permission lookup through `AccessControlProtection.RESOURCE_PERMISSIONS` (acts as policy registry / allow matrix).
4. Class Scope (if a grade argument is present and role in {classteacher, teacher}):
   - Resolve grade/stream IDs (numeric passthrough or name → id lookup).
   - Call `PermissionService.check_class_access` (head/admin bypass, teacher/classteacher require active `ClassTeacherPermission`).
5. (Deferred) Ownership & subject-level scoping hooks (placeholder for Phase 2 expansion).
6. Log success/failure through existing ACP logging channel for centralized audit trail.

## 4. Notable Design Choices

- Kept resource matrix in legacy module to avoid duplicating policy data; unified layer wraps it.
- Allowed `teacher` role back into `marks.write` but enforced class scope via decorator path to prevent silent global escalation while maintaining existing behavior for routes not yet migrated.
- Introduced `enforce` composite decorator to reduce repetitive boilerplate (resource + optional class scope + optional role list).
- Added (not yet broadly applied) `enforce_ownership` for future fine-grained object ownership control.

## 5. New / Modified APIs

### Decorators

- `@require_roles(*roles)` – strict role allow-list.
- `@require_permission(resource, action)` – resource/action check only.
- `@require_class_scope(...)` – attaches class scope to an operation (internal use where partial migration needed).
- `@enforce(resource, action, class_scope=..., roles=[...])` – canonical unified entrypoint.
- `@enforce_ownership(owner_arg=...)` – ownership + elevated role override (future adoption).

### Service Method

`PermissionService.check_class_access(user_id, grade_id, stream_id)`

- Returns True for elevated roles.
- Validates active, non‑expired permission record for teacher / classteacher.

## 6. Tests Implemented (`tests/test_access_control.py`)

| Test                                                    | Scenario                                  | Expected Result       | Status |
| ------------------------------------------------------- | ----------------------------------------- | --------------------- | ------ |
| `test_authentication_required`                          | Unauth access to class-scope route        | 401                   | PASS   |
| `test_role_allow_list_enforced`                         | Non-headteacher hitting headteacher route | 403 → headteacher 200 | PASS   |
| `test_class_scope_denied_without_permission`            | Classteacher w/out permission             | 403                   | PASS   |
| `test_class_scope_allowed_with_permission`              | Classteacher with granted permission      | 200                   | PASS   |
| `test_headteacher_bypasses_class_scope`                 | Headteacher no class permission record    | 200                   | PASS   |
| `test_teacher_requires_permission_same_as_classteacher` | Teacher receives class permission         | 200 after grant       | PASS   |

## 7. Known Limitations / Deferred Items

| Item                                                   | Deferral Reason                                   | Planned Phase |
| ------------------------------------------------------ | ------------------------------------------------- | ------------- |
| Subject-level scope                                    | Requires subject ↔ assignment graph consolidation | Phase 2       |
| Ownership integration across all sensitive routes      | Needs inventory & potential model changes         | Phase 2       |
| Full migration of remaining legacy-decorated endpoints | Reduce regression risk (incremental)              | Ongoing       |
| Function-level permission integration in `authorize`   | Await stabilization of EnhancedPermissionService  | Phase 2       |
| Automatic removal of debug scaffolds                   | Completed – instrumentation removed               | N/A           |

## 8. Security Impact

- Eliminates silent divergence between routes using different decorators for similar resources.
- Central logging ensures uniform audit trail for allow/deny events.
- Class scope enforcement prevents horizontal (IDOR-like) access to marks/report endpoints by teachers lacking explicit delegation.
- Clear separation of concerns allows future extension (ownership, subject scope) without re-touching route logic.

## 9. Edge Case Handling

| Edge Case                                | Handling                                                                                    |
| ---------------------------------------- | ------------------------------------------------------------------------------------------- |
| Grade name vs id                         | Dynamic resolution attempts numeric passthrough first, then name lookup.                    |
| Missing / unresolved grade               | Immediate 403 to avoid ambiguous over-permission.                                           |
| Stream provided without grade resolution | Deny (cannot validate permission reliably).                                                 |
| Expired permissions                      | `ClassTeacherPermission.has_permission` internally expires stale records before evaluation. |
| Teacher vs Classteacher roles            | Both require permission; head/admin bypass.                                                 |

## 10. Rollback / Mitigation Strategy

- Reverting to pre-unified state only requires switching route decorators back; legacy module left intact.
- Policy matrix unchanged (low blast radius); class scope enforcement can be disabled per route by toggling `class_scope=False` in `@enforce` without code removal.

## 11. Recommendations (Next Steps)

1. Expand test matrix to cover report generation endpoints (PDF downloads) with mixed roles.
2. Implement ownership-based decorator on teacher profile update/self-service endpoints.
3. Integrate function-level permission checks into `authorize` (optional argument gating).
4. Add structured audit persistence (DB or SIEM sink) for high-value access attempts.
5. Begin gradual removal / aliasing of legacy decorators after full route audit.

## 12. Verification Summary

All newly added authorization tests pass (`pytest tests/test_access_control.py`). No failing regressions observed in the access control module after class-scope adjustments and teacher role refinement.

---

Generated on: 2025-09-14
