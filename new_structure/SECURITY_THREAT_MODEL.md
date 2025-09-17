# Security Threat Model (Initial Draft)

## 1. Assets

- Teacher Accounts (credentials, roles)
- Student Academic Data (marks, reports, assignments)
- Configuration & Permissions (role-based policies, function permissions)
- Session Cookies (`hillview_secure_session`, `hillview_session` legacy)
- Database (MySQL) schema & integrity
- Uploaded Files (marksheets)
- Audit / Security Counters

## 2. Trust Boundaries

- Browser <-> Flask (HTTPS enforced in production)
- Flask <-> MySQL (credentialed connection)
- Flask <-> Redis (rate limiting / caching; optional)
- Admin-debug separation (debug routes stripped unless explicitly enabled)

## 3. Threat Actors

- External unauthenticated attacker
- Authenticated low-privilege teacher (horizontal / vertical escalation)
- Compromised headteacher credentials
- Malicious file uploader
- Automated scanners / bots

## 4. Key Threats (OWASP Top 10 Alignment)

| OWASP A#                            | Threat                                    | Mitigation Status                                                                                               |
| ----------------------------------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| A01: Broken Access Control          | Horizontal/vertical privilege abuse       | Central authorization layer (`authorization.py`), new API ownership check, decorators, session role enforcement |
| A02: Cryptographic Failures         | Weak secret key / password exposure       | SECRET_KEY hardening + fail-fast, PBKDF2 hashing, session rotation                                              |
| A03: Injection                      | SQL injection / template injection        | ORM usage, global input validation filters, Marshmallow schema scaffold, sanitization filters                   |
| A04: Insecure Design                | Missing session rotation / debug exposure | Session rotation implemented, debug route non-registration                                                      |
| A05: Security Misconfiguration      | Weak headers / debug in prod              | Comprehensive security headers, fail-fast config validation                                                     |
| A06: Vulnerable Components          | Dependency CVEs                           | GitHub Actions `pip-audit` + pinned versions                                                                    |
| A07: Identification & Auth Failures | Session fixation / brute force            | Lockout fields, rotation, rate limiting                                                                         |
| A08: Data Integrity                 | Unauthorized class data access            | Class scope permission checks, ownership enforcement                                                            |
| A09: Logging & Monitoring Failures  | Blind attacks undetected                  | Audit counters + structured logging + correlation IDs                                                           |
| A10: SSRF / Misc (mapped)           | Path traversal / file misuse              | Path traversal middleware, upload restrictions                                                                  |

## 5. Abuse Cases & Controls

- Horizontal Teacher Data Access → Ownership check + 403.
- Privilege Escalation via Debug Routes → Routes not registered unless enabled.
- Brute Force Login → Rate limiter + lockout + audit counters.
- Session Fixation → `rotate_session()` on successful login.
- Sensitive Data in Logs → Avoid plaintext passwords / usernames in success logs.
- Dependency Exploit → Weekly `pip-audit` schedule + pinned critical libs.

## 6. Residual Risks

- Function-level permissions partially stubbed (Phase 2 expansion).
- Subject-level scoping simplified (future refinement required).
- Legacy debug artifacts still present but registration skipped—should be fully removed in future hardening.
- No automated DAST pipeline yet.

## 7. Future Enhancements

1. Expand function & subject-level permission enforcement.
2. Add JWT / API token model for programmatic access with scoped claims.
3. Integrate Bandit severity gating with CVSS parsing for pip-audit.
4. Add SAST/DAST combo (e.g., ZAP baseline scan in CI).
5. Encrypt sensitive at-rest fields (if PII growth continues) using key rotation service.
6. Formal incident response runbook + alerting pipeline (metrics export).

## 8. Validation Checklist

- [x] Security headers present (CSP, HSTS, Frame, Referrer, Permissions)
- [x] SECRET_KEY strength enforced (production fail-fast)
- [x] Rate limit health endpoint & production backend sanity check
- [x] Authorization decorators integrated in critical views
- [x] Debug route registration suppression
- [x] Session rotation test passes (cookie change detection heuristic)
- [x] Password hashing verified in tests
- [x] Dependency scanning workflow committed

## 9. Summary

Core high-risk access control, session integrity, configuration hardening, and supply chain protections are now embedded. Remaining medium-depth items focus on expanding fine-grained permission semantics, automated dynamic analysis, and security operations maturity.
