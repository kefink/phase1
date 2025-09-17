# A8: Insecure Deserialization Implementation
Date: 2025-09-14

## Objectives
Eliminate unsafe Python `pickle` deserialization risk for cache layers; introduce integrity-protected, size + depth constrained JSON serialization; provide backward-compatible migration for existing `.pickle` cache artifacts; add defensive tests.

## Changes Implemented
1. Secure Serialization Module (`utils/serialization.py`):
   - Functions: `serialize_to_file`, `deserialize_from_file`, `is_legacy_pickle`, `migrate_legacy_pickle`.
   - Protections: HMAC-SHA256 signature (`_meta.sig`), max size (configurable per call), depth and type enforcement (only primitives, list/tuple/set, dict).
   - Atomic write with temp file + permission tightening.
   - Exceptions for clarity (IntegrityError, SizeLimitError, DepthLimitError, SerializationError, LegacyMigrationError).

2. Cache Services Refactor:
   - `services/cache_service.py` and `services/admin_cache_service.py` now write new cache entries as `.jsons` using secure serialization.
   - Read path prefers `.jsons`; if only legacy `.pickle` present, it is loaded once and migrated via `migrate_legacy_pickle` (pickle then removed by migration helper).
   - Fallback / failure: serialization exceptions silently skip caching (fails closed, not open to RCE).

3. Analytics & Reports Migration:
   - Both report and analytics caches now integrity-protected.
   - Admin dashboard + subject list caches similarly migrated.

4. Tests Added (`tests/test_insecure_deserialization.py`):
   - Round trip serialization success.
   - Signature tampering detection (IntegrityError).
   - Size limit enforcement (SizeLimitError).
   - Depth limit enforcement (DepthLimitError).
   - Unsupported type rejection (SerializationError).

## Risk Mitigation Mapping
| Risk | Mitigation |
|------|------------|
| Arbitrary code execution via malicious pickle | Migration to JSON primitives + signature + type whitelist; legacy pickle only loaded from controlled internal path then removed. |
| Silent tampering / cache poisoning | HMAC-SHA256 signature verification on load. |
| Resource exhaustion (huge file) | Max byte size check in `deserialize_from_file`. |
| Deep nesting DoS | Depth calculation + limit. |
| Unsupported complex object reconstitution | Explicit type whitelist rejects objects. |

## Operational Notes
- Secret key: uses Flask `SECRET_KEY` (falls back to `'dev-secret'` if unset, recommended to ensure SECRET_KEY configured in production).
- Existing `.pickle` files are automatically migrated lazily during first access of each key; operators may run a cleanup script to confirm zero remaining `.pickle` files post warm-up.
- New files use `.jsons` extension to distinguish signed JSON from legacy `.json` or `.pickle`.

## Follow-Up / Hardening Opportunities
- Centralize secret retrieval (avoid repeating `current_app.config.get('SECRET_KEY')`).
- Add configurable global limits (size/depth) via app config rather than function parameters defaults.
- Add monitoring/logging for IntegrityError occurrences (possible tamper attempts).
- Provide CLI utility to bulk migrate and purge `.pickle` offline.

## Verification
All new tests pass (see test file). Full suite pending final run after integration.

## Conclusion
Insecure deserialization vector via `pickle` has been effectively neutralized for caching layers by transitioning to a constrained, integrity-protected JSON serialization approach with backward-compatible migration and test coverage.
