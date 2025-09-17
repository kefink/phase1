"""Secure serialization utilities to phase out unsafe pickle usage.

Design Goals:
- Provide JSON-based serialization for cache/session data comprised of primitives, lists, dicts.
- Add integrity protection (HMAC-SHA256) to detect tampering.
- Enforce size and depth limits to mitigate resource exhaustion.
- Offer legacy migration helper for existing `.pickle` files (lazy upgrade upon first access).

Public API:
- serialize_to_file(obj, path, secret_key, *, version=1)
- deserialize_from_file(path, secret_key, *, max_bytes=262144, max_depth=50, require_signature=True)
- is_legacy_pickle(path) -> bool
- migrate_legacy_pickle(path, secret_key, delete_legacy=True)

Exceptions:
- SerializationError
- IntegrityError
- SizeLimitError
- DepthLimitError
- LegacyMigrationError
"""
from __future__ import annotations

import json, os, hmac, hashlib, pickle, io, stat
from typing import Any
from pathlib import Path

__all__ = [
    'serialize_to_file', 'deserialize_from_file', 'is_legacy_pickle', 'migrate_legacy_pickle',
    'SerializationError', 'IntegrityError', 'SizeLimitError', 'DepthLimitError', 'LegacyMigrationError'
]

class SerializationError(Exception):
    pass
class IntegrityError(SerializationError):
    pass
class SizeLimitError(SerializationError):
    pass
class DepthLimitError(SerializationError):
    pass
class LegacyMigrationError(SerializationError):
    pass

META_KEY = '_meta'
DATA_KEY = 'data'

ALLOWED_PRIMITIVES = (str, int, float, bool, type(None))

def _calc_depth(obj: Any, current: int = 0, max_depth: int = 50) -> int:
    if current > max_depth:
        raise DepthLimitError(f'Max depth {max_depth} exceeded')
    if isinstance(obj, (list, tuple, set)):
        for item in obj:
            _calc_depth(item, current + 1, max_depth)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _calc_depth(k, current + 1, max_depth)
            _calc_depth(v, current + 1, max_depth)
    return current

def _enforce_supported_types(obj: Any):
    if isinstance(obj, ALLOWED_PRIMITIVES):
        return
    if isinstance(obj, (list, tuple, set)):
        for item in obj:
            _enforce_supported_types(item)
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            _enforce_supported_types(k)
            _enforce_supported_types(v)
        return
    raise SerializationError(f'Unsupported type for secure serialization: {type(obj)!r}')

def _hmac_digest(secret_key: str, payload: bytes) -> str:
    return hmac.new(secret_key.encode('utf-8'), payload, hashlib.sha256).hexdigest()

def serialize_to_file(obj: Any, path: str | os.PathLike[str], secret_key: str, *, version: int = 1) -> None:
    """Serialize object to JSON with integrity metadata.
    Raises SerializationError for unsupported types.
    """
    _enforce_supported_types(obj)
    _calc_depth(obj, 0)
    data = {META_KEY: {'alg': 'HMAC-SHA256', 'ver': version}, DATA_KEY: obj}
    json_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
    sig = _hmac_digest(secret_key, json_bytes)
    data[META_KEY]['sig'] = sig
    final_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
    tmp_path = f"{path}.tmp"
    with open(tmp_path, 'wb') as f:
        f.write(final_bytes)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)
    # Restrict permissions (best effort, ignore on Windows limitations)
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass

def deserialize_from_file(path: str | os.PathLike[str], secret_key: str, *, max_bytes: int = 262144, max_depth: int = 50, require_signature: bool = True) -> Any:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(path))
    size = p.stat().st_size
    if size > max_bytes:
        raise SizeLimitError(f'File size {size} exceeds max {max_bytes}')
    raw = p.read_bytes()
    try:
        data = json.loads(raw)
    except Exception as e:
        raise SerializationError(f'Invalid JSON: {e}')
    if not isinstance(data, dict) or META_KEY not in data or DATA_KEY not in data:
        raise SerializationError('Malformed serialized structure')
    meta = data[META_KEY]
    payload_without_sig = dict(data)
    meta_no_sig = dict(meta)
    sig = meta_no_sig.pop('sig', None)
    payload_without_sig[META_KEY] = meta_no_sig
    if require_signature:
        if not sig:
            raise IntegrityError('Missing signature')
        recomputed = _hmac_digest(secret_key, json.dumps(payload_without_sig, separators=(',', ':')).encode('utf-8'))
        if not hmac.compare_digest(sig, recomputed):
            raise IntegrityError('Signature mismatch')
    obj = data[DATA_KEY]
    _calc_depth(obj, 0, max_depth)
    _enforce_supported_types(obj)
    return obj

def is_legacy_pickle(path: str | os.PathLike[str]) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    if p.suffix != '.pickle':
        return False
    # Quick heuristic: attempt limited pickle load in isolation
    try:
        with open(p, 'rb') as f:
            # Use a restricted unpickler? For now just detect readability
            pickle.Unpickler(io.BytesIO(f.read(16)))  # minimal read attempt
        return True
    except Exception:
        return False

def migrate_legacy_pickle(path: str | os.PathLike[str], secret_key: str, delete_legacy: bool = True) -> Path:
    p = Path(path)
    if not is_legacy_pickle(p):
        raise LegacyMigrationError('Not a legacy pickle file')
    # Load full pickle (trusted internal path assumption during controlled migration)
    with open(p, 'rb') as f:
        try:
            obj = pickle.load(f)
        except Exception as e:
            raise LegacyMigrationError(f'Failed to load legacy pickle: {e}')
    new_path = p.with_suffix('.jsons')
    serialize_to_file(obj, new_path, secret_key)
    if delete_legacy:
        try:
            p.unlink()
        except Exception:
            pass
    return new_path
