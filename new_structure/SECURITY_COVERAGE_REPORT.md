# Security Coverage Report (Interim)

Date: 2025-09-16
Scope: Core academic/reporting, permission management, selected mutation & debug endpoints.

## Control Legend

- AUTH: Role / session enforcement
- PERM: Fine-grained or assignment validation (class/subject ownership)
- RATE: Rate limiting present (limiter or in-memory helper)
- VALID: Input/path or file/schema validation
- ERR: Unified JSON error envelope (`error_response` / secure_endpoint)
- AUDIT: Structured audit logging (`audit_log` events)
- DEBUG-GATE: Disabled outside debug/test

## Recently Hardened / Enhanced (Updated)

| Endpoint                                 | Category               | Controls Implemented                                             | Notes                                                                              |
| ---------------------------------------- | ---------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `/classteacher/preview_class_report/...` | Reporting              | AUTH, PERM, VALID, ERR, AUDIT (success + metrics), RATE (in-mem) | Assignment + headteacher override enforced; timing + student/subject counts logged |
| `/classteacher/subject_report/...`       | Reporting              | AUTH, PERM, RATE, VALID, ERR, AUDIT                              | Structured logging + JSON envelope                                                 |
| `/permission/grant`                      | Permission Mgmt        | AUTH (role), RATE, VALID, ERR, AUDIT                             | `secure_endpoint` wrapper                                                          |
| `/permission/revoke`                     | Permission Mgmt        | AUTH (role), RATE, VALID, ERR, AUDIT                             | Migrated from legacy decorator                                                     |
| `/permission/grant_function`             | Function Perm          | AUTH, RATE, VALID, ERR, AUDIT                                    | Numeric teacher_id validation                                                      |
| `/permission/revoke_function`            | Function Perm          | AUTH, RATE, VALID, ERR, AUDIT                                    | Consistent audit event naming                                                      |
| `/permission/bulk_grant_functions`       | Function Perm          | AUTH, RATE, VALID (list & type), ERR, AUDIT                      | Separate rate window (20/60)                                                       |
| `/classteacher/bulk_import_subjects`     | Subject Mgmt           | AUTH, RATE, VALID (ext + cols + size), ERR, AUDIT                | CSV/Excel extensions + size limit + required cols                                  |
| `/school_setup/api/upload-logo`          | Branding               | AUTH, RATE, VALID (ext + size + mime), ERR, AUDIT                | Central file validator; image extensions & size capped                             |
| `/classteacher/test_component_upload`    | Debug                  | AUTH, DEBUG-GATE, ERR (JSON negotiation), AUDIT                  | Gated outside debug/test                                                           |
| `/classteacher/add_term_ajax`            | Term Mgmt (AJAX)       | AUTH, RATE, VALID, ERR, AUDIT                                    | Duplicate term name validation                                                     |
| `/classteacher/edit_term_ajax`           | Term Mgmt (AJAX)       | AUTH, RATE, VALID, ERR, AUDIT                                    | Prevents duplicate rename                                                          |
| `/classteacher/delete_assessment_ajax`   | Assessment Mgmt (AJAX) | AUTH, RATE, VALID (id), ERR, AUDIT                               | Force delete logic preserved                                                       |
| `/classteacher/delete_term_ajax`         | Term Mgmt (AJAX)       | AUTH, RATE, VALID, ERR, AUDIT                                    | Prevent deletion when marks exist (validator)                                      |
| `/classteacher/add_assessment_ajax`      | Assessment Mgmt (AJAX) | AUTH, RATE, VALID, ERR, AUDIT                                    | Duplicate name & weight parsing validation                                         |
| `/classteacher/edit_assessment_ajax`     | Assessment Mgmt (AJAX) | AUTH, RATE, VALID, ERR, AUDIT                                    | Duplicate rename prevention                                                        |

## High-Risk Endpoints (Pending Hardening)

