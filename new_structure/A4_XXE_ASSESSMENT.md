## OWASP A4: XML External Entities (XXE) – Assessment

### 1. Overview

The current application (Hillview School Management System) does not actively process XML payloads. Data interchange is JSON / form based. However, proactive mitigation is introduced to prevent future insecure XML usage or third‑party library introduction that might implicitly parse XML.

### 2. Inventory

| Vector                      | Current Usage               | Notes                                          |
| --------------------------- | --------------------------- | ---------------------------------------------- |
| XML Upload Endpoints        | None                        | No import endpoints accept XML today.          |
| XML Libraries Imported      | None (pre-mitigation)       | No `xml.etree`, `lxml`, `minidom` usage found. |
| Config / Template XML Files | None                        | No `.xml` assets located.                      |
| Third-party Dependencies    | Standard Flask / SQLAlchemy | No transitive XML parsers invoked at runtime.  |

### 3. Threat Scenarios Considered

1. Future feature adds an XML import using unsafe parser → external entity expansion leaks `/etc/passwd`.
2. SSRF-like retrieval via `SYSTEM` entity causing internal network enumeration.
3. Billion Laughs / exponential entity expansion causing resource exhaustion (DoS).
4. Chained attack: unsafely parsed XML → injected values persisted → used in later template context leading to secondary exploit.

### 4. Risk Analysis

| Risk                            | Likelihood (Current) | Impact | Notes                                   |
| ------------------------------- | -------------------- | ------ | --------------------------------------- |
| External Entity File Disclosure | Low                  | High   | Blocked with proactive rejection.       |
| Entity Expansion DoS            | Low                  | Medium | Size cap + defusedxml (if available).   |
| SSRF via SYSTEM Entities        | Low                  | High   | Disallowed `<!DOCTYPE>` / `<!ENTITY>`.  |
| Future Developer Misuse         | Medium               | Medium | Mitigated by documented secure wrapper. |

### 5. Controls Selected

| Control                                    | Rationale                                                    |
| ------------------------------------------ | ------------------------------------------------------------ |
| Central secure wrapper `secure_parse_xml`  | Prevent scattered unsafe parser usage.                       |
| Pre-parse lexical DOCTYPE/ENTITY rejection | Cheap first-line defense independent of parser behavior.     |
| Size ceiling (512 KB)                      | Reduce DoS surface.                                          |
| Prefer `defusedxml` if installed           | Harden against entity expansion / known parser pitfalls.     |
| Fallback to stdlib only after pre-scan     | Maintains functionality without elevating risk.              |
| Explicit custom exception `XXEError`       | Consistent error handling & logging integration possibility. |

### 6. Gaps / Residual Risk

| Gap                                      | Justification / Mitigation Path                               |
| ---------------------------------------- | ------------------------------------------------------------- |
| No automatic logging of rejections       | Could add security audit log hook later.                      |
| No schema validation                     | Out of scope; consider XSD with secure lib if schema emerges. |
| No multi-part scanning for mixed uploads | Add if XML file uploads introduced.                           |
| defusedxml optional                      | Acceptable; wrapper blocks core XXE even w/out it.            |

### 7. Acceptance Criteria

1. Any XML containing `<!DOCTYPE`, `<!ENTITY`, or conditional sections is rejected.
2. Oversized (>512 KB) XML rejected.
3. Simple well‑formed small XML parses successfully.
4. Tests cover malicious DOCTYPE, size limit, and valid baseline.

### 8. Next Steps (Post A4)

- Add security logging for rejected XML with correlation ID (avoid dumping payloads).
- Introduce configurable size limit via environment variable.
- Add optional schema validation pipeline if business XML appears.

### 9. Conclusion

While no active XML parsing exists, establishing a hardened parsing primitive now reduces future time-to-secure for new features and prevents accidental unsafe adoption of Python’s default XML modules.
