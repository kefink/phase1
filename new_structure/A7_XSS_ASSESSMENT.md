# OWASP A7: Cross-Site Scripting (XSS) – Assessment

Date: 2025-09-14
Scope: Server-side templates, debug routes, user-supplied data rendering, CSP posture, custom filters.

## Context
Application uses Jinja2 (autoescape enabled by default for `.html`) plus numerous large composite templates. CSP is present but currently permissive (`'unsafe-inline'` for scripts & styles), so DOM-based or reflected XSS relies primarily on server-side encoding discipline.

## Discovery Method
- Grep for dangerous Jinja constructs: `|safe`, `Markup(`
- Scan templates for inline `<script>` blocks embedding unescaped variables.
- Review debug/admin routes building raw HTML strings (string concatenation).
- Examine CSP configuration for mitigation strength.

## Key Findings
1. Liberal `|safe` Usage for Message Slots
   - Templates: `classteacher.html`, `classteacher/dashboard.html`, `classteacher/simplified.html`, `manage_students.html` embed `error_message|safe` / `confirmation_message|safe`.
   - Risk: If any message originates from unsanitized user input (e.g., reflected query parameter, form field error echo), attacker can inject HTML/JS.

2. JavaScript String Interpolation with `|safe`
   - `manage_students.html`: `const successMessage = "{{ success_message|safe if success_message else '' }}";` and same for `errorMessage`.
   - Risk: Break out of JS string context -> execute arbitrary script (stored or reflected).

3. Component Template Raw HTML Injection
   - `_components/metrics.html` uses `icon_svg|safe` and `buttons|safe`.
   - Risk: If upstream source is not strictly curated (e.g., dynamic admin-provided SVG/HTML), potential SVG-based script injection or event handler attributes.

4. Debug Routes Produce Raw HTML via String Concatenation
   - In `__init__.py` multiple debug endpoints (`/debug/check_users`, `/debug/add_kevin`, `/debug/blueprints`, etc.) assemble HTML with database-derived values (e.g., usernames, passwords) without escaping.
   - Risk: Stored XSS if an attacker can register or modify teacher names, subjects, etc. Debug routes may not be production exposed but defense-in-depth warranted.

5. CSP Weaknesses
   - Current CSP includes `'unsafe-inline'` and `'unsafe-eval'` for `script-src` plus multiple CDNs.
   - Risk: Inline script execution allowed; mitigates little against XSS payload once injected. Nonce/hashed approach absent.

6. Lack of Central Sanitization Abstraction
   - No common helper for safe HTML subsets (e.g., limited tags). Ad hoc `|safe` usage encourages bypassing autoescaping.

7. Potential JSON Embedding Without `|tojson` Filter
   - Some templates may embed Python objects in inline JS without `|tojson` (not yet enumerated) increasing risk of improper escaping.

## Risk Rating (Representative)
| Vector | Likelihood | Impact | Priority |
|--------|------------|--------|----------|
| Reflected XSS via error/confirmation messages | Medium | High | High |
| Stored XSS via debug route listing data | Medium | Medium | Medium |
| SVG/HTML injection in metrics components | Low→Medium (depends on source) | High | Medium |
| CSP overly permissive (unsafe-inline) | High | Defense only | High |
| Inline JS variable interpolation with `|safe` | Medium | High | High |

## Root Causes
- Over-reliance on `|safe` as a convenience for controlled messages without guaranteeing their provenance.
- Absence of a formal sanitization whitelist (e.g., bleach) for rich content.
- Permissive CSP fails to provide a second barrier.
- Large monolithic templates encourage inline scripting patterns.

## Recommended Remediations
1. Replace direct `error_message|safe` / `confirmation_message|safe` with a dedicated filter: `|sanitize_html` that strips scripts & dangerous attributes (bleach allowlist) OR remove `|safe` and ensure upstream text is plain.
2. For JS string embedding, use `|tojson` (e.g., `const errorMessage = {{ error_message|tojson }};`) eliminating manual quoting + removing `|safe`.
3. Create `sanitize_html` Jinja filter using `bleach` (allow tags: `b`, `strong`, `i`, `em`, `br`, `ul`, `ol`, `li`, `span`, `p`, simple `a` with `href` + rel noopener) and auto-strip everything else.
4. Wrap `icon_svg` and `buttons` sources with provenance check: only pass trusted static literals; otherwise sanitize as SVG (or pre-render server-side templates not relying on `|safe`). Consider renaming context variables to `trusted_icon_svg` to signal trust boundary.
5. Refactor debug routes to use `flask.render_template` with escaped context or apply `html.escape` on dynamic insertions. At minimum, escape user fields.
6. Introduce CSP tightening roadmap: Phase 1 remove `'unsafe-eval'`, Phase 2 add nonce for inline essential blocks, Phase 3 drop `'unsafe-inline'`.
7. Add tests:
   - Attempt to inject `<script>alert(1)</script>` into an error message; ensure sanitized output shows escaped `<script>` tags and does not execute.
   - JS context injection test ensures quotes / angle brackets properly escaped using `|tojson`.
   - Stored XSS simulation in debug listing route.
8. Add implementation & policy docs: `A7_XSS_IMPLEMENTATION.md`.

## Acceptance Criteria (Remediation Phase)
- No remaining use of raw `|safe` for user-influenced message channels.
- Sanitization filter present & unit tested.
- JS string embedding uses `|tojson` exclusively.
- CSP policy updated (unsafe-eval removed) & documented; plan filed for nonce migration.
- All new tests pass.

## Next Step
Proceed to implement sanitization utility + template refactors per plan.

---
Generated automatically as part of A7 security hardening cycle.
