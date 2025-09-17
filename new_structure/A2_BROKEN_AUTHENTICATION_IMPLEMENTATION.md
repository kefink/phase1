# OWASP A2: Broken Authentication Hardening

## Summary

Implemented multiple defenses to mitigate broken authentication risks:

- Account lockout: 5 failed attempts triggers 30 minute lock (`failed_login_attempts`, `locked_until`).
- Session fixation mitigation: Session cleared & rebuilt after successful login (rotate_session).
- Per-route rate limiting: `admin_login` (10/min; 3/5s), `teacher_login` & `classteacher_login` (15/min; 5/10s) plus existing default limits.
- Credential stuffing / brute-force noise reduction via combined rate limits + lockout.
- Secure metadata tracking: `last_login` timestamp recorded on success.
- Debug route gating: Blocks access to `/debug/simple_login` in non-debug environments.
- Input validation & injection defenses retained (A1) integrated with new flows.

## Files Modified

- `models/user.py`: Added new security fields and password setter guidance.
- `views/auth.py`: Added helper functions (`rotate_session`, `register_successful_login`, `register_failed_login`, `is_locked`) and integrated lockout + session rotation + rate limiting.
- `tests/test_auth_lockout.py`: Added tests for lockout threshold behavior and session rotation.
- `alembic/versions/a2_add_auth_security_fields.py`: Migration adding new columns.

## Test Coverage

Added `tests/test_auth_lockout.py`:

- `test_failed_attempts_increment_and_lockout`: Verifies failed attempt counter, lock activation, post-expiry successful reset.
- `test_session_rotation_on_login`: Verifies session cookie value changes across successive logins (rotation emulation).

## Migration

Apply migration:

```
alembic upgrade head
```

The script is additive (safe on existing data). A default of 0 is set for `failed_login_attempts` for existing rows.

## Operational Guidance

- Monitor authentication logs for repeated lockouts; consider alerting on high frequency from single IP.
- If legitimate users frequently hit lockouts, tune threshold/window (environment variables recommended for production).
- Implement future password complexity enforcement (currently placeholder len>=6 tolerance for backward compatibility).
- Consider adding exponential backoff or adaptive throttling for repeated failures beyond lockout window.

## Residual Risks / Next Steps

- Parent model not yet unified with lockout logic.
- Rate limiting storage falls back to memory if Redis unavailable (improve detection / error logging).
- Password policy not enforced (only advisory placeholder) – implement complexity & reuse checks.
- Add tests for: rate limiting breach, debug route gating (returns 404 when DEBUG False), parent login (once unified).
- Consider issuing session identifiers (server-side) if moving off signed-cookie sessions for stronger fixation mitigation & server invalidation.

## Change Log

Date: 2025-09-14
Author: Automation (GitHub Copilot)

Changes:

1. Added security fields to `Teacher` model.
2. Implemented account lockout & session rotation in auth routes.
3. Added per-route rate limiting decorators.
4. Added migration script.
5. Added and stabilized security tests (lockout & session rotation).

## Verification

All new tests passing:

```
pytest tests/test_auth_lockout.py -q  # passed
```

## Rollback Plan

- Downgrade migration: `alembic downgrade -1` (removes added columns) if necessary.
- Revert commit containing A2 hardening.

## Metrics / Instrumentation (Future)

- Track lockout events count per day.
- Track average failed attempts before success.
- Track session rotation anomalies (if any failures).
