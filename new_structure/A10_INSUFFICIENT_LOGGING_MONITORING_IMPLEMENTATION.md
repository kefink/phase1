# A10: Insufficient Logging & Monitoring – Implementation

## Objectives

Provide comprehensive, structured, and actionable logging & monitoring to detect and investigate security events (auth failures, permission denials, rate limit abuses, file upload violations) while supporting traceability (request correlation IDs) and operational insight (counters endpoint, JSON logs for ingestion).

## Key Enhancements

| Feature                        | Description                                                                                                                | Files                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Correlation IDs                | Assigns `X-Request-ID` per request; included in all logs                                                                   | `__init__.py`, `logging_config.py`                                                                                     |
| Structured Audit Helper        | Single `audit_event()` function for normalized audit entries                                                               | `utils/audit.py`                                                                                                       |
| Security Event Instrumentation | Auth & role failures, permission denials, function/class/subject scope failures, rate limit exceed, file upload violations | `security/authorization.py`, `security/access_control.py`, `utils/rate_limiter.py`, `security/file_upload_security.py` |
| JSON Logging Mode              | Toggle via `ENABLE_JSON_LOGS=1`; outputs JSON lines for all handlers                                                       | `logging_config.py`                                                                                                    |
| Sensitive Data Redaction       | Email / phone patterns redacted automatically                                                                              | `logging_config.py`                                                                                                    |
| Audit & App Log Separation     | Dedicated rotating handlers: `app.log`, `audit.log`, `mark_validation.log`                                                 | `logging_config.py`                                                                                                    |
| Monitoring Counters Endpoint   | `/health/log-metrics` exposes top aggregated audit counters                                                                | `__init__.py`                                                                                                          |
| In-Memory Audit Counters       | Counts by category:action:outcome via wrapped `audit_event`                                                                | `__init__.py`                                                                                                          |
| Tests                          | Verifies request ID header, JSON logging activation, metrics endpoint shape                                                | `tests/test_logging_audit.py`                                                                                          |

## Audit Event Schema

Each audit line starts with `AUDIT` (plain mode) or JSON object (JSON mode) containing fields:

- `timestamp` (UTC ISO)
- `request_id`
- `actor` (user id if available)
- `action` (e.g., `permission_denied`, `rate_limit_exceeded`)
- `target` (resource/function/filename)
- `outcome` (`success` | `denied` | other)
- `category` (`authorization`, `auth`, `file_upload`, `rate_limit`, etc.)
- `ip`
- `user_agent`
- `severity`
- `details` (scrubbed; sensitive keys redacted; long strings truncated)

## Using `audit_event`

```python
from new_structure.utils.audit import audit_event

audit_event('custom_action', actor=user_id, target='resource:id', outcome='success', category='business', details={'extra':'value'})
```

## Enabling JSON Logs

Set environment variable before app start:

```
EXPORT ENABLE_JSON_LOGS=1  # bash
set ENABLE_JSON_LOGS=1     # Windows cmd
```

Log lines become JSON objects suitable for ingestion into ELK / Loki / CloudWatch.

## Monitoring Endpoint

`GET /health/log-metrics` returns JSON mapping of the top (<=50) counters:

```
{
  "authorization:permission_denied:denied": 3,
  "rate_limit:rate_limit_exceeded:denied": 12
}
```

Intended for lightweight dashboards and smoke visibility, not full metrics replacement.

## Extending Counters

Wrap any new sensitive action with:

```python
current_app.audit_event('data_export', actor=user_id, target=export_id, category='export', outcome='success')
```

If `current_app.audit_event` unavailable, fall back to direct `audit_event` import.

## Operational Notes

- Rotating handlers limit file growth (10MB \* 10 backups per log type).
- Redaction filter prevents accidental leakage of basic PII patterns.
- Log formatting remains human-readable unless JSON mode enabled.
- Counter storage is in-memory; resets on process restart (sufficient for development / initial observability pass). A persistent or Prometheus-backed implementation can replace this later.

## Future Hardening (Backlog)

1. Emit structured logs to external sink (e.g., syslog / OpenTelemetry).
2. Add anomaly detection hooks (sudden spike in `permission_denied`).
3. Persist counters via Redis or expose Prometheus metrics endpoint.
4. Expand redaction (JWTs, API keys by regex, numeric IDs outside allowed sets).
5. Add tracing integration (OpenTelemetry span IDs correlated with request IDs).

## Validation

- Test suite additions validate correlation header and JSON mode parser.
- Manual checks confirm audit lines in `logs/audit.log` including request IDs.

## Summary

This implementation closes OWASP A10 gaps by: (a) guaranteeing traceability through request IDs, (b) centralizing security event capture, (c) providing structured, optionally machine-ingestible logs, and (d) exposing lightweight operational counters for rapid visibility.
