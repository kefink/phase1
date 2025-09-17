# A10: Insufficient Logging & Monitoring - Assessment

## Scope

Evaluate current observability (logging, auditability, monitoring) against OWASP Top 10 A10 requirements.

## Current State Summary

| Aspect                     | Current Status                                                  | Gaps                                                                                                         |
| -------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Basic App Logging          | Present via `logging_config.setup_logging` and enhanced variant | No correlation IDs; inconsistent formatting between modules                                                  |
| Structured Logging         | Partial (`utils/enhanced_logging.StructuredLogger`)             | Not integrated globally; no toggle to force JSON-only mode                                                   |
| Security Event Logging     | Some wrappers (`log_security_event`) exist                      | Not automatically invoked on auth failures, permission denials, rate limit exceed, template integrity issues |
| Audit Trail (Who did what) | User action logger present                                      | No standard schema (actor, action, target, outcome, request_id); not enforced app-wide                       |
| Error Logging              | Errors captured to `errors.log`                                 | Lacks request context (request id, user id) automatically                                                    |
| Performance Metrics        | In-memory performance monitor                                   | Not exposed via endpoint; no health / saturation indicators                                                  |
| Sensitive Data Redaction   | Email/phone redaction filter exists                             | Does not cover tokens, session IDs, potential secrets                                                        |
| Monitoring & Alertability  | No thresholds / counters endpoint                               | No support for external alert integration (HTTP metrics endpoint)                                            |
| Dependency for JSON Logs   | No structlog integration                                        | Hard to standardize key ordering / add processors                                                            |

## Risks

- Incident investigations slowed due to absence of correlation IDs.
- Security-relevant events may go undetected (failed logins, permission denials) without consistent logging.
- Potential leakage of sensitive structured context without uniform redaction.
- Lack of metrics endpoint inhibits proactive monitoring (latency/error spikes).

## Recommended Remediations

1. Introduce request correlation IDs (UUID v4) injected at request start; include in all log records.
2. Centralize audit logging helper with standard fields: `timestamp, request_id, actor, action, target, outcome, ip, user_agent`.
3. Instrument authentication, authorization failures, rate limit exceeded, validation failures with security event logger.
4. Add in-memory counters (auth_failures, permission_denied, rate_limited, integrity_errors) + `/health/log-metrics` endpoint.
5. Optional JSON mode (env `ENABLE_JSON_LOGS=1`) using structlog for consistent machine parsing.
6. Improve redaction (regex for bearer/API tokens, session cookies patterns) before emission.
7. Expose performance + counters in a lightweight JSON health response (no PII).
8. Add tests verifying: request_id propagation, audit record emission on a dummy action, security log on forced auth failure.

## Acceptance Criteria

- Every request log & structured/audit event includes `request_id`.
- Auth failure triggers `security_event` log with severity mapped by count (e.g., escalation after multiple attempts).
- `/health/log-metrics` returns counters + performance snapshot without user data.
- Tests pass and no sensitive raw token output appears in captured logs.

## Deferred (Future)

- Central log shipping (e.g., ELK / OpenSearch).
- Anomaly detection (sudden spike detection) hooks.
- Async log dispatch (queue-based) for high volume.

---

(Assessment prepared for remediation phase)
