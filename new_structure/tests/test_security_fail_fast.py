import os
import sys
import pytest
from importlib import import_module

pytestmark = pytest.mark.nodb

# NOTE: Intentionally no 'app' fixture here to prevent pytest-flask plugin
# autouse fixtures from pushing a request context or expecting a full Flask app.

def _purge_new_structure_modules():
    for mod in list(sys.modules.keys()):
        if mod.startswith('new_structure'):
            del sys.modules[mod]

def test_fail_fast_weak_secret_rejected(monkeypatch):
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', 'weak')
    monkeypatch.setenv('REDIS_DISABLED', '1')
    _purge_new_structure_modules()
    ns = import_module('new_structure')
    with pytest.raises(RuntimeError) as exc:
        ns.create_app('production')
    assert 'SECRET_KEY' in str(exc.value)
    for var in ['FLASK_ENV','SECRET_KEY','REDIS_DISABLED']:
        os.environ.pop(var, None)

def test_fail_fast_memory_backend_blocked_without_override(monkeypatch):
    strong = 'a4f9b2c7d8e1f3a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9'
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', strong)
    monkeypatch.setenv('REDIS_DISABLED', '1')  # force memory backend
    _purge_new_structure_modules()
    ns = import_module('new_structure')
    with pytest.raises(RuntimeError) as exc:
        ns.create_app('production')
    assert 'rate limiting' in str(exc.value).lower() or 'in-memory' in str(exc.value).lower()
    for var in ['FLASK_ENV','SECRET_KEY','REDIS_DISABLED']:
        os.environ.pop(var, None)

def test_fail_fast_memory_backend_allowed_with_override(monkeypatch):
    strong = 'a4f9b2c7d8e1f3a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9'
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', strong)
    monkeypatch.setenv('REDIS_DISABLED', '1')
    monkeypatch.setenv('ALLOW_IN_MEMORY_LIMITS', '1')
    _purge_new_structure_modules()
    ns = import_module('new_structure')
    app = ns.create_app('production')
    assert app is not None
    for var in ['FLASK_ENV','SECRET_KEY','REDIS_DISABLED','ALLOW_IN_MEMORY_LIMITS']:
        os.environ.pop(var, None)

