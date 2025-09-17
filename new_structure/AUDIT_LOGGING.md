# Audit Logging (Phase 2)

## Objective

Persist every authorization decision (success or denial) for security monitoring, anomaly detection, and forensics.

## Components

1. Model: `models/access_audit.py` (`AccessAudit`)
   - Fields: user_id, role, resource, action, success, ip_address, function, grade_id, stream_id, subject, owner_id, message, created_at.
   - Method: `AccessAudit.record(**kwargs)` handles insertion with rollback safety.
2. Integration: `AccessControlProtection.log_access_attempt`
   - After logging to standard logger, now writes an `AccessAudit` row.
   - Fail-safe: Swallows DB exceptions (`debug` level trace) to avoid impacting request flow.

## Captured Data

| Field              | Purpose                                                              |
| ------------------ | -------------------------------------------------------------------- |
| user_id            | Actor performing the action (nullable for unauthenticated attempts). |
| role               | Snapshot of role at time of attempt.                                 |
| resource           | Canonical resource name (post-alias).                                |
| action             | CRUD-like or semantic action.                                        |
| success            | Boolean outcome. Indexed for quick querying.                         |
| ip_address         | Source IP for correlation.                                           |
| function           | (Optional) Function-level permission target.                         |
| grade_id/stream_id | Class scope context.                                                 |
| subject            | Subject context (string).                                            |
| owner_id           | Ownership target when applicable.                                    |
| message            | Future flexible annotation slot.                                     |
| created_at         | Server timestamp. Indexed for temporal queries.                      |

## Usage Examples

Query last 50 denied attempts:

```python
AccessAudit.query.filter_by(success=False).order_by(AccessAudit.id.desc()).limit(50).all()
```

Aggregate success ratio:

```python
from sqlalchemy import func
total = AccessAudit.query.count()
denied = AccessAudit.query.filter_by(success=False).count()
print(f"Denied rate: {denied/total:.2%}")
```

## Testing

Test added: `test_audit_log_records_success_and_denial`

- Verifies a denied then successful class-scoped access produces two rows.
- Asserts latest row has `success=True` and resource prefix.

## Future Enhancements

- Enrich with latency / response code.
- Add structured JSON export endpoint for SIEM ingestion.
- Batch write strategy or async queue to reduce transaction overhead under load.
- Add index on (resource, action, created_at) once volume justifies.
- Include correlation id / request id for multi-layer tracing.

## Status

Audit logging persistence integrated and validated. Ready for analytics or alerting extensions.
