# OWASP A3: Sensitive Data Exposure – Assessment & Inventory

Date: 2025-09-14
Scope: Hillview School Management System (current codebase snapshot)

## 1. Data Classification Inventory

| Data Type                        | Examples / Columns                                                | Sensitivity | Location(s)                            | At Rest Protection                        | In Transit                             | Notes                                                 |
| -------------------------------- | ----------------------------------------------------------------- | ----------- | -------------------------------------- | ----------------------------------------- | -------------------------------------- | ----------------------------------------------------- |
| Authentication Secrets           | `Teacher.password` (hashed), session cookie                       | High        | DB (teacher table), client cookie      | PBKDF2 hash (OK), cookie unsigned content | HTTPS intended (force disabled in dev) | Password hashing OK; cookies not marked Secure in dev |
| Personal Identifiable Info (PII) | Teacher names, `email`, `phone`, student names, admission numbers | High        | Multiple tables (`teacher`, `student`) | Plaintext                                 | TLS only if FORCE_HTTPS enabled        | Consider field-level encryption for phone/email       |
| Academic Records                 | Marks, reports, assignments                                       | Medium      | `mark`, reporting tables               | Plaintext                                 | TLS intention                          | Aggregate risk of profiling                           |
| Configuration / Secrets          | `SECRET_KEY`, DB creds in `Config`                                | High        | `config.py`, env vars                  | Hardcoded fallback present                | N/A                                    | Hardcoded MySQL password default risk                 |
| Session Data                     | `hillview_secure_session` cookie                                  | High        | Browser                                | Signed only                               | TLS needed                             | Lax SameSite; not Secure in dev                       |
| System Metadata                  | Timestamps, login attempts                                        | Medium      | `teacher` table                        | Plaintext                                 | TLS intention                          | Could reveal behavior patterns                        |
| Email Templates                  | Template variables                                                | Low         | FS (`templates/`)                      | N/A                                       | N/A                                    | Potential injection if not sanitized                  |

## 2. Current Protective Controls

- Passwords hashed using Werkzeug PBKDF2 (strong default iterations)
- CSRF protection for forms (WTF-CSRF) except debug routes
- Rate limiting and lockout (A2) reducing brute-force risk
- Some security headers (when not stripped in dev) – HSTS, CSP, etc.
- Session cookie HTTPOnly & SameSite=Lax configured

## 3. Gaps / Weaknesses

| Gap                                                                 | Impact                                       | Priority |
| ------------------------------------------------------------------- | -------------------------------------------- | -------- |
| Hardcoded SECRET_KEY fallback in `Config`                           | Predictable sessions if unchanged in prod    | Critical |
| Hardcoded MySQL password default                                    | Credential disclosure risk                   | Critical |
| No runtime enforcement requiring SECRET_KEY sourced from env (prod) | Misconfiguration silent failure              | High     |
| FORCE_HTTPS disabled in dev; no auto elevation in prod if mis-set   | Downgrade/ MITM risk                         | High     |
| No encryption for PII (email/phone)                                 | Database compromise exposes raw contact info | High     |
| No automatic redaction in logs                                      | Possible leak of usernames / context         | Medium   |
| Debug routes expose system info if DEBUG accidentally on            | Info disclosure                              | Medium   |
| No check for weak default passwords in seed data                    | Account takeover / lateral movement          | Medium   |
| No retention/anonymization strategy for historical marks            | Long-term privacy risk                       | Low      |

## 4. Proposed A3 Mitigations (Phase 1)

| Control                                  | Description                                                                           | Scope          | Effort | Risk Reduction |
| ---------------------------------------- | ------------------------------------------------------------------------------------- | -------------- | ------ | -------------- |
| Secret Enforcement                       | Fail fast if SECRET_KEY or DB password uses known placeholder patterns in non-testing | App factory    | Low    | High           |
| Config Sanitization                      | Remove inline default DB password for production; require env override                | Config         | Low    | High           |
| Field-Level Encryption (Optional Toggle) | Encrypt Teacher.email & phone using Fernet if DATA_ENCRYPTION_KEY provided            | Model events   | Medium | High           |
| Secure Cookie Hardening                  | Force `SESSION_COOKIE_SECURE=True` in prod regardless of config fallback              | App factory    | Low    | Medium         |
| Production HTTPS Guard                   | Auto-enable FORCE_HTTPS if ENV=production and not explicitly disabled                 | App factory    | Low    | Medium         |
| Sensitive Logging Filter                 | Central log filter to redact values matching email/phone/username patterns            | logging_config | Medium | Medium         |
| Weak Secret Detector Test                | Pytest check failing build if placeholder secret present                              | tests          | Low    | High           |
| Data Protection Documentation            | Implementation & operational guide                                                    | Docs           | Low    | Support        |

## 5. Field-Level Encryption Design (Optional)

- Use `cryptography` Fernet (AES-128 in GCM with HMAC) for simplicity and authenticated encryption.
- Key loaded from env: `DATA_ENCRYPTION_KEY` (base64 32-byte key). If absent → encryption disabled (graceful).
- Columns: `teacher.email`, `teacher.phone` (store ciphertext base64). Detect already-encrypted by prefix `enc:`.
- SQLAlchemy event listeners: before_flush encrypts; after_load decrypts (in-memory only).
- Backward compatibility: If plaintext found and key available → encrypt on next update.

## 6. Acceptance Criteria (Phase 1 Implementation)

- Application refuses to start in production if SECRET_KEY or DB password uses default placeholder pattern.
- Session cookie flagged Secure + HttpOnly + SameSite=Lax (or Strict) in production.
- Optional encryption: When key set, newly saved teacher emails & phones stored as ciphertext (unit test verifies roundtrip).
- Tests detect placeholder secrets.
- Documentation describing controls & residual risks.

## 7. Out-of-Scope (Defer)

- Full database transparent encryption / TDE
- At-rest encryption for large academic datasets
- Automatic retroactive encryption migration for existing PII
- Key rotation & KMS integration

## 8. Next Steps After Phase 1

- Add encryption for student PII (names, admission numbers) with pseudonymization option.
- Implement structured audit logging for access to decrypted values.
- Introduce configurable retention & purge policies.
- Integrate dynamic secrets management (HashiCorp Vault or AWS KMS).

## 9. Risk Reassessment Post-Implementation (Expected)

| Risk                                           | Current | Target                                  |
| ---------------------------------------------- | ------- | --------------------------------------- |
| Secret leakage via hardcoded defaults          | High    | Low                                     |
| PII exposure on DB dump                        | High    | Medium (teachers only encrypted)        |
| Session hijack over HTTP                       | Medium  | Low (Secure cookie + HTTPS enforcement) |
| Credential replay using predictable SECRET_KEY | High    | Low                                     |

## 10. Validation Strategy

- Pytest: configuration validation & encryption roundtrip
- Manual: Start app without env secrets in production mode → fails fast
- DB inspection: Confirm encrypted values when key set

---

Prepared as foundation for A3 implementation tasks.
