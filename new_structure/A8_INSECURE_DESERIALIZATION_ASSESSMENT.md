# A8: Insecure Deserialization Assessment

Date: 2025-09-14
Scope: Server-side Python code, client-provided data handling, caching/session utilities, ancillary scripts.

## Summary
The application uses Python `pickle` extensively for server-side caching of computed report/admin datasets (`services/admin_cache_service.py`, `services/cache_service.py`, `utils/cache_manager.py`, `utils/session_manager.py`). While current usage appears to serialize only server-generated structures, any exposure of these pickle files to user tampering (path traversal, predictable cache keys, direct download) would enable remote code execution (RCE) upon `pickle.load`. No YAML unsafe loaders or custom eval-based deserialization were found. JSON handling uses the safe `json` module (not inherently unsafe) but lacks guards against excessively large or nested payloads (potential resource exhaustion). No `marshal`, `dill`, or `ast.literal_eval` usage on user data detected. One occurrence of `eval` is present only inside a test vector in `security_verification.py` (benign).

## Findings Detail

### 1. Pickle-Based Cache Layers (High Risk if Attack Surface Exposed)
Files:
- `services/admin_cache_service.py`
- `services/cache_service.py`
- `utils/cache_manager.py`
- `utils/session_manager.py`

Patterns:
- `pickle.dump()` and `pickle.load()` on local filesystem paths derived from cache keys.

Risks:
- If an attacker can influence cache file contents (upload/overwrite) or cause the application to read an arbitrary file path (path traversal via cache key), they can craft a malicious pickle leading to code execution.
- Predictable cache key naming (e.g., `<key>.pickle`) may enable planting or swapping files if write access is obtained through another vulnerability.

### 2. Absence of Safer Serialization Abstractions
- No wrapper enforcing a strict allowlist of types or moving to a JSON-based representation for simple data structures.
- Repeated pickle logic duplicates risk and complicates future migration.

### 3. Lack of Integrity / Freshness Validation
- No HMAC/signature on serialized blobs.
- No versioning or schema hash to prevent confusion attacks (feeding stale but valid pickle data to alter logic outcomes).

### 4. Large JSON Payload Handling (Moderate)
- `json.loads` used directly without size / depth guard. Potential vector: memory exhaustion or performance degradation if large or deeply nested JSON is accepted from user-controlled sources. (Need to confirm actual sources of these inputs – assumed potential risk.)

### 5. YAML / Other Formats (None Found)
- No `yaml.load` / `yaml.safe_load` usage; no `marshal` / `dill` / `ujson` custom hooks.

## Risk Ranking
| Finding | Likelihood | Impact | Risk |
|---------|------------|--------|------|
| Unprotected pickle deserialization | Medium (depends on file write exposure) | Critical (RCE) | High |
| Lack of integrity/signature on cache blobs | Medium | High | High |
| Large JSON payload handling | Medium | Medium | Medium |
| Absence of safer abstraction layer | High (code complexity) | Medium | Medium |

## Recommended Remediations
1. Introduce a secure serialization module:
   - Replace `pickle` with JSON for supported data types.
   - For complex objects, serialize to primitive dict/list forms; prohibit arbitrary class instance pickling.
   - Provide `secure_dump(obj)` / `secure_load(path)` with HMAC (e.g., using an `APP_SECRET_KEY`).
2. Transitional Compatibility:
   - Implement detection: if existing `.pickle` file found, load once (legacy path), re-write as new `.jsons` (signed JSON) then remove old pickle.
3. Cache Key Hardening:
   - Enforce regex allowlist for cache keys, rejecting path separators or suspicious patterns.
4. Integrity Protection:
   - Append or store alongside JSON: `{"_meta": {"alg": "HMAC-SHA256", "sig": "...", "ver": 1}, "data": <payload>}`.
5. Size & Depth Guards:
   - Reject payloads exceeding a configurable byte size (e.g., 256KB) or nesting depth > 50.
6. Add tests:
   - Attempt loading a malicious pickle file (expect refusal / exception).
   - Oversized JSON input should raise controlled error.
   - Tampered signature should cause verification failure.
7. Document migration & provide operational script to purge residual `.pickle` files after rollout.

## Out of Scope (For Now)
- Full encrypted at-rest storage (can be added; integrity currently prioritized).
- Alternative formats like MessagePack unless performance becomes concern.

## Next Steps
Proceed to implement secure serialization utilities, refactor cache services to adopt them, create migration logic for legacy pickle files, and add protective tests.
