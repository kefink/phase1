# OWASP A6: Security Misconfiguration – Assessment

## Scope

Files reviewed:

- `config.py`
- `run.py`
- `https_redirect.py`
- `logging_config.py`
- `extensions.py`

## Key Findings

1. Duplicate & Conflicting Session Settings

   - `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`, `PERMANENT_SESSION_LIFETIME` defined multiple times with different values in `Config`.
   - Secure defaults (Strict, Secure=True) overridden later (Lax, Secure=False), causing ambiguity and potential downgrade.

2. Hardcoded Weak / Placeholder Secret Key

   - `SECRET_KEY` default `'your_secret_key_here_change_in_production'` if env var missing.
   - No startup validation or warning when insecure default is used.

3. HTTPS Enforcement Implementation Gaps

   - `https_redirect.py` references `@app.before_request` but `app` not imported/defined in file (likely never executed).
   - HSTS applied only if `SECURITY_HEADERS` loaded; no fallback in dev with HTTPS enabled.

4. Debug Mode Exposure

   - `run.py` forces `app.run(debug=True, ...)` regardless of environment selection passed to `create_app`.
   - Production safeguard absent if environment variable mis-set.

5. Missing/Incomplete Security Headers

   - `ProductionConfig.SECURITY_HEADERS` missing CSP, Permissions-Policy, and Cross-Origin headers (COEP/COOP) placeholders.
   - No uniform middleware applying headers across environments (only production path).

6. CSRF & Cookie Scope

   - CSRF enabled but no SameSite=Strict in final effective config (overridden to Lax). Potential CSRF risk on newer browsers.

7. Logging Redaction Partial

   - Redaction filters email/phone; no generic pattern for tokens/API keys or potential secrets.

8. Rate Limiting Storage Inconsistency

   - `Limiter` instantiated with `storage_uri=None` then maybe overridden; risk of silent fallback to in-memory in production.

9. CORS Not Explicitly Defined

   - No CORS configuration; implicitly everything blocked or later ad-hoc with potential misconfiguration if added unsafely.

10. Secret & Credential Handling

    - MySQL password baked into source via default (encoded). Should enforce environment variable presence for production.

11. Session Lifetime Inconsistency
    - Different lifetimes (1800s vs 86400s) redefined; unclear final effective value.

## Risk Summary

| Risk                             | Impact                      | Likelihood | Priority |
| -------------------------------- | --------------------------- | ---------- | -------- |
| Debug enabled in prod            | Sensitive info disclosure   | Medium     | High     |
| Cookie secure flags inconsistent | Session hijack / CSRF       | Medium     | High     |
| Weak secret key default          | Session tampering           | High       | High     |
| Missing CSP & modern headers     | XSS / Clickjacking exposure | Medium     | Medium   |
| HTTPS redirect not active        | MITM risk                   | High       | High     |
| Credential defaults in code      | Secret leakage              | Medium     | Medium   |

## Remediation Plan (High-Level)

1. Normalize session/cookie settings in `Config`; keep single authoritative definition.
2. Add startup validator that logs error (and optionally aborts) if weak secret or default DB creds used in production.
3. Replace `https_redirect.py` with application factory hook + unified security headers middleware.
4. Add security headers middleware (CSP default deny, frame deny, referrer policy, permissions-policy placeholder).
5. Enforce `debug=False` when `FLASK_ENV=production` regardless of run script flags.
6. Add configurable allowed origins list; fail closed if unset.
7. Harden logging filter for generic credential patterns (Bearer/API key).
8. Require explicit REDIS/RATE LIMIT storage configuration in production (warn if memory backend).
9. Document all changes in implementation report.

## Next Steps

Proceed with implementation tasks: header middleware, config normalization, startup validation, tests, documentation.
