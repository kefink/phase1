# Rate Limiting Storage Update

We have transitioned from implicit in-memory rate limiting to an explicit, configurable storage backend setup using Redis (with graceful fallback).

## Key Changes

- Added `RATE_LIMIT_STORAGE_URI` configuration (auto-generated from REDIS\_\* environment variables).
- Backwards compatibility maintained via `RATELIMIT_STORAGE_URL` for older patterns.
- Updated `extensions.py` to select storage URI deterministically and avoid implicit warnings.
- Added test `tests/test_rate_limiter_storage.py` ensuring:
  - Storage URI is explicitly set.
  - Rate limits are enforced.
- Introduced `Flask-Limiter==3.5.0` pin in `requirements.txt` for reproducibility.

## Environment Variables

| Variable                 | Purpose                                                           | Default                |
| ------------------------ | ----------------------------------------------------------------- | ---------------------- |
| `REDIS_HOST`             | Redis host                                                        | `localhost`            |
| `REDIS_PORT`             | Redis port                                                        | `6379`                 |
| `REDIS_DB`               | Redis DB index                                                    | `0`                    |
| `REDIS_PASSWORD`         | Redis auth (optional)                                             | _(empty)_              |
| `RATE_LIMIT_STORAGE_URI` | Override full storage URI                                         | (auto-computed)        |
| `REDIS_DISABLED`         | Force memory fallback when `1`                                    | _(unset)_              |
| `FORCE_REDIS`            | Force Redis usage during tests                                    | _(unset)_              |
| `ALLOW_IN_MEMORY_LIMITS` | Temporary prod override allowing memory backend (NOT recommended) | _(unset / disallowed)_ |

## Fallback Logic

Priority order when choosing storage:

1. Explicit `RATE_LIMIT_STORAGE_URI` env or app config.
2. If `REDIS_DISABLED=1` or running under pytest without `FORCE_REDIS`, use `memory://`.
3. Otherwise assume `redis://localhost:6379/0`.

### Runtime Behavior Details (Post-Refactor)

- A **single fast probe** (300ms connect + ping budget) is executed at import time only if a Redis URI is selected.
- On any exception during that probe, we immediately fall back to `memory://` and log exactly **one** warning:
  `Redis unavailable during initialization; using in-memory rate limiting`.
- No further Redis connection attempts are made during the request lifecycle when fallback occurs—this prevents the repeated stack traces previously observed in the traceback you supplied.
- The final backend actually used is logged once during `configure_rate_limiter(app)` as:
  `Rate limiter storage active: memory://` (or the redis URI on success).
- If an explicit Redis URI was forced (via `FORCE_REDIS=1`) and Redis is down, the system still degrades gracefully to memory rather than crashing startup.

### Test Alignment

`tests/test_rate_limiter_storage.py` asserts that:

- An explicit storage URI is present in `app.config` (`RATE_LIMIT_STORAGE_URI` or `RATELIMIT_STORAGE_URL`).
- The limiter's internal `_storage_uri` matches this configured value after `configure_rate_limiter` runs.

This is satisfied because the chosen URI (after fallback) is also injected into configuration when necessary (memory override when original config was redis but probe failed).

### Operational Notes

- In multi-instance / horizontal scaling scenarios, `memory://` provides per-process limits only; switch to Redis (or another distributed backend) in production for global rate enforcement.
- To silence Redis warnings in a development environment without running Redis, simply set `REDIS_DISABLED=1` (or rely on implicit pytest behavior).
- To force exercising Redis logic in tests/CI (e.g., integration environment), start a Redis container/service and set `FORCE_REDIS=1`.

### Future Hardening Ideas

- Add a periodic health re-check (circuit breaker) to promote back to Redis automatically when it becomes available (currently we do a single decision at import time for determinism).
- Emit Prometheus-friendly metric for active limiter backend (e.g., `limiter_backend{type="memory"} 1`).
- Support alternative backends (Memcached, Mongo) via configuration abstraction.

## New Health Endpoint

Endpoint: `GET /health/rate-limiter`

Sample JSON (development fallback):

```
{
  "backend": "memory://",
  "distributed": false,
  "enabled": true,
  "default_limit": "100 per hour",
  "enforcement_active": false,
  "redis": { "status": "not-redis" },
  "status": "ok"
}
```

Sample JSON (production with healthy Redis):

```
{
  "backend": "redis://redis:6379/1",
  "distributed": true,
  "enabled": true,
  "default_limit": "200 per hour",
  "enforcement_active": true,
  "redis": {
    "status": "up",
    "info": {
      "used_memory_human": "3.12M",
      "used_memory": 3276800,
      "connected_clients": 12
    },
    "error": null
  },
  "status": "ok"
}
```

If production starts with a memory backend (and `ALLOW_IN_MEMORY_LIMITS` is not set), startup will abort with a clear error to prevent accidental non-distributed deployment.

## Recent Activity Fallback

The headteacher universal dashboard now falls back to an “all‑time last 10 uploads” query if no marks were found in the last 7 days. Fallback entries append `(all-time fallback)` in their description to distinguish them from windowed results.

## SECRET_KEY Policy Update

- Production: Application aborts on weak `SECRET_KEY` (length < 24 or containing: changeme, secret, dev, etc.).
- Non-production: Weak keys are auto-upgraded to a generated 64 hex char value persisted at `instance/secret_key.txt` (ephemeral if persistence fails).
- To set manually: export `SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")` before startup.

## Production Backend Requirement

Running with `memory://` in production now causes startup failure unless `ALLOW_IN_MEMORY_LIMITS=1` is explicitly provided (intended only for emergency maintenance). Always supply a Redis URI (or other supported distributed storage) for horizontally scaled deployments.

## Usage Notes

- In production set `RATE_LIMIT_STORAGE_URI` explicitly (e.g., `redis://:password@redis-host:6379/2`).
- For local dev without Redis, no change needed; fallback to `memory://` automatically and no warning spam.
- To simulate Redis in tests, set `FORCE_REDIS=1` and ensure a Redis server is reachable.

## Future Enhancements

- Expose limiter metrics endpoint.
- Add circuit-breaker if Redis becomes unavailable mid-flight.
- Promote per-route dynamic limits via configuration.

---

This update removes the earlier runtime warning about implicit in-memory rate limiting and prepares the application for scalable distributed rate limiting.