| Endpoint Pattern                            | Risk Rationale                    | Needed Controls                                          |
| ------------------------------------------- | --------------------------------- | -------------------------------------------------------- |
| `/permission/*` (other than grant)          | Privilege escalation / revocation | Migrate to `secure_endpoint` + audit + rate              |
| `/classteacher/*_ajax`                      | Direct term/assessment mutations  | VALID schemas, RATE, ERR, AUDIT                          |
| `/classteacher/delete_*`                    | Destructive actions               | Confirm ownership, soft-delete? audit                    |
| `/analytics_api/*delete*`                   | Report/subject deletions          | AUTH refine, RATE, AUDIT, ERR                            |
| `/universal_bp/proxy/*`                     | Privilege proxying                | Enforce headteacher & downstream target allowlist        |
| `/upload*` (class & subject marks)          | Bulk grade data                   | File validation, RATE, AUDIT, size/type guard            |
| `/parent_*` management                      | PII exposure / link management    | AUTH consistency, RATE (brute force), AUDIT              |
| Auth routes (`*_login`, password reset)     | Brute force                       | RATE (credential stuffing), delayed timing               |
| Setup flows (`/setup/*`, `/school_setup/*`) | Initial config tampering          | One-time lockout, AUTH gating post-initialization, audit |

## Helper Coverage Status

| Helper                   | Purpose                                                              | Integration Status                                                            |
| ------------------------ | -------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `secure_endpoint`        | Unified guard (roles, rate, validation, audit, errors, debug gating) | Applied to permission AJAX set, report preview, logo upload ( >10 endpoints ) |
| `wants_json`             | Content negotiation                                                  | Used universally via `secure_endpoint` for error negotiation                  |
| `audit_log`              | Structured logging                                                   | Success + failure events; added performance metrics for report preview        |
| `validate_uploaded_file` | Central file validation (ext, size, mime)                            | Used by bulk subject import & logo upload (Phase C)                           |

## Gaps & Next Steps (Revised)

1. Propagate correlation IDs: echo `X-Correlation-ID` response header (currently only generated for audit events).
2. Extend file validation to any remaining uploads (marksheets, bulk promotions) using `validate_uploaded_file`.
3. Brute-force protection: add adaptive throttling to all login and password reset routes (Phase D).
4. Harden universal proxy: allowlist target routes, enforce headteacher role, full audit of target path.
5. Additional metrics: subject & individual report endpoints (timing, counts) + deletion events.
6. Introduce soft-delete or confirmation for destructive endpoints (`delete_report`, `delete_marksheet`).
7. Parent portal sensitive endpoints: enforce relationship validation + consistent JSON 403 envelope.
8. Finish migration of legacy decorators (residual classteacher routes) to `secure_endpoint`.
9. Replace SQLAlchemy `Query.get` legacy usages with `Session.get` to reduce deprecation noise (non-security hygiene).

## Recommended Prioritization (Risk-Aligned)

1. Permission & destructive delete endpoints (privilege misuse risk).
2. Upload / bulk mutation endpoints (data integrity risk).
3. Login & auth-related brute force protections.
4. Proxy / headteacher universal access consolidation.
5. Parent management & linking operations.
6. Debug/test route purge or gating finalization.

## Metrics to Track (Post Full Rollout)

- Unauthorized attempts per endpoint (daily)
- Rate limit activations (should remain low; spikes indicate abuse)
- Error envelope integrity (percentage of 4xx/5xx using JSON format)
- Mean time to detect (MTTD) unauthorized pattern (via logs)
- Coverage: percentage of endpoints wrapped with `secure_endpoint`

## Appendix: Audit Event Naming Conventions

`<domain>.<action>:<phase>` where phase ∈ {`success`, `forbidden_role`, `invalid`, `rate_limited`, `error`}

Example: `permission.grant:forbidden_role`, `subjects.bulk_import:success`.

---

Interim report complete. Next milestone: expand helper adoption and add validation schemas to term/assessment AJAX routes.
