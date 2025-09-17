# A5 Broken Access Control Assessment

Date: 2025-09-14
Status: Discovery complete – implementation phase beginning.

## 1. Overview

The codebase implements multiple overlapping access control mechanisms:

- Legacy `access_control.py` (simple role list & object type checks)
- Enhanced `security/access_control.py` (role hierarchy + resource/action map + ownership/class checks + logging)
- Domain delegation layer: `PermissionService`, `EnhancedPermissionService` (class/stream + function-level permissions)
- Ad hoc decorators: `classteacher_required`, `teacher_or_classteacher_required`, `headteacher_required`, `admin_required` (implicit logic duplication)
- Mixed direct session role reads (e.g., `session.get('role')`) inside views.

This fragmentation increases risk of inconsistent enforcement, bypass, and future regression.

## 2. Risk Categories

| Category                      | Description                                          | Current Exposure                                                                         | Impact | Likelihood |
| ----------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------ | ---------- |
| Vertical Escalation           | Lower role accessing higher-privilege functions      | Some routes rely only on generic role presence & broad decorators                        | High   | Medium     |
| Horizontal Data Access (IDOR) | Teacher accessing unassigned grade/stream resources  | Many endpoints accept `grade`, `stream`, `student_name` without uniform permission check | High   | High       |
| Function-Level Drift          | Newly added routes forget to apply correct decorator | Manual pattern, no central registration                                                  | Medium | Medium     |
| Over-Privileged Session       | Session retains stale elevated role after change     | No revalidation of downgraded roles in-session                                           | Medium | Low        |
| Inconsistent Deny Responses   | Different abort codes/messages hamper monitoring     | Mixed `abort`, `redirect`, JSON custom messages                                          | Low    | Medium     |
| Logging Gaps                  | Unauthorized attempts not uniformly logged           | Only enhanced module logs some                                                           | Medium | Medium     |
| Confused Deputy               | Internal helper functions invoked without re-check   | Some services assume caller already validated                                            | Medium | Low        |

## 3. High-Risk Endpoint Archetypes

1. Report generation & download (`/classteacher/*report*`, `/download_*`, `/print_individual_report`, `/generate_*reports`)
2. Marks modification endpoints (`/update_class_marks`, `/edit_class_marks`, component/subject upload flows)
3. Grade / stream scoped data fetch APIs (`/get_streams_by_level`, `/get_subjects...`, analytics data endpoints)
4. Permission management (`/permission_management*` routes, grant/revoke/bulk, function permissions)
5. Staff / headteacher delegation (`staff_management`, assigning head/deputy, `assign_headteacher`, `assign_deputy_headteacher`)
6. Class / marksheet destructive actions (`/delete_marksheet`, bulk operations)

## 4. Observed Patterns & Gaps

- Role decorators vary in strategy (redirect vs abort) – inconsistent semantics (401 vs 403 vs redirect).
- Lack of a single semantic call like `authorize(resource='marks', action='write', grade=..., stream=...)` leads to hand-crafted permission logic.
- `PermissionService.check_classteacher_permission` covers only classteacher scope; plain `teacher` subject scoping absent for some endpoints (subject teacher may over-view classes via report projection endpoints).
- Ownership checks limited; student/parent features rely on simple session parent_id existence.
- No systematic test matrix ensuring denial for cross-class attempts.

## 5. Target Unified Model

Introduce `security/authorization.py` providing:

```
authorize(resource, action, *, grade=None, stream=None, subject=None, owner_id=None, require_roles=None, allow_head=True, audit=True)
```

Resolution order:

1. Session validation (auth + freshness) – reuse `AccessControlProtection.validate_session()`.
2. Role gate (if `require_roles` specified) – direct allow-list.
3. Resource/action policy (maps to or augments `AccessControlProtection.RESOURCE_PERMISSIONS`).
4. Scope enforcement:
   - Class scope: use `PermissionService.check_class_access(user_id, grade_id, stream_id)` (or existing wrapper) for `classteacher`.
   - Teacher subject scope (Phase 2 enhancement) via `RoleBasedDataService.get_accessible_subjects` if subject param present.
5. Ownership (if `owner_id` provided) with fallback to privileged roles.
6. Logging (success/deny) standard format.

Decorators:

- `@require_roles(*roles)` – minimal role gate.
- `@require_permission(resource, action)` – policy check only.
- `@require_class_scope(grade_arg='grade', stream_arg='stream')` – adds class scope enforcement.
- `@enforce(resource='marks', action='write', class_scope=True)` – composite convenience.

Return semantics:

- 401 for unauthenticated / invalid session.
- 403 for authenticated but unauthorized (policy/role/scope failure).
- JSON vs HTML response decided by `request.accept_mimetypes` or path prefix; default HTML abort for browser.

## 6. Migration & Refactor Strategy

Phase 1 (Minimal invasive):

- Implement new authorization module & decorators.
- Apply to a representative, high-risk subset (reports download, marks update, permission grant/revoke, staff head/deputy assign, delete marksheet).
- Leave legacy decorators in place for untouched routes (backwards compatible).

Phase 2 (Progressive rollout):

- Replace `classteacher_required` usage across report/marks endpoints with composite decorators combining permission + class scope.
- Add subject-level scope for plain teachers (later – after baseline stabilized).

Phase 3 (Hardening & Clean-up):

- Deprecate legacy `access_control.py` simple module; keep enhanced module but adapt to call unified functions.
- Add automated test matrix for vertical/horizontal access.

## 7. Test Plan (Initial Set)

| Test | Scenario                                                         | Expected |
| ---- | ---------------------------------------------------------------- | -------- |
| T1   | Teacher tries to download class report for unassigned grade      | 403      |
| T2   | Classteacher with permission downloads report                    | 200      |
| T3   | Headteacher downloads any report                                 | 200      |
| T4   | Unauthenticated request to marks update                          | 401      |
| T5   | Classteacher tries delete marksheet for class without permission | 403      |
| T6   | Permission grant endpoint accessed by classteacher               | 403      |
| T7   | Permission grant endpoint accessed by headteacher                | 200      |
| T8   | Staff assign headteacher endpoint by teacher                     | 403      |

## 8. Future Considerations

- Cache authorization decisions (short-lived) to reduce DB hits under load.
- Central audit sink (DB table) for deny events > threshold.
- Dynamic function permission enforcement integration into decorators (phase after baseline).
- Parent/student portal segmentation following same abstraction.

## 9. Acceptance Criteria for A5 Completion

- Central `authorization.py` module exists with documented contract.
- High-risk routes migrated (at least 5 distinct endpoints across report, marks, permission, staff, deletion domains).
- All new tests pass; no regression in existing suites.
- Assessment and implementation docs committed.
- Legacy decorators flagged with deprecation comments where overlapping.

## 10. Go / No-Go

Go – Clear duplication and risk; incremental adoption path defined with low regression risk.

---

Prepared as part of OWASP A5 remediation initiative.
