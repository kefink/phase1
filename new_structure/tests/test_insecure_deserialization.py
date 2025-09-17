import os
import json
import tempfile
import pytest
from utils.serialization import (
    serialize_to_file,
    deserialize_from_file,
    IntegrityError,
    SizeLimitError,
    DepthLimitError,
    SerializationError,
)

SECRET = 'test-secret-key'


def test_round_trip_serialization(tmp_path):
    data = {'numbers': [1,2,3], 'info': {'a': True, 'b': None}}
    target = tmp_path / 'cache.jsons'
    serialize_to_file(data, target, SECRET)
    loaded = deserialize_from_file(target, SECRET)
    assert loaded == data


def test_signature_tampering_detected(tmp_path):
    data = {'value': 'x'}
    target = tmp_path / 'sig.jsons'
    serialize_to_file(data, target, SECRET)
    # Load JSON, surgically modify the signature so structure stays valid
    raw = target.read_text()
    parsed = json.loads(raw)
    sig = parsed['_meta']['sig']
    # Flip first hex nibble deterministically
    flipped = ('0' if sig[0] != '0' else '1') + sig[1:]
    parsed['_meta']['sig'] = flipped
    target.write_text(json.dumps(parsed, separators=(',', ':')))
    with pytest.raises(IntegrityError):
        deserialize_from_file(target, SECRET)


def test_size_limit_enforced(tmp_path):
    data = {'blob': 'x' * 300000}
    target = tmp_path / 'big.jsons'
    serialize_to_file({'blob': 'x' * 10}, target, SECRET)  # ok
    # Manually create an oversized file
    target.write_bytes(b'x' * 300001)
    with pytest.raises(SizeLimitError):
        deserialize_from_file(target, SECRET, max_bytes=262144)


def test_depth_limit_enforced(tmp_path):
    # Create nested structure deeper than 50
    nested = current = {}
    for i in range(52):
        nxt = {}
        current[str(i)] = nxt
        current = nxt
    target = tmp_path / 'deep.jsons'
    with pytest.raises(DepthLimitError):
        serialize_to_file(nested, target, SECRET)


def test_unsupported_type_rejected(tmp_path):
    class X: pass
    target = tmp_path / 'obj.jsons'
    with pytest.raises(SerializationError):
        serialize_to_file({'x': X()}, target, SECRET)
